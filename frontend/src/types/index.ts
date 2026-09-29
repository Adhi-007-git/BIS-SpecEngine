// SIH26108 Types — Phase 2 (evidence_list, score_factors, retrieval_mode, embedding_mode)
// Phase 4 additions: Engineer Review, Verified Knowledge, Standards Management
// Phase 4 Query Understanding: StructuredRequirements, expanded QueryAnalysis

export interface RelatedStandard {
  standard_number: string;
  title?: string;
  relation: string; // NORMATIVE_REFERENCE | REQUIRES_TESTING_VIA | SUPERSEDES | MANDATED_BY
}

export interface ComplianceItem {
  scheme: string;
  mark?: string;
  authority?: string;
  mandate?: string;
  status: string;
  evidence_ref?: string;
}

/** Phase 2: structured evidence snippet from document chunks */
export interface EvidenceSnippet {
  text: string;
  page?: number | null;
  section?: string | null;
  source?: string | null;
}

/** Phase 2: per-factor relevance breakdown (Semantic, Material, Environment, Technical) */
export interface ScoreFactors {
  semantic?: number;
  material?: number;
  environment?: number;
  technical?: number;
  [key: string]: number | undefined;
}

export interface RecommendationItem {
  standard_number: string;
  title: string;
  relevance_score: number;
  reason: string;
  status: string;
  source: string;
  // Legacy preserved fields
  evidence: string;
  page?: number | null;
  section?: string | null;
  related_standards: RelatedStandard[];
  compliance: ComplianceItem[];
  is_demo: boolean;
  demo_tag: string;
  // Phase 2 additions
  evidence_list?: EvidenceSnippet[];
  score_factors?: ScoreFactors | null;
  // Extended Phase 6/Final metadata
  lifecycle_status?: string;
  last_verified?: string | null;
  normative_references?: RelatedStandard[];
  qco_enforcement_flag?: boolean;
  applicable_scheme?: string | null;
  compliance_alerts?: string[];
  foreign_standard_warning?: string | null;
  applicability_type?: 'DIRECTLY_APPLICABLE' | 'RELATED_REFERENCE' | 'INCOMPATIBLE';
  exclusion_reason?: string | null;
  officer_verification_needed?: boolean;
}

/** Phase 4: Structured procurement requirements extracted by the LLM or rule extractor.
 *  Mirrors ai_engine/query/schema.py :: StructuredRequirements */
export interface StructuredRequirements {
  product?: string | null;
  capacity?: string | null;
  cooling?: string | null;
  installation?: string | null;
  primary_voltage?: string | null;
  secondary_voltage?: string | null;
  foreign_standards?: string[];
  application?: string | null;
  additional_parameters?: Record<string, unknown>;
}

export interface QueryAnalysis {
  raw_query: string;
  clean_tokens: string[];
  detected_domains: string[];
  concepts: {
    materials: string[];
    environments: string[];
    specifications: string[];
  };
  // Phase 4: LLM Query Understanding fields
  structured_requirements?: StructuredRequirements | null;
  llm_used?: boolean;
  llm_provider?: string;
  is_empty?: boolean;
  // Feature M9 Multilingual fields
  detected_language?: string;
  detected_script?: string;
  original_query?: string;
  normalized_english_query?: string | null;
  normalization_method?: string;
  normalization_status?: string;
  normalization_message?: string;
}

export interface SearchResponse {
  recommendation_id: string;
  query: string;
  total_recommendations: number;
  data_mode: string;
  // Phase 2 additions
  retrieval_mode?: string;   // IN_MEMORY | QDRANT
  embedding_mode?: string;   // DEMO_FALLBACK | REAL_BGE_M3
  recommendations: RecommendationItem[];
  query_analysis?: QueryAnalysis;
  structured_requirements?: StructuredRequirements | null;
  message?: string | null;
  excluded_candidates?: Array<{
    standard_number: string;
    title: string;
    exclusion_reason: string;
  }>;
  advisory_notices?: string[];
  verified_memory?: {
    verified_answer_id: string;
    recommendation_id?: string;
    original_query: string;
    primary_standard: string;
    related_standards?: string[];
    evidence?: any;
    engineer_status: string;
    engineer_comment?: string;
    verified_at?: string;
    dataset_version: string;
    status_verification?: {
      is_active: boolean;
      status: string;
      warning?: string | null;
    };
  } | null;
}

export interface ComplianceReportDTO {
  report_title: string;
  recommendation_id: string;
  generated_at: string;
  dataset_version: string;
  document_id?: string | null;
  procurement_requirement: string;
  extracted_technical_requirements?: Record<string, any>;
  primary_recommended_standard: {
    standard_number: string;
    title: string;
    relevance_score: number;
    score_factors?: ScoreFactors | null;
    reason: string;
    lifecycle_status: string;
    last_verified_date: string;
    source: string;
  };
  related_standards: RelatedStandard[];
  normative_references: RelatedStandard[];
  lifecycle_status: string;
  last_verified_date: string;
  qco_enforcement: {
    is_mandatory: boolean;
    mandates: ComplianceItem[];
    alerts: string[];
  };
  applicable_scheme: string;
  foreign_standard_conflict_warning?: string | null;
  compliance_alerts: string[];
  evidence_audit_trail: any[];
  engineer_review_status: string;
  verification_information: {
    status: string;
    comment?: string | null;
    verified_at?: string | null;
  };
  all_recommendations: RecommendationItem[];
  retrieval_metadata?: {
    retrieval_mode: string;
    embedding_mode: string;
    data_mode: string;
  };
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  file_size: number;
  pages_extracted: number;
  total_chunks: number;
  detected_explicit_standards: string[];
  // Phase 2 additions
  retrieval_mode?: string;
  embedding_mode?: string;
  message: string;
}

export interface EvidenceItem {
  recommendation_id: string;
  standard_number: string;
  evidence_text: string;
  page?: number | null;
  section?: string | null;
  confidence: number;
  audit_status: string;
  // Phase 2 addition
  evidence_list?: EvidenceSnippet[];
}

export interface GraphNode {
  id: string;
  type?: string;
  position: { x: number; y: number };
  data: {
    label: string;
    standard_number?: string;
    node_type?: string;
    status?: string;
  };
  style?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  animated?: boolean;
  style?: Record<string, any>;
}

export interface GraphResponse {
  standard_number: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
}

export interface StandardDetails {
  standard_number: string;
  title: string;
  edition?: string;
  status: string;
  scope: string;
  source: string;
  is_demo: boolean;
  demo_tag: string;
  compliance: ComplianceItem[];
  normative_references: RelatedStandard[];
  test_methods: RelatedStandard[];
  supersedes?: string | null;
}

export interface SystemHealth {
  status: string;
  project: string;
  version: string;
  qdrant_connected: boolean;
  neo4j_connected: boolean;
  database_connected: boolean;
  environment: string;
  dev_mode: boolean;
  // Phase 2 additions
  retrieval_mode?: string;
  embedding_mode?: string;
}

// ─── Phase 4: Engineer Review & Verified Knowledge ───────────────────────────

export type ReviewAction = 'APPROVED' | 'MODIFIED' | 'REJECTED' | 'PENDING';

export interface ReviewActionResponse {
  recommendation_id: string;
  action: ReviewAction;
  status: ReviewAction;
  message: string;
  timestamp: string;
}

export interface VerifiedAnswerDTO {
  id: string;
  recommendation_id: string;
  original_query: string;
  primary_standard: string;
  related_standards: string[];
  engineer_status: ReviewAction;
  engineer_comment?: string | null;
  verified_at?: string | null;
  dataset_version?: string | null;
  current_status?: string;
  is_superseded?: boolean;
}

export interface ReviewHistoryEntry {
  id: string;
  action: ReviewAction;
  engineer_comment?: string | null;
  modifications?: Record<string, any> | null;
  timestamp?: string | null;
}

// ─── Phase 4: Standards Management ───────────────────────────────────────────

export interface StandardManageAddRequest {
  standard_number: string;
  title: string;
  scope?: string;
  edition?: string;
  status?: string;
  source?: string;
  department?: string;
  keywords?: string[];
  supersedes?: string;
  normative_references?: string[];
  test_methods?: string[];
  amendments?: string[];
  compliance?: Record<string, any>[];
  last_verified?: string;
}

export interface StandardManageUpdateRequest {
  title?: string;
  scope?: string;
  edition?: string;
  status?: string;
  department?: string;
  keywords?: string[];
  supersedes?: string;
  compliance?: Record<string, any>[];
  last_verified?: string;
}

export interface VersionHistoryItem {
  standard_number: string;
  previous_version?: string | null;
  new_version?: string | null;
  status: string;
  change_date: string;
  change_type: string;
  source?: string | null;
  verified_date?: string | null;
  notes?: string | null;
}

// ─── Feature M10: Pre-Publish Tender Validation Types ─────────────────────────

export type ValidationSeverity = 'CRITICAL' | 'WARNING' | 'INFO' | 'MANUAL_REVIEW_REQUIRED';
export type ValidationWorkflowStatus = 'REQUIRES_AMENDMENT' | 'OFFICER_REVIEW_REQUIRED' | 'NO_BLOCKING_ISSUES_DETECTED';
export type OfficerDecisionType = 'APPROVED_WITH_NOTES' | 'AMENDMENT_REQUESTED' | 'REJECTED';

export interface ValidationFinding {
  id: string;
  rule_id: string;
  rule_name: string;
  severity: ValidationSeverity;
  description: string;
  clause_excerpt?: string | null;
  standard_identifier?: string | null;
  recommended_action: string;
  evidence_source?: string | null;
  evidence_record_id?: string | null;
  evidence_excerpt?: string | null;
  confidence_status: 'VERIFIED_FACT' | 'UNCERTAIN_MATCH';
}

export interface OfficerReviewDecision {
  reviewer_id: string;
  decision: OfficerDecisionType;
  comments: string;
  reviewed_at?: string | null;
}

export interface TenderValidationReport {
  validation_id: string;
  document_id?: string | null;
  input_source: string;
  timestamp: string;
  summary_counts: {
    CRITICAL: number;
    WARNING: number;
    INFO: number;
    MANUAL_REVIEW_REQUIRED: number;
    [key: string]: number;
  };
  overall_status: ValidationWorkflowStatus;
  findings: ValidationFinding[];
  checks_completed: string[];
  checks_not_completed: string[];
  data_limitations: string[];
  advisory_disclaimer: string;
  officer_review_status: string;
  officer_review?: OfficerReviewDecision | null;
}

export interface ValidationReviewRequest {
  decision: OfficerDecisionType;
  officer_id?: string;
  comments?: string;
}


