"""
Embedding Service with Pluggable Provider Architecture.
Supports real BGE-M3 multilingual embeddings and transparent deterministic development fallback.
Explicitly reports whether real embeddings or demo/fallback embeddings are active.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import hashlib
import math
import logging

# Load .env before any model initialization so HF_HOME is set before
# SentenceTransformer resolves the model cache directory.
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
except ImportError:
    pass

logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(ABC):
    """Abstract interface for dense embedding generation."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Embeds single text string into a dense vector."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embeds batch of texts into dense vectors."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name/identifier of provider (e.g. REAL_BGE_M3, DEMO_FALLBACK)."""
        pass

    @property
    @abstractmethod
    def is_fallback(self) -> bool:
        """True if using synthetic or pseudo-vector fallback."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimension."""
        pass


class BGEM3EmbeddingProvider(BaseEmbeddingProvider):
    """Production BGE-M3 embedding provider using sentence-transformers."""

    _shared_models: Dict[str, Any] = {}

    def __init__(self, model_name: str = "BAAI/bge-m3", dimension: int = 1024):
        self._model_name = model_name
        self._dimension = dimension
        self._model = None
        self._load_model()

    def _load_model(self):
        if self._model_name in BGEM3EmbeddingProvider._shared_models:
            self._model = BGEM3EmbeddingProvider._shared_models[self._model_name]
            return
        try:
            from sentence_transformers import SentenceTransformer
            cache_dir = os.getenv("HF_HOME", r"E:\huggingface_cache")
            self._model = SentenceTransformer(self._model_name, cache_folder=cache_dir)
            BGEM3EmbeddingProvider._shared_models[self._model_name] = self._model
            logger.info(f"Loaded BGE-M3 embedding model: {self._model_name} (cache: {cache_dir})")
        except Exception as e:
            self._model = None
            logger.warning(f"Could not load SentenceTransformer ({e}). Falling back to development provider.")

    def is_available(self) -> bool:
        return self._model is not None

    def embed_text(self, text: str) -> List[float]:
        if self._model is None:
            raise RuntimeError("BGE-M3 model is not initialized.")
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if self._model is None:
            raise RuntimeError("BGE-M3 model is not initialized.")
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()

    @property
    def provider_name(self) -> str:
        return "REAL_BGE_M3"

    @property
    def is_fallback(self) -> bool:
        return False

    @property
    def dimension(self) -> int:
        return self._dimension


class DevelopmentFallbackEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic token-hash unit-vector embedding provider for zero-dependency development."""

    def __init__(self, dimension: int = 1024):
        self._dimension = dimension

    def embed_text(self, text: str) -> List[float]:
        tokens = text.lower().split()
        vec = [0.0] * self._dimension

        for idx, token in enumerate(tokens):
            h = int(hashlib.sha256(token.encode('utf-8')).hexdigest(), 16)
            pos = h % self._dimension
            weight = 1.0 / (1.0 + (idx * 0.05))
            vec[pos] += weight

        # Normalize to unit length
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            return [x / norm for x in vec]
        vec[0] = 1.0
        return vec

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]

    @property
    def provider_name(self) -> str:
        return "DEMO_FALLBACK"

    @property
    def is_fallback(self) -> bool:
        return True

    @property
    def dimension(self) -> int:
        return self._dimension


class EmbeddingService:
    """Configurable embedding coordinator supporting production and fallback providers."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        dimension: int = 1024,
        force_provider: Optional[str] = None
    ):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
        self._dimension = dimension
        
        provider_preference = force_provider or os.getenv("EMBEDDING_PROVIDER", "auto").lower()
        self._active_provider: BaseEmbeddingProvider

        if provider_preference in ("bge-m3", "real", "production"):
            real_provider = BGEM3EmbeddingProvider(self.model_name, self._dimension)
            if real_provider.is_available():
                self._active_provider = real_provider
            else:
                logger.warning("Requested REAL_BGE_M3 but dependencies missing. Using DEMO_FALLBACK.")
                self._active_provider = DevelopmentFallbackEmbeddingProvider(self._dimension)
        elif provider_preference in ("fallback", "dev", "mock"):
            self._active_provider = DevelopmentFallbackEmbeddingProvider(self._dimension)
        else: # "auto"
            real_provider = BGEM3EmbeddingProvider(self.model_name, self._dimension)
            if real_provider.is_available():
                self._active_provider = real_provider
            else:
                self._active_provider = DevelopmentFallbackEmbeddingProvider(self._dimension)

        logger.info(f"EmbeddingService initialized with provider: {self.provider_name} (Fallback: {self.is_fallback})")

    def embed_text(self, text: str) -> List[float]:
        return self._active_provider.embed_text(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return self._active_provider.embed_batch(texts)

    @property
    def provider_name(self) -> str:
        return self._active_provider.provider_name

    @property
    def is_fallback(self) -> bool:
        return self._active_provider.is_fallback

    @property
    def dimension(self) -> int:
        return self._active_provider.dimension

    def get_mode_info(self) -> Dict[str, Any]:
        """Returns diagnostic metadata about current embedding engine."""
        return {
            "embedding_mode": self.provider_name,
            "is_fallback": self.is_fallback,
            "dimension": self.dimension,
            "model_name": self.model_name if not self.is_fallback else "deterministic_hash_fallback"
        }
