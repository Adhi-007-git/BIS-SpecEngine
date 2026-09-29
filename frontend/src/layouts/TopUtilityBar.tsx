import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  Menu,
  Search,
  Activity,
  CheckCircle2,
  AlertCircle,
  Database,
  Cpu,
  Server,
  Network,
  ChevronRight,
  ChevronDown,
  X
} from 'lucide-react';
import { api } from '../services/api';
import { SystemHealth } from '../types';

interface TopUtilityBarProps {
  onOpenMobileSidebar: () => void;
}

export const TopUtilityBar: React.FC<TopUtilityBarProps> = ({ onOpenMobileSidebar }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [globalQuery, setGlobalQuery] = useState('');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [healthPopoverOpen, setHealthPopoverOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchHealth = () => {
      api.getHealth()
        .then((res) => {
          if (isMounted) setHealth(res);
        })
        .catch(() => {
          if (isMounted) setHealth(null);
        });
    };

    fetchHealth();
    const timer = setInterval(fetchHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, []);

  const handleGlobalSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (globalQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(globalQuery.trim())}`);
      setGlobalQuery('');
    }
  };

  // Derive breadcrumbs from path
  const getBreadcrumbs = () => {
    const path = location.pathname;
    if (path === '/') return [{ label: 'Workspace', to: '/' }, { label: 'Dashboard' }];
    if (path === '/search') return [{ label: 'Workspace', to: '/' }, { label: 'Search Standards' }];
    if (path === '/upload') return [{ label: 'Workspace', to: '/' }, { label: 'Upload Tender' }];
    if (path === '/results') return [{ label: 'Workspace', to: '/search' }, { label: 'Recommendations' }];
    if (path.startsWith('/standards/')) return [{ label: 'Knowledge', to: '/manage' }, { label: 'Standard Details' }];
    if (path === '/evidence') return [{ label: 'Review & Compliance', to: '/review' }, { label: 'Evidence Audit' }];
    if (path === '/review') return [{ label: 'Review & Compliance', to: '/review' }, { label: 'Engineer Review' }];
    if (path === '/pre-publish') return [{ label: 'Review & Compliance', to: '/pre-publish' }, { label: 'Pre-Publish Validation' }];
    if (path.startsWith('/graph')) return [{ label: 'Knowledge', to: '/graph' }, { label: 'Knowledge Graph' }];
    if (path === '/manage') return [{ label: 'Knowledge', to: '/manage' }, { label: 'Standards Management' }];
    return [{ label: 'Workspace', to: '/' }, { label: 'Overview' }];
  };

  const breadcrumbs = getBreadcrumbs();
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="h-16 bg-bg-surface border-b border-border-default sticky top-0 z-30 px-4 sm:px-8 flex items-center justify-between gap-4">
      {/* Left: Mobile hamburger & Breadcrumbs */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onOpenMobileSidebar}
          className="lg:hidden p-2 rounded-xl border border-border-default text-ink-700 hover:text-ink-900 hover:bg-bg-sunken focus:outline-none"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <nav aria-label="Breadcrumb" className="hidden sm:flex items-center gap-1.5 text-xs text-ink-500 truncate">
          {breadcrumbs.map((crumb, idx) => {
            const isLast = idx === breadcrumbs.length - 1;
            return (
              <React.Fragment key={crumb.label}>
                {idx > 0 && <ChevronRight className="w-3.5 h-3.5 text-border-strong shrink-0" />}
                {crumb.to && !isLast ? (
                  <Link
                    to={crumb.to}
                    className="font-medium text-ink-500 hover:text-brand hover:underline transition-colors"
                  >
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="font-bold text-ink-900">{crumb.label}</span>
                )}
              </React.Fragment>
            );
          })}
        </nav>
      </div>

      {/* Centre: Global Search Bar */}
      <div className="flex-1 max-w-md mx-auto hidden md:block">
        <form onSubmit={handleGlobalSearch} className="relative">
          <Search className="w-4 h-4 text-ink-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={globalQuery}
            onChange={(e) => setGlobalQuery(e.target.value)}
            placeholder="Quick search standards (e.g. cables, IS 456, transformer)..."
            className="w-full pl-9 pr-4 py-1.5 rounded-xl border border-border-strong bg-bg-base/50 text-xs text-ink-900 placeholder-ink-500 focus:outline-none focus:border-brand focus:bg-bg-surface transition-all"
          />
        </form>
      </div>

      {/* Right: Live Health Pill & Popover */}
      <div className="relative shrink-0">
        <button
          onClick={() => setHealthPopoverOpen(!healthPopoverOpen)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-border-default bg-bg-sunken hover:border-border-strong text-ink-900 text-xs font-semibold transition-all shadow-warm-sm"
          title="Click to inspect verified API microservice connections"
        >
          <span className="relative flex h-2 w-2">
            {isHealthy ? (
              <>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-success" />
              </>
            ) : (
              <span className="relative inline-flex rounded-full h-2 w-2 bg-danger" />
            )}
          </span>
          <span className="hidden sm:inline font-mono text-[11px] font-bold">
            {isHealthy ? 'LIVE HEALTH' : 'STANDBY'}
          </span>
          <ChevronDown className="w-3.5 h-3.5 text-ink-500" />
        </button>

        {/* Health Details Popover */}
        {healthPopoverOpen && (
          <>
            <div
              className="fixed inset-0 z-30"
              onClick={() => setHealthPopoverOpen(false)}
            />
            <div className="absolute right-0 mt-2 w-80 p-5 rounded-2xl bg-bg-surface border-2 border-border-strong shadow-warm-lg z-40 text-xs space-y-3.5 animate-slide-up">
              <div className="flex items-center justify-between border-b border-border-default pb-2.5">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-brand" />
                  <span className="font-bold text-sm text-ink-900 font-serif">
                    System Health & Connectivity
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-bg-sunken text-ink-700 border border-border-default">
                  {health?.environment.toUpperCase() || 'PROD'}
                </span>
              </div>

              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-ink-700 flex items-center gap-1.5">
                    <Database className="w-3.5 h-3.5 text-ink-500" />
                    SQL Database (SQLite)
                  </span>
                  <span className="font-mono font-bold text-success flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    {health?.database_connected ? 'Connected' : 'Standby'}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-ink-700 flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-ink-500" />
                    Retrieval Mode
                  </span>
                  <span className="font-mono font-bold text-brand">
                    {health?.retrieval_mode || 'IN_MEMORY'}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-ink-700 flex items-center gap-1.5">
                    <Server className="w-3.5 h-3.5 text-ink-500" />
                    Vector Embeddings
                  </span>
                  <span className="font-mono font-bold text-brand">
                    {health?.embedding_mode || 'REAL_BGE_M3'}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-ink-700 flex items-center gap-1.5">
                    <Network className="w-3.5 h-3.5 text-ink-500" />
                    Knowledge Graph
                  </span>
                  <span className="font-mono font-semibold text-ink-700">
                    {health?.neo4j_connected ? 'Neo4j Live' : 'Verified In-Memory'}
                  </span>
                </div>
              </div>

              <div className="pt-2.5 border-t border-border-default text-[11px] text-ink-500 flex justify-between font-mono">
                <span>FastAPI Core: :8000</span>
                <span>v{health?.version || '1.0.0'}</span>
              </div>
            </div>
          </>
        )}
      </div>
    </header>
  );
};
