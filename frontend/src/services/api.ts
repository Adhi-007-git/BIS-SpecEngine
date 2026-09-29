import axios from 'axios';
import {
  SearchResponse,
  UploadResponse,
  StandardDetails,
  RelatedStandard,
  EvidenceItem,
  GraphResponse,
  SystemHealth,
  // Phase 4
  ReviewActionResponse,
  VerifiedAnswerDTO,
  ReviewHistoryEntry,
  StandardManageAddRequest,
  StandardManageUpdateRequest,
  VersionHistoryItem,
  ComplianceReportDTO,
  TenderValidationReport,
  ValidationReviewRequest,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const api = {
  // System Health
  async getHealth(): Promise<SystemHealth> {
    const res = await apiClient.get<SystemHealth>('/health');
    return res.data;
  },

  // Search Applicable Standards
  async searchStandards(query: string, limit: number = 5, domain?: string): Promise<SearchResponse> {
    const res = await apiClient.post<SearchResponse>('/search', {
      query,
      limit,
      domain_filter: domain || null,
    });
    return res.data;
  },

  // Upload Tender / PDF Document
  async uploadTender(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post<UploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  // Analyze Document
  async analyzeDocument(documentId: string, queryHint?: string): Promise<SearchResponse> {
    const res = await apiClient.post<SearchResponse>('/analyze-document', {
      document_id: documentId,
      query_hint: queryHint || null,
    });
    return res.data;
  },

  // Recommendation lookup
  async getRecommendation(id: string): Promise<SearchResponse> {
    const res = await apiClient.get<SearchResponse>(`/recommendations/${encodeURIComponent(id)}`);
    return res.data;
  },

  // Standard details
  async getStandardDetails(standardId: string): Promise<StandardDetails> {
    const res = await apiClient.get<StandardDetails>(`/standards/${encodeURIComponent(standardId)}`);
    return res.data;
  },

  // Related standards
  async getRelatedStandards(standardId: string): Promise<RelatedStandard[]> {
    const res = await apiClient.get<RelatedStandard[]>(`/standards/${encodeURIComponent(standardId)}/related`);
    return res.data;
  },

  // List all standards for selectors
  async listStandards(): Promise<Array<{ standard_number: string; title: string; status: string; edition?: string }>> {
    const res = await apiClient.get<Array<{ standard_number: string; title: string; status: string; edition?: string }>>('/standards');
    return res.data;
  },

  // Evidence audit trail
  async getEvidence(recommendationId: string): Promise<EvidenceItem[]> {
    const res = await apiClient.get<EvidenceItem[]>(`/evidence/${encodeURIComponent(recommendationId)}`);
    return res.data;
  },

  // Knowledge graph visualization
  async getStandardGraph(standardId: string): Promise<GraphResponse> {
    const res = await apiClient.get<GraphResponse>(`/graph/${encodeURIComponent(standardId)}`);
    return res.data;
  },

  // ─── Phase 4: Engineer Review ─────────────────────────────────────────────

  async approveRecommendation(
    recommendationId: string,
    comment?: string
  ): Promise<ReviewActionResponse> {
    const res = await apiClient.post<ReviewActionResponse>(
      `/review/${encodeURIComponent(recommendationId)}/approve`,
      { comment: comment || null }
    );
    return res.data;
  },

  async modifyRecommendation(
    recommendationId: string,
    primaryStandard: string,
    relatedStandards: string[],
    modifications?: Record<string, any>,
    comment?: string
  ): Promise<ReviewActionResponse> {
    const res = await apiClient.post<ReviewActionResponse>(
      `/review/${encodeURIComponent(recommendationId)}/modify`,
      {
        primary_standard: primaryStandard,
        related_standards: relatedStandards,
        modifications: modifications || null,
        comment: comment || null,
      }
    );
    return res.data;
  },

  async rejectRecommendation(
    recommendationId: string,
    comment: string
  ): Promise<ReviewActionResponse> {
    const res = await apiClient.post<ReviewActionResponse>(
      `/review/${encodeURIComponent(recommendationId)}/reject`,
      { comment }
    );
    return res.data;
  },

  async getVerifiedKnowledge(statusFilter?: string): Promise<VerifiedAnswerDTO[]> {
    const params: Record<string, string> = {};
    if (statusFilter) params.status_filter = statusFilter;
    const res = await apiClient.get<VerifiedAnswerDTO[]>('/review/knowledge', { params });
    return res.data;
  },

  async getReviewHistory(recommendationId: string): Promise<ReviewHistoryEntry[]> {
    const res = await apiClient.get<ReviewHistoryEntry[]>(
      `/review/history/${encodeURIComponent(recommendationId)}`
    );
    return res.data;
  },

  // ─── Phase 4: Standards Management ───────────────────────────────────────

  async addStandard(payload: StandardManageAddRequest): Promise<{ message: string; standard_number: string; status: string }> {
    const res = await apiClient.post('/standards/manage/add', payload);
    return res.data;
  },

  async updateStandard(
    standardNumber: string,
    payload: StandardManageUpdateRequest
  ): Promise<{ message: string; standard_number: string; status: string }> {
    const res = await apiClient.put(`/standards/manage/${encodeURIComponent(standardNumber)}`, payload);
    return res.data;
  },

  async getVersionHistory(): Promise<VersionHistoryItem[]> {
    const res = await apiClient.get<VersionHistoryItem[]>('/standards/manage/versions');
    return res.data;
  },

  async reindexSearch(): Promise<{ message: string; total_standards_indexed: number; collection: string }> {
    const res = await apiClient.post('/standards/manage/reindex');
    return res.data;
  },

  // ─── Phase 6/Final: Compliance Reports ───────────────────────────────────

  async getReport(recommendationId: string, format: 'json' | 'html' = 'json'): Promise<ComplianceReportDTO | string> {
    const res = await apiClient.get(`/reports/${encodeURIComponent(recommendationId)}`, {
      params: { format },
    });
    return res.data;
  },

  getReportDownloadUrl(recommendationId: string): string {
    return `${API_BASE_URL}/reports/${encodeURIComponent(recommendationId)}/download`;
  },

  // ─── Feature M10: Pre-Publish Tender Validation ───────────────────────────

  async validateTender(payload: { tender_text?: string; document_id?: string }): Promise<TenderValidationReport> {
    const res = await apiClient.post<TenderValidationReport>('/pre-publish/validate', payload);
    return res.data;
  },

  async getValidationReport(validationId: string): Promise<TenderValidationReport> {
    const res = await apiClient.get<TenderValidationReport>(`/pre-publish/validate/${encodeURIComponent(validationId)}`);
    return res.data;
  },

  async reviewValidationReport(
    validationId: string,
    payload: ValidationReviewRequest
  ): Promise<TenderValidationReport> {
    const res = await apiClient.post<TenderValidationReport>(
      `/pre-publish/validate/${encodeURIComponent(validationId)}/review`,
      payload
    );
    return res.data;
  },

  getValidationDownloadUrl(validationId: string): string {
    return `${API_BASE_URL}/pre-publish/validate/${encodeURIComponent(validationId)}/download`;
  },
};

