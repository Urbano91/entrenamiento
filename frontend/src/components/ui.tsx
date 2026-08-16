import React from 'react';
import { Link, LinkProps } from 'react-router-dom';
import { LucideIcon, X } from 'lucide-react';
import { useModalBehavior } from './useModalBehavior';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
type Size = 'sm' | 'md';

const variantClasses: Record<Variant, string> = {
    primary: 'bg-primary-700 text-white shadow-sm hover:bg-primary-800 disabled:bg-slate-300 disabled:text-slate-600',
    secondary: 'border border-slate-300 bg-white text-slate-800 hover:border-primary-400 hover:bg-primary-50 disabled:bg-slate-100 disabled:text-slate-600',
    ghost: 'bg-transparent text-slate-700 hover:bg-slate-100 hover:text-slate-950 disabled:bg-slate-100 disabled:text-slate-600',
    danger: 'bg-red-600 text-white shadow-sm hover:bg-red-700 disabled:bg-red-200 disabled:text-red-700',
};

const sizeClasses: Record<Size, string> = {
    sm: 'min-h-11 px-3 py-1.5 text-sm',
    md: 'min-h-11 px-4 py-2.5 text-sm',
};

const actionClasses = (variant: Variant, size: Size) =>
    `inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-colors ${variantClasses[variant]} ${sizeClasses[size]}`;

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: Variant;
    size?: Size;
    loading?: boolean;
    loadingText?: string;
}

export const Button: React.FC<ButtonProps> = ({ variant = 'primary', size = 'md', className = '', loading, loadingText, children, disabled, ...props }) => (
    <button
        className={`${actionClasses(variant, size)} ${className}`}
        disabled={disabled || loading}
        {...props}
    >
        {loading && (
            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
        )}
        {loading ? (loadingText ?? children) : children}
    </button>
);

interface ActionLinkProps extends LinkProps {
    variant?: Variant;
    size?: Size;
}

export const ActionLink: React.FC<ActionLinkProps> = ({ variant = 'primary', size = 'md', className = '', ...props }) => (
    <Link className={`${actionClasses(variant, size)} ${className}`} {...props} />
);

interface PageHeaderProps {
    eyebrow?: string;
    title: string;
    description?: string;
    actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({ eyebrow, title, description, actions }) => (
    <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
            {eyebrow && <p className="mb-1 text-xs font-semibold uppercase tracking-[0.14em] text-primary-700">{eyebrow}</p>}
            <h1 className="text-[22px] font-bold leading-tight tracking-tight text-slate-950 sm:text-[28px]">{title}</h1>
            {description && <p className="mt-1 max-w-2xl text-sm leading-5 text-slate-600">{description}</p>}
        </div>
        {actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}
    </div>
);

export const Surface: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', ...props }) => (
    <div className={`rounded-2xl border border-slate-200 bg-white shadow-panel ${className}`} {...props} />
);

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    tone?: 'green' | 'slate' | 'blue' | 'amber';
}

const badgeClasses = {
    green: 'bg-primary-100 text-primary-800 ring-primary-200',
    slate: 'bg-slate-100 text-slate-700 ring-slate-200',
    blue: 'bg-blue-50 text-blue-700 ring-blue-200',
    amber: 'bg-amber-50 text-amber-800 ring-amber-200',
};

export const Badge: React.FC<BadgeProps> = ({ tone = 'slate', className = '', ...props }) => (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${badgeClasses[tone]} ${className}`} {...props} />
);

interface EmptyStateProps {
    icon: LucideIcon;
    title: string;
    description: string;
    action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon: Icon, title, description, action }) => (
    <div className="flex flex-col items-center px-5 py-9 text-center sm:py-10">
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-500">
            <Icon className="h-5 w-5" />
        </div>
        <h3 className="font-semibold text-slate-900">{title}</h3>
        <p className="mt-1 max-w-sm text-sm leading-6 text-slate-600">{description}</p>
        {action && <div className="mt-4">{action}</div>}
    </div>
);

interface ModalProps {
    title: string;
    description?: string;
    children: React.ReactNode;
    footer?: React.ReactNode;
    onClose: () => void;
    size?: 'sm' | 'md' | 'lg' | 'xl';
}

const modalWidths = { sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-2xl', xl: 'max-w-5xl' };

const ModalHeader: React.FC<Pick<ModalProps, 'title' | 'description' | 'onClose'>> = ({ title, description, onClose }) => (
    <div className="flex shrink-0 items-start justify-between gap-3 border-b border-slate-200 px-4 py-3 sm:px-5 sm:py-4">
        <div className="min-w-0">
            <h2 className="break-words text-lg font-bold text-slate-950">{title}</h2>
            {description && <p className="mt-1 break-words text-sm text-slate-600">{description}</p>}
        </div>
        <button
            type="button"
            onClick={onClose}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 transition-colors hover:bg-slate-100 hover:text-slate-950"
            aria-label="Cerrar"
        >
            <X className="h-5 w-5" aria-hidden="true" />
        </button>
    </div>
);

export const Modal: React.FC<ModalProps> = ({ title, description, children, footer, onClose, size = 'md' }) => {
    useModalBehavior(onClose);

    return (
        <div
            className="fixed inset-0 z-[60] flex items-center justify-center overflow-x-hidden bg-slate-950/60 p-3 backdrop-blur-sm sm:p-4"
            onClick={event => { if (event.target === event.currentTarget) onClose(); }}
        >
            <div
                role="dialog"
                aria-modal="true"
                aria-label={title}
                className={`flex max-h-[calc(100dvh-1.5rem)] min-w-0 w-full flex-col overflow-hidden rounded-2xl bg-white shadow-2xl sm:max-h-[92dvh] ${modalWidths[size]}`}
                onClick={event => event.stopPropagation()}
            >
                <ModalHeader title={title} description={description} onClose={onClose} />
                <div className="min-w-0 overflow-x-hidden overflow-y-auto overscroll-contain p-4 sm:p-5">{children}</div>
                {footer && <div className="min-w-0 shrink-0 border-t border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">{footer}</div>}
            </div>
        </div>
    );
};
