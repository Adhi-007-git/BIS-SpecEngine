import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { clsx } from 'clsx';

interface CodeChipProps {
  code: string;
  variant?: 'primary' | 'secondary' | 'accent' | 'clause';
  copyable?: boolean;
  className?: string;
  onClick?: () => void;
}

export const CodeChip: React.FC<CodeChipProps> = ({
  code,
  variant = 'primary',
  copyable = false,
  className,
  onClick,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  const variantStyles = {
    primary:
      'bg-bg-surface text-brand border-border-strong font-semibold shadow-warm-sm',
    secondary:
      'bg-bg-surface text-ink-700 border-border-default font-medium',
    accent:
      'bg-bg-surface text-accent border-accent/60 font-semibold shadow-warm-sm',
    clause:
      'bg-bg-surface text-success border-success/60 font-semibold shadow-warm-sm',
  };

  return (
    <span
      onClick={onClick}
      className={clsx(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md font-mono text-[13px] border tracking-tight tabular-nums',
        variantStyles[variant],
        onClick && 'cursor-pointer hover:border-brand transition-colors',
        className
      )}
      title={copyable ? `Copy ${code}` : undefined}
    >
      <span>{code}</span>
      {copyable && (
        <button
          type="button"
          onClick={handleCopy}
          className="text-ink-500 hover:text-ink-900 transition-colors p-0.5 rounded focus:outline-none"
          aria-label={`Copy ${code}`}
        >
          {copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
        </button>
      )}
    </span>
  );
};
