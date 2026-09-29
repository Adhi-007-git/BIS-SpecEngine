import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  FileCheck2,
  CheckCircle2,
  Loader2,
  Search,
  ArrowLeft,
  Copy,
  Check,
  BookOpen,
  ShieldAlert
} from 'lucide-react';
import { clsx } from 'clsx';
import { api } from '../services/api';
import { EvidenceItem } from '../types';
import { CodeChip, ConfidenceMeter, Badge, EmptyState, Alert, PageHeader } from '../components/ui';

export const EvidenceViewer: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const recIdParam = searchParams.get('recId');
  const stdFilter = searchParams.get('std');

  const [inputRecId, setInputRecId] = useState(recIdParam || '');
  const [evidences, setEvidences] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const fetchEvidence = async (id: string) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getEvidence(id.trim());
      setEvidences(data);
      setSearchParams({ recId: id.trim() });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'No evidence records found for this recommendation session.');
      setEvidences([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (recIdParam) {
      fetchEvidence(recIdParam);
    } else {
      // Run quick query to get a live recommendation session if accessed directly
      api.searchStandards("waterproof electrical cables in buildings", 3)
        .then((res) => {
          setInputRecId(res.recommendation_id);
          fetchEvidence(res.recommendation_id);
        })
        .catch(() => {});
    }
  }, [recIdParam]);

  const filteredEvidences = stdFilter
    ? evidences.filter((e) => e.standard_number.toLowerCase().includes(stdFilter.toLowerCase()))
    : evidences;

  const handleCopyCitation = (ev: EvidenceItem, idx: number) => {
    const citation = `"${ev.evidence_text}" — ${ev.standard_number}, Page ${ev.page || 'N/A'}, Section ${ev.section || 'Scope'}`;
    navigator.clipboard.writeText(citation);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 1800);
  };

  // Group evidences by standard number
  const groupedEvidences: Record<string, EvidenceItem[]> = {};
  filteredEvidences.forEach((ev) => {
    if (!groupedEvidences[ev.standard_number]) {
      groupedEvidences[ev.standard_number] = [];
    }
    groupedEvidences[ev.standard_number].push(ev);
  });

  return (
    <div className="space-y-8">
      {/* ── 1. Page Header ─────────────────────────────────────────────────── */}
      <PageHeader
        title="Evidence-First Verification & Audit Trail"
        description="Every recommendation is substantiated by verbatim text extracts with page and clause coordinates from official BIS documents. Synthetic claims are rejected."
        badge={
          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-success-soft text-success border border-success/40">
            Audit Grade Provenance
          </span>
        }
        action={
          <Link
            to="/search"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-border-default bg-bg-surface hover:bg-bg-sunken text-xs font-bold text-ink-900 transition-colors shadow-warm-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Search</span>
          </Link>
        }
      />

      {/* ── 2. Session Inspector Bar ────────────────────────────────────────── */}
      <div className="p-6 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-4">
        <div className="flex flex-col sm:flex-row items-stretch gap-3">
          <div className="relative flex-1">
            <span className="text-xs font-bold text-ink-500 uppercase tracking-wider block mb-1.5">
              Inspect Recommendation Session ID:
            </span>
            <input
              type="text"
              value={inputRecId}
              onChange={(e) => setInputRecId(e.target.value)}
              placeholder="e.g. rec_cb78e38d-8a6c..."
              className="w-full px-4 py-2.5 rounded-xl border border-border-strong bg-bg-base/50 text-xs font-mono text-ink-900 placeholder-ink-500 focus:outline-none focus:border-brand focus:bg-bg-surface"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => fetchEvidence(inputRecId)}
              disabled={loading || !inputRecId.trim()}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-warm flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              <span>Fetch Evidence Records</span>
            </button>
          </div>
        </div>

        {recIdParam && (
          <div className="flex items-center gap-2 text-xs font-mono text-ink-500 border-t border-border-default pt-3">
            <span className="font-bold text-ink-700">Active Session:</span>
            <span className="px-2 py-0.5 rounded bg-bg-sunken border border-border-default text-ink-900">
              {recIdParam}
            </span>
          </div>
        )}
      </div>

      {/* ── 3. Evidence Cards Content ───────────────────────────────────────── */}
      {loading && (
        <div className="p-12 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-brand animate-spin mx-auto" />
          <p className="text-sm font-semibold text-ink-500">Retrieving official clause extractions...</p>
        </div>
      )}

      {error && (
        <Alert variant="error" title="Evidence Query Notice">
          {error}
        </Alert>
      )}

      {!loading && !error && Object.keys(groupedEvidences).length === 0 && (
        <EmptyState
          icon={FileCheck2}
          title="No Grounding Evidence Loaded"
          description="Enter a recommendation session ID above or run a search to inspect verbatim clause provenance."
        />
      )}

      {!loading && Object.keys(groupedEvidences).length > 0 && (
        <div className="space-y-8">
          {Object.entries(groupedEvidences).map(([stdNumber, items]) => (
            <div
              key={stdNumber}
              className="p-6 sm:p-8 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-6"
            >
              {/* Group Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-default pb-4">
                <div className="flex items-center gap-3">
                  <CodeChip code={stdNumber} variant="primary" />
                  <span className="text-xs font-mono font-bold text-ink-500">
                    {items.length} Citation{items.length !== 1 ? 's' : ''} Grounded
                  </span>
                </div>
                <Link
                  to={`/standards/${encodeURIComponent(stdNumber)}`}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-brand hover:underline"
                >
                  <span>View Standard Scope</span>
                  <BookOpen className="w-3.5 h-3.5" />
                </Link>
              </div>

              {/* Clause Excerpts */}
              <div className="space-y-4">
                {items.map((ev, idx) => {
                  const isInsufficient = !ev.evidence_text || ev.evidence_text.trim() === 'Insufficient evidence' || ev.evidence_text.toLowerCase().startsWith('insufficient evidence');

                  return (
                    <div
                      key={idx}
                      className={clsx(
                        "p-6 rounded-2xl bg-bg-surface border shadow-warm-sm space-y-3.5",
                        isInsufficient ? "border-warning/50 border-l-4 border-l-warning" : "border-border-default border-l-4 border-l-brand"
                      )}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="flex flex-wrap items-center gap-2">
                          {ev.page != null && (
                            <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-bg-sunken text-ink-900 border border-border-default">
                              Page {ev.page}
                            </span>
                          )}
                          {ev.section && (
                            <span className="px-2.5 py-0.5 rounded text-xs font-mono font-semibold bg-bg-sunken text-ink-700 border border-border-default">
                              {ev.section}
                            </span>
                          )}
                          {isInsufficient ? (
                            <span className="inline-flex items-center gap-1 text-xs font-bold text-warning">
                              <ShieldAlert className="w-4 h-4 text-warning" />
                              Insufficient evidence — Verification Required
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-xs font-bold text-success">
                              <CheckCircle2 className="w-4 h-4 text-success" />
                              {ev.audit_status || 'Grounded in Source'}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-4">
                          <span className="text-xs font-mono font-semibold text-ink-700 bg-bg-sunken px-2.5 py-1 rounded border border-border-default" title="Algorithmic relevance match score (0.00 to 1.00)">
                            Relevance: {typeof ev.confidence === 'number' ? ev.confidence.toFixed(2) : 'N/A'}
                          </span>
                          {!isInsufficient && (
                            <button
                              type="button"
                              onClick={() => handleCopyCitation(ev, idx)}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold border border-border-default bg-bg-surface text-ink-900 hover:bg-bg-sunken shadow-warm-sm transition-colors"
                              title="Copy verbatim citation"
                            >
                              {copiedIdx === idx ? (
                                <>
                                  <Check className="w-3.5 h-3.5 text-success" />
                                  <span className="text-success text-xs">Copied</span>
                                </>
                              ) : (
                                <>
                                  <Copy className="w-3.5 h-3.5 text-ink-500" />
                                  <span>Copy Citation</span>
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Display clause quotation ONLY when actual text is available */}
                      {isInsufficient ? (
                        <div className="p-4 rounded-xl bg-warning-soft/60 border border-warning/30 space-y-1.5 text-xs">
                          <div className="flex items-center gap-2 text-warning font-bold">
                            <ShieldAlert className="w-4 h-4" />
                            <span>Insufficient Evidence Warning</span>
                          </div>
                          <p className="text-ink-700 leading-relaxed font-medium">
                            No verbatim supporting clause quotation is available from the retrieved source for this standard. Page numbers, section labels, or source names alone do not prove standard applicability. Manual review by the procurement officer is required.
                          </p>
                        </div>
                      ) : (
                        <blockquote className="italic font-serif text-base text-ink-900 leading-relaxed border-l-2 border-border-strong pl-4 py-1">
                          &ldquo;{ev.evidence_text}&rdquo;
                        </blockquote>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
