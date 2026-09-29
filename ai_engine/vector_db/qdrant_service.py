"""
Qdrant Vector Database Service: Connects to Qdrant cluster for semantic indexing and search.
Supports document chunk vector insertion, payload metadata preservation (pages, sections, sources),
and transparent in-memory cosine-similarity fallback for zero-dependency development.
"""
from typing import List, Dict, Any, Optional
import math
import logging

logger = logging.getLogger(__name__)

class QdrantService:
    """Manages vector collections, chunk vector upserts, and cosine similarity search."""

    def __init__(self, url: str = "http://localhost:6333", api_key: Optional[str] = None):
        self.url = url
        self.api_key = api_key
        self.client = None
        self._memory_store: Dict[str, List[Dict[str, Any]]] = {}
        self._is_live = False
        self._init_client()

    def _init_client(self):
        """Attempts connection to live Qdrant instance."""
        try:
            from qdrant_client import QdrantClient
            self.client = QdrantClient(url=self.url, api_key=self.api_key or None, timeout=2.0)
            # Ping
            self.client.get_collections()
            self._is_live = True
            logger.info(f"Connected to live Qdrant cluster at {self.url}")
        except Exception as e:
            self.client = None
            self._is_live = False
            logger.warning(f"Qdrant not reachable at {self.url} ({e}). Using in-memory fallback store.")

    @property
    def retrieval_mode(self) -> str:
        """Explicitly reports retrieval mode for traceability."""
        return "QDRANT" if self._is_live else "IN_MEMORY"

    def is_connected(self) -> bool:
        return self._is_live

    def get_mode_info(self) -> Dict[str, Any]:
        """Returns diagnostic metadata about retrieval store."""
        return {
            "retrieval_mode": self.retrieval_mode,
            "is_live": self._is_live,
            "qdrant_url": self.url if self._is_live else None,
            "collections_in_memory": list(self._memory_store.keys())
        }

    def ensure_collection(self, collection_name: str, vector_size: int = 1024):
        """Creates collection if not present."""
        if self._is_live and self.client:
            try:
                from qdrant_client.models import Distance, VectorParams
                collections = [c.name for c in self.client.get_collections().collections]
                if collection_name not in collections:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                    )
            except Exception as e:
                logger.error(f"Error ensuring Qdrant collection: {e}")
        else:
            if collection_name not in self._memory_store:
                self._memory_store[collection_name] = []

    def upsert_points(self, collection_name: str, points: List[Dict[str, Any]]):
        """
        Points format: list of:
        {
            'id': int/str,
            'vector': List[float],
            'payload': {
                'document_id': str,
                'filename': str,
                'page_number': int,
                'section': str,
                'chunk_id': str,
                'source': str,
                'document_type': str,
                'standard_number': Optional[str],
                'text': str,
                ...
            }
        }
        """
        if not points:
            return

        if self._is_live and self.client:
            try:
                from qdrant_client.models import PointStruct
                qdrant_points = [
                    PointStruct(
                        id=p["id"],
                        vector=p["vector"],
                        payload=p.get("payload", {})
                    )
                    for p in points
                ]
                self.client.upsert(collection_name=collection_name, points=qdrant_points)
                return
            except Exception as e:
                logger.error(f"Failed to upsert to Qdrant: {e}. Falling back to in-memory store.")

        # Fallback to in-memory store
        self.ensure_collection(collection_name)
        existing_ids = {str(p["id"]): idx for idx, p in enumerate(self._memory_store[collection_name])}
        for p in points:
            pid = str(p["id"])
            if pid in existing_ids:
                self._memory_store[collection_name][existing_ids[pid]] = p
            else:
                self._memory_store[collection_name].append(p)

    def insert_document_chunks(self, collection_name: str, chunk_records: List[Dict[str, Any]]):
        """Convenience method to insert chunk vectors with preserved metadata."""
        points = []
        for c in chunk_records:
            points.append({
                "id": c.get("chunk_id") or c.get("id"),
                "vector": c["vector"],
                "payload": {
                    "document_id": c.get("document_id", "unknown_doc"),
                    "filename": c.get("filename", "document.pdf"),
                    "page_number": c.get("page_number", c.get("page", 1)),
                    "section": c.get("section", "General Section"),
                    "chunk_id": c.get("chunk_id", "chunk_1"),
                    "source": c.get("source", "Uploaded Document"),
                    "document_type": c.get("document_type", "tender_specification"),
                    "standard_number": c.get("standard_number"),
                    "text": c.get("text", c.get("content", ""))
                }
            })
        self.upsert_points(collection_name, points)

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        standard_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns top matches with score and preserved metadata payload."""
        if self._is_live and self.client:
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                query_filter = None
                if standard_filter:
                    query_filter = Filter(
                        must=[
                            FieldCondition(
                                key="standard_number",
                                match=MatchValue(value=standard_filter)
                            )
                        ]
                    )

                results = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=limit
                )
                return [
                    {
                        "id": hit.id,
                        "score": round(hit.score, 4),
                        "payload": hit.payload
                    }
                    for hit in results
                ]
            except Exception as e:
                logger.error(f"Qdrant search error: {e}. Falling back to in-memory similarity.")

        # In-memory cosine search fallback
        self.ensure_collection(collection_name)
        candidates = self._memory_store.get(collection_name, [])
        if not candidates:
            return []

        def cosine_similarity(v1: List[float], v2: List[float]) -> float:
            dot = sum(a * b for a, b in zip(v1, v2))
            mag1 = math.sqrt(sum(a * a for a in v1)) or 1.0
            mag2 = math.sqrt(sum(b * b for b in v2)) or 1.0
            return dot / (mag1 * mag2)

        scored = []
        for item in candidates:
            payload = item.get("payload", {})
            if standard_filter and payload.get("standard_number") != standard_filter:
                continue

            score = cosine_similarity(query_vector, item["vector"])
            scored.append({
                "id": item["id"],
                "score": round(score, 4),
                "payload": payload
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def count_points(self, collection_name: str) -> int:
        """Returns total vectors stored in collection."""
        if self._is_live and self.client:
            try:
                res = self.client.count(collection_name=collection_name)
                return res.count
            except Exception:
                pass
        return len(self._memory_store.get(collection_name, []))
