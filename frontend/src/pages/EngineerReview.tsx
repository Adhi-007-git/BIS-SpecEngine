import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  ClipboardCheck,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Search,
  History,
  CheckCircle2,
  Calendar,
  Layers,
  ArrowRight,
  Loader2
} from 'lucide-react';
import { api } from '../services/api';
import { VerifiedAnswerDTO, ReviewAction, ReviewHistoryEntry } from '../types';
import { Badge, CodeChip, EmptyState, Modal, PageHeader } from '../components/ui';

export const EngineerReview: React.FC = () => {
  const [records, setRecords] = useState<VerifiedAnswerDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [historyModalRecord, setHistoryModalRecord] = useState<VerifiedAnswerDTO | null>(null);
  const [historyEntries, setHistoryEntries] = useState<ReviewHistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchKnowledge = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const filter = statusFilter === 'ALL' ? undefined : statusFilter;
      const data = await api.getVerifiedKnowledge(filter);
      setRecords(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load verified knowledge records.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchKnowledge();
  }, [fetchKnowledge]);

  const viewHistory = async (rec: VerifiedAnswerDTO) => {
    setHistoryModalRecord(rec);
    if (!rec.recommendation_id) return;
    setHistoryLoading(true);
    try {
      const entries = await api.getReviewHistory(rec.recommendation_id);
      setHistoryEntries(entries);
    } catch {
      setHistoryEntries([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const filteredRecords = records.filter((r) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.original_query.toLowerCase().includes(q) ||
      r.primary_standard.toLowerCase().includes(q) ||
      (r.engineer_comment && r.engineer_comment.toLowerCase().includes(q))
    );
  });

  const counts = {
    ALL: records.length,
    APPROVED: records.filter((r) => r.engineer_status === 'APPROVED').length,
    MODIFIED: records.filter((r) => r.engineer_status === 'MODIFIED').length,
    REJECTED: records.filter((r) => r.engineer_status === 'REJECTED').length,
    PENDING: records.filter((r) => r.engineer_status === 'PENDING').length,
  };

  return (
    <div className="space-y-8">
      {/* ── 1. Page Header ─────────────────────────────────────────────────── */}
      <PageHeader
        title="Verified Knowledge & Engineer Review Queue"
        description="Persistent repository of technical engineer decisions. Approved and modified decisions serve as pre-verified answers for matching tender specifications."
        badge={
          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-bg-sunken text-ink-900 border border-border-default">
            Human-in-the-Loop Authority
          </span>
        }
        action={
          <button
            onClick={fetchKnowledge}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-border-default bg-bg-surface hover:bg-bg-sunken text-xs font-bold text-ink-900 transition-colors shadow-warm-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Queue</span>
          </button>
        }
      />

      {/* ── 2. Filters & Search Bar ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Status Tab Pills */}
        <div className="flex items-center gap-1.5 bg-bg-sunken p-1.5 rounded-2xl border border-border-default overflow-x-auto w-full sm:w-auto">
          {(['ALL', 'APPROVED', 'MODIFIED', 'REJECTED', 'PENDING'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                statusFilter === status
                  ? 'bg-bg-surface text-ink-900 border border-border-strong shadow-warm-sm'
                  : 'text-ink-500 hover:text-ink-900'
              }`}
            >
              {status} ({counts[status] || 0})
            </button>
          ))}
        </div>

        {/* Search Filter */}
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-2.5 w-4 h-4 text-ink-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by query, standard, comment..."
            className="w-full pl-10 pr-4 py-2 rounded-xl border border-border-strong bg-bg-surface text-xs text-ink-900 placeholder-ink-500 focus:outline-none focus:border-brand"
          />
        </div>
      </div>

      {/* ── 3. Queue List / Table ───────────────────────────────────────────── */}
      {loading && (
        <div className="p-12 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-brand animate-spin mx-auto" />
          <p className="text-sm font-semibold text-ink-500">Loading verified memory records...</p>
        </div>
      )}

      {!loading && filteredRecords.length === 0 && (
        <EmptyState
          icon={ClipboardCheck}
          title="No Review Records Found"
          description={
            searchQuery
              ? `No records match query '${searchQuery}' with filter '${statusFilter}'.`
              : `No verified memory records currently under '${statusFilter}'. Decisions recorded in search results appear here.`
          }
        />
      )}

      {!loading && filteredRecords.length > 0 && (
        <div className="space-y-4">
          {filteredRecords.map((rec) => {
            const isExpanded = expandedId === rec.id;
            return (
              <div
                key={rec.id}
                className="p-6 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-4 transition-all"
              >
                {/* Header row */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-2 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <CodeChip code={rec.primary_standard} variant="primary" />
                      <Badge
                        variant={
                          rec.engineer_status === 'APPROVED'
                            ? 'approved'
                            : rec.engineer_status === 'MODIFIED'
                            ? 'modified'
                            : rec.engineer_status === 'REJECTED'
                            ? 'rejected'
                            : 'pending'
                        }
                      />
                      {rec.dataset_version && (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-bg-sunken text-ink-500 border border-border-default">
                          {rec.dataset_version}
                        </span>
                      )}
                    </div>

                    <h3 className="font-bold text-base text-ink-900 leading-snug">
                      &ldquo;{rec.original_query}&rdquo;
                    </h3>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => viewHistory(rec)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border-default bg-bg-sunken hover:bg-border-default text-xs font-bold text-ink-900 transition-colors shadow-warm-sm"
                      title="Inspect immutable audit history"
                    >
                      <History className="w-3.5 h-3.5 text-brand" />
                      <span>Audit Trail</span>
                    </button>

                    <button
                      onClick={() => setExpandedId(isExpanded ? null : rec.id)}
                      className="p-1.5 rounded-lg border border-border-default bg-bg-sunken hover:bg-border-default text-ink-700 hover:text-ink-900 transition-colors"
                      title={isExpanded ? 'Collapse' : 'Expand details'}
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Comment excerpt if present */}
                {rec.engineer_comment && (
                  <p className="text-xs text-ink-700 bg-bg-sunken/60 p-3 rounded-xl border border-border-default italic">
                    Note: &ldquo;{rec.engineer_comment}&rdquo;
                  </p>
                )}

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="pt-4 border-t border-border-default space-y-4 text-xs animate-slide-up">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="p-4 rounded-xl border border-border-default bg-bg-sunken space-y-2">
                        <span className="font-bold uppercase tracking-wider text-ink-500 block">
                          Related References Grounded:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {rec.related_standards && rec.related_standards.length > 0 ? (
                            rec.related_standards.map((rel, idx) => (
                              <CodeChip key={idx} code={rel} variant="secondary" />
                            ))
                          ) : (
                            <span className="text-ink-500 italic">No secondary references recorded.</span>
                          )}
                        </div>
                      </div>

                      <div className="p-4 rounded-xl border border-border-default bg-bg-sunken space-y-2">
                        <span className="font-bold uppercase tracking-wider text-ink-500 block">
                          Verification Provenance:
                        </span>
                        <div className="space-y-1 text-ink-700">
                          <div>Record ID: <strong className="font-mono text-ink-900">{rec.id}</strong></div>
                          <div>Verified At: <strong className="text-ink-900">{rec.verified_at || 'Recorded in Session'}</strong></div>
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-end gap-2 pt-2">
                      <Link
                        to={`/standards/${encodeURIComponent(rec.primary_standard)}`}
                        className="px-4 py-2 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-warm flex items-center gap-1.5"
                      >
                        <span>Inspect Primary Standard</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ── 4. Immutable Audit Trail Modal ─────────────────────────────────── */}
      <Modal
        isOpen={!!historyModalRecord}
        onClose={() => setHistoryModalRecord(null)}
        title="Immutable Verification Audit Log"
        subtitle={historyModalRecord ? `Recommendation ${historyModalRecord.recommendation_id || historyModalRecord.id}` : undefined}
      >
        {historyLoading ? (
          <div className="p-8 text-center space-y-2">
            <Loader2 className="w-6 h-6 text-brand animate-spin mx-auto" />
            <p className="text-xs text-ink-500">Loading audit log events...</p>
          </div>
        ) : historyEntries.length === 0 ? (
          <div className="p-6 text-center text-xs text-ink-500">
            No audit log entries recorded for this item.
          </div>
        ) : (
          <div className="space-y-4">
            {historyEntries.map((entry, idx) => (
              <div
                key={entry.id || idx}
                className="p-4 rounded-xl border border-border-default bg-bg-sunken space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <Badge
                    variant={
                      entry.action === 'APPROVED'
                        ? 'approved'
                        : entry.action === 'MODIFIED'
                        ? 'modified'
                        : 'rejected'
                    }
                  />
                  <span className="font-mono text-[11px] text-ink-500">
                    {entry.timestamp || 'Recorded'}
                  </span>
                </div>
                {entry.engineer_comment && (
                  <p className="text-ink-700 italic">
                    &ldquo;{entry.engineer_comment}&rdquo;
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
};
