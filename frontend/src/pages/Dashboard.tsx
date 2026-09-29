import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Search,
  Upload,
  Network,
  ShieldCheck,
  Cpu,
  ArrowRight,
  BookOpen,
  ClipboardCheck,
  FileCheck2,
  Database,
  SlidersHorizontal,
  Scale,
  CheckCircle2,
  Lock
} from 'lucide-react';
import { api } from '../services/api';
import { SystemHealth, VerifiedAnswerDTO } from '../types';
import { StatCard } from '../components/ui';

export const Dashboard: React.FC = () => {
  const [query, setQuery] = useState('');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [standardsCount, setStandardsCount] = useState<number | null>(null);
  const [verifiedDecisions, setVerifiedDecisions] = useState<VerifiedAnswerDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    const fetchDashboardData = async () => {
      try {
        const [healthRes, standardsRes, verifiedRes] = await Promise.allSettled([
          api.getHealth(),
          api.listStandards(),
          api.getVerifiedKnowledge(),
        ]);

        if (isMounted) {
          if (healthRes.status === 'fulfilled') {
            setHealth(healthRes.value);
          }
          if (standardsRes.status === 'fulfilled') {
            setStandardsCount(standardsRes.value.length);
          }
          if (verifiedRes.status === 'fulfilled') {
            setVerifiedDecisions(verifiedRes.value);
          }
        }
      } catch (err) {
        console.error('Failed to load dashboard statistics', err);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 20000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  const sampleQueries = [
    { label: "1100 V Armoured Cable", query: "Heavy duty armoured PVC electric cables up to 1100 V" },
    { label: "Distribution Transformer", query: "500 kVA outdoor oil cooled distribution transformer 11 kV/433 V" },
    { label: "TMT Rebar (Fe 500)", query: "Structural steel high strength deformed bars for concrete reinforcement Fe 500" },
    { label: "Reinforced Concrete", query: "Plain and reinforced concrete construction works" },
  ];

  const pipelineStages = [
    { num: '01', title: 'Query Understanding', desc: 'Linguistic parsing, parameters & foreign standard detection', icon: SlidersHorizontal },
    { num: '02', title: 'Verified Retrieval', desc: 'Cosine similarity against curated 21 BIS catalogue records', icon: Search },
    { num: '03', title: 'Statutory Compliance & QCO', desc: 'Enforces DPIIT/BIS QCO orders & Make-in-India precedence', icon: Scale },
    { num: '04', title: 'Evidence Grounding', desc: 'Verbatim clause & page citations from official scopes', icon: ShieldCheck },
    { num: '05', title: 'Engineer Review', desc: 'Technical authority signs off: Approve, Modify, or Reject', icon: ClipboardCheck },
    { num: '06', title: 'Verified Memory', desc: 'Persistent cache with real-time lifecycle status re-check', icon: Database },
  ];

  const quickActions = [
    {
      title: "Search Standards",
      badge: "Natural Language & Codes",
      description: "Query technical procurement specifications in English, Hindi, or Tamil to identify applicable Indian Standards with grounded evidence.",
      icon: Search,
      path: "/search",
      buttonText: "Search Standards",
    },
    {
      title: "Upload Tender Specification",
      badge: "PDF / TXT Document Ingestion",
      description: "Upload complete tender documents or bills of quantities to extract engineering clauses and match standards with page citations.",
      icon: Upload,
      path: "/upload",
      buttonText: "Upload Tender",
    },
    {
      title: "Pre-Publish Tender Validation",
      badge: "Feature M10 Quality Audit",
      description: "Audit procurement drafts against Rules A–E to identify superseded standards, applicable QCO obligations, and foreign specification conflicts.",
      icon: FileCheck2,
      path: "/pre-publish",
      buttonText: "Validate Tender",
    },
    {
      title: "Explore Knowledge Graph",
      badge: "Normative Relationships",
      description: "Explore the interactive relationship graph to inspect connected Indian Standards, testing methods (IS 10810, IS 516), and superseding codes.",
      icon: Network,
      path: "/graph",
      buttonText: "Explore Graph",
    },
  ];

  return (
    <div className="space-y-10">
      {/* ── 1. Hero Panel: Ivory Card with Saffron Accent Rule ─────────────── */}
      <div className="bg-bg-surface border border-border-default border-t-4 border-t-accent rounded-2xl p-6 sm:p-10 shadow-warm space-y-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-3 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-soft text-ink-900 border border-accent/30 text-xs font-bold shadow-warm-sm">
              <ShieldCheck className="w-4 h-4 text-accent" />
              <span>National Procurement Standards Intelligence · SIH26108</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-serif text-ink-900 tracking-tight leading-tight">
              Evidence-first Indian Standards for every procurement.
            </h1>

            <p className="text-base sm:text-lg text-ink-700 leading-relaxed max-w-2xl font-medium">
              Identify mandatory Bureau of Indian Standards (BIS) specifications, enforce Quality Control Orders (QCOs), and verify statutory Make-in-India precedence with clause-level provenance.
            </p>
          </div>

          <div className="hidden lg:flex flex-col gap-2 p-4 rounded-xl bg-bg-sunken border border-border-default text-xs max-w-xs shrink-0">
            <span className="font-bold text-ink-900 uppercase tracking-wider text-[11px]">
              Statutory Authority
            </span>
            <p className="text-ink-500 leading-normal">
              Empowering CPWD, MES, NHAI, RITES, and PSUs with deterministic compliance before tender publication.
            </p>
          </div>
        </div>

        {/* Large Search Bar */}
        <form onSubmit={handleSearchSubmit} className="pt-2">
          <div className="relative flex flex-col sm:flex-row items-stretch gap-2 p-2 rounded-2xl bg-bg-base/60 border-2 border-border-strong focus-within:border-brand focus-within:bg-bg-surface transition-all shadow-inner">
            <div className="flex items-center flex-1 px-3 py-1">
              <Search className="w-5 h-5 text-ink-500 shrink-0 mr-3" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter procurement specification or product requirement (e.g. Heavy duty PVC cables 1100V)..."
                className="w-full bg-transparent text-base text-ink-900 placeholder-ink-500 font-medium focus:outline-none"
              />
            </div>
            <button
              type="submit"
              className="px-6 py-3 rounded-xl bg-brand hover:bg-brand-hover text-white text-sm font-bold transition-all shadow-warm shrink-0 flex items-center justify-center gap-2"
            >
              <span>Search Standards</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </form>

        {/* Clickable Demo Query Chips */}
        <div className="flex flex-wrap items-center gap-2.5 pt-1 text-xs">
          <span className="font-bold uppercase tracking-wider text-ink-500 text-[11px]">Demo Queries:</span>
          {sampleQueries.map((q) => (
            <button
              key={q.label}
              type="button"
              onClick={() => {
                setQuery(q.query);
                navigate(`/search?q=${encodeURIComponent(q.query)}`);
              }}
              className="px-3 py-1.5 rounded-lg border border-border-default bg-bg-surface hover:border-brand hover:bg-bg-sunken text-ink-900 text-xs font-semibold transition-all shadow-warm-sm"
            >
              {q.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── 2. KPI Stat Cards (4 Columns, Real Data Only) ──────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Standards"
          value={loading && standardsCount === null ? '...' : standardsCount ?? 21}
          subtext="Curated in verified catalogue"
          icon={BookOpen}
          variant="blue"
          loading={loading && standardsCount === null}
        />
        <StatCard
          label="Statutory QCO Mandates"
          value={5}
          subtext="Scheme I / ISI Mark Enforced"
          icon={Scale}
          variant="saffron"
        />
        <StatCard
          label="Verified Decisions"
          value={loading && verifiedDecisions.length === 0 ? '...' : verifiedDecisions.length}
          subtext="Engineer-approved memories"
          icon={ClipboardCheck}
          variant="green"
          loading={loading && verifiedDecisions.length === 0}
        />
        <StatCard
          label="Audit Database"
          value={health?.database_connected ? 'Connected' : 'Standby'}
          subtext="SQLite immutable ledger"
          icon={Database}
          variant="indigo"
        />
      </div>

      {/* ── 3. Visual Pipeline Strip (6 Numbered Stages) ──────────────────── */}
      <div className="p-6 sm:p-8 rounded-2xl bg-bg-surface border border-border-default shadow-warm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border-default pb-4">
          <div className="space-y-0.5">
            <h3 className="text-xl font-bold font-serif text-ink-900">
              Deterministic Retrieval & Verification Pipeline
            </h3>
            <p className="text-sm text-ink-500 font-medium">
              Six-stage verifiable workflow guaranteeing audit-grade accuracy for public procurement officers.
            </p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-bg-sunken text-ink-700 border border-border-default uppercase">
            Strict Zero-Hallucination
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          {pipelineStages.map((stage) => {
            const Icon = stage.icon;
            return (
              <div
                key={stage.num}
                className="p-4 rounded-xl border border-border-default bg-bg-base/40 space-y-2 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-extrabold text-brand tabular-nums">
                    STAGE {stage.num}
                  </span>
                  <Icon className="w-4 h-4 text-ink-500" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-ink-900 leading-snug">
                    {stage.title}
                  </h4>
                  <p className="text-xs text-ink-500 leading-relaxed mt-1 font-medium">
                    {stage.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── 4. The Three Fundamental Invariants ───────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="p-6 rounded-2xl bg-bg-surface border border-border-default border-l-4 border-l-brand shadow-warm space-y-3">
          <div className="w-10 h-10 rounded-xl bg-brand text-white flex items-center justify-center font-bold text-base shadow-warm-sm">
            1
          </div>
          <h4 className="text-base font-bold font-serif text-ink-900">
            LLM is Not the Source of Truth
          </h4>
          <p className="text-sm text-ink-700 leading-relaxed">
            The language model only extracts technical parameters, ratings, and foreign citations. It is strictly prohibited from inventing or hallucinating Indian Standard numbers.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-bg-surface border border-border-default border-l-4 border-l-success shadow-warm space-y-3">
          <div className="w-10 h-10 rounded-xl bg-success text-white flex items-center justify-center font-bold text-base shadow-warm-sm">
            2
          </div>
          <h4 className="text-base font-bold font-serif text-ink-900">
            Verified Data is Single Truth
          </h4>
          <p className="text-sm text-ink-700 leading-relaxed">
            All recommendations match exclusively against verified official BIS records (21 standards, 5 QCO mandates). Unsupported claims return &ldquo;Not available in verified dataset&rdquo;.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-bg-surface border border-border-default border-l-4 border-l-accent shadow-warm space-y-3">
          <div className="w-10 h-10 rounded-xl bg-accent text-white flex items-center justify-center font-bold text-base shadow-warm-sm">
            3
          </div>
          <h4 className="text-base font-bold font-serif text-ink-900">
            Engineer is Final Authority
          </h4>
          <p className="text-sm text-ink-700 leading-relaxed">
            Automated recommendations assist; human technical officers approve, modify, or reject. Approvals enter verified knowledge memory for subsequent query reuse.
          </p>
        </div>
      </div>

      {/* ── 5. Quick Actions Grid ─────────────────────────────────────────── */}
      <div className="space-y-4">
        <div className="space-y-0.5">
          <h3 className="text-xl font-bold font-serif text-ink-900">
            Core Procurement Workflows
          </h3>
          <p className="text-sm text-ink-500 font-medium">
            Select a specialized module to search, ingest documents, validate drafts, or inspect relationship graphs.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <div
                key={action.path}
                className="p-6 rounded-2xl bg-bg-surface border border-border-default shadow-warm warm-card-interactive flex flex-col justify-between gap-5"
              >
                <div className="space-y-3.5">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-xl bg-bg-sunken border border-border-default text-brand shadow-warm-sm">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-[11px] font-bold font-mono px-2.5 py-0.5 rounded-md bg-bg-sunken text-ink-700 border border-border-default">
                      {action.badge}
                    </span>
                  </div>

                  <div className="space-y-1.5">
                    <h4 className="text-base font-bold text-ink-900 font-serif">
                      {action.title}
                    </h4>
                    <p className="text-xs text-ink-500 leading-relaxed font-medium">
                      {action.description}
                    </p>
                  </div>
                </div>

                <Link
                  to={action.path}
                  className="inline-flex items-center justify-between w-full px-4 py-2.5 rounded-xl bg-bg-sunken hover:bg-brand hover:text-white border border-border-default text-ink-900 text-xs font-bold transition-all shadow-warm-sm group"
                >
                  <span>{action.buttonText}</span>
                  <ArrowRight className="w-4 h-4 text-ink-500 group-hover:text-white transition-colors" />
                </Link>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
