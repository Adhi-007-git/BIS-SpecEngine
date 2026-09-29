"""
Evidence API Route: Provides grounded evidence audit trail with exact page and section citations.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.schemas.dtos import EvidenceResponse
from backend.app.api.dependencies import get_database, get_pipeline
from backend.app.models.entities import Evidence, Recommendation
from ai_engine.pipeline.recommendation_pipeline import RecommendationPipeline

router = APIRouter(prefix="/evidence", tags=["Evidence & Provenance"])

@router.get("/{recommendation_id}", response_model=List[EvidenceResponse])
def get_evidence_for_recommendation(
    recommendation_id: str,
    db: Session = Depends(get_database),
    pipeline: RecommendationPipeline = Depends(get_pipeline)
):
    """Retrieves grounded evidence items, page citations, and audit status for a recommendation."""
    # First check database records
    evidences = db.query(Evidence).filter(Evidence.recommendation_id == recommendation_id).all()
    if evidences:
        return [
            EvidenceResponse(
                recommendation_id=e.recommendation_id,
                standard_number=e.standard_number,
                evidence_text=e.evidence_text,
                page=e.page_number,
                section=e.section_name,
                confidence=e.confidence_score,
                audit_status=e.audit_status
            )
            for e in evidences
        ]

    # Fallback to recommendation payload if DB write was bypassed in lightweight testing
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if rec and rec.results_json:
        items = rec.results_json.get("recommendations", [])
        return [
            EvidenceResponse(
                recommendation_id=recommendation_id,
                standard_number=it.get("standard_number"),
                evidence_text=it.get("evidence", "Insufficient evidence"),
                page=it.get("page"),
                section=it.get("section"),
                confidence=it.get("relevance_score", 0.8),
                audit_status="Grounded in Source" if it.get("page") else "Audit Pending"
            )
            for it in items
        ]

    raise HTTPException(status_code=404, detail=f"No evidence found for recommendation '{recommendation_id}'.")
