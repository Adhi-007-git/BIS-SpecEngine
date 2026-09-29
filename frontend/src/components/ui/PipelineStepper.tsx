import React from 'react';
import { clsx } from 'clsx';
import { Check, Loader2, AlertCircle } from 'lucide-react';

export interface StepItem {
  id: string;
  label: string;
  description?: string;
}

interface PipelineStepperProps {
  steps: StepItem[];
  currentStepIndex: number; // 0 to steps.length - 1
  isError?: boolean;
  errorMessage?: string;
  className?: string;
}

export const PipelineStepper: React.FC<PipelineStepperProps> = ({
  steps,
  currentStepIndex,
  isError = false,
  errorMessage,
  className,
}) => {
  return (
    <div className={clsx('w-full space-y-4', className)}>
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {steps.map((step, idx) => {
          const isCompleted = idx < currentStepIndex;
          const isCurrent = idx === currentStepIndex;
          const isPending = idx > currentStepIndex;

          return (
            <div
              key={step.id}
              className={clsx(
                'relative p-4 rounded-xl border transition-all duration-300 flex flex-col justify-between gap-2.5',
                isCompleted &&
                  'bg-success-soft border-success/50 text-ink-900 shadow-warm-sm',
                isCurrent &&
                  !isError &&
                  'bg-bg-surface border-2 border-brand text-ink-900 shadow-warm animate-pulse-glow',
                isCurrent &&
                  isError &&
                  'bg-danger-soft border-2 border-danger text-ink-900',
                isPending &&
                  'bg-bg-sunken border-border-default text-ink-500 opacity-80'
              )}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-ink-500 tabular-nums">
                  0{idx + 1}
                </span>
                <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs">
                  {isCompleted && <Check className="w-4 h-4 text-success font-extrabold" />}
                  {isCurrent && !isError && <Loader2 className="w-4 h-4 text-brand animate-spin" />}
                  {isCurrent && isError && <AlertCircle className="w-4 h-4 text-danger" />}
                  {isPending && <span className="w-2 h-2 rounded-full bg-border-strong" />}
                </div>
              </div>

              <div>
                <p className="text-[13px] font-bold text-ink-900 leading-tight">{step.label}</p>
                {step.description && (
                  <p className="text-xs text-ink-500 truncate mt-1">
                    {step.description}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {isError && errorMessage && (
        <div className="p-4 rounded-xl border border-danger/40 bg-danger-soft text-ink-900 text-sm font-medium flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-danger" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
};
