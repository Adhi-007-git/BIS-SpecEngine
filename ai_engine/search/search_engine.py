"""
Search Engine: Retrieves candidate Indian Standards and evidence passages
using dense semantic search over chunk-level indices with metadata preservation.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import logging

from ai_engine.embeddings.embedding_service import EmbeddingService
from ai_engine.vector_db.qdrant_service import QdrantService

logger = logging.getLogger(__name__)

class SearchEngine:
    """Manages standards and chunk indexing, semantic retrieval, and metadata aggregation."""

    COLLECTION_STANDARDS = "indian_standards"
    COLLECTION_CHUNKS = "tender_chunks"

    def __init__(self, embedding_service: EmbeddingService, qdrant_service: QdrantService):
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service
        self._standards_cache: Dict[str, Dict[str, Any]] = {}
        self._ensure_index()

    def _ensure_index(self):
        """Loads seed standards and chunk-level evidence into the search index."""
        from ai_engine.ingestion.manual_json_connector import ManualJsonConnector
        connector = ManualJsonConnector()
        standards = connector.fetch_standards()
        if not standards:
            return

        try:


            self.qdrant_service.ensure_collection(self.COLLECTION_STANDARDS, vector_size=self.embedding_service.dimension)
            self.qdrant_service.ensure_collection(self.COLLECTION_CHUNKS, vector_size=self.embedding_service.dimension)
            points = []

            for idx, std in enumerate(standards, start=1):
                std_num = std.get("standard_number")
                self._standards_cache[std_num] = std
                
                # Compose rich semantic representation for standards catalogue
                corpus_text = f"{std.get('standard_number')} {std.get('title')} {std.get('scope')} {' '.join(std.get('keywords', []))}"
                vector = self.embedding_service.embed_text(corpus_text)

                # Standard-level payload
                ev_sample = std.get("evidence_sample", {})
                payload = {
                    "standard_number": std_num,
                    "title": std.get("title", ""),
                    "edition": std.get("edition", ""),
                    "status": std.get("status", "Active"),
                    "scope": std.get("scope", ""),
                    "source": std.get("source", "Bureau of Indian Standards"),
                    "keywords": std.get("keywords", []),
                    "page": ev_sample.get("page", 1),
                    "page_number": ev_sample.get("page", 1),
                    "section": ev_sample.get("section", "General"),
                    "evidence_text": ev_sample.get("text", ""),
                    "evidence_sample": ev_sample,
                    "is_demo": std.get("is_demo", True),
                    "demo_tag": std.get("demo_tag", "DEMO DATA"),
                    "compliance": std.get("compliance", []),
                    "normative_references": std.get("normative_references", []),
                    "test_methods": std.get("test_methods", []),
                    "supersedes": std.get("supersedes")
                }

                points.append({
                    "id": f"std_{idx}",
                    "vector": vector,
                    "payload": payload
                })

            self.qdrant_service.upsert_points(self.COLLECTION_STANDARDS, points)
            logger.info(f"Indexed {len(points)} Indian Standards into SearchEngine collection '{self.COLLECTION_STANDARDS}'.")
        except Exception as e:
            logger.error(f"Error loading standards index: {e}")

    def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves top candidate standards for a query with similarity scores and chunk evidence."""
        query_vec = self.embedding_service.embed_text(query)
        hits = self.qdrant_service.search(self.COLLECTION_STANDARDS, query_vec, limit=limit)
        return hits

    def retrieve_chunks(self, query: str, collection_name: str = "tender_chunks", limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves top granular document chunks with page numbers and clause locations."""
        query_vec = self.embedding_service.embed_text(query)
        hits = self.qdrant_service.search(collection_name, query_vec, limit=limit)
        return hits

    def get_standard_by_id(self, standard_id: str) -> Dict[str, Any]:
        """Looks up cached standard by exact or partial standard code."""
        cleaned = standard_id.replace("-", " ").replace("_", " ").strip().lower()
        for key, val in self._standards_cache.items():
            if cleaned in key.lower() or key.lower() in cleaned:
                return val
        return {}

    def get_all_standards(self) -> List[Dict[str, Any]]:
        """Returns all registered standards."""
        return list(self._standards_cache.values())

    def add_or_update_standard(self, std: Dict[str, Any]):
        """Adds or updates a standard in the cache and vector search index."""
        std_num = std.get("standard_number")
        if not std_num:
            return

        self._standards_cache[std_num] = std
        corpus_text = f"{std.get('standard_number')} {std.get('title')} {std.get('scope', '')} {' '.join(std.get('keywords', []))}"
        vector = self.embedding_service.embed_text(corpus_text)

        payload = {
            "standard_number": std_num,
            "title": std.get("title", ""),
            "edition": std.get("edition", ""),
            "status": std.get("status", "Active"),
            "scope": std.get("scope", ""),
            "source": std.get("source", "Bureau of Indian Standards"),
            "keywords": std.get("keywords", []),
            "page": 1,
            "section": "Scope",
            "evidence_text": std.get("scope", "Authoritative BIS standard specification."),
            "is_demo": False,
            "demo_tag": "VERIFIED SOURCE",
            "compliance": std.get("compliance", []),
            "normative_references": std.get("normative_references", []),
            "test_methods": std.get("test_methods", []),
            "supersedes": std.get("supersedes")
        }

        point_id = f"std_custom_{abs(hash(std_num)) % 1000000}"
        self.qdrant_service.upsert_points(self.COLLECTION_STANDARDS, [{
            "id": point_id,
            "vector": vector,
            "payload": payload
        }])
        logger.info(f"Upserted standard '{std_num}' into SearchEngine collection '{self.COLLECTION_STANDARDS}'.")

    def rebuild_index(self):
        """Re-initializes the standards collection and re-indexes all cached standards."""
        self._ensure_index()
        logger.info(f"Rebuilt SearchEngine index. Total standards: {len(self._standards_cache)}")

