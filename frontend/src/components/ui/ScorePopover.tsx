import React, { useState } from 'react';
import { BarChart3, X } from 'lucide-react';
import { clsx } from 'clsx';

interface ScorePopoverProps {
  scoreFactors?: Record<string, any>;
  relevanceScore?: number;
  className?: string;
}

export const ScorePopover: React.FC<ScorePopoverProps> = ({
  scoreFactors,
  relevanceScore,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!scoreFactors && relevanceScore == null) return null;

  const weights = [
    { key: 'semantic_score', label: 'Semantic Similarity', weight: '40%' },
    { key: 'material_score', label: 'Material Match', weight: '20%' },
    { key: 'environment_score', label: 'Environment / Scope', weight: '20%' },
    { key: 'technical_alignment_score', label: 'Technical Term Alignment', weight: '20%' },
  ];

  return (
    <div className={clsx('relative inline-block', className)}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1.5 text-xs font-bold text-brand hover:text-brand-hover transition-colors px-2 py-1 rounded-md border border-brand/20 bg-brand/5 hover:bg-brand/10 shadow-warm-sm"
        title="View algorithmic score breakdown"
      >
        <BarChart3 className="w-3.5 h-3.5 text-brand" />
        <span>Why this standard?</span>
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 bottom-full mb-2 w-80 p-5 rounded-2xl bg-bg-surface border border-border-strong shadow-warm-lg z-50 text-xs space-y-3.5 animate-slide-up">
            <div className="flex items-center justify-between border-b border-border-default pb-2.5">
              <span className="font-bold text-sm text-ink-900 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-brand" />
                Score Factor Breakdown
              </span>
              <button
                onClick={() => setIsOpen(false)}
                className="text-ink-500 hover:text-ink-900 p-1 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2.5">
              {weights.map((w) => {
                const val = scoreFactors ? scoreFactors[w.key] : null;
                const scoreNum = val != null ? Number(val) : null;
                const displayScore = scoreNum != null ? (scoreNum <= 1.0 ? scoreNum.toFixed(2) : (scoreNum / 100).toFixed(2)) : null;
                const pct = scoreNum != null ? Math.round(scoreNum <= 1.0 ? scoreNum * 100 : scoreNum) : null;
                return (
                  <div key={w.key} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="font-medium text-ink-700">
                        {w.label}{' '}
                        <span className="text-[11px] font-semibold text-ink-500">({w.weight})</span>
                      </span>
                      <span className="font-mono font-bold text-ink-900 tabular-nums">
                        {displayScore != null ? `${displayScore} / 1.00` : 'N/A'}
                      </span>
                    </div>
                    {pct != null && (
                      <div className="h-2 w-full bg-bg-sunken border border-border-default rounded-full overflow-hidden p-0.5">
                        <div
                          className="h-full bg-brand rounded-full transition-all"
                          style={{ width: `${Math.min(100, pct)}%` }}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {relevanceScore != null && (
              <div className="pt-2.5 border-t border-border-default space-y-1.5">
                <div className="flex justify-between items-center text-xs font-bold text-ink-900">
                  <span>Weighted Relevance Score</span>
                  <span className="font-mono text-sm text-brand font-extrabold tabular-nums">
                    {relevanceScore.toFixed(2)} <span className="text-xs text-ink-500 font-normal">/ 1.00</span>
                  </span>
                </div>
                <p className="text-[11px] text-ink-500 leading-snug">
                  Relevance score reflects weighted algorithmic similarity across technical parameters (40% semantic, 20% material, 20% environment, 20% terminology) on a 0.00–1.00 scale. It is strictly a retrieval relevance metric, not an empirical confidence percentage.
                </p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
