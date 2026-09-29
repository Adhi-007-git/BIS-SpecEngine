"""
Standards Management API Routes for SIH26108.
Supports adding standards, updating status, preserving version history,
and updating the semantic search index.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any

from backend.app.schemas.dtos import (
    StandardManageAddRequest,
    StandardManageUpdateRequest,
    VersionHistoryItem
)
from backend.app.api.dependencies import get_database, get_pipeline
from backend.app.models.entities import Standard, StandardVersionHistory
from ai_engine.pipeline.recommendation_pipeline import RecommendationPipeline

router = APIRouter(prefix="/standards/manage", tags=["Engineer Standards Management"])

@router.post("/add", status_code=status.HTTP_201_CREATED)
def add_new_standard(
    request: StandardManageAddRequest,
    pipeline: RecommendationPipeline = Depends(get_pipeline),
    db: Session = Depends(get_database)
):
    """
    Adds a new verified Indian Standard to the catalogue and search index.
    Enforces validation: standard_number and title are mandatory.
    If superseding an existing standard, marks previous version as SUPERSEDED.
    """
    std_num = request.standard_number.strip()
    title = request.title.strip()

    if not std_num or not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="standard_number and title are mandatory fields."
        )

    # Check for existing standard in DB
    existing = db.query(Standard).filter(Standard.standard_number == std_num).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Standard '{std_num}' already exists in registry."
        )

    now = datetime.utcnow()

    # Create standard entity in relational DB
    std_entity = Standard(
        standard_number=std_num,
        title=title,
        edition=request.edition,
        status=request.status or "Active",
        scope=request.scope or "",
        source=request.source or "Bureau of Indian Standards",
        is_demo=False,
        metadata_json={
            "department": request.department,
            "keywords": request.keywords or [],
            "last_verified": request.last_verified or now.strftime("%Y-%m-%d"),
            "amendments": request.amendments or [],
            "normative_references": request.normative_references or [],
            "test_methods": request.test_methods or [],
            "supersedes": request.supersedes,
            "compliance": request.compliance or []
        }
    )
    db.add(std_entity)

    # If this standard supersedes a previous standard, record history & update previous standard
    if request.supersedes:
        prev_num = request.supersedes.strip()
        prev_std = db.query(Standard).filter(Standard.standard_number == prev_num).first()
        if prev_std:
            prev_std.status = "Superseded"

        history_entry = StandardVersionHistory(
            standard_number=prev_num,
            previous_version=prev_num,
            new_version=std_num,
            status="Superseded",
            change_date=now,
            change_type="SUPERSEDED",
            source=request.source or "Bureau of Indian Standards",
            verified_date=now,
            notes=f"Superseded by {std_num}"
        )
        db.add(history_entry)

    # Record version creation entry for the new standard
    new_version_history = StandardVersionHistory(
        standard_number=std_num,
        previous_version=request.supersedes,
        new_version=std_num,
        status=request.status or "Active",
        change_date=now,
        change_type="CREATED",
        source=request.source or "Bureau of Indian Standards",
        verified_date=now,
        notes=f"New standard registered: {title}"
    )
    db.add(new_version_history)
    db.commit()

    # Update in-memory search index immediately
    std_dict = {
        "standard_number": std_num,
        "title": title,
        "edition": request.edition or "",
        "status": request.status or "Active",
        "scope": request.scope or "",
        "keywords": request.keywords or [],
        "source": request.source or "Bureau of Indian Standards",
        "supersedes": request.supersedes,
        "compliance": request.compliance or [],
        "normative_references": request.normative_references or [],
        "test_methods": request.test_methods or []
    }
    pipeline.search_engine.add_or_update_standard(std_dict)

    return {
        "message": f"Standard '{std_num}' successfully added and indexed.",
        "standard_number": std_num,
        "status": request.status or "Active"
    }


@router.put("/{standard_number}")
def update_standard(
    standard_number: str,
    request: StandardManageUpdateRequest,
    pipeline: RecommendationPipeline = Depends(get_pipeline),
    db: Session = Depends(get_database)
):
    """
    Updates an existing standard's title, scope, status, edition, or compliance.
    Preserves version history when status changes to Superseded or Withdrawn.
    """
    std = db.query(Standard).filter(Standard.standard_number == standard_number).first()
    now = datetime.utcnow()

    old_status = std.status if std else "Active"

    if std:
        if request.title:
            std.title = request.title
        if request.edition:
            std.edition = request.edition
        if request.status:
            std.status = request.status
        if request.scope:
            std.scope = request.scope

        meta = std.metadata_json or {}
        if request.department:
            meta["department"] = request.department
        if request.keywords:
            meta["keywords"] = request.keywords
        if request.last_verified:
            meta["last_verified"] = request.last_verified
        if request.supersedes:
            meta["supersedes"] = request.supersedes
        if request.compliance:
            meta["compliance"] = request.compliance

        std.metadata_json = meta
        db.commit()

    # Record status changes in version history if status updated
    if request.status and request.status != old_status:
        v_hist = StandardVersionHistory(
            standard_number=standard_number,
            previous_version=standard_number,
            new_version=request.supersedes or standard_number,
            status=request.status,
            change_date=now,
            change_type="STATUS_CHANGE",
            source="Bureau of Indian Standards",
            verified_date=now,
            notes=f"Status changed from {old_status} to {request.status}"
        )
        db.add(v_hist)
        db.commit()

    # Update search engine index
    cached_std = pipeline.search_engine.get_standard_by_id(standard_number)
    updated_dict = cached_std.copy() if cached_std else {"standard_number": standard_number}
    if request.title:
        updated_dict["title"] = request.title
    if request.status:
        updated_dict["status"] = request.status
    if request.scope:
        updated_dict["scope"] = request.scope
    if request.edition:
        updated_dict["edition"] = request.edition

    pipeline.search_engine.add_or_update_standard(updated_dict)

    return {
        "message": f"Standard '{standard_number}' successfully updated.",
        "standard_number": standard_number,
        "status": request.status or old_status
    }


@router.get("/versions", response_model=List[VersionHistoryItem])
def get_version_history(db: Session = Depends(get_database)):
    """
    Returns the complete version history timeline showing previous and new versions,
    superseded standards, and change dates.
    """
    history = db.query(StandardVersionHistory).order_by(
        StandardVersionHistory.change_date.desc()
    ).all()

    return [
        VersionHistoryItem(
            standard_number=h.standard_number,
            previous_version=h.previous_version,
            new_version=h.new_version,
            status=h.status,
            change_date=h.change_date.strftime("%Y-%m-%d %H:%M:%S") if h.change_date else "",
            change_type=h.change_type,
            source=h.source,
            verified_date=h.verified_date.strftime("%Y-%m-%d") if h.verified_date else "",
            notes=h.notes
        )
        for h in history
    ]


@router.post("/reindex")
def reindex_search_engine(
    pipeline: RecommendationPipeline = Depends(get_pipeline)
):
    """
    Rebuilds the semantic search index across all registered standards.
    """
    pipeline.search_engine.rebuild_index()
    total = len(pipeline.search_engine.get_all_standards())
    return {
        "message": "Search index successfully rebuilt.",
        "total_standards_indexed": total,
        "collection": pipeline.search_engine.COLLECTION_STANDARDS
    }
