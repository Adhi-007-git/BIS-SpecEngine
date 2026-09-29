import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopUtilityBar } from './TopUtilityBar';
import { DemoDataRibbon } from './DemoDataRibbon';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-bg-base text-ink-700 flex flex-col font-sans antialiased">
      {/* Fixed Left Sidebar */}
      <Sidebar
        isOpen={mobileSidebarOpen}
        onClose={() => setMobileSidebarOpen(false)}
      />

      {/* Main Content Column (offset by sidebar width on lg screens) */}
      <div className="lg:pl-[264px] flex flex-col flex-1 min-w-0 transition-all duration-300">
        {/* Top Utility Bar */}
        <TopUtilityBar onOpenMobileSidebar={() => setMobileSidebarOpen(true)} />

        {/* Demo Data Ribbon (always visible) */}
        <DemoDataRibbon />

        {/* Dynamic Page Content */}
        <main className="flex-1 w-full max-w-[1360px] mx-auto px-4 sm:px-8 py-8 animate-fade-in">
          {children}
        </main>

        {/* Enterprise GovTech Footer */}
        <footer className="border-t border-border-default bg-bg-surface py-6 text-xs text-ink-500 no-print mt-auto">
          <div className="max-w-[1360px] mx-auto px-4 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
            <div className="space-y-0.5">
              <p className="font-semibold text-ink-900">
                Smart India Hackathon 2026 • <strong>SIH26108</strong> • Bureau of Indian Standards (BIS) SpecEngine
              </p>
              <p className="text-[12px] text-ink-500 font-mono">
                Verified Catalogue: 21 Standards · 5 Statutory QCO Mandates · Deterministic Grounding
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs font-bold text-brand">
              <span className="px-3 py-1 rounded-md bg-bg-sunken border border-border-default tracking-wide uppercase">
                AI assists. Engineer decides.
              </span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};
