"""
Pydantic schemas for SIH26108 request validation and typed API responses.
Preserves all legacy fields (evidence, page, section) while adding Phase 2 fields
(evidence_list, score_factors, retrieval_mode, embedding_mode).
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class RelatedStandardItem(BaseModel):
    standard_number: str
    title: Optional[str] = ""
    relation: str = "NORMATIVE_REFERENCE"

class ComplianceItem(BaseModel):
    scheme: str
    mark: Optional[str] = "Verification required"
    authority: Optional[str] = "Bureau of Indian Standards"
    mandate: Optional[str] = ""
    status: str = "Mandatory"
    evidence_ref: Optional[str] = ""

class EvidenceSnippet(BaseModel):
    text: str
    page: Optional[int] = None
    section: Optional[str] = None
    source: Optional[str] = None

class RecommendationItem(BaseModel):
    standard_number: str
    title: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    reason: str
    status: str
    source: str
    # Legacy preserved fields
    evidence: str
    page: Optional[int] = None
    section: Optional[str] = None
    # Phase 2 structured evidence & score factors
    evidence_list: List[EvidenceSnippet] = []
    score_factors: Optional[Dict[str, Any]] = None
    related_standards: List[RelatedStandardItem] = []
    compliance: List[ComplianceItem] = []
    is_demo: bool = True
    demo_tag: str = "DEMO DATA"
    # Extended Phase 6/Final metadata fields
    lifecycle_status: Optional[str] = "Active"
    last_verified: Optional[str] = None
    normative_references: Optional[List[RelatedStandardItem]] = []
    qco_enforcement_flag: Optional[bool] = False
    applicable_scheme: Optional[str] = None
    compliance_alerts: Optional[List[str]] = []
    foreign_standard_warning: Optional[str] = None
    applicability_type: Optional[str] = "DIRECTLY_APPLICABLE"
    exclusion_reason: Optional[str] = None
    officer_verification_needed: Optional[bool] = False
    title_explanation: Optional[str] = None
    applicability_reasoning: Optional[str] = None
    next_steps: Optional[str] = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural-language procurement requirement or product specification")
    limit: Optional[int] = Field(5, ge=1, le=20)
    domain_filter: Optional[str] = None

class SearchResponse(BaseModel):
    recommendation_id: str
    query: str
    total_recommendations: int
    data_mode: str = "DEMO"
    retrieval_mode: str = "IN_MEMORY"
    embedding_mode: str = "DEMO_FALLBACK"
    recommendations: List[RecommendationItem]
    query_analysis: Optional[Dict[str, Any]] = None
    structured_requirements: Optional[Dict[str, Any]] = None
    verified_memory: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    excluded_candidates: Optional[List[Dict[str, Any]]] = []
    advisory_notices: Optional[List[str]] = []
    response_language: Optional[str] = "en"
    response_language_name: Optional[str] = "English"
    summary: Optional[str] = None

class DocumentAnalyzeRequest(BaseModel):
    document_id: str
    query_hint: Optional[str] = None

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    file_size: int
    pages_extracted: int
    total_chunks: int
    detected_explicit_standards: List[str]
    retrieval_mode: Optional[str] = "IN_MEMORY"
    embedding_mode: Optional[str] = "DEMO_FALLBACK"
    message: str

class EvidenceResponse(BaseModel):
    recommendation_id: str
    standard_number: str
    evidence_text: str
    page: Optional[int] = None
    section: Optional[str] = None
    confidence: float
    audit_status: str
    evidence_list: Optional[List[EvidenceSnippet]] = []

class GraphNode(BaseModel):
    id: str
    type: Optional[str] = "default"
    position: Dict[str, float]
    data: Dict[str, Any]
    style: Optional[Dict[str, Any]] = None

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    animated: Optional[bool] = False
    style: Optional[Dict[str, Any]] = None

class GraphResponse(BaseModel):
    standard_number: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int

class StandardDetailResponse(BaseModel):
    standard_number: str
    title: str
    edition: Optional[str] = None
    status: str
    scope: str
    source: str
    is_demo: bool = True
    demo_tag: str = "DEMO DATA"
    compliance: List[ComplianceItem] = []
    normative_references: List[RelatedStandardItem] = []
    test_methods: List[RelatedStandardItem] = []
    supersedes: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    project: str
    version: str
    qdrant_connected: bool
    neo4j_connected: bool
    database_connected: bool
    environment: str
    dev_mode: bool
    retrieval_mode: str = "IN_MEMORY"
    embedding_mode: str = "DEMO_FALLBACK"


# ─── Phase 4 Review & Standards Management DTOs ──────────────────────────────

class ReviewApproveRequest(BaseModel):
    comment: Optional[str] = Field(None, description="Optional engineer review comment on approval")

class ReviewModifyRequest(BaseModel):
    primary_standard: str = Field(..., description="Engineer-corrected primary standard number")
    related_standards: Optional[List[Any]] = Field(default_factory=list, description="Engineer-selected related standards")
    comment: Optional[str] = Field(None, description="Engineer rationale for modifying recommendations")
    modifications: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Detailed parameter overrides")

class ReviewRejectRequest(BaseModel):
    comment: str = Field(..., min_length=2, description="Mandatory engineer reason for rejecting recommendation")

class ReviewActionResponse(BaseModel):
    recommendation_id: str
    action: str
    status: str
    message: str
    timestamp: str

class StandardManageAddRequest(BaseModel):
    standard_number: str = Field(..., min_length=2, description="Authoritative standard code (e.g., IS 9999:2026)")
    title: str = Field(..., min_length=2, description="Official specification title")
    edition: Optional[str] = Field(None, description="Standard edition / revision")
    status: Optional[str] = Field("Active", description="Active / Superseded / Withdrawn")
    scope: Optional[str] = Field("", description="Standard scope and domain coverage")
    department: Optional[str] = Field(None, description="BIS Division / Department")
    keywords: Optional[List[str]] = Field(default_factory=list)
    source: Optional[str] = Field("Bureau of Indian Standards")
    last_verified: Optional[str] = Field(None)
    amendments: Optional[List[str]] = Field(default_factory=list)
    normative_references: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    test_methods: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    supersedes: Optional[str] = Field(None)
    compliance: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    QCO: Optional[Dict[str, Any]] = Field(default=None)

class StandardManageUpdateRequest(BaseModel):
    title: Optional[str] = None
    edition: Optional[str] = None
    status: Optional[str] = None
    scope: Optional[str] = None
    department: Optional[str] = None
    keywords: Optional[List[str]] = None
    source: Optional[str] = None
    last_verified: Optional[str] = None
    amendments: Optional[List[str]] = None
    normative_references: Optional[List[Dict[str, Any]]] = None
    test_methods: Optional[List[Dict[str, Any]]] = None
    supersedes: Optional[str] = None
    compliance: Optional[List[Dict[str, Any]]] = None
    QCO: Optional[Dict[str, Any]] = None

class VersionHistoryItem(BaseModel):
    standard_number: str
    previous_version: Optional[str] = None
    new_version: str
    status: str
    change_date: str
    change_type: str
    source: str
    verified_date: str
    notes: Optional[str] = None

class VerifiedAnswerDTO(BaseModel):
    id: str
    recommendation_id: Optional[str] = None
    original_query: str
    primary_standard: str
    related_standards: Optional[Any] = None
    engineer_status: str
    engineer_comment: Optional[str] = None
    verified_at: Optional[str] = None
    dataset_version: str
    current_status: Optional[str] = None
    is_superseded: bool = False


# ─── Feature M10: Pre-Publish Tender Validation DTOs ────────────────────────

class ValidationFinding(BaseModel):
    id: str
    rule_id: str
    rule_name: str
    severity: str  # CRITICAL | WARNING | INFO | MANUAL_REVIEW_REQUIRED
    description: str
    clause_excerpt: Optional[str] = None
    standard_identifier: Optional[str] = None
    recommended_action: str
    evidence_source: Optional[str] = None
    evidence_record_id: Optional[str] = None
    evidence_excerpt: Optional[str] = None
    confidence_status: str  # VERIFIED_FACT | UNCERTAIN_MATCH

class TenderValidationRequest(BaseModel):
    tender_text: Optional[str] = Field(None, description="Direct technical specification or tender text")
    document_id: Optional[str] = Field(None, description="Document ID of an existing uploaded tender document")

class OfficerReviewDecision(BaseModel):
    reviewer_id: str = Field("DEV_OFFICER_DEFAULT", description="Procurement officer identifier (dev-mode fallback)")
    decision: str = Field(..., description="APPROVED_WITH_NOTES | AMENDMENT_REQUESTED | REJECTED")
    comments: Optional[str] = Field("", description="Officer notes and instructions")
    reviewed_at: Optional[str] = None

class TenderValidationReport(BaseModel):
    validation_id: str
    document_id: Optional[str] = None
    input_source: str = "DIRECT_TEXT"
    timestamp: str
    summary_counts: Dict[str, int]
    overall_status: str  # REQUIRES_AMENDMENT | OFFICER_REVIEW_REQUIRED | NO_BLOCKING_ISSUES_DETECTED
    findings: List[ValidationFinding]
    checks_completed: List[str]
    checks_not_completed: List[str]
    data_limitations: List[str]
    advisory_disclaimer: str
    officer_review_status: str = "PENDING"
    officer_review: Optional[OfficerReviewDecision] = None

class ValidationReviewRequest(BaseModel):
    decision: str = Field(..., description="APPROVED_WITH_NOTES | AMENDMENT_REQUESTED | REJECTED")
    officer_id: Optional[str] = Field("DEV_OFFICER_DEFAULT", description="Procurement officer identifier")
    comments: Optional[str] = Field(None, description="Officer review notes or amendment instructions")

