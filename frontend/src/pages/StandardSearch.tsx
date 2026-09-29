import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import {
  Search,
  SlidersHorizontal,
  Loader2,
  FileText,
  ShieldCheck,
  CheckCircle,
  Network,
  ChevronRight,
  BookOpen,
  Check,
  Edit3,
  ThumbsDown,
  Clock,
  X,
  Plus,
  ClipboardCheck,
  FileDown,
  Printer,
  Scale,
  Copy,
  ChevronDown,
  ChevronUp,
  AlertTriangle
} from 'lucide-react';
import { api } from '../services/api';
import {
  SearchResponse,
  RecommendationItem,
  StructuredRequirements,
  QueryAnalysis,
  ReviewAction,
} from '../types';
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
              placeholder="e.g. Verified against CPWD technical specifications clause 12.4..."
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
            {/* Original AI Output */}
            <div className="p-3.5 rounded-xl border border-border-default bg-bg-surface space-y-2">
              <span className="font-bold text-[11px] uppercase tracking-wider text-ink-500 block">
                Original AI Output:
              </span>
              <div className="space-y-1">
                <span className="text-ink-500 text-[11px]">Primary:</span>
                <div><CodeChip code={primaryStandard} variant="secondary" /></div>
              </div>
              <div className="space-y-1">
                <span className="text-ink-500 text-[11px]">Related References:</span>
                <div className="flex flex-wrap gap-1">
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

            {/* Engineer Modified Version */}
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
                  {modRelated.map((r, i) => (
                    <span key={i} className="inline-flex items-center gap-1 font-mono text-[11px] px-2 py-0.5 rounded bg-info-soft text-info border border-info/30">
                      {r}
                      <button type="button" onClick={() => removeRelated(i)} className="text-info hover:text-ink-900">
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
                    placeholder="Add standard (e.g. IS 2026)..."
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
              placeholder="e.g. Project voltage rating requires Part 2 specification..."
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
            Rejected items are recorded in the immutable audit trail and excluded from Verified Knowledge Memory.
          </p>
          <div className="space-y-1">
            <label className="text-xs font-bold text-ink-700">
              Rejection Justification <span className="text-danger">*</span>
            </label>
            <textarea
              rows={2}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="State technical reason (e.g. Scope inapplicable for high-voltage transmission)..."
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

// ─── Main Standard Search Page ────────────────────────────────────────────────
export const StandardSearch: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [domain, setDomain] = useState(searchParams.get('domain') || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [expandedExcluded, setExpandedExcluded] = useState(false);

  const addToast = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const executeSearch = useCallback(async (searchQuery: string, domainFilter?: string) => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.searchStandards(searchQuery.trim(), 5, domainFilter || undefined);
      setResult(data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to retrieve standards. Check server connectivity.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const q = searchParams.get('q');
    const d = searchParams.get('domain');
    if (q) {
      setQuery(q);
      if (d) setDomain(d);
      executeSearch(q, d || undefined);
    }
  }, [searchParams, executeSearch]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    const params: Record<string, string> = { q: query.trim() };
    if (domain) params.domain = domain;
    setSearchParams(params);
  };

  const primaryRec = result?.recommendations?.[0];
  const secondaryRecs = result?.recommendations?.slice(1) || [];

  return (
    <div className="space-y-8">
      {/* Toast Notification Container */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
        {toasts.map((t) => (
          <div key={t.id} className="pointer-events-auto">
            <Toast toast={t} onClose={removeToast} />
          </div>
        ))}
      </div>

      {/* ── 1. Page Header ─────────────────────────────────────────────────── */}
      <PageHeader
        title="Search Indian Standards (IS)"
        description="Deterministic query extraction and grounded retrieval across 21 verified BIS standards with DPIIT Quality Control Orders."
        badge={
          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-bg-sunken text-ink-900 border border-border-default">
            SIH26108 · Active Catalogue
          </span>
        }
      />

      {/* ── 2. Search Input & Domain Filter Form ────────────────────────────── */}
      <div className="p-6 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex flex-col lg:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-5 h-5 text-ink-500 absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter procurement specification (e.g. Heavy duty armoured PVC electric cables up to 1100 V)..."
                className="w-full pl-12 pr-4 py-3 text-sm rounded-xl border border-border-strong bg-bg-base/50 text-ink-900 placeholder-ink-500 focus:outline-none focus:border-brand focus:bg-bg-surface font-medium transition-all"
              />
            </div>

            <div className="flex gap-2">
              <select
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="px-4 py-3 rounded-xl border border-border-strong bg-bg-surface text-ink-900 text-xs font-bold focus:outline-none focus:border-brand"
              >
                <option value="">All Domains</option>
                <option value="electrical">Electrical & Cables</option>
                <option value="civil">Civil & Structural Steel</option>
                <option value="mechanical">Mechanical & Pipes</option>
                <option value="transformers">Distribution Transformers</option>
              </select>

              <button
                type="submit"
                disabled={loading}
                className="px-6 py-3 rounded-xl bg-brand hover:bg-brand-hover text-white text-sm font-bold transition-all shadow-warm shrink-0 flex items-center gap-2 disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                <span>Search Standards</span>
              </button>
            </div>
          </div>
        </form>

        {/* Demo Query Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-border-default text-xs">
          <span className="font-bold uppercase tracking-wider text-ink-500 text-[11px]">Suggested Queries:</span>
          {[
            { label: "1100V Armoured Cable", q: "Heavy duty armoured PVC electric cables up to 1100 V" },
            { label: "Oil Cooled Transformer", q: "500 kVA outdoor oil cooled distribution transformer 11 kV/433 V" },
            { label: "TMT Rebars Fe 500", q: "Structural steel high strength deformed bars for concrete reinforcement Fe 500" },
            { label: "Reinforced Concrete", q: "Plain and reinforced concrete construction works" },
            { label: "ASTM A36 Foreign Conflict", q: "ASTM A36 carbon structural steel plates for fabrication" },
          ].map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => {
                setQuery(item.q);
                setSearchParams({ q: item.q });
              }}
              className="px-2.5 py-1 rounded-lg border border-border-default bg-bg-sunken hover:border-brand hover:bg-bg-surface text-ink-900 text-xs font-semibold transition-all shadow-warm-sm"
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── 3. Results Layout (Two-Column on Large Screens) ─────────────────── */}
      {loading && (
        <div className="space-y-4">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      )}

      {error && (
        <Alert variant="error" title="Retrieval Failure">
          {error}
        </Alert>
      )}

      {!loading && !result && !error && (
        <EmptyState
          icon={Search}
          title="Ready to Search Indian Standards"
          description="Type a procurement specification or click one of the suggested query chips above to evaluate applicability, QCO mandates, and evidence citations."
        />
      )}

      {!loading && result && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Main Column (8 of 12 columns) */}
          <div className="lg:col-span-8 space-y-6">
            {/* Verified Knowledge Match Banner */}
            {result.verified_memory && (
              <Alert variant="verified-knowledge" title="Verified Knowledge Memory Match Found">
                <div className="space-y-1">
                  <p>
                    This technical specification was previously pre-verified by an authorized engineer (Status:{' '}
                    <strong>{result.verified_memory.engineer_status}</strong>).
                  </p>
                  {result.verified_memory.engineer_comment && (
                    <p className="italic text-xs text-ink-700">
                      &ldquo;{result.verified_memory.engineer_comment}&rdquo;
                    </p>
                  )}
                  {result.verified_memory.status_verification && !result.verified_memory.status_verification.is_active && (
                    <p className="text-danger font-bold text-xs">
                      Warning: Standard status changed since verification ({result.verified_memory.status_verification.status}). Re-verification required.
                    </p>
                  )}
                </div>
              </Alert>
            )}

            {/* Foreign Standard Statutory Precedence Alert */}
            {primaryRec?.foreign_standard_warning && (
              <Alert variant="statutory-precedence" title="Statutory Precedence Warning (Make in India Order)">
                <div className="space-y-1">
                  <p className="font-semibold text-ink-900">
                    Foreign specification detected in requirement. Under Public Procurement (Preference to Make in India) Order 2017:
                  </p>
                  <p className="font-bold text-accent text-sm">
                    {primaryRec.foreign_standard_warning}
                  </p>
                </div>
              </Alert>
            )}

            {/* Primary Recommendation Hero Card */}
            {primaryRec ? (
              <div className="p-6 sm:p-8 rounded-2xl bg-bg-surface border-2 border-border-strong shadow-warm space-y-6">
                {/* Header row */}
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
                    <h2 className="text-xl sm:text-2xl font-bold font-serif text-ink-900 leading-snug">
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

                {/* Score popover & Reason */}
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

                {/* Evidence Clause Preview */}
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

                {/* Normative & Related Standards */}
                {primaryRec.related_standards && primaryRec.related_standards.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-ink-500">
                      Normative References & Mandatory Testing Standards:
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

                {/* Card Actions Toolbar */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-border-default">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      to={`/standards/${encodeURIComponent(primaryRec.standard_number)}`}
                      className="px-3.5 py-1.5 rounded-lg border border-border-default bg-bg-surface hover:bg-bg-sunken text-xs font-bold text-ink-900 transition-colors shadow-warm-sm"
                    >
                      View Details
                    </Link>
                    <Link
                      to={`/evidence?rec_id=${result.recommendation_id}`}
                      className="px-3.5 py-1.5 rounded-lg border border-border-default bg-bg-surface hover:bg-bg-sunken text-xs font-bold text-ink-900 transition-colors shadow-warm-sm"
                    >
                      View Full Evidence
                    </Link>
                    <Link
                      to={`/graph/${encodeURIComponent(primaryRec.standard_number)}`}
                      className="px-3.5 py-1.5 rounded-lg border border-border-default bg-bg-surface hover:bg-bg-sunken text-xs font-bold text-ink-900 transition-colors shadow-warm-sm flex items-center gap-1"
                    >
                      <Network className="w-3.5 h-3.5 text-brand" />
                      <span>Graph</span>
                    </Link>
                  </div>

                  <div className="flex items-center gap-2">
                    <a
                      href={api.getReportDownloadUrl(result.recommendation_id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3.5 py-1.5 rounded-lg bg-bg-sunken hover:bg-border-default text-ink-900 border border-border-default text-xs font-bold transition-colors flex items-center gap-1.5 shadow-warm-sm"
                    >
                      <FileDown className="w-3.5 h-3.5" />
                      <span>PDF</span>
                    </a>
                    <a
                      href={`/api/reports/${encodeURIComponent(result.recommendation_id)}?format=html`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3.5 py-1.5 rounded-lg bg-bg-sunken hover:bg-border-default text-ink-900 border border-border-default text-xs font-bold transition-colors flex items-center gap-1.5 shadow-warm-sm"
                    >
                      <Printer className="w-3.5 h-3.5" />
                      <span>Print</span>
                    </a>
                  </div>
                </div>

                {/* Inline Engineer Review Bar */}
                <ReviewPanel
                  recommendationId={result.recommendation_id}
                  primaryStandard={primaryRec.standard_number}
                  relatedStandards={primaryRec.related_standards?.map((r) => r.standard_number) || []}
                  status={(result.verified_memory?.engineer_status as ReviewAction) || 'PENDING'}
                  onStatusChange={(newStatus) => {
                    if (result.verified_memory) {
                      result.verified_memory.engineer_status = newStatus;
                    }
                  }}
                  onToast={addToast}
                />
              </div>
            ) : (
              <EmptyState
                icon={BookOpen}
                title="No Standard Met Grounding Threshold"
                description="The verified BIS catalogue did not return an applicable Indian Standard with sufficient grounding confidence."
              />
            )}

            {/* Secondary Recommendations List */}
            {secondaryRecs.length > 0 && (
              <div className="space-y-4 pt-4">
                <h3 className="text-lg font-bold font-serif text-ink-900">
                  Alternative & Related Candidates ({secondaryRecs.length})
                </h3>
                <div className="space-y-3">
                  {secondaryRecs.map((rec, idx) => (
                    <div
                      key={idx}
                      className="p-5 rounded-2xl bg-bg-surface border border-border-default shadow-warm warm-card-interactive flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                    >
                      <div className="space-y-1.5 flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <CodeChip code={rec.standard_number} variant="secondary" />
                          <Badge
                            variant={
                              rec.lifecycle_status === 'SUPERSEDED'
                                ? 'superseded'
                                : rec.lifecycle_status === 'WITHDRAWN'
                                ? 'withdrawn'
                                : 'active'
                            }
                          />
                          {rec.qco_enforcement_flag ? (
                            <Badge variant="qco" scheme={rec.applicable_scheme || undefined} />
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-bg-sunken text-ink-500 border border-border-default" title="No verified standalone mandatory QCO order confirmed in active registry. Confirmation recommended prior to tender publishing.">
                              QCO verification required
                            </span>
                          )}
                        </div>
                        <h4 className="font-bold text-sm text-ink-900 truncate">
                          {rec.title}
                        </h4>
                        <p className="text-xs text-ink-500 line-clamp-2">
                          {rec.reason}
                        </p>
                      </div>

                      <div className="flex items-center gap-4 shrink-0 sm:border-l sm:border-border-default sm:pl-4">
                        <div className="text-right">
                          <span className="text-[10px] uppercase font-bold text-ink-500 block">Relevance</span>
                          <span className="font-mono text-sm font-bold text-ink-900 tabular-nums">
                            {rec.relevance_score.toFixed(2)} <span className="text-xs font-normal text-ink-500">/ 1.00</span>
                          </span>
                          <ConfidenceMeter score={rec.relevance_score} size="sm" showPercent={false} label="Relevance Alignment" className="w-20" />
                        </div>
                        <Link
                          to={`/standards/${encodeURIComponent(rec.standard_number)}`}
                          className="p-2 rounded-lg border border-border-default hover:border-brand text-brand hover:bg-bg-sunken transition-colors"
                          title="View Details"
                        >
                          <ChevronRight className="w-5 h-5" />
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Excluded Candidates Section */}
            {result.excluded_candidates && result.excluded_candidates.length > 0 && (
              <div className="rounded-2xl border border-border-default bg-bg-surface shadow-warm overflow-hidden">
                <button
                  type="button"
                  onClick={() => setExpandedExcluded(!expandedExcluded)}
                  className="w-full p-4 flex items-center justify-between bg-bg-sunken/60 hover:bg-bg-sunken text-left transition-colors"
                >
                  <span className="text-xs font-bold uppercase tracking-wider text-ink-700">
                    Excluded Standards ({result.excluded_candidates.length}) · Technical Constraint Incompatibilities
                  </span>
                  {expandedExcluded ? <ChevronUp className="w-4 h-4 text-ink-500" /> : <ChevronDown className="w-4 h-4 text-ink-500" />}
                </button>
                {expandedExcluded && (
                  <div className="p-4 divide-y divide-border-default space-y-3">
                    {result.excluded_candidates.map((exc, i) => (
                      <div key={i} className="pt-3 first:pt-0 space-y-1 text-xs">
                        <div className="flex items-center gap-2">
                          <CodeChip code={exc.standard_number} variant="secondary" />
                          <span className="font-bold text-ink-900">{exc.title}</span>
                        </div>
                        <p className="text-ink-500 font-medium pl-2 border-l-2 border-border-strong">
                          Reason: {exc.exclusion_reason}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Sticky Side Rail (4 of 12 columns) */}
          <div className="lg:col-span-4 space-y-6 lg:sticky lg:top-24">
            {/* Extracted Requirements Key-Value Panel */}
            <div className="p-6 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-4">
              <div className="flex items-center justify-between border-b border-border-default pb-3">
                <span className="font-bold text-sm font-serif text-ink-900 flex items-center gap-2">
                  <SlidersHorizontal className="w-4 h-4 text-brand" />
                  Extracted Parameters
                </span>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-bg-sunken text-ink-700 border border-border-default uppercase">
                  Deterministic
                </span>
              </div>

              {result.structured_requirements ? (
                <div className="space-y-3 text-xs">
                  {result.structured_requirements.product && (
                    <div className="flex justify-between border-b border-border-default/60 pb-1.5">
                      <span className="font-semibold text-ink-500">Equipment / Product:</span>
                      <span className="font-bold text-ink-900 text-right">{result.structured_requirements.product}</span>
                    </div>
                  )}
                  {result.structured_requirements.primary_voltage && (
                    <div className="flex justify-between border-b border-border-default/60 pb-1.5">
                      <span className="font-semibold text-ink-500">Voltage Rating:</span>
                      <span className="font-mono font-bold text-ink-900">{result.structured_requirements.primary_voltage}</span>
                    </div>
                  )}
                  {result.structured_requirements.capacity && (
                    <div className="flex justify-between border-b border-border-default/60 pb-1.5">
                      <span className="font-semibold text-ink-500">Capacity / Power:</span>
                      <span className="font-mono font-bold text-ink-900">{result.structured_requirements.capacity}</span>
                    </div>
                  )}
                  {result.structured_requirements.cooling && (
                    <div className="flex justify-between border-b border-border-default/60 pb-1.5">
                      <span className="font-semibold text-ink-500">Cooling Medium:</span>
                      <span className="font-bold text-ink-900">{result.structured_requirements.cooling}</span>
                    </div>
                  )}
                  {result.structured_requirements.installation && (
                    <div className="flex justify-between border-b border-border-default/60 pb-1.5">
                      <span className="font-semibold text-ink-500">Installation:</span>
                      <span className="font-bold text-ink-900">{result.structured_requirements.installation}</span>
                    </div>
                  )}
                  {result.structured_requirements.foreign_standards && result.structured_requirements.foreign_standards.length > 0 && (
                    <div className="pt-1">
                      <span className="font-semibold text-accent block mb-1">Foreign Standards Detected:</span>
                      <div className="flex flex-wrap gap-1">
                        {result.structured_requirements.foreign_standards.map((f, i) => (
                          <span key={i} className="px-2 py-0.5 rounded bg-warning-soft text-accent border border-accent/40 font-mono text-[11px] font-bold">
                            {f}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-ink-500 italic">
                  No technical constraints extracted from raw tokens.
                </p>
              )}
            </div>

            {/* Compliance & Regulatory Alerts */}
            {primaryRec?.compliance_alerts && primaryRec.compliance_alerts.length > 0 && (
              <div className="p-6 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-3">
                <span className="text-xs font-bold uppercase tracking-wider text-ink-900 flex items-center gap-1.5">
                  <Scale className="w-4 h-4 text-accent" />
                  Statutory Compliance Advisories
                </span>
                <ul className="space-y-2 text-xs">
                  {primaryRec.compliance_alerts.map((alert, i) => (
                    <li key={i} className="p-2.5 rounded-lg bg-warning-soft text-ink-900 border border-border-default text-xs leading-normal flex items-start gap-2">
                      <span className="text-accent font-bold">•</span>
                      <span>{alert}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Official Audit Report Generation */}
            <div className="p-6 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-ink-900 block">
                Audit Trail & Procurement Documentation
              </span>
              <p className="text-xs text-ink-500 leading-relaxed">
                Generate the 15-section verified recommendation compliance certificate for procurement file records.
              </p>
              <div className="flex flex-col gap-2 pt-1">
                <a
                  href={api.getReportDownloadUrl(result.recommendation_id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full py-2.5 px-4 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-warm flex items-center justify-center gap-2"
                >
                  <FileDown className="w-4 h-4" />
                  <span>Download Compliance PDF</span>
                </a>
                <a
                  href={`/api/reports/${encodeURIComponent(result.recommendation_id)}?format=html`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full py-2.5 px-4 rounded-xl bg-bg-sunken hover:bg-border-default border border-border-default text-ink-900 text-xs font-bold transition-all shadow-warm-sm flex items-center justify-center gap-2"
                >
                  <Printer className="w-4 h-4" />
                  <span>Official Printable Document</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
