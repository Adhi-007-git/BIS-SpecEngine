import React from 'react';
import { clsx } from 'clsx';

interface PageHeaderProps {
  title: string;
  description: string;
  badge?: React.ReactNode;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  badge,
  icon,
  action,
  className,
}) => {
  return (
    <div className={clsx('space-y-3 pb-5 border-b border-border-default', className)}>
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-4">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2.5">
            {icon && <span className="text-brand shrink-0">{icon}</span>}
            <h1 className="text-2xl sm:text-[32px] font-extrabold font-serif text-ink-900 tracking-tight leading-tight">
              {title}
            </h1>
            {badge && <div>{badge}</div>}
          </div>
          <p className="text-sm sm:text-[15px] font-medium text-ink-500 leading-relaxed max-w-3xl">
            {description}
          </p>
        </div>

        {action && (
          <div className="flex items-center gap-2 shrink-0 sm:self-center">
            {action}
          </div>
        )}
      </div>
    </div>
  );
};
