import React from 'react';
import { clsx } from 'clsx';

interface ConfidenceMeterProps {
  score: number; // 0.0 to 1.0 or 0 to 100
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  showPercent?: boolean;
  className?: string;
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
  score,
  label = 'Confidence',
  size = 'md',
  showPercent = true,
  className,
}) => {
  // Normalize to 0-100
  const normalized = score <= 1.0 ? Math.round(score * 100) : Math.round(score);
  const clamped = Math.max(0, Math.min(100, normalized));

  // Determine band
  let barColor = 'bg-success';
  let textColor = 'text-success';
  let bandLabel = 'High';

  if (clamped < 60) {
    barColor = 'bg-danger';
    textColor = 'text-danger';
    bandLabel = 'Low';
  } else if (clamped < 80) {
    barColor = 'bg-warning';
    textColor = 'text-warning';
    bandLabel = 'Medium';
  }

  const heightClass = size === 'sm' ? 'h-2' : size === 'lg' ? 'h-3.5' : 'h-2.5';

  return (
    <div className={clsx('space-y-1', className)} title={`${label}: ${clamped}% (${bandLabel})`}>
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-ink-500">{label}</span>
        {showPercent && (
          <span className="font-mono font-bold text-ink-900 tabular-nums">
            {clamped}%
            <span className={clsx('ml-1 text-[11px] font-bold uppercase', textColor)}>
              ({bandLabel})
            </span>
          </span>
        )}
      </div>
      <div className={clsx('w-full rounded-full bg-bg-sunken border border-border-default overflow-hidden p-0.5', heightClass)}>
        <div
          className={clsx('h-full rounded-full transition-all duration-500 ease-out', barColor)}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
};
