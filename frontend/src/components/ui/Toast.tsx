import React, { useEffect } from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';
import { clsx } from 'clsx';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
}

interface ToastProps {
  toast: ToastMessage;
  onClose: (id: string) => void;
  duration?: number;
}

export const Toast: React.FC<ToastProps> = ({ toast, onClose, duration = 4000 }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose(toast.id);
    }, duration);
    return () => clearTimeout(timer);
  }, [toast.id, onClose, duration]);

  const typeStyles = {
    success: {
      box: 'bg-bg-surface border-2 border-success text-ink-900 shadow-warm-lg',
      icon: <CheckCircle2 className="w-5 h-5 text-success shrink-0 mt-0.5" />,
    },
    error: {
      box: 'bg-bg-surface border-2 border-danger text-ink-900 shadow-warm-lg',
      icon: <AlertCircle className="w-5 h-5 text-danger shrink-0 mt-0.5" />,
    },
    warning: {
      box: 'bg-bg-surface border-2 border-warning text-ink-900 shadow-warm-lg',
      icon: <AlertTriangle className="w-5 h-5 text-warning shrink-0 mt-0.5" />,
    },
    info: {
      box: 'bg-bg-surface border-2 border-brand text-ink-900 shadow-warm-lg',
      icon: <Info className="w-5 h-5 text-brand shrink-0 mt-0.5" />,
    },
  };

  const current = typeStyles[toast.type];

  return (
    <div
      role="alert"
      className={clsx(
        'flex items-start gap-3.5 p-4 rounded-xl shadow-warm-lg max-w-md w-full animate-slide-up',
        current.box
      )}
    >
      {current.icon}
      <div className="flex-1 text-xs space-y-0.5">
        {toast.title && <p className="font-bold text-sm text-ink-900 leading-snug">{toast.title}</p>}
        <p className="text-ink-700 leading-relaxed font-sans">{toast.message}</p>
      </div>
      <button
        onClick={() => onClose(toast.id)}
        className="text-ink-500 hover:text-ink-900 transition-colors p-0.5 rounded"
        aria-label="Close notification"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

export const ToastContainer: React.FC<{
  toasts: ToastMessage[];
  onClose: (id: string) => void;
}> = ({ toasts, onClose }) => {
  if (toasts.length === 0) return null;
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
      {toasts.map((t) => (
        <div key={t.id} className="pointer-events-auto">
          <Toast toast={t} onClose={onClose} />
        </div>
      ))}
    </div>
  );
};
