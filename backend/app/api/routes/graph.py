"""
Knowledge Graph API Route: Provides node-edge structures for React Flow visualization.
"""
from fastapi import APIRouter, Depends, HTTPException

from backend.app.schemas.dtos import GraphResponse, GraphNode, GraphEdge
from backend.app.api.dependencies import get_pipeline
from ai_engine.pipeline.recommendation_pipeline import RecommendationPipeline

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])

@router.get("/{standard_id}", response_model=GraphResponse)
def get_standard_graph(
    standard_id: str,
    pipeline: RecommendationPipeline = Depends(get_pipeline)
):
    """Returns React Flow nodes and edges mapping primary standards, testing methods,
    normative references, and QCO regulations."""
    details = pipeline.get_standard_details(standard_id)
    if not details or not details.get("graph"):
        raise HTTPException(status_code=404, detail=f"Knowledge graph for '{standard_id}' not found.")

    graph_data = details["graph"]
    return GraphResponse(
        standard_number=standard_id,
        nodes=[GraphNode(**n) for n in graph_data.get("nodes", [])],
        edges=[GraphEdge(**e) for e in graph_data.get("edges", [])],
        total_nodes=graph_data.get("total_nodes", 0),
        total_edges=graph_data.get("total_edges", 0)
    )
