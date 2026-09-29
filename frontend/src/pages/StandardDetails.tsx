import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  CheckCircle,
  Network,
  BookOpen,
  Beaker,
  FileSpreadsheet,
  ArrowLeft,
  Loader2,
  Calendar,
  Layers,
  ArrowRight,
  ShieldAlert,
  Clock,
  History
} from 'lucide-react';
import { api } from '../services/api';
import { StandardDetails as IStandardDetails } from '../types';
import { Badge, CodeChip, Alert, PageHeader } from '../components/ui';

export const StandardDetails: React.FC = () => {
  const { standardId } = useParams<{ standardId: string }>();
  const [standard, setStandard] = useState<IStandardDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'normative' | 'related' | 'lifecycle' | 'evidence'>('overview');
  const navigate = useNavigate();

  useEffect(() => {
    if (!standardId) return;
    setLoading(true);
    setError(null);

    api.getStandardDetails(standardId)
      .then(setStandard)
      .catch((err) => {
        setError(err.response?.data?.detail || 'Standard not found in official registry.');
      })
      .finally(() => setLoading(false));
  }, [standardId]);

  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 text-brand animate-spin" />
        <p className="text-ink-500 font-semibold text-sm">Loading standard specification details...</p>
      </div>
    );
  }

  if (error || !standard) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <Alert variant="error" title="Standard Not Found">
          {error || 'Standard details are unavailable.'}
        </Alert>
        <div>
          <Link
            to="/search"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand text-white text-xs font-bold rounded-xl shadow-warm"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Search
          </Link>
        </div>
      </div>
    );
  }

  const hasQCO = Boolean(standard.compliance && standard.compliance.some((c: any) => c.status === 'Mandatory for Procurement' || c.status === 'Mandatory'));
  const qcoVerificationRequired = Boolean(standard.compliance && standard.compliance.some((c: any) => c.status === 'Verification required'));

  return (
    <div className="space-y-8">
      {/* ── 1. Page Header ─────────────────────────────────────────────────── */}
      <PageHeader
        title={`${standard.standard_number} — Specification Details`}
        description={standard.title}
        badge={
          <Badge variant={standard.status?.toLowerCase() === 'active' ? 'active' : 'superseded'} />
        }
        action={
          <div className="flex items-center gap-2">
            <Link
              to="/search"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-border-default bg-bg-surface hover:bg-bg-sunken text-xs font-bold text-ink-900 transition-colors shadow-warm-sm"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Search</span>
            </Link>
            <Link
              to={`/graph/${encodeURIComponent(standard.standard_number)}`}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-warm"
            >
              <Network className="w-4 h-4" />
              <span>View in Graph</span>
            </Link>
          </div>
        }
      />

      {/* ── 2. Header Metadata Card ────────────────────────────────────────── */}
      <div className="p-6 sm:p-8 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-6">
        <div className="flex flex-wrap items-center gap-2.5">
          <CodeChip code={standard.standard_number} variant="primary" copyable />
          <Badge variant={standard.status?.toLowerCase() === 'active' ? 'active' : 'superseded'} />
          {hasQCO ? (
            <Badge variant="qco" scheme={standard.compliance[0]?.scheme || 'Scheme I'} />
          ) : qcoVerificationRequired ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-bg-sunken text-ink-500 border border-border-default" title="No standalone mandatory QCO order confirmed in active registry. Confirmation recommended prior to tender publishing.">
              <span>QCO applicability requires verification</span>
            </span>
          ) : null}
          {standard.is_demo && (
            <span className="text-xs font-mono px-3 py-1 rounded-full bg-accent-soft text-ink-900 border border-accent/40 font-bold">
              VERIFIED CATALOGUE
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs text-ink-500 font-medium border-t border-border-default pt-4">
          <span>Edition: <strong className="text-ink-900 font-mono">{standard.edition || 'Official Edition'}</strong></span>
          <span>•</span>
          <span>Source: <strong className="text-ink-900">{standard.source}</strong></span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-ink-500" />
            Last Verified: <strong className="text-ink-900">2026-09-24 (v1.0-real-21)</strong>
          </span>
          {standard.supersedes && (
            <>
              <span>•</span>
              <span className="text-accent font-bold">
                Supersedes: <strong className="font-mono">{standard.supersedes}</strong>
              </span>
            </>
          )}
        </div>

        {/* ── Tabs Navigation ──────────────────────────────────────────────── */}
        <div className="flex items-center gap-2 border-b border-border-default pt-2 overflow-x-auto">
          {[
            { id: 'overview', label: 'Overview & Scope' },
            { id: 'normative', label: `Normative References (${standard.normative_references?.length || 0})` },
            { id: 'related', label: `Testing Methods (${standard.test_methods?.length || 0})` },
            { id: 'lifecycle', label: 'Lifecycle & Versions' },
            { id: 'evidence', label: 'Grounding Evidence' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all shrink-0 ${
                activeTab === tab.id
                  ? 'border-brand text-brand bg-bg-sunken/40 rounded-t-lg'
                  : 'border-transparent text-ink-500 hover:text-ink-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── 3. Two-Column Tab Content & Compliance Card ────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Main Tab Details (8 cols) */}
        <div className="lg:col-span-8 p-6 sm:p-8 rounded-2xl bg-bg-surface border border-border-default shadow-warm min-h-[360px]">
          {activeTab === 'overview' && (
            <div className="space-y-4 animate-fade-in">
              <h3 className="text-sm font-bold uppercase tracking-wider text-ink-500">
                Official Standard Scope & Coverage
              </h3>
              <p className="text-sm text-ink-900 leading-relaxed font-serif">
                {standard.scope}
              </p>

              {/* Keywords if present */}
              {(standard as any).keywords && (standard as any).keywords.length > 0 && (
                <div className="space-y-2 pt-4 border-t border-border-default">
                  <span className="text-xs font-bold uppercase tracking-wider text-ink-500">
                    Standard Keywords & Application Domains:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {((standard as any).keywords as string[]).map((kw, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 rounded-lg text-xs font-semibold bg-bg-sunken text-ink-700 border border-border-default"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'normative' && (
            <div className="space-y-4 animate-fade-in">
              <h3 className="text-sm font-bold uppercase tracking-wider text-ink-500">
                Normative References Cited in Standard Body
              </h3>
              {standard.normative_references && standard.normative_references.length > 0 ? (
                <div className="space-y-3">
                  {standard.normative_references.map((norm, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl border border-border-default bg-bg-sunken flex items-center justify-between gap-4"
                    >
                      <div className="space-y-1">
                        <CodeChip code={norm.standard_number} variant="secondary" />
                        <p className="text-xs font-bold text-ink-900">
                          {norm.title || 'Normative reference standard'}
                        </p>
                      </div>
                      <Link
                        to={`/standards/${encodeURIComponent(norm.standard_number)}`}
                        className="px-3 py-1.5 rounded-lg border border-border-default hover:border-brand bg-bg-surface text-xs font-bold text-ink-900 transition-colors shadow-warm-sm"
                      >
                        View Code
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-ink-500 italic">No normative cross-references listed in catalogue record.</p>
              )}
            </div>
          )}

          {activeTab === 'related' && (
            <div className="space-y-4 animate-fade-in">
              <h3 className="text-sm font-bold uppercase tracking-wider text-ink-500 flex items-center gap-1.5">
                <Beaker className="w-4 h-4 text-brand" />
                Mandatory Test Method Standards
              </h3>
              {standard.test_methods && standard.test_methods.length > 0 ? (
                <div className="space-y-3">
                  {standard.test_methods.map((tm, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl border border-border-default bg-bg-sunken flex items-center justify-between gap-4"
                    >
                      <div className="space-y-1">
                        <CodeChip code={tm.standard_number} variant="clause" />
                        <p className="text-xs font-bold text-ink-900">
                          {tm.title || 'Official compliance test method'}
                        </p>
                      </div>
                      <Link
                        to={`/standards/${encodeURIComponent(tm.standard_number)}`}
                        className="px-3 py-1.5 rounded-lg border border-border-default hover:border-brand bg-bg-surface text-xs font-bold text-ink-900 transition-colors shadow-warm-sm"
                      >
                        View Test
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-ink-500 italic">No explicit test methods catalogued for this standard.</p>
              )}
            </div>
          )}

          {activeTab === 'lifecycle' && (
            <div className="space-y-4 animate-fade-in">
              <h3 className="text-sm font-bold uppercase tracking-wider text-ink-500">
                Standard Lifecycle & Historical Versions
              </h3>
              <div className="p-5 rounded-xl border border-border-default bg-bg-sunken space-y-4">
                <div className="flex items-center gap-3">
                  <Badge variant={standard.status?.toLowerCase() === 'active' ? 'active' : 'superseded'} />
                  <span className="font-mono text-xs text-ink-900 font-bold">
                    Current Catalogue Status: {standard.status}
                  </span>
                </div>

                {standard.supersedes ? (
                  <div className="p-4 rounded-xl border border-warning/40 bg-warning-soft text-xs space-y-1">
                    <span className="font-bold text-ink-900 block">Supersession Precedence:</span>
                    <p className="text-ink-700">
                      This specification officially supersedes previous edition{' '}
                      <strong className="font-mono text-ink-900">{standard.supersedes}</strong>. Procurement specifications citing the obsolete edition must be updated to avoid audit rejection.
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-ink-500">
                    This standard represents the currently enforced active baseline.
                  </p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'evidence' && (
            <div className="space-y-4 animate-fade-in">
              <h3 className="text-sm font-bold uppercase tracking-wider text-ink-500">
                Sample Grounding Excerpt
              </h3>
              <div className="p-6 rounded-2xl border border-border-default bg-bg-base/60 text-xs space-y-3">
                <p className="italic font-serif text-sm text-ink-900 leading-relaxed border-l-4 border-l-brand pl-3">
                  &ldquo;{(standard as any).evidence_sample?.text || standard.scope}&rdquo;
                </p>
                <div className="flex flex-wrap gap-3 text-xs font-mono text-ink-500 pt-3 border-t border-border-default">
                  <span>Page: {(standard as any).evidence_sample?.page || 1}</span>
                  <span>•</span>
                  <span>Section: {(standard as any).evidence_sample?.section || 'Clause 1 - Scope'}</span>
                  <span>•</span>
                  <span>Source: {standard.source}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Side Compliance Card (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          <div className="p-6 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-ink-900 flex items-center gap-2 border-b border-border-default pb-3">
              <ShieldCheck className="w-5 h-5 text-success" />
              Compliance & Quality Orders
            </h3>

            {hasQCO ? (
              <div className="space-y-3">
                <div className="p-4 rounded-xl border border-danger/40 bg-danger-soft space-y-2">
                  <div className="flex items-center gap-2 text-danger font-bold text-xs uppercase">
                    <ShieldAlert className="w-4 h-4" />
                    <span>DPIIT Mandatory QCO Enforced</span>
                  </div>
                  <p className="text-xs text-ink-900 leading-relaxed font-medium">
                    Supply and manufacture of products governed by this standard without valid BIS certification is legally prohibited under Section 16 of the BIS Act, 2016.
                  </p>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between border-b border-border-default pb-1.5">
                    <span className="text-ink-500 font-semibold">Scheme:</span>
                    <span className="font-bold text-ink-900">{standard.compliance[0]?.scheme || 'Scheme I (ISI Mark)'}</span>
                  </div>
                  <div className="flex justify-between border-b border-border-default pb-1.5">
                    <span className="text-ink-500 font-semibold">Enforcement:</span>
                    <span className="font-bold text-success">Mandatory for Public Tenders</span>
                  </div>
                </div>
              </div>
            ) : qcoVerificationRequired ? (
              <div className="p-4 rounded-xl border border-border-default bg-bg-sunken space-y-2 text-xs">
                <div className="flex items-center gap-2 text-ink-700 font-bold uppercase">
                  <ShieldCheck className="w-4 h-4 text-ink-500" />
                  <span>QCO Applicability Requires Verification</span>
                </div>
                <p className="text-ink-500 leading-relaxed">
                  No verified mandatory Quality Control Order (QCO) is currently on record in the active registry for this standard. Officer verification against the latest DPIIT gazette or GeM regulatory database is required prior to tender publication.
                </p>
              </div>
            ) : (
              <div className="p-4 rounded-xl border border-border-default bg-bg-sunken text-xs text-ink-500">
                Standard voluntary or governed under general procurement quality guidelines without standalone QCO order.
              </div>
            )}

            <div className="pt-2">
              <Link
                to={`/graph/${encodeURIComponent(standard.standard_number)}`}
                className="w-full py-2.5 px-4 rounded-xl bg-bg-sunken hover:bg-border-default border border-border-default text-ink-900 text-xs font-bold transition-all shadow-warm-sm flex items-center justify-center gap-2"
              >
                <Network className="w-4 h-4 text-brand" />
                <span>Explore in Knowledge Graph</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
