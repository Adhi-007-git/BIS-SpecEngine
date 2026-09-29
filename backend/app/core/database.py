"""
Database session and connection management.
Supports PostgreSQL for production with automated SQLite dev fallback.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import logging
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
connect_args = {}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
except Exception as e:
    logger.warning(f"Failed to connect to primary DB ({e}). Falling back to local SQLite.")
    db_url = "sqlite:///./sih_standards_dev.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency that yields an active database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
