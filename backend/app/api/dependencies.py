"""
FastAPI dependency providers for Database and AI Pipeline singleton.
"""
from typing import Generator
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.core.config import settings
from ai_engine.pipeline.recommendation_pipeline import RecommendationPipeline

_pipeline_instance: RecommendationPipeline = None

def get_pipeline() -> RecommendationPipeline:
    """Provides a singleton instance of the AI Recommendation Pipeline."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RecommendationPipeline(
            qdrant_url=settings.QDRANT_URL,
            neo4j_uri=settings.NEO4J_URI,
            neo4j_user=settings.NEO4J_USER,
            neo4j_password=settings.NEO4J_PASSWORD
        )
    return _pipeline_instance

def get_database() -> Generator[Session, None, None]:
    """Provides an active database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

_validator_instance = None

def get_tender_validator():
    """Provides a singleton instance of the TenderValidator."""
    global _validator_instance
    if _validator_instance is None:
        from ai_engine.validation.tender_validator import TenderValidator
        _validator_instance = TenderValidator()
    return _validator_instance
