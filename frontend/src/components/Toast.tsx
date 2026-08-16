import React from 'react';
import { CheckCircle, Info, XCircle, X } from 'lucide-react';
import { Toast, ToastContext, useToastState } from '../utils/useToast';

const icons = {
    success: <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0" />,
    error: <XCircle className="h-5 w-5 text-red-500 shrink-0" />,
    info: <Info className="h-5 w-5 text-blue-500 shrink-0" />,
};

const backgrounds = {
    success: 'bg-white border-emerald-200 shadow-emerald-100',
    error: 'bg-white border-red-200 shadow-red-100',
    info: 'bg-white border-blue-200 shadow-blue-100',
};

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: () => void }) {
    return (
        <div
            className={`flex items-start gap-3 rounded-2xl border px-4 py-3 shadow-lg transition-all duration-300 animate-toast-in ${backgrounds[toast.type]}`}
            role="alert"
            aria-live="polite"
        >
            {icons[toast.type]}
            <p className="flex-1 text-sm font-semibold text-slate-900 leading-5">{toast.message}</p>
            <button
                type="button"
                onClick={onDismiss}
                className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
                aria-label="Cerrar notificación"
            >
                <X className="h-4 w-4" />
            </button>
        </div>
    );
}

export function ToastContainer() {
    const state = React.useContext(ToastContext);
    if (!state || state.toasts.length === 0) return null;

    return (
        <div
            className="fixed bottom-4 left-4 z-[200] flex w-full max-w-sm flex-col gap-2 sm:bottom-6 sm:left-6"
            aria-label="Notificaciones"
        >
            {state.toasts.map(toast => (
                <ToastItem
                    key={toast.id}
                    toast={toast}
                    onDismiss={() => state.dismiss(toast.id)}
                />
            ))}
        </div>
    );
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
    const state = useToastState();
    return (
        <ToastContext.Provider value={state}>
            {children}
            <ToastContainer />
        </ToastContext.Provider>
    );
}
