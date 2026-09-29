import React from 'react';
import { clsx } from 'clsx';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  variant?: 'blue' | 'green' | 'amber' | 'indigo' | 'saffron';
  trend?: string;
  loading?: boolean;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  subtext,
  icon: Icon,
  variant = 'blue',
  trend,
  loading = false,
  className,
}) => {
  const variantStyles = {
    blue: {
      iconBox: 'bg-brand/10 text-brand border border-brand/20',
      accentRule: 'border-l-4 border-l-brand',
    },
    green: {
      iconBox: 'bg-success-soft text-success border border-success/30',
      accentRule: 'border-l-4 border-l-success',
    },
    amber: {
      iconBox: 'bg-warning-soft text-warning border border-warning/30',
      accentRule: 'border-l-4 border-l-warning',
    },
    indigo: {
      iconBox: 'bg-info-soft text-info border border-info/30',
      accentRule: 'border-l-4 border-l-info',
    },
    saffron: {
      iconBox: 'bg-accent-soft text-accent border border-accent/40',
      accentRule: 'border-l-4 border-l-accent',
    },
  };

  const current = variantStyles[variant];

  return (
    <div
      className={clsx(
        'p-6 rounded-2xl bg-bg-surface border border-border-default shadow-warm warm-card-interactive flex items-start justify-between gap-4',
        current.accentRule,
        className
      )}
    >
      <div className="space-y-1.5 min-w-0">
        <span className="text-[13px] font-bold uppercase tracking-wider text-ink-500">
          {label}
        </span>
        <div className="text-3xl sm:text-4xl font-extrabold font-serif text-ink-900 tracking-tight tabular-nums">
          {loading ? (
            <div className="h-9 w-20 bg-bg-sunken border border-border-default rounded animate-pulse" />
          ) : (
            value
          )}
        </div>
        {subtext && (
          <p className="text-[13px] font-semibold text-ink-700 truncate">
            {subtext}
          </p>
        )}
        {trend && (
          <span className="inline-block text-xs font-mono font-medium text-ink-500">
            {trend}
          </span>
        )}
      </div>

      <div className={clsx('p-3 rounded-xl shrink-0 shadow-warm-sm', current.iconBox)}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
};
