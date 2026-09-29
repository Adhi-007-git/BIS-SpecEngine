"""
Pydantic Schemas export.
"""
from backend.app.schemas.dtos import (
    SearchRequest,
    SearchResponse,
    RecommendationItem,
    ComplianceItem,
    RelatedStandardItem,
    UploadResponse,
    DocumentAnalyzeRequest,
    EvidenceResponse,
    GraphNode,
    GraphEdge,
    GraphResponse,
    StandardDetailResponse,
    HealthResponse,
    ReviewApproveRequest,
    ReviewModifyRequest,
    ReviewRejectRequest,
    ReviewActionResponse,
    StandardManageAddRequest,
    StandardManageUpdateRequest,
    VersionHistoryItem,
    VerifiedAnswerDTO
)

# Alias for backward compatibility
EvidenceItem = EvidenceResponse

__all__ = [
    "SearchRequest",
    "SearchResponse",
    "RecommendationItem",
    "EvidenceItem",
    "ComplianceItem",
    "RelatedStandardItem",
    "UploadResponse",
    "DocumentAnalyzeRequest",
    "EvidenceResponse",
    "GraphNode",
    "GraphEdge",
    "GraphResponse",
    "StandardDetailResponse",
    "HealthResponse",
    "ReviewApproveRequest",
    "ReviewModifyRequest",
    "ReviewRejectRequest",
    "ReviewActionResponse",
    "StandardManageAddRequest",
    "StandardManageUpdateRequest",
    "VersionHistoryItem",
    "VerifiedAnswerDTO"
]
