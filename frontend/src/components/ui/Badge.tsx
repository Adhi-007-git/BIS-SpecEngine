import React from 'react';
import {
  ArrowRight,
  ShieldAlert,
  ShieldCheck,
  Ban,
  Clock,
  ThumbsDown,
  Edit3,
  CheckCheck,
  Scale
} from 'lucide-react';
import { clsx } from 'clsx';

export type BadgeVariant =
  | 'active'
  | 'superseded'
  | 'withdrawn'
  | 'qco'
  | 'verified'
  | 'foreign-conflict'
  | 'approved'
  | 'modified'
  | 'rejected'
  | 'pending'
  | 'neutral'
  | 'saffron';

interface BadgeProps {
  variant: BadgeVariant;
  label?: string;
  scheme?: string;
  className?: string;
  supersededBy?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  variant,
  label,
  scheme,
  className,
  supersededBy,
}) => {
  switch (variant) {
    case 'active':
      return (
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-semibold',
            'bg-success-soft text-success border border-success/30 shadow-warm-sm',
            className
          )}
          title="Active standard in official catalogue"
        >
          <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
          {label || 'Active'}
        </span>
      );

    case 'superseded':
      return (
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-semibold',
            'bg-warning-soft text-warning border border-warning/40 shadow-warm-sm',
            className
          )}
          title={supersededBy ? `Superseded by ${supersededBy}` : 'Superseded standard'}
        >
          <ArrowRight className="w-3.5 h-3.5 text-warning" />
          {label || 'Superseded'}
          {supersededBy && (
            <span className="font-mono text-xs font-bold text-ink-900 ml-1">→ {supersededBy}</span>
          )}
        </span>
      );

    case 'withdrawn':
      return (
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-semibold',
            'bg-danger-soft text-danger border border-danger/40 line-through decoration-danger decoration-2',
            className
          )}
          title="Withdrawn from active catalogue"
        >
          <Ban className="w-3.5 h-3.5 text-danger" />
          {label || 'Withdrawn'}
        </span>
      );

    case 'qco':
      return (
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-bold tracking-wider',
            'bg-danger text-white border border-danger/90 shadow-warm-sm',
            className
          )}
          title="Mandatory Quality Control Order enforced by DPIIT / BIS"
        >
          <ShieldAlert className="w-3.5 h-3.5 text-white" />
          <span>QCO MANDATORY</span>
          {scheme && (
            <span className="pl-1.5 border-l border-white/40 text-xs font-semibold normal-case">
              {scheme}
            </span>
          )}
        </span>
      );

    case 'verified':
      return (
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-bold',
            'bg-success-soft text-success border border-success/40 shadow-warm-sm',
            className
          )}
        >
          <ShieldCheck className="w-4 h-4 text-success" />
          {label || 'Verified Grounded'}
        </span>
      );

    case 'foreign-conflict':
      return (
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-bold',
            'bg-warning-soft text-accent border border-accent/40 shadow-warm-sm',
            className
          )}
        >
          <Scale className="w-3.5 h-3.5 text-accent" />
          {label || 'Foreign Precedence Conflict'}
        </span>
      );

    case 'approved':
      return (
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-semibold',
            'bg-success-soft text-success border border-success/40 shadow-warm-sm',
            className
          )}
        >
          <CheckCheck className="w-3.5 h-3.5 text-success" />
          {label || 'Approved'}
        </span>
      );

    case 'modified':
      return (
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-semibold',
            'bg-info-soft text-info border border-info/40 shadow-warm-sm',
            className
          )}
        >
          <Edit3 className="w-3.5 h-3.5 text-info" />
          {label || 'Modified'}
        </span>
      );

    case 'rejected':
      return (
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-semibold',
            'bg-danger-soft text-danger border border-danger/40 shadow-warm-sm',
            className
          )}
        >
          <ThumbsDown className="w-3.5 h-3.5 text-danger" />
          {label || 'Rejected'}
        </span>
      );

    case 'pending':
      return (
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-semibold',
            'bg-warning-soft text-warning border border-warning/40 shadow-warm-sm',
            className
          )}
        >
          <Clock className="w-3.5 h-3.5 text-warning" />
          {label || 'Pending Review'}
        </span>
      );

    case 'saffron':
      return (
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-semibold',
            'bg-accent-soft text-ink-900 border border-accent/40 shadow-warm-sm',
            className
          )}
        >
          {label}
        </span>
      );

    case 'neutral':
    default:
      return (
        <span
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[13px] font-semibold',
            'bg-bg-sunken text-ink-700 border border-border-default shadow-warm-sm',
            className
          )}
        >
          {label}
        </span>
      );
  }
};
