import React from 'react';
import {
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Info,
  Scale
} from 'lucide-react';
import { clsx } from 'clsx';

export type AlertVariant = 'statutory-precedence' | 'verified-knowledge' | 'warning' | 'info' | 'error';

interface AlertProps {
  variant: AlertVariant;
  title: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}

export const Alert: React.FC<AlertProps> = ({
  variant,
  title,
  children,
  icon,
  className,
  action,
}) => {
  const variantStyles = {
    'statutory-precedence': {
      box: 'bg-warning-soft border border-border-strong border-l-4 border-l-accent text-ink-900 shadow-warm',
      title: 'text-ink-900 font-bold',
      defaultIcon: <Scale className="w-5 h-5 text-accent shrink-0 mt-0.5" />,
      badge: 'Statutory Precedence Conflict',
      badgeColor: 'bg-accent/20 text-accent border border-accent/40',
    },
    'verified-knowledge': {
      box: 'bg-success-soft border border-success/40 border-l-4 border-l-success text-ink-900 shadow-warm',
      title: 'text-ink-900 font-bold',
      defaultIcon: <ShieldCheck className="w-5 h-5 text-success shrink-0 mt-0.5" />,
      badge: 'Verified Knowledge Match',
      badgeColor: 'bg-success/20 text-success border border-success/40',
    },
    warning: {
      box: 'bg-warning-soft border border-border-default border-l-4 border-l-warning text-ink-900 shadow-warm-sm',
      title: 'text-ink-900 font-bold',
      defaultIcon: <AlertTriangle className="w-5 h-5 text-warning shrink-0 mt-0.5" />,
      badge: 'Warning',
      badgeColor: 'bg-warning/20 text-warning border border-warning/40',
    },
    info: {
      box: 'bg-info-soft border border-border-default border-l-4 border-l-info text-ink-900 shadow-warm-sm',
      title: 'text-ink-900 font-bold',
      defaultIcon: <Info className="w-5 h-5 text-info shrink-0 mt-0.5" />,
      badge: 'Advisory Notice',
      badgeColor: 'bg-info/20 text-info border border-info/40',
    },
    error: {
      box: 'bg-danger-soft border border-border-default border-l-4 border-l-danger text-ink-900 shadow-warm-sm',
      title: 'text-ink-900 font-bold',
      defaultIcon: <ShieldAlert className="w-5 h-5 text-danger shrink-0 mt-0.5" />,
      badge: 'Critical Non-Compliance',
      badgeColor: 'bg-danger/20 text-danger border border-danger/40',
    },
  };

  const current = variantStyles[variant];

  return (
    <div
      role="alert"
      className={clsx(
        'p-5 rounded-xl flex items-start gap-3.5 transition-all duration-200',
        current.box,
        className
      )}
    >
      {icon || current.defaultIcon}
      <div className="flex-1 space-y-1.5 text-sm">
        <div className="flex flex-wrap items-center gap-2">
          <h4 className={clsx('text-base', current.title)}>{title}</h4>
          {current.badge && (
            <span className={clsx('px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider', current.badgeColor)}>
              {current.badge}
            </span>
          )}
        </div>
        <div className="text-ink-700 leading-relaxed font-sans">{children}</div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
};
