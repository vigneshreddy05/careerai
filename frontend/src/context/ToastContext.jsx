import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (message, type = 'info', duration = 4000) => {
      const id = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const newToast = { id, message, type, duration };

      setToasts((prev) => [...prev, newToast]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }

      return id;
    },
    [removeToast]
  );

  // Helper convenience methods
  const toast = useCallback(
    (msg, type = 'info', duration = 4000) => addToast(msg, type, duration),
    [addToast]
  );
  toast.success = (msg, dur) => addToast(msg, 'success', dur);
  toast.error = (msg, dur) => addToast(msg, 'error', dur);
  toast.warning = (msg, dur) => addToast(msg, 'warning', dur);
  toast.info = (msg, dur) => addToast(msg, 'info', dur);

  // Global event listener for custom toast events emitted by api.js or window
  useEffect(() => {
    const handleGlobalToast = (event) => {
      if (event.detail) {
        const { message, type, duration } = event.detail;
        addToast(message, type || 'info', duration || 4000);
      }
    };

    window.addEventListener('careerai:toast', handleGlobalToast);
    return () => {
      window.removeEventListener('careerai:toast', handleGlobalToast);
    };
  }, [addToast]);

  return (
    <ToastContext.Provider value={{ toast, addToast, removeToast }}>
      {children}

      {/* Floating Toast Container */}
      <div className="fixed top-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
        {toasts.map((t) => {
          const typeConfig = {
            success: {
              bg: 'bg-emerald-50 text-emerald-950 border-emerald-200/80',
              icon: CheckCircle2,
              iconColor: 'text-emerald-600',
            },
            error: {
              bg: 'bg-rose-50 text-rose-950 border-rose-200/80',
              icon: AlertCircle,
              iconColor: 'text-rose-600',
            },
            warning: {
              bg: 'bg-amber-50 text-amber-950 border-amber-200/80',
              icon: AlertTriangle,
              iconColor: 'text-amber-600',
            },
            info: {
              bg: 'bg-indigo-50 text-indigo-950 border-indigo-200/80',
              icon: Info,
              iconColor: 'text-indigo-600',
            },
          }[t.type] || {
            bg: 'bg-slate-50 text-slate-900 border-slate-200',
            icon: Info,
            iconColor: 'text-slate-600',
          };

          const IconComponent = typeConfig.icon;

          return (
            <div
              key={t.id}
              className={`pointer-events-auto p-4 rounded-2xl border shadow-lg backdrop-blur-sm flex items-start gap-3 transition-all animate-fadeIn ${typeConfig.bg}`}
            >
              <IconComponent className={`w-4 h-4 shrink-0 mt-0.5 ${typeConfig.iconColor}`} />
              <div className="flex-1 text-xs font-medium leading-relaxed">
                {t.message}
              </div>
              <button
                type="button"
                onClick={() => removeToast(t.id)}
                className="text-slate-400 hover:text-slate-600 p-0.5 rounded-lg transition-colors cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
