"""
Engineer Review API Routes for SIH26108.
Supports APPROVE, MODIFY, REJECT workflows with persistent audit history.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import uuid

from backend.app.schemas.dtos import (
    ReviewApproveRequest,
    ReviewModifyRequest,
    ReviewRejectRequest,
    ReviewActionResponse,
    VerifiedAnswerDTO
)
from backend.app.api.dependencies import get_database
from backend.app.models.entities import Recommendation, VerifiedAnswer, ReviewRecord
from backend.app.services.query_memory import QueryMemoryService

router = APIRouter(prefix="/review", tags=["Engineer Review & Verified Knowledge"])
memory_service = QueryMemoryService()

@router.post("/{recommendation_id}/approve", response_model=ReviewActionResponse)
def approve_recommendation(
    recommendation_id: str,
    request: ReviewApproveRequest,
    db: Session = Depends(get_database)
):
    """
    Marks a recommendation as APPROVED by an engineer.
    Saves final verified answer to the persistent knowledge database.
    """
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    
    # Extract query text and primary standard from recommendation or defaults
    query_text = rec.query_text if rec else f"Session query for {recommendation_id}"
    results_json = rec.results_json if rec else {}
    recs_list = results_json.get("recommendations", [])
    primary_std = recs_list[0].get("standard_number", "IS 1786:2008") if recs_list else "IS 1786:2008"
    related_stds = [r.get("standard_number") for r in recs_list[1:]] if len(recs_list) > 1 else []
    evidence = recs_list[0].get("evidence") if recs_list else "Grounded in Source"
    compliance = recs_list[0].get("compliance", []) if recs_list else []
    extracted_reqs = results_json.get("query_analysis", {}).get("structured_requirements")

    now = datetime.utcnow()
    norm_query = QueryMemoryService.normalize_query(query_text)

    # Check for existing verified answer
    va = db.query(VerifiedAnswer).filter(VerifiedAnswer.recommendation_id == recommendation_id).first()
    if not va:
        va = VerifiedAnswer(
            id=f"va_{uuid.uuid4().hex[:8]}",
            recommendation_id=recommendation_id,
            original_query=query_text,
            normalized_query=norm_query,
            extracted_requirements=extracted_reqs,
            primary_standard=primary_std,
            related_standards=related_stds,
            compliance_result=compliance,
            evidence=evidence,
            engineer_status="APPROVED",
            engineer_comment=request.comment or "Approved without modification",
            verified_at=now,
            dataset_version="v1.0-real-21",
            original_ai_recommendation=results_json
        )
        db.add(va)
    else:
        va.engineer_status = "APPROVED"
        va.engineer_comment = request.comment or va.engineer_comment
        va.verified_at = now

    # Append immutable review audit record
    audit = ReviewRecord(
        recommendation_id=recommendation_id,
        action="APPROVED",
        engineer_comment=request.comment or "Approved by engineer",
        modifications=None,
        timestamp=now
    )
    db.add(audit)
    db.commit()

    return ReviewActionResponse(
        recommendation_id=recommendation_id,
        action="APPROVED",
        status="APPROVED",
        message=f"Recommendation '{recommendation_id}' approved and committed to verified knowledge.",
        timestamp=now.isoformat()
    )


@router.post("/{recommendation_id}/modify", response_model=ReviewActionResponse)
def modify_recommendation(
    recommendation_id: str,
    request: ReviewModifyRequest,
    db: Session = Depends(get_database)
):
    """
    Allows engineer to modify primary and related standards.
    Preserves original AI recommendation in audit history and saves final verified answer.
    """
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    query_text = rec.query_text if rec else f"Session query for {recommendation_id}"
    results_json = rec.results_json if rec else {}
    extracted_reqs = results_json.get("query_analysis", {}).get("structured_requirements")

    now = datetime.utcnow()
    norm_query = QueryMemoryService.normalize_query(query_text)

    va = db.query(VerifiedAnswer).filter(VerifiedAnswer.recommendation_id == recommendation_id).first()
    if not va:
        va = VerifiedAnswer(
            id=f"va_{uuid.uuid4().hex[:8]}",
            recommendation_id=recommendation_id,
            original_query=query_text,
            normalized_query=norm_query,
            extracted_requirements=extracted_reqs,
            primary_standard=request.primary_standard,
            related_standards=request.related_standards or [],
            compliance_result=[],
            evidence={"modification_note": "Adjusted by technical engineer review"},
            engineer_status="MODIFIED",
            engineer_comment=request.comment or "Modified by engineer",
            verified_at=now,
            dataset_version="v1.0-real-21",
            original_ai_recommendation=results_json
        )
        db.add(va)
    else:
        va.primary_standard = request.primary_standard
        va.related_standards = request.related_standards or va.related_standards
        va.engineer_status = "MODIFIED"
        va.engineer_comment = request.comment or va.engineer_comment
        va.verified_at = now
        if not va.original_ai_recommendation and results_json:
            va.original_ai_recommendation = results_json

    audit = ReviewRecord(
        recommendation_id=recommendation_id,
        action="MODIFIED",
        engineer_comment=request.comment or "Modified by engineer",
        modifications={
            "primary_standard": request.primary_standard,
            "related_standards": request.related_standards,
            "extra": request.modifications
        },
        timestamp=now
    )
    db.add(audit)
    db.commit()

    return ReviewActionResponse(
        recommendation_id=recommendation_id,
        action="MODIFIED",
        status="MODIFIED",
        message=f"Recommendation '{recommendation_id}' modified and saved with primary standard {request.primary_standard}.",
        timestamp=now.isoformat()
    )


@router.post("/{recommendation_id}/reject", response_model=ReviewActionResponse)
def reject_recommendation(
    recommendation_id: str,
    request: ReviewRejectRequest,
    db: Session = Depends(get_database)
):
    """
    Marks a recommendation as REJECTED.
    Stores engineer rejection comment and ensures answer is NOT returned as approved knowledge.
    """
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    now = datetime.utcnow()

    va = db.query(VerifiedAnswer).filter(VerifiedAnswer.recommendation_id == recommendation_id).first()
    if va:
        va.engineer_status = "REJECTED"
        va.engineer_comment = request.comment
        va.verified_at = now
    else:
        # Create non-approved rejection record so audit is preserved
        query_text = rec.query_text if rec else f"Session {recommendation_id}"
        va = VerifiedAnswer(
            id=f"va_{uuid.uuid4().hex[:8]}",
            recommendation_id=recommendation_id,
            original_query=query_text,
            normalized_query=QueryMemoryService.normalize_query(query_text),
            primary_standard="NONE",
            engineer_status="REJECTED",
            engineer_comment=request.comment,
            verified_at=now,
            dataset_version="v1.0-real-21"
        )
        db.add(va)

    audit = ReviewRecord(
        recommendation_id=recommendation_id,
        action="REJECTED",
        engineer_comment=request.comment,
        modifications=None,
        timestamp=now
    )
    db.add(audit)
    db.commit()

    return ReviewActionResponse(
        recommendation_id=recommendation_id,
        action="REJECTED",
        status="REJECTED",
        message=f"Recommendation '{recommendation_id}' rejected. Excluded from approved knowledge memory.",
        timestamp=now.isoformat()
    )


@router.get("/knowledge", response_model=List[VerifiedAnswerDTO])
def get_verified_knowledge(
    status_filter: Optional[str] = Query(None, description="Filter by APPROVED, MODIFIED, or all"),
    db: Session = Depends(get_database)
):
    """
    Returns list of verified answers with live status verification for the Engineer Knowledge page.
    """
    query = db.query(VerifiedAnswer)
    if status_filter:
        query = query.filter(VerifiedAnswer.engineer_status == status_filter.upper())
    else:
        query = query.filter(VerifiedAnswer.engineer_status.in_(["APPROVED", "MODIFIED"]))

    records = query.order_by(VerifiedAnswer.created_at.desc()).all()
    results = []

    for r in records:
        status_check = memory_service.verify_current_status(r.primary_standard, db=db)
        results.append(
            VerifiedAnswerDTO(
                id=r.id,
                recommendation_id=r.recommendation_id,
                original_query=r.original_query,
                primary_standard=r.primary_standard,
                related_standards=r.related_standards,
                engineer_status=r.engineer_status,
                engineer_comment=r.engineer_comment,
                verified_at=r.verified_at.isoformat() if r.verified_at else None,
                dataset_version=r.dataset_version,
                current_status=status_check.get("status", "Active"),
                is_superseded=status_check.get("is_superseded", False)
            )
        )

    return results


@router.get("/history/{recommendation_id}")
def get_review_history(
    recommendation_id: str,
    db: Session = Depends(get_database)
):
    """Fetches the sequential review audit history for a recommendation session."""
    history = db.query(ReviewRecord).filter(
        ReviewRecord.recommendation_id == recommendation_id
    ).order_by(ReviewRecord.timestamp.asc()).all()

    return [
        {
            "id": h.id,
            "action": h.action,
            "engineer_comment": h.engineer_comment,
            "modifications": h.modifications,
            "timestamp": h.timestamp.isoformat() if h.timestamp else None
        }
        for h in history
    ]
