import React from 'react';
import { Link, LinkProps } from 'react-router-dom';
import { LucideIcon } from 'lucide-react';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
type Size = 'sm' | 'md';

const variantClasses: Record<Variant, string> = {
    primary: 'bg-primary-700 text-white shadow-sm hover:bg-primary-800 disabled:bg-slate-300 disabled:text-slate-600',
    secondary: 'border border-slate-300 bg-white text-slate-800 hover:border-primary-400 hover:bg-primary-50 disabled:bg-slate-100 disabled:text-slate-600',
    ghost: 'bg-transparent text-slate-700 hover:bg-slate-100 hover:text-slate-950 disabled:bg-slate-100 disabled:text-slate-600',
    danger: 'bg-red-600 text-white shadow-sm hover:bg-red-700 disabled:bg-red-200 disabled:text-red-700',
};

const sizeClasses: Record<Size, string> = {
    sm: 'min-h-9 px-3 py-1.5 text-sm',
    md: 'min-h-11 px-4 py-2.5 text-sm',
};

const actionClasses = (variant: Variant, size: Size) =>
    `inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-colors ${variantClasses[variant]} ${sizeClasses[size]}`;

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: Variant;
    size?: Size;
}

export const Button: React.FC<ButtonProps> = ({ variant = 'primary', size = 'md', className = '', ...props }) => (
    <button className={`${actionClasses(variant, size)} ${className}`} {...props} />
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
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
            {eyebrow && <p className="mb-1 text-xs font-bold uppercase tracking-[0.18em] text-primary-700">{eyebrow}</p>}
            <h1 className="text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">{title}</h1>
            {description && <p className="mt-1.5 max-w-2xl text-sm leading-6 text-slate-600">{description}</p>}
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
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${badgeClasses[tone]} ${className}`} {...props} />
);

interface EmptyStateProps {
    icon: LucideIcon;
    title: string;
    description: string;
    action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon: Icon, title, description, action }) => (
    <div className="flex flex-col items-center px-6 py-12 text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
            <Icon className="h-6 w-6" />
        </div>
        <h3 className="font-semibold text-slate-900">{title}</h3>
        <p className="mt-1 max-w-sm text-sm leading-6 text-slate-600">{description}</p>
        {action && <div className="mt-5">{action}</div>}
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

export const Modal: React.FC<ModalProps> = ({ title, description, children, footer, onClose, size = 'md' }) => (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm" onMouseDown={onClose}>
        <div
            role="dialog"
            aria-modal="true"
            aria-label={title}
            className={`flex max-h-[92vh] w-full flex-col overflow-hidden rounded-2xl bg-white shadow-2xl ${modalWidths[size]}`}
            onMouseDown={event => event.stopPropagation()}
        >
            <div className="border-b border-slate-200 px-6 py-5">
                <h2 className="text-lg font-bold text-slate-950">{title}</h2>
                {description && <p className="mt-1 text-sm text-slate-600">{description}</p>}
            </div>
            <div className="overflow-y-auto p-6">{children}</div>
            {footer && <div className="border-t border-slate-200 bg-slate-50 px-6 py-4">{footer}</div>}
        </div>
    </div>
);
