import React from 'react';
import { LucideIcon, FileQuestion } from 'lucide-react';
import { clsx } from 'clsx';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = FileQuestion,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div
      className={clsx(
        'p-10 rounded-2xl border-2 border-dashed border-border-strong bg-bg-surface text-center space-y-4 flex flex-col items-center justify-center max-w-lg mx-auto shadow-warm',
        className
      )}
    >
      <div className="w-14 h-14 rounded-2xl bg-bg-sunken text-ink-700 border border-border-default flex items-center justify-center shadow-warm-sm">
        <Icon className="w-7 h-7 text-brand" />
      </div>
      <div className="space-y-1.5">
        <h4 className="font-bold text-lg text-ink-900 font-serif">
          {title}
        </h4>
        <p className="text-sm text-ink-500 leading-relaxed max-w-md">
          {description}
        </p>
      </div>
      {action && (
        <button
          onClick={action.onClick}
          className="mt-2 px-5 py-2.5 bg-brand hover:bg-brand-hover text-white rounded-xl text-sm font-bold transition-colors shadow-warm"
        >
          {action.label}
        </button>
      )}
    </div>
  );
};
