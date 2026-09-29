"""
SQLAlchemy ORM models for SIH26108:
User, Document, DocumentChunk, Standard, Recommendation, Evidence, ComplianceRequirement.
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    department = Column(String(150), default="Public Procurement")
    created_at = Column(DateTime, default=datetime.utcnow)

    recommendations = relationship("Recommendation", back_populates="user")
    documents = relationship("Document", back_populates="uploader")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(50), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), default="application/pdf")
    total_pages = Column(Integer, default=1)
    file_size_bytes = Column(Integer, default=0)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    uploader = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(100), primary_key=True, index=True)
    document_id = Column(String(50), ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    section = Column(String(150), nullable=True)
    content = Column(Text, nullable=False)
    qdrant_point_id = Column(String(100), nullable=True)

    document = relationship("Document", back_populates="chunks")


class Standard(Base):
    __tablename__ = "standards"

    id = Column(Integer, primary_key=True, index=True)
    standard_number = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    edition = Column(String(100), nullable=True)
    status = Column(String(50), default="Active")
    scope = Column(Text, nullable=False)
    source = Column(String(255), default="Bureau of Indian Standards")
    is_demo = Column(Boolean, default=False)
    metadata_json = Column(JSON, nullable=True)

    compliance_items = relationship("ComplianceRequirement", back_populates="standard")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query_text = Column(Text, nullable=False)
    document_id = Column(String(50), ForeignKey("documents.id"), nullable=True)
    results_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="recommendations")
    evidences = relationship("Evidence", back_populates="recommendation", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidences"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(String(50), ForeignKey("recommendations.id"), nullable=False)
    standard_number = Column(String(100), index=True, nullable=False)
    evidence_text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    section_name = Column(String(150), nullable=True)
    confidence_score = Column(Float, default=1.0)
    audit_status = Column(String(100), default="Grounded in Source")

    recommendation = relationship("Recommendation", back_populates="evidences")


class ComplianceRequirement(Base):
    __tablename__ = "compliance_requirements"

    id = Column(Integer, primary_key=True, index=True)
    standard_id = Column(Integer, ForeignKey("standards.id"), nullable=True)
    standard_number = Column(String(100), index=True, nullable=False)
    scheme_type = Column(String(100), nullable=False) # e.g. ISI Mark, CRS, QCO
    mandated_by = Column(String(255), nullable=True)
    details = Column(Text, nullable=False)
    status = Column(String(50), default="Mandatory")

    standard = relationship("Standard", back_populates="compliance_items")


class VerifiedAnswer(Base):
    """
    Persistent database for engineer-approved knowledge.
    Stores final reviewed answers, modifications, and audit status.
    """
    __tablename__ = "verified_answers"

    id = Column(String(50), primary_key=True, index=True)
    recommendation_id = Column(String(50), index=True, nullable=True)
    original_query = Column(Text, nullable=False)
    normalized_query = Column(Text, index=True, nullable=False)
    extracted_requirements = Column(JSON, nullable=True)
    primary_standard = Column(String(100), index=True, nullable=False)
    related_standards = Column(JSON, nullable=True)
    compliance_result = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=True)
    engineer_status = Column(String(50), default="PENDING")  # PENDING, APPROVED, MODIFIED, REJECTED
    engineer_comment = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    dataset_version = Column(String(50), default="v1.0-real-21")
    original_ai_recommendation = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReviewRecord(Base):
    """
    Immutable review audit trail for all engineer decisions (Approve, Modify, Reject).
    Never overwrites historical review records.
    """
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(String(50), index=True, nullable=False)
    action = Column(String(50), nullable=False)  # APPROVED, MODIFIED, REJECTED
    engineer_comment = Column(Text, nullable=True)
    modifications = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class StandardVersionHistory(Base):
    """
    Tracks lifecycle and version changes when standards are updated or superseded.
    Preserves historical records (e.g., IS XXXX:2014 superseded by IS XXXX:2026).
    """
    __tablename__ = "standard_version_history"

    id = Column(Integer, primary_key=True, index=True)
    standard_number = Column(String(100), index=True, nullable=False)
    previous_version = Column(String(100), nullable=True)
    new_version = Column(String(100), nullable=False)
    status = Column(String(50), default="Active")  # Active, Superseded, Withdrawn
    change_date = Column(DateTime, default=datetime.utcnow)
    change_type = Column(String(50), default="SUPERSEDED")  # SUPERSEDED, CREATED, REVISED, WITHDRAWN
    source = Column(String(255), default="Bureau of Indian Standards")
    verified_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)


class TenderValidationRecord(Base):
    """
    Feature M10: Persistent audit storage for pre-publish tender validations and officer reviews.
    """
    __tablename__ = "tender_validations"

    id = Column(String(50), primary_key=True, index=True)
    document_id = Column(String(50), ForeignKey("documents.id"), nullable=True)
    input_text_snippet = Column(Text, nullable=True)
    report_json = Column(JSON, nullable=False)
    overall_status = Column(String(50), nullable=False)
    officer_status = Column(String(50), default="PENDING")
    officer_id = Column(String(100), nullable=True)
    officer_comments = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

