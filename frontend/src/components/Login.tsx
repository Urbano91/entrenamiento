import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, ShieldCheck } from 'lucide-react';
import { useAuth, User } from './AuthContext';
import { api } from '../services/api';

export const Login: React.FC = () => {
    const [usuario, setUsuario] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const submit = async (event: React.FormEvent) => {
        event.preventDefault();
        setLoading(true);
        setError('');
        try {
            await api.post<{ message: string }>('/auth/login', { usuario, password });
            const user = await api.get<User>('/auth/me');
            login(user);
            if (user.must_change_password) {
                navigate(user.account_type === 'ENTRENADOR' ? '/onboarding' : '/first-access');
            } else if (user.account_type === 'ADMIN') {
                navigate('/admin');
            } else if (user.account_type === 'CLUB') {
                navigate('/club');
            } else {
                navigate('/dashboard');
            }
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : 'Usuario o contraseña incorrectos.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-primary-950 px-4 py-6">
            <div className="w-full max-w-sm rounded-3xl bg-white p-6 shadow-2xl sm:p-8">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-primary-100 text-primary-800">
                    <ShieldCheck className="h-7 w-7" />
                </div>
                <p className="mt-4 text-center text-sm font-bold uppercase tracking-[0.18em] text-primary-700">ScoutIA</p>
                <h1 className="mt-1 text-center text-2xl font-bold text-slate-950">Acceso a ScoutIA</h1>
                <form onSubmit={submit} className="mt-6 space-y-4">
                    <div><label className="field-label">Usuario</label><input className="field-control" value={usuario} onChange={event => setUsuario(event.target.value)} autoComplete="username" autoFocus required /></div>
                    <div><label className="field-label">Contraseña</label><input type="password" className="field-control" value={password} onChange={event => setPassword(event.target.value)} autoComplete="current-password" required /></div>
                    {error && <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-center text-sm font-semibold text-red-800">{error}</p>}
                    <button type="submit" disabled={loading || !usuario || !password} className="flex min-h-12 w-full items-center justify-center rounded-xl bg-primary-700 px-4 py-3 text-sm font-bold uppercase tracking-wide text-white hover:bg-primary-800 disabled:bg-slate-300">
                        {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Iniciar sesión'}
                    </button>
                </form>
                <p className="mt-5 text-center text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Acceso para clubes y entrenadores
                </p>
            </div>
        </div>
    );
};
