"""
Standards API Route: Official Indian Standard catalogue lookup and related standards inspection.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from backend.app.schemas.dtos import StandardDetailResponse, RelatedStandardItem
from backend.app.api.dependencies import get_pipeline
from ai_engine.pipeline.recommendation_pipeline import RecommendationPipeline

router = APIRouter(prefix="/standards", tags=["Indian Standards Catalogue"])

@router.get("", response_model=List[Dict[str, Any]])
def list_all_standards(pipeline: RecommendationPipeline = Depends(get_pipeline)):
    """Returns a list of all registered Indian Standards in the catalogue for UI selectors."""
    stds = pipeline.search_engine.get_all_standards()
    return [
        {
            "standard_number": s.get("standard_number"),
            "title": s.get("title", ""),
            "status": s.get("status", "Active"),
            "edition": s.get("edition", "")
        }
        for s in stds
    ]

@router.get("/{standard_id}", response_model=StandardDetailResponse)
def get_standard_details(
    standard_id: str,
    pipeline: RecommendationPipeline = Depends(get_pipeline)
):
    """Fetches comprehensive specification details, testing methods, and compliance mandates for a standard."""
    data = pipeline.get_standard_details(standard_id)
    if not data or not data.get("standard"):
        raise HTTPException(status_code=404, detail=f"Indian Standard '{standard_id}' not found in registry.")

    std = data["standard"]
    return StandardDetailResponse(
        standard_number=std.get("standard_number"),
        title=std.get("title"),
        edition=std.get("edition"),
        status=std.get("status"),
        scope=std.get("scope"),
        source=std.get("source"),
        is_demo=std.get("is_demo", True),
        demo_tag=std.get("demo_tag", "DEMO DATA"),
        compliance=data.get("compliance", []),
        normative_references=[
            RelatedStandardItem(**ref) for ref in std.get("normative_references", [])
        ],
        test_methods=[
            RelatedStandardItem(**tm) for tm in std.get("test_methods", [])
        ],
        supersedes=std.get("supersedes")
    )

@router.get("/{standard_id}/related", response_model=List[RelatedStandardItem])
def get_related_standards(
    standard_id: str,
    pipeline: RecommendationPipeline = Depends(get_pipeline)
):
    """Returns normative references, test methods, and superseding standards for the requested standard."""
    std = pipeline.search_engine.get_standard_by_id(standard_id)
    if not std:
        raise HTTPException(status_code=404, detail=f"Standard '{standard_id}' not found.")

    related = pipeline.neo4j_service.get_related_standards(std.get("standard_number"))
    return [RelatedStandardItem(**item) for item in related]
