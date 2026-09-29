import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  Upload,
  ClipboardCheck,
  FileCheck2,
  Network,
  Layers,
  Sparkles,
  ShieldCheck,
  X
} from 'lucide-react';
import { clsx } from 'clsx';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation();

  const navGroups: NavGroup[] = [
    {
      label: 'Workspace',
      items: [
        { name: 'Dashboard', href: '/', icon: LayoutDashboard },
        { name: 'Search Standards', href: '/search', icon: Search },
        { name: 'Upload Tender', href: '/upload', icon: Upload },
      ],
    },
    {
      label: 'Review & Compliance',
      items: [
        { name: 'Engineer Review', href: '/review', icon: ClipboardCheck },
        { name: 'Pre-Publish Validation', href: '/pre-publish', icon: FileCheck2 },
      ],
    },
    {
      label: 'Knowledge',
      items: [
        { name: 'Knowledge Graph', href: '/graph', icon: Network },
        { name: 'Standards Management', href: '/manage', icon: Layers },
      ],
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-[#14110C]/60 backdrop-blur-[2px] z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={clsx(
          'fixed top-0 bottom-0 left-0 z-50 w-[264px] bg-bg-sunken border-r border-border-default flex flex-col justify-between transition-transform duration-300 ease-in-out',
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Top Header & Brand Wordmark */}
        <div>
          <div className="p-5 flex items-center justify-between">
            <NavLink to="/" onClick={onClose} className="flex items-center gap-2.5 group">
              <div className="w-10 h-10 rounded-xl bg-brand text-white flex items-center justify-center font-serif font-black text-xl shadow-warm-sm group-hover:bg-brand-hover transition-colors">
                BIS
              </div>
              <div className="leading-tight">
                <span className="font-serif font-bold text-lg text-ink-900 tracking-tight block">
                  BIS SpecEngine
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] font-mono font-bold text-ink-500 uppercase tracking-wider">
                  SIH 2026 · SIH26108
                </span>
              </div>
            </NavLink>

            {/* Mobile close button */}
            <button
              onClick={onClose}
              className="lg:hidden p-1.5 rounded-lg text-ink-500 hover:text-ink-900 hover:bg-bg-surface transition-colors"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* 3px Tricolour Hairline */}
          <div className="tricolour-hairline" />

          {/* Navigation Groups */}
          <nav className="p-4 space-y-6 overflow-y-auto max-h-[calc(100vh-210px)]">
            {navGroups.map((group) => (
              <div key={group.label} className="space-y-1.5">
                <h3 className="px-3 text-[11px] font-bold uppercase tracking-wider text-ink-500">
                  {group.label}
                </h3>
                <div className="space-y-1">
                  {group.items.map((item) => {
                    const Icon = item.icon;
                    const isActive =
                      item.href === '/'
                        ? location.pathname === '/'
                        : location.pathname.startsWith(item.href);

                    return (
                      <NavLink
                        key={item.name}
                        to={item.href}
                        onClick={onClose}
                        className={clsx(
                          'flex items-center gap-3 px-3 h-11 rounded-xl text-[15px] font-semibold transition-all duration-150',
                          isActive
                            ? 'bg-brand text-white shadow-warm-sm'
                            : 'text-ink-700 hover:text-ink-900 hover:bg-bg-surface'
                        )}
                      >
                        <Icon className={clsx('w-5 h-5 shrink-0', isActive ? 'text-white' : 'text-ink-500')} />
                        <span className="truncate">{item.name}</span>
                      </NavLink>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>
        </div>

        {/* Bottom Dataset Info Card */}
        <div className="p-4 border-t border-border-default bg-bg-surface/50">
          <div className="p-3 rounded-xl bg-bg-surface border border-border-default space-y-2 shadow-warm-sm">
            <div className="flex items-center gap-2 text-xs font-bold text-ink-900">
              <ShieldCheck className="w-4 h-4 text-success" />
              <span>Verified Catalogue</span>
            </div>
            <p className="text-[12px] text-ink-500 leading-tight">
              21 Indian Standards · 5 Statutory QCO Mandates
            </p>
            <div className="pt-1.5 border-t border-border-default/60 flex items-center justify-between text-[11px] font-semibold text-brand">
              <span>AI assists.</span>
              <span className="text-ink-900 font-bold">Engineer decides.</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
