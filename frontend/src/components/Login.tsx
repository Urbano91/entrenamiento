import React, { useState } from 'react';
import { useAuth, User } from './AuthContext';
import { api } from '../services/api';
import { Loader2, Shield, Trophy } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Login: React.FC = () => {
    const [usuario, setUsuario] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await api.post<{ message: string }>('/auth/login', { usuario, password });
            const userData = await api.get<User>('/auth/me');
            login(userData);
            navigate('/');
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Usuario o contraseña incorrectos.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-primary-950 px-4 py-10">
            <div className="grid w-full max-w-4xl overflow-hidden rounded-3xl bg-white shadow-2xl lg:grid-cols-2">
                <div className="relative hidden overflow-hidden bg-gradient-to-br from-primary-950 to-primary-700 p-10 text-white lg:flex lg:flex-col lg:justify-between">
                    <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full border-[46px] border-white/5" />
                    <div className="relative flex items-center gap-3"><span className="rounded-xl bg-primary-600 p-2.5"><Shield className="h-6 w-6" /></span><span className="font-bold tracking-wide">PLATAFORMA ENTRENADOR</span></div>
                    <div className="relative"><Trophy className="mb-5 h-9 w-9 text-primary-300" /><h2 className="text-3xl font-bold leading-tight">Planifica cada sesión con criterio profesional.</h2><p className="mt-4 text-sm leading-6 text-primary-100">Calendario, biblioteca y gestión del trabajo diario del cuerpo técnico en un único espacio.</p></div>
                </div>

                <div className="p-7 sm:p-10">
                    <div className="mb-8 lg:hidden"><div className="flex items-center gap-3 text-primary-900"><Shield className="h-7 w-7" /><span className="font-bold">PLATAFORMA ENTRENADOR</span></div></div>
                    <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary-700">Acceso privado</p>
                    <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Bienvenido</h1>
                    <p className="mt-2 text-sm text-slate-600">Accede al espacio de planificación de tu equipo.</p>
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="pt-3">
                            <label className="field-label">Usuario</label>
                            <input
                                type="text"
                                className="field-control"
                                value={usuario}
                                onChange={(e) => setUsuario(e.target.value)}
                                required
                            />
                        </div>
                        <div>
                            <label className="field-label">Contraseña</label>
                            <input
                                type="password"
                                className="field-control"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>

                        {error && (
                            <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-center text-sm font-semibold text-red-800">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading || !usuario || !password}
                            className="flex min-h-12 w-full items-center justify-center rounded-xl bg-primary-700 px-4 py-3 font-semibold text-white transition-colors hover:bg-primary-800 disabled:bg-slate-300 disabled:text-slate-600"
                        >
                            {loading ? <Loader2 className="animate-spin w-5 h-5" /> : 'INICIAR SESIÓN'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};
