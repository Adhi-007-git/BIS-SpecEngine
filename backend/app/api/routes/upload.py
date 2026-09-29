"""
Upload API Route: Accepts tender PDF documents and technical specifications,
performing page-preserving text extraction, chunk indexing via DocumentIngestionService,
and optional Qdrant vector storage. Falls back gracefully to IN_MEMORY mode.
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
import logging

from backend.app.schemas.dtos import UploadResponse
from backend.app.api.dependencies import get_pipeline, get_database
from backend.app.models.entities import Document, DocumentChunk
from ai_engine.pipeline.recommendation_pipeline import RecommendationPipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["Document Ingestion"])


@router.post("", response_model=UploadResponse)
async def upload_tender_document(
    file: UploadFile = File(...),
    pipeline: RecommendationPipeline = Depends(get_pipeline),
    db: Session = Depends(get_database)
):
    """
    Uploads a tender PDF or TXT specification, extracts text per page,
    chunks with provenance metadata, optionally indexes into Qdrant,
    and persists Document + DocumentChunk records.
    """
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT specification files are currently supported."
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    doc_id = f"doc_{uuid.uuid4().hex[:8]}"

    # ── Save Raw File ────────────────────────────────────────────────────────────
    raw_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file_path = raw_dir / f"{doc_id}_{file.filename}"
    with open(raw_file_path, "wb") as f:
        f.write(content)

    # ── Full Ingestion via DocumentIngestionService ─────────────────────────────
    # Handles: extraction → chunking → embedding → Qdrant (or IN_MEMORY fallback)
    retrieval_mode = "IN_MEMORY"
    embedding_mode = "DEMO_FALLBACK"
    pages_extracted = 0
    total_chunks = 0
    detected_explicit_standards: list = []

    try:
        ingestion_service = getattr(pipeline, "ingestion_service", None)
        if ingestion_service is not None:
            ingest_result = ingestion_service.ingest_document(
                file_bytes=content,
                filename=file.filename,
                document_id=doc_id
            )
            pages_extracted = ingest_result.get("pages_extracted", 0)
            total_chunks = ingest_result.get("total_chunks", 0)
            detected_explicit_standards = ingest_result.get("detected_explicit_standards", [])
            retrieval_mode = ingest_result.get("retrieval_mode", "IN_MEMORY")
            embedding_mode = ingest_result.get("embedding_mode", "DEMO_FALLBACK")
            chunks = ingest_result.get("chunks", [])
            logger.info(
                "Document %s indexed: %d chunks across %d pages. "
                "retrieval=%s, embedding=%s",
                doc_id, total_chunks, pages_extracted, retrieval_mode, embedding_mode
            )
        else:
            # Fallback: manual extraction if ingestion service not wired
            logger.warning("ingestion_service not found on pipeline — using direct extraction fallback.")
            pages = pipeline.pdf_parser.extract_pages(content, filename=file.filename)
            full_text = "\n".join([p["text"] for p in pages])
            text_info = pipeline.text_extractor.process_text(full_text)
            chunks = pipeline.chunker.chunk_pages(pages, document_id=doc_id)
            pages_extracted = len(pages)
            total_chunks = len(chunks)
            detected_explicit_standards = text_info.get("detected_standards", [])

    except Exception as exc:
        logger.error("Ingestion failed for %s: %s", doc_id, exc, exc_info=True)
        # Non-fatal — return partial result
        pages_extracted = pages_extracted or 0
        total_chunks = total_chunks or 0
        chunks = []

    # ── Persist Document + Chunks in DB ─────────────────────────────────────────
    try:
        db_doc = Document(
            id=doc_id,
            filename=file.filename,
            file_type=file.content_type or "application/pdf",
            total_pages=pages_extracted,
            file_size_bytes=len(content)
        )
        db.add(db_doc)

        for c in (chunks or []):
            db_chunk = DocumentChunk(
                id=c["chunk_id"],
                document_id=doc_id,
                page_number=c.get("page") or c.get("page_number", 1),
                section=c.get("section", ""),
                content=c["content"]
            )
            db.add(db_chunk)

        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("DB persistence failed for %s (non-fatal): %s", doc_id, exc)

    return UploadResponse(
        document_id=doc_id,
        filename=file.filename,
        file_size=len(content),
        pages_extracted=pages_extracted,
        total_chunks=total_chunks,
        detected_explicit_standards=detected_explicit_standards,
        retrieval_mode=retrieval_mode,
        embedding_mode=embedding_mode,
        message=(
            f"Document processed and indexed: {total_chunks} chunks across "
            f"{pages_extracted} pages. Retrieval mode: {retrieval_mode}."
        )
    )
