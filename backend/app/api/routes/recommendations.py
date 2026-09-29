"""
Recommendations API Route: Document analysis and historic recommendation lookup.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.schemas.dtos import SearchResponse, DocumentAnalyzeRequest
from backend.app.api.dependencies import get_pipeline, get_database
from backend.app.models.entities import Document, DocumentChunk, Recommendation, Evidence
from ai_engine.pipeline.recommendation_pipeline import RecommendationPipeline

router = APIRouter(tags=["Recommendations"])

@router.post("/analyze-document", response_model=SearchResponse)
def analyze_uploaded_document(
    request: DocumentAnalyzeRequest,
    pipeline: RecommendationPipeline = Depends(get_pipeline),
    db: Session = Depends(get_database)
):
    """Executes AI recommendations over the extracted content of a previously uploaded document."""
    doc = db.query(Document).filter(Document.id == request.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{request.document_id}' not found.")

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == request.document_id).order_by(DocumentChunk.page_number).all()
    chunk_dicts = [
        {
            "chunk_id": c.id,
            "document_id": doc.id,
            "filename": doc.filename,
            "page_number": c.page_number,
            "section": c.section,
            "content": c.content
        }
        for c in chunks
    ]

    concatenated_text = " ".join([c.content for c in chunks])
    if len(concatenated_text) > 3500:
        concatenated_text = concatenated_text[:3500]

    query_prompt = f"{request.query_hint or ''} {concatenated_text}".strip()
    results = pipeline.run_query_pipeline(query_prompt, limit=5, document_chunks=chunk_dicts)
    results["document_id"] = doc.id

    # Persist in DB
    try:
        rec_id = results.get("recommendation_id")
        db_rec = Recommendation(
            id=rec_id,
            query_text=f"Document Analysis: {doc.filename}",
            document_id=doc.id,
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
                audit_status="Grounded in Document" if item.get("page") else "Manual Review Required"
            )
            db.add(db_evidence)

        db.commit()
    except Exception:
        db.rollback()

    return results

@router.get("/recommendations/{recommendation_id}", response_model=SearchResponse)
def get_recommendation_by_id(
    recommendation_id: str,
    db: Session = Depends(get_database)
):
    """Fetches recommendation details by ID."""
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Recommendation '{recommendation_id}' not found.")
    return rec.results_json
