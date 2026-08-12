import React, { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { KeyRound, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import { useAuth, User } from '../components/AuthContext';

export const FirstAccess: React.FC = () => {
    const { user, login } = useAuth();
    const navigate = useNavigate();
    const [password, setPassword] = useState('');
    const [confirmation, setConfirmation] = useState('');
    const [error, setError] = useState('');
    const [saving, setSaving] = useState(false);
    if (!user?.must_change_password) return <Navigate to="/" replace />;

    const submit = async (event: React.FormEvent) => {
        event.preventDefault();
        if (password !== confirmation) return setError('Las contraseñas no coinciden.');
        setSaving(true);
        setError('');
        try {
            const updated = await api.post<User>('/auth/change-provisional-password', { password });
            login(updated);
            navigate(updated.account_type === 'ADMIN' ? '/admin' : updated.account_type === 'CLUB' ? '/club' : '/dashboard');
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : 'No se pudo cambiar la contraseña.');
        } finally {
            setSaving(false);
        }
    };

    return <div className="flex min-h-screen items-center justify-center bg-primary-950 p-4"><div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl sm:p-8"><KeyRound className="h-9 w-9 text-primary-700" /><h1 className="mt-4 text-2xl font-bold text-slate-950">Cambia tu contraseña</h1><p className="mt-2 text-sm leading-6 text-slate-600">Esta es una contraseña provisional. Debes cambiarla para continuar.</p><form onSubmit={submit} className="mt-6 space-y-4"><div><label className="field-label">Nueva contraseña</label><input type="password" minLength={8} className="field-control" value={password} onChange={event => setPassword(event.target.value)} required autoFocus /></div><div><label className="field-label">Repetir contraseña</label><input type="password" minLength={8} className="field-control" value={confirmation} onChange={event => setConfirmation(event.target.value)} required /></div>{error && <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-800">{error}</p>}<button className="flex min-h-12 w-full items-center justify-center rounded-xl bg-primary-700 px-4 font-bold text-white disabled:bg-slate-300" disabled={saving}>{saving ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Guardar y continuar'}</button></form></div></div>;
};
