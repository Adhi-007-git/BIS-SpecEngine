import React from 'react';
import { Info } from 'lucide-react';

export const DemoDataRibbon: React.FC = () => {
  return (
    <div className="h-9 bg-accent-soft border-b border-accent/40 px-4 sm:px-8 flex items-center justify-between text-xs text-ink-900 font-bold tracking-tight">
      <div className="flex items-center gap-2">
        <Info className="w-3.5 h-3.5 text-accent shrink-0" />
        <span>Demo Data · Verified catalogue of 21 standards & 5 QCO mandates</span>
      </div>
      <span className="hidden sm:inline-block font-mono text-[11px] text-accent font-semibold uppercase">
        Statutory Evidence-First Architecture
      </span>
    </div>
  );
};
