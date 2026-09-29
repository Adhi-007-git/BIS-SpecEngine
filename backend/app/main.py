"""
SIH26108 - Indian Standards AI Engine FastAPI Backend Application.
"""
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.schemas.dtos import HealthResponse
from backend.app.api.dependencies import get_pipeline
from backend.app.api.routes import (
    search,
    upload,
    recommendations,
    standards,
    evidence,
    graph,
    review,
    standards_management,
    reports,
    validation
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sih26108")

# Create database tables automatically
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
except Exception as e:
    logger.warning(f"Could not auto-create database tables: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers under /api
app.include_router(search.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(standards.router, prefix="/api")
app.include_router(evidence.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(review.router, prefix="/api")
app.include_router(standards_management.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(validation.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """System health check verifying database, vector store, and graph engine connectivity."""
    pipeline = get_pipeline()

    # Check database
    db_ok = True
    try:
        with engine.connect() as conn:
            pass
    except Exception:
        db_ok = False

    # Read live embedding and retrieval mode from the pipeline
    try:
        embedding_mode = pipeline.embedding_service.provider_name
    except Exception:
        embedding_mode = "UNKNOWN"

    try:
        retrieval_mode = pipeline.qdrant_service.retrieval_mode
    except Exception:
        retrieval_mode = "IN_MEMORY"

    return HealthResponse(
        status="healthy",
        project="SIH26108 - Indian Standards Recommendation Engine",
        version="1.0.0",
        qdrant_connected=pipeline.qdrant_service.is_connected(),
        neo4j_connected=pipeline.neo4j_service.is_connected(),
        database_connected=db_ok,
        environment=settings.ENVIRONMENT,
        dev_mode=settings.DEV_MODE,
        embedding_mode=embedding_mode,
        retrieval_mode=retrieval_mode
    )

@app.get("/", tags=["Root"])
def root_status():
    return {
        "project": "SIH26108 Indian Standards AI Recommendation Engine",
        "documentation": "/docs",
        "health": "/api/health",
        "status": "Operational"
    }
