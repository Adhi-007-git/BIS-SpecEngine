import React, { useEffect, useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import {
  Layers,
  CheckCircle,
  FileText,
  ShieldCheck,
  Network,
  ChevronRight,
  Info,
  Loader2,
  BookOpen,
  ClipboardCheck,
  ThumbsDown,
  Edit3,
  X,
  Plus,
  Clock,
  FileDown,
  Printer,
  SlidersHorizontal,
  ArrowLeft,
  Scale,
  Check,
  AlertTriangle
} from 'lucide-react';
import { api } from '../services/api';
import { SearchResponse, ReviewAction } from '../types';
import {
  Badge,
  CodeChip,
  ConfidenceMeter,
  Alert,
  ScorePopover,
  EmptyState,
  CardSkeleton,
  PageHeader,
  Toast,
  ToastMessage
} from '../components/ui';

// ─── Inline Review Panel ──────────────────────────────────────────────────────
interface ReviewPanelProps {
  recommendationId: string;
  primaryStandard: string;
  relatedStandards: string[];
  status: ReviewAction;
  onStatusChange: (status: ReviewAction) => void;
  onToast: (msg: string, type: 'success' | 'error') => void;
}

const ReviewPanel: React.FC<ReviewPanelProps> = ({
  recommendationId,
  primaryStandard,
  relatedStandards,
  status,
  onStatusChange,
  onToast,
}) => {
  const [mode, setMode] = useState<'idle' | 'approve' | 'modify' | 'reject'>('idle');
  const [comment, setComment] = useState('');
  const [modPrimary, setModPrimary] = useState(primaryStandard);
  const [modRelated, setModRelated] = useState<string[]>(relatedStandards);
  const [newRelated, setNewRelated] = useState('');
  const [loading, setLoading] = useState(false);

  const reset = () => {
    setMode('idle');
    setComment('');
    setModPrimary(primaryStandard);
    setModRelated(relatedStandards);
    setNewRelated('');
  };

  const handleApprove = async () => {
    setLoading(true);
    try {
      await api.approveRecommendation(recommendationId, comment || undefined);
      onStatusChange('APPROVED');
      onToast('Recommendation approved and committed to Verified Knowledge Memory.', 'success');
      reset();
    } catch (e: any) {
      onToast(e.response?.data?.detail || 'Approval failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleModify = async () => {
    if (!modPrimary.trim()) {
      onToast('Primary standard is required.', 'error');
      return;
    }
    setLoading(true);
    try {
      await api.modifyRecommendation(
        recommendationId,
        modPrimary.trim(),
        modRelated,
        undefined,
        comment || undefined
      );
      onStatusChange('MODIFIED');
      onToast('Recommendation modified and saved to Verified Knowledge.', 'success');
      reset();
    } catch (e: any) {
      onToast(e.response?.data?.detail || 'Modification failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!comment.trim()) {
      onToast('Reason is required to reject recommendation.', 'error');
      return;
    }
    setLoading(true);
    try {
      await api.rejectRecommendation(recommendationId, comment.trim());
      onStatusChange('REJECTED');
      onToast('Recommendation rejected. Excluded from Verified Memory.', 'success');
      reset();
    } catch (e: any) {
      onToast(e.response?.data?.detail || 'Rejection failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const addRelated = () => {
    const trimmed = newRelated.trim();
    if (trimmed && !modRelated.includes(trimmed)) {
      setModRelated([...modRelated, trimmed]);
      setNewRelated('');
    }
  };

  const removeRelated = (idx: number) => {
    setModRelated(modRelated.filter((_, i) => i !== idx));
  };

  return (
    <div className="pt-4 border-t border-border-default space-y-3">
      {/* Action Buttons Bar */}
      {mode === 'idle' && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-ink-500">
              Engineer Decision:
            </span>
            <Badge
              variant={
                status === 'APPROVED'
                  ? 'approved'
                  : status === 'MODIFIED'
                  ? 'modified'
                  : status === 'REJECTED'
                  ? 'rejected'
                  : 'pending'
              }
            />
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setMode('approve')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-success-soft hover:bg-success/20 text-success border border-success/40 transition-colors shadow-warm-sm"
            >
              <Check className="w-3.5 h-3.5 text-success" />
              <span>Approve</span>
            </button>
            <button
              onClick={() => setMode('modify')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-info-soft hover:bg-info/20 text-info border border-info/40 transition-colors shadow-warm-sm"
            >
              <Edit3 className="w-3.5 h-3.5 text-info" />
              <span>Modify</span>
            </button>
            <button
              onClick={() => setMode('reject')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-danger-soft hover:bg-danger/20 text-danger border border-danger/40 transition-colors shadow-warm-sm"
            >
              <ThumbsDown className="w-3.5 h-3.5 text-danger" />
              <span>Reject</span>
            </button>
          </div>
        </div>
      )}

      {/* Approve Panel */}
      {mode === 'approve' && (
        <div className="p-5 rounded-xl border border-success/40 bg-success-soft/50 space-y-3 animate-slide-up">
          <div className="flex items-center justify-between">
            <span className="text-sm font-bold text-ink-900 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-success" />
              Approve Recommendation & Commit to Verified Memory
            </span>
            <button onClick={reset} className="text-ink-500 hover:text-ink-900">
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-ink-700">
            Confirming this recommendation establishes a verified question-answer memory pair. Future matching queries will surface this verified standard instantly.
          </p>
          <div className="space-y-1">
            <label className="text-xs font-bold text-ink-700">
              Engineer Approval Notes (Optional)
            </label>
            <textarea
              rows={2}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="e.g. Confirmed voltage parameters and physical construction against CPWD specs..."
              className="w-full px-3 py-2 text-xs rounded-lg border border-border-strong bg-bg-surface text-ink-900 placeholder-ink-500 focus:outline-none focus:border-brand"
            />
          </div>
          <div className="flex items-center justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={reset}
              className="px-3.5 py-1.5 rounded-lg border border-border-default text-xs font-semibold text-ink-700 hover:bg-bg-sunken"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleApprove}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-success hover:bg-success-hover text-white text-xs font-bold shadow-warm disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
              Confirm Approval
            </button>
          </div>
        </div>
      )}

      {/* Modify Panel (Side-by-Side Diff) */}
      {mode === 'modify' && (
        <div className="p-5 rounded-xl border border-info/40 bg-info-soft/40 space-y-4 animate-slide-up">
          <div className="flex items-center justify-between">
            <span className="text-sm font-bold text-ink-900 flex items-center gap-2">
              <Edit3 className="w-4 h-4 text-info" />
              Modify Recommended Standards (Side-by-Side Diff)
            </span>
            <button onClick={reset} className="text-ink-500 hover:text-ink-900">
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-3.5 rounded-xl border border-border-default bg-bg-surface space-y-2">
              <span className="font-bold text-[11px] uppercase tracking-wider text-ink-500 block">
                Original AI Output:
              </span>
              <div>
                <span className="text-ink-500 text-[11px]">Primary:</span>
                <div className="mt-0.5"><CodeChip code={primaryStandard} variant="secondary" /></div>
              </div>
              <div>
                <span className="text-ink-500 text-[11px]">Related References:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {relatedStandards.length > 0 ? (
                    relatedStandards.map((r, i) => (
                      <span key={i} className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-bg-sunken border border-border-default text-ink-700">
                        {r}
                      </span>
                    ))
                  ) : (
                    <span className="text-ink-500 italic">None</span>
                  )}
                </div>
              </div>
            </div>

            <div className="p-3.5 rounded-xl border border-info/60 bg-bg-surface space-y-3">
              <span className="font-bold text-[11px] uppercase tracking-wider text-info block">
                Engineer Proposed Override:
              </span>
              <div className="space-y-1">
                <label className="text-ink-700 font-semibold block text-[11px]">Primary Standard Code:</label>
                <input
                  type="text"
                  value={modPrimary}
                  onChange={(e) => setModPrimary(e.target.value)}
                  className="w-full px-2.5 py-1.5 text-xs font-mono rounded-lg border border-border-strong bg-bg-base text-ink-900 focus:outline-none focus:border-brand"
                />
              </div>

              <div className="space-y-1">
                <label className="text-ink-700 font-semibold block text-[11px]">Related Standards:</label>
                <div className="flex flex-wrap gap-1 mb-1.5">
                  {modRelated.map((r, idx) => (
                    <span key={idx} className="inline-flex items-center gap-1 font-mono text-[11px] px-2 py-0.5 rounded bg-info-soft text-info border border-info/30">
                      {r}
                      <button type="button" onClick={() => removeRelated(idx)} className="text-info hover:text-ink-900">
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-1.5">
                  <input
                    type="text"
                    value={newRelated}
                    onChange={(e) => setNewRelated(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addRelated())}
                    placeholder="Add code (e.g. IS 2026)..."
                    className="flex-1 px-2.5 py-1 text-xs font-mono rounded-lg border border-border-default bg-bg-base text-ink-900 focus:outline-none focus:border-brand"
                  />
                  <button
                    type="button"
                    onClick={addRelated}
                    className="px-2.5 py-1 rounded-lg bg-bg-sunken hover:bg-border-default text-ink-900 text-xs font-bold border border-border-default"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-bold text-ink-700">Modification Justification:</label>
            <input
              type="text"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="e.g. Voltage requirements dictate Part 2 instead of Part 1..."
              className="w-full px-3 py-1.5 text-xs rounded-lg border border-border-strong bg-bg-surface text-ink-900 placeholder-ink-500 focus:outline-none focus:border-brand"
            />
          </div>

          <div className="flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={reset}
              className="px-3.5 py-1.5 rounded-lg border border-border-default text-xs font-semibold text-ink-700 hover:bg-bg-sunken"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleModify}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-info hover:bg-info-hover text-white text-xs font-bold shadow-warm disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Edit3 className="w-3.5 h-3.5" />}
              Save Modification
            </button>
          </div>
        </div>
      )}

      {/* Reject Panel */}
      {mode === 'reject' && (
        <div className="p-5 rounded-xl border border-danger/40 bg-danger-soft/40 space-y-3 animate-slide-up">
          <div className="flex items-center justify-between">
            <span className="text-sm font-bold text-ink-900 flex items-center gap-2">
              <ThumbsDown className="w-4 h-4 text-danger" />
              Reject AI Recommendation
            </span>
            <button onClick={reset} className="text-ink-500 hover:text-ink-900">
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-ink-700">
            Rejected recommendations are recorded in the audit history and excluded from verified memory.
          </p>
          <div className="space-y-1">
            <label className="text-xs font-bold text-ink-700">
              Rejection Justification <span className="text-danger">*</span>
            </label>
            <textarea
              rows={2}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="State why this standard does not match the procurement requirements..."
              className="w-full px-3 py-2 text-xs rounded-lg border border-border-strong bg-bg-surface text-ink-900 placeholder-ink-500 focus:outline-none focus:border-danger"
            />
          </div>
          <div className="flex items-center justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={reset}
              className="px-3.5 py-1.5 rounded-lg border border-border-default text-xs font-semibold text-ink-700 hover:bg-bg-sunken"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleReject}
              disabled={loading || !comment.trim()}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-danger hover:bg-danger-hover text-white text-xs font-bold shadow-warm disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ThumbsDown className="w-3.5 h-3.5" />}
              Confirm Rejection
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export const RecommendationResults: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const recId = searchParams.get('rec_id') || searchParams.get('recommendation_id');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SearchResponse | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  useEffect(() => {
    if (!recId) return;
    setLoading(true);
    setError(null);

    // Call report endpoint to reconstruct search response view
    (api.getReport(recId) as Promise<any>)
      .then((rep) => {
        setData({
          recommendation_id: rep.recommendation_id,
          query: rep.procurement_requirement,
          total_recommendations: rep.all_recommendations?.length || 1,
          data_mode: rep.retrieval_metadata?.data_mode || 'OFFICIAL_CATALOGUE',
          retrieval_mode: rep.retrieval_metadata?.retrieval_mode || 'IN_MEMORY',
          embedding_mode: rep.retrieval_metadata?.embedding_mode || 'REAL_BGE_M3',
          recommendations: rep.all_recommendations || [
            {
              standard_number: rep.primary_recommended_standard.standard_number,
              title: rep.primary_recommended_standard.title,
              relevance_score: rep.primary_recommended_standard.relevance_score,
              score_factors: rep.primary_recommended_standard.score_factors,
              reason: rep.primary_recommended_standard.reason,
              lifecycle_status: rep.primary_recommended_standard.lifecycle_status,
              source: rep.primary_recommended_standard.source,
              status: rep.primary_recommended_standard.lifecycle_status,
              evidence: rep.evidence_audit_trail?.[0]?.evidence_text || 'Official BIS catalogue standard reference.',
              page: rep.evidence_audit_trail?.[0]?.page || 1,
              section: rep.evidence_audit_trail?.[0]?.section || 'Scope',
              related_standards: rep.related_standards,
              compliance: rep.qco_enforcement?.mandates || [],
              is_demo: false,
              demo_tag: 'verified',
              qco_enforcement_flag: rep.qco_enforcement?.is_mandatory || false,
              applicable_scheme: rep.applicable_scheme,
              foreign_standard_warning: rep.foreign_standard_conflict_warning,
              compliance_alerts: rep.compliance_alerts,
            }
          ],
          structured_requirements: rep.extracted_technical_requirements as any,
          verified_memory: rep.verification_information?.verified_at ? {
            verified_answer_id: `va_${rep.recommendation_id.substring(0, 8)}`,
            original_query: rep.procurement_requirement,
            primary_standard: rep.primary_recommended_standard.standard_number,
            engineer_status: rep.engineer_review_status,
            engineer_comment: rep.verification_information.comment || undefined,
            verified_at: rep.verification_information.verified_at || undefined,
            dataset_version: rep.dataset_version,
          } : null,
        });
      })
      .catch((err: any) => {
        console.error(err);
        setError(err.response?.data?.detail || 'Failed to retrieve recommendation session.');
      })
      .finally(() => setLoading(false));
  }, [recId]);

  const primaryRec = data?.recommendations?.[0];
  const secondaryRecs = data?.recommendations?.slice(1) || [];

  return (
    <div className="space-y-8">
      {/* Toast notifications */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
        {toasts.map((t) => (
          <div key={t.id} className="pointer-events-auto">
            <Toast toast={t} onClose={removeToast} />
          </div>
        ))}
      </div>

      {/* Header */}
      <PageHeader
        title="Recommendation Session Results"
        description="Inspect identified Indian Standards, clause provenance, and review decisions for this procurement inquiry."
        action={
          <Link
            to="/search"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-border-default bg-bg-surface hover:bg-bg-sunken text-xs font-bold text-ink-900 transition-colors shadow-warm-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>New Search</span>
          </Link>
        }
      />

      {loading && <CardSkeleton />}

      {error && (
        <Alert variant="error" title="Session Not Found">
          {error}
        </Alert>
      )}

      {!loading && !data && !error && (
        <EmptyState
          icon={Layers}
          title="No Recommendation Session Selected"
          description="Enter a search query or provide a valid recommendation ID in the URL to view results."
          action={{
            label: 'Go to Search',
            onClick: () => navigate('/search'),
          }}
        />
      )}

      {!loading && data && primaryRec && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Main Column */}
          <div className="lg:col-span-8 space-y-6">
            {/* Verified Knowledge Match Banner */}
            {data.verified_memory && (
              <Alert variant="verified-knowledge" title="Verified Knowledge Memory Match Found">
                <p>
                  This technical requirement was approved by technical authority (Status:{' '}
                  <strong>{data.verified_memory.engineer_status}</strong>).
                </p>
              </Alert>
            )}

            {/* Foreign Conflict Alert */}
            {primaryRec.foreign_standard_warning && (
              <Alert variant="statutory-precedence" title="Statutory Precedence Warning (Make in India Order)">
                <p className="font-bold text-accent text-sm">
                  {primaryRec.foreign_standard_warning}
                </p>
              </Alert>
            )}

            {/* Primary Recommendation Card */}
            <div className="p-6 sm:p-8 rounded-2xl bg-bg-surface border-2 border-border-strong shadow-warm space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <CodeChip code={primaryRec.standard_number} variant="primary" copyable />
                    <Badge
                      variant={
                        primaryRec.lifecycle_status === 'SUPERSEDED'
                          ? 'superseded'
                          : primaryRec.lifecycle_status === 'WITHDRAWN'
                          ? 'withdrawn'
                          : 'active'
                      }
                    />
                    {primaryRec.qco_enforcement_flag ? (
                      <Badge variant="qco" scheme={primaryRec.applicable_scheme || 'Scheme I'} />
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-bg-sunken text-ink-500 border border-border-default" title="No verified standalone mandatory QCO order confirmed in active registry. Confirmation recommended prior to tender publishing.">
                        QCO applicability requires verification
                      </span>
                    )}
                  </div>
                  <h2 className="text-xl sm:text-2xl font-bold font-serif text-ink-900">
                    {primaryRec.title}
                  </h2>
                </div>

                <div className="sm:text-right shrink-0">
                  <span className="text-[11px] uppercase font-bold tracking-wider text-ink-500 block">
                    Relevance Score
                  </span>
                  <span className="font-mono text-3xl font-extrabold text-ink-900 tabular-nums">
                    {primaryRec.relevance_score.toFixed(2)}
                    <span className="text-sm font-normal text-ink-500 ml-1">/ 1.00</span>
                  </span>
                  <div className="text-[10px] text-ink-500 font-medium">Weighted similarity</div>
                  <ConfidenceMeter score={primaryRec.relevance_score} size="sm" showPercent={false} label="Relevance Alignment" className="w-28 mt-1" />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-bg-sunken border border-border-default space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-ink-700">
                    Recommendation Grounding Rationale
                  </span>
                  <ScorePopover
                    scoreFactors={primaryRec.score_factors || undefined}
                    relevanceScore={primaryRec.relevance_score}
                  />
                </div>
                <p className="text-sm text-ink-700 leading-relaxed font-medium">
                  {primaryRec.reason}
                </p>
              </div>

              {/* Evidence Quote */}
              <div className="space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-ink-500 flex items-center gap-1.5">
                  <BookOpen className="w-4 h-4 text-brand" />
                  Official Clause Provenance
                </span>
                {primaryRec.evidence && !primaryRec.evidence.toLowerCase().includes('insufficient evidence') ? (
                  <div className="p-4 rounded-xl bg-bg-base/60 border border-border-default border-l-4 border-l-brand text-xs space-y-2">
                    <p className="italic font-serif text-ink-900 leading-relaxed text-sm">
                      &ldquo;{primaryRec.evidence}&rdquo;
                    </p>
                    <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-ink-500 pt-1 border-t border-border-default">
                      <span>Page: {primaryRec.page || 'N/A'}</span>
                      <span>•</span>
                      <span>Section: {primaryRec.section || 'Scope & Applications'}</span>
                      <span>•</span>
                      <span>Source: {primaryRec.source || 'BIS Standards Catalogue'}</span>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 border-l-4 border-l-amber-500 text-xs space-y-2">
                    <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400 font-bold text-xs uppercase tracking-wider">
                      <AlertTriangle className="w-4 h-4 shrink-0" />
                      <span>Insufficient evidence &mdash; Clause verification required</span>
                    </div>
                    <p className="text-ink-700 leading-relaxed text-xs">
                      Supporting clause text could not be verified from the retrieved source record. Catalog metadata, section titles, or page references alone do not prove statutory or technical applicability. Manual clause-level provenance verification is required.
                    </p>
                  </div>
                )}
              </div>

              {/* Related Standards */}
              {primaryRec.related_standards && primaryRec.related_standards.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-ink-500">
                    Normative References & Testing Standards:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {primaryRec.related_standards.map((rel, idx) => (
                      <Link
                        key={idx}
                        to={`/standards/${encodeURIComponent(rel.standard_number)}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg border border-border-default bg-bg-surface hover:border-brand text-xs text-ink-900 font-semibold transition-all shadow-warm-sm"
                      >
                        <span className="font-mono text-brand">{rel.standard_number}</span>
                        <span className="text-[10px] text-ink-500 font-mono">({rel.relation.replace(/_/g, ' ')})</span>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Review Bar */}
              <ReviewPanel
                recommendationId={data.recommendation_id}
                primaryStandard={primaryRec.standard_number}
                relatedStandards={primaryRec.related_standards?.map((r) => r.standard_number) || []}
                status={(data.verified_memory?.engineer_status as ReviewAction) || 'PENDING'}
                onStatusChange={(newStatus) => {
                  if (data.verified_memory) {
                    data.verified_memory.engineer_status = newStatus;
                  }
                }}
                onToast={addToast}
              />
            </div>

            {/* Secondary Recs */}
            {secondaryRecs.length > 0 && (
              <div className="space-y-4 pt-4">
                <h3 className="text-lg font-bold font-serif text-ink-900">
                  Alternative Standards ({secondaryRecs.length})
                </h3>
                <div className="space-y-3">
                  {secondaryRecs.map((rec, idx) => (
                    <div
                      key={idx}
                      className="p-5 rounded-2xl bg-bg-surface border border-border-default shadow-warm flex items-center justify-between gap-4"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <CodeChip code={rec.standard_number} variant="secondary" />
                          <Badge variant={rec.lifecycle_status === 'SUPERSEDED' ? 'superseded' : 'active'} />
                        </div>
                        <h4 className="font-bold text-sm text-ink-900">{rec.title}</h4>
                      </div>
                      <Link
                        to={`/standards/${encodeURIComponent(rec.standard_number)}`}
                        className="p-2 rounded-lg border border-border-default hover:border-brand text-brand hover:bg-bg-sunken transition-colors"
                      >
                        <ChevronRight className="w-5 h-5" />
                      </Link>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Side Rail */}
          <div className="lg:col-span-4 space-y-6 lg:sticky lg:top-24">
            <div className="p-6 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-4">
              <span className="font-bold text-sm font-serif text-ink-900 block border-b border-border-default pb-3">
                Session Metadata
              </span>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-ink-500 font-semibold">Session ID:</span>
                  <span className="font-mono font-bold text-ink-900">{data.recommendation_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-500 font-semibold">Retrieval:</span>
                  <span className="font-mono font-bold text-brand">{data.retrieval_mode}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-500 font-semibold">Embeddings:</span>
                  <span className="font-mono font-bold text-brand">{data.embedding_mode}</span>
                </div>
              </div>

              <div className="pt-3 border-t border-border-default flex flex-col gap-2">
                <a
                  href={api.getReportDownloadUrl(data.recommendation_id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full py-2.5 px-4 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-warm flex items-center justify-center gap-2"
                >
                  <FileDown className="w-4 h-4" />
                  <span>Download Audit PDF</span>
                </a>
                <a
                  href={`${api.getReportDownloadUrl(data.recommendation_id)}?format=html`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full py-2.5 px-4 rounded-xl bg-bg-sunken hover:bg-border-default border border-border-default text-ink-900 text-xs font-bold transition-all shadow-warm-sm flex items-center justify-center gap-2"
                >
                  <Printer className="w-4 h-4" />
                  <span>Print Document</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
