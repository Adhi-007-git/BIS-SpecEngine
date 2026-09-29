"""
Search API Route: Accepts natural-language procurement queries and returns
ranked Indian Standard recommendations with verified evidence and compliance tags.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from backend.app.schemas.dtos import SearchRequest, SearchResponse
from backend.app.api.dependencies import get_pipeline, get_database
from backend.app.models.entities import Recommendation, Evidence
from ai_engine.pipeline.recommendation_pipeline import RecommendationPipeline

router = APIRouter(prefix="/search", tags=["Search & Recommendations"])

@router.post("", response_model=SearchResponse)
def search_applicable_standards(
    request: SearchRequest,
    pipeline: RecommendationPipeline = Depends(get_pipeline),
    db: Session = Depends(get_database)
):
    """Executes the AI recommendation pipeline for a natural language procurement specification."""
    if not request.query or len(request.query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    results = pipeline.run_query_pipeline(request.query, limit=request.limit or 5)

    # Check for verified engineer knowledge memory match (Phase 4/6)
    try:
        from backend.app.services.query_memory import QueryMemoryService
        mem_service = QueryMemoryService()
        memory_match = mem_service.find_memory_match(request.query)
        if memory_match:
            results["verified_memory"] = memory_match
    except Exception as mem_err:
        pass

    # Persist recommendation history and evidence in database
    try:
        rec_id = results.get("recommendation_id")
        db_rec = Recommendation(
            id=rec_id,
            query_text=request.query,
            results_json=results
        )
        db.add(db_rec)

        # Store individual evidence audit entries
        for item in results.get("recommendations", []):
            db_evidence = Evidence(
                recommendation_id=rec_id,
                standard_number=item.get("standard_number"),
                evidence_text=item.get("evidence", "Insufficient evidence"),
                page_number=item.get("page"),
                section_name=item.get("section"),
                confidence_score=item.get("relevance_score", 0.5),
                audit_status="Grounded in Source" if item.get("page") else "Audit Pending"
            )
            db.add(db_evidence)

        db.commit()
    except Exception:
        db.rollback() # Don't fail the user request if history caching has an issue

    return results
