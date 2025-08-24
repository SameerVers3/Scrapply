import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Info, AlertTriangle } from 'lucide-react';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message?: string;
  duration?: number;
}

interface ToastProps {
  toast: Toast;
  onRemove: (id: string) => void;
}

function ToastItem({ toast, onRemove }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onRemove(toast.id);
    }, toast.duration || 5000);

    return () => clearTimeout(timer);
  }, [toast.id, toast.duration, onRemove]);

  const icons = {
    success: CheckCircle,
    error: XCircle,
    info: Info,
    warning: AlertTriangle,
  };

  const colors = {
    success: 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-200',
    error: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-200',
    info: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-200',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-800 dark:text-yellow-200',
  };

  const Icon = icons[toast.type];

  return (
    <div className={`border rounded-lg p-4 shadow-lg backdrop-blur-sm ${colors[toast.type]} animate-in slide-in-from-right-full duration-300`}>
      <div className="flex items-start space-x-3">
        <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="font-medium">{toast.title}</p>
          {toast.message && (
            <p className="text-sm mt-1 opacity-90">{toast.message}</p>
          )}
        </div>
        <button
          onClick={() => onRemove(toast.id)}
          className="text-current opacity-60 hover:opacity-100 transition-opacity"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { ...toast, id }]);
  };

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };

  const success = (title: string, message?: string, duration?: number) => {
    addToast({ type: 'success', title, message, duration });
  };

  const error = (title: string, message?: string, duration?: number) => {
    addToast({ type: 'error', title, message, duration });
  };

  const info = (title: string, message?: string, duration?: number) => {
    addToast({ type: 'info', title, message, duration });
  };

  const warning = (title: string, message?: string, duration?: number) => {
    addToast({ type: 'warning', title, message, duration });
  };

  const ToastContainer = () => (
    <div className="fixed top-4 right-4 z-50 space-y-3 max-w-sm w-full">
      {toasts.map(toast => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onRemove={removeToast}
        />
      ))}
    </div>
  );

  return {
    success,
    error,
    info,
    warning,
    ToastContainer,
  };
}
