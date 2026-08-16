import { createContext, useCallback, useContext, useRef, useState } from 'react';

export type ToastType = 'success' | 'error' | 'info';

export interface Toast {
    id: string;
    type: ToastType;
    message: string;
}

interface ToastContextValue {
    toasts: Toast[];
    success: (message: string) => void;
    error: (message: string) => void;
    info: (message: string) => void;
    dismiss: (id: string) => void;
}

export const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast(): ToastContextValue {
    const ctx = useContext(ToastContext);
    if (!ctx) throw new Error('useToast must be used inside ToastProvider');
    return ctx;
}

export function useToastState() {
    const [toasts, setToasts] = useState<Toast[]>([]);
    const timers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

    const dismiss = useCallback((id: string) => {
        clearTimeout(timers.current[id]);
        delete timers.current[id];
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    const add = useCallback((type: ToastType, message: string) => {
        const id = `${Date.now()}-${Math.random()}`;
        setToasts(prev => {
            const next = [...prev, { id, type, message }];
            return next.length > 3 ? next.slice(next.length - 3) : next;
        });
        timers.current[id] = setTimeout(() => dismiss(id), 4000);
    }, [dismiss]);

    const success = useCallback((message: string) => add('success', message), [add]);
    const error = useCallback((message: string) => add('error', message), [add]);
    const info = useCallback((message: string) => add('info', message), [add]);

    return { toasts, success, error, info, dismiss };
}
