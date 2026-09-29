"""
Document Ingestion Service: Orchestrates the complete end-to-end document ingestion pipeline:
PDF/TXT -> Parser -> Page Extraction -> Cleaning -> Chunking -> Metadata -> Embedding -> Qdrant.
Preserves page numbers, clauses, and document coordinates for evidence-first retrieval.
"""
from typing import Dict, Any, List, Optional
import uuid
import logging

from ai_engine.documents.pdf_parser import PDFParser
from ai_engine.documents.text_extractor import TextExtractor
from ai_engine.documents.chunker import DocumentChunker
from ai_engine.embeddings.embedding_service import EmbeddingService
from ai_engine.vector_db.qdrant_service import QdrantService

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    """Manages document parsing, chunking, embedding, and vector database insertion."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService,
        chunk_size: int = 350,
        chunk_overlap: int = 50
    ):
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service
        self.pdf_parser = PDFParser()
        self.text_extractor = TextExtractor()
        self.chunker = DocumentChunker(chunk_size=chunk_size, overlap=chunk_overlap)

    def ingest_document(
        self,
        file_bytes: bytes,
        filename: str,
        document_id: Optional[str] = None,
        collection_name: str = "tender_chunks",
        document_type: str = "tender_specification",
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes complete ingestion pipeline:
        1. Page-preserving text extraction
        2. Text cleaning & standard detection
        3. Metadata-rich chunking (retaining page_number and section)
        4. Vector embedding generation
        5. Storage into Qdrant collection
        """
        doc_id = document_id or f"doc_{uuid.uuid4().hex[:8]}"
        doc_source = source or f"Uploaded Tender ({filename})"

        # 1. Page Extraction
        pages = self.pdf_parser.extract_pages(file_bytes, filename=filename)
        if not pages:
            pages = [{"page_number": 1, "text": ""}]

        # 2. Text Cleaning & Detection
        full_text = "\n".join([p["text"] for p in pages])
        text_info = self.text_extractor.process_text(full_text)
        detected_standards = text_info.get("detected_standards", [])

        # 3. Chunking with strict metadata retention
        chunks = self.chunker.chunk_pages(
            pages=pages,
            document_id=doc_id,
            filename=filename,
            source=doc_source,
            document_type=document_type,
            standard_number=detected_standards[0] if detected_standards else None
        )

        # 4. Dense Embedding Generation
        if chunks:
            chunk_texts = [c["content"] for c in chunks]
            vectors = self.embedding_service.embed_batch(chunk_texts)

            # 5. Qdrant Vector Storage
            self.qdrant_service.ensure_collection(
                collection_name=collection_name,
                vector_size=self.embedding_service.dimension
            )

            chunk_records = []
            for c, vec in zip(chunks, vectors):
                rec = dict(c)
                rec["vector"] = vec
                chunk_records.append(rec)

            self.qdrant_service.insert_document_chunks(
                collection_name=collection_name,
                chunk_records=chunk_records
            )
            logger.info(f"Ingested {len(chunks)} chunks from '{filename}' into collection '{collection_name}'.")

        return {
            "document_id": doc_id,
            "filename": filename,
            "source": doc_source,
            "document_type": document_type,
            "pages_extracted": len(pages),
            "total_chunks": len(chunks),
            "vectors_indexed": len(chunks),
            "detected_explicit_standards": detected_standards,
            "retrieval_mode": self.qdrant_service.retrieval_mode,
            "embedding_mode": self.embedding_service.provider_name,
            "chunks": chunks
        }
