import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Perfil, Temporada } from '../types/fase2';
import { BriefcaseBusiness, Building2, CalendarRange, Plus, Save, ShieldCheck, UserCircle2 } from 'lucide-react';
import { Badge, Button, PageHeader, Surface } from './ui';

interface Props {
    isSetup?: boolean;  // true = primer login, false = edición desde perfil
}

export const PerfilForm: React.FC<Props> = ({ isSetup = false }) => {
    const navigate = useNavigate();
    const [temporadas, setTemporadas] = useState<Temporada[]>([]);
    const [form, setForm] = useState({
        nombre: '',
        apellidos: '',
        club_actual: '',
        temporada_actual_id: '' as string | number,
    });
    const [nuevaTemp, setNuevaTemp] = useState({
        nombre: '', fecha_inicio: '', fecha_fin: '',
    });
    const [loading, setLoading] = useState(!isSetup);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        api.get<Temporada[]>('/temporadas').then(setTemporadas).catch(() => setError('No se pudieron cargar las temporadas.'));
        if (!isSetup) {
            api.get<Perfil>('/perfil').then(p => {
                setForm({
                    nombre: p.nombre,
                    apellidos: p.apellidos,
                    club_actual: p.club_actual || '',
                    temporada_actual_id: p.temporada_actual_id || '',
                });
                setLoading(false);
            }).catch(() => {
                setError('No se pudo cargar el perfil.');
                setLoading(false);
            });
        }
    }, [isSetup]);

    const crearTemporada = async () => {
        if (!nuevaTemp.nombre.trim()) return;
        try {
            const t = await api.post<Temporada>('/temporadas', {
                nombre: nuevaTemp.nombre.trim(),
                fecha_inicio: nuevaTemp.fecha_inicio || null,
                fecha_fin: nuevaTemp.fecha_fin || null,
            });
            setTemporadas(prev => [
                ...prev.map(season => ({ ...season, activa: false })), t,
            ]);
            setForm(f => ({ ...f, temporada_actual_id: t.id }));
            setNuevaTemp({ nombre: '', fecha_inicio: '', fecha_fin: '' });
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'No se pudo crear la temporada.');
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!form.nombre.trim() || !form.apellidos.trim()) {
            setError('Nombre y apellidos son obligatorios.');
            return;
        }
        setSaving(true);
        setError('');
        try {
            await api.put<Perfil>('/perfil', {
                nombre: form.nombre.trim(),
                apellidos: form.apellidos.trim(),
                club_actual: form.club_actual.trim() || null,
                temporada_actual_id: form.temporada_actual_id ? Number(form.temporada_actual_id) : null,
            });
            navigate('/dashboard');
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Error al guardar el perfil.');
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="flex justify-center py-20 font-semibold text-primary-700">Cargando perfil…</div>;

    return (
        <div className={isSetup ? 'min-h-screen bg-slate-100 px-4 py-10 sm:py-16' : ''}>
            <div className="mx-auto max-w-5xl">
                <PageHeader
                    eyebrow={isSetup ? 'Primer acceso' : 'Cuenta profesional'}
                    title={isSetup ? 'Configura tu perfil de entrenador' : 'Mi perfil'}
                    description={isSetup ? 'Completa estos datos para personalizar tu espacio de trabajo y acceder al dashboard.' : 'Actualiza la información que identifica tu contexto deportivo actual.'}
                />

                <div className="grid gap-6 lg:grid-cols-[300px_minmax(0,1fr)]">
                    <div className="h-fit overflow-hidden rounded-2xl bg-primary-950 text-white shadow-panel">
                        <div className="p-6">
                            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-700 ring-4 ring-white/10">
                                <UserCircle2 className="h-9 w-9" />
                            </div>
                            <h2 className="mt-5 text-xl font-bold">{form.nombre || 'Tu nombre'} {form.apellidos}</h2>
                            <Badge className="mt-3 bg-white/10 text-white ring-white/20"><ShieldCheck className="mr-1 h-3.5 w-3.5" />Perfil de entrenador</Badge>
                        </div>
                        <div className="space-y-4 border-t border-white/10 bg-primary-900/60 p-6 text-sm">
                            <div className="flex items-center gap-3 text-primary-100"><Building2 className="h-4 w-4 text-primary-300" /><span>{form.club_actual || 'Club sin asignar'}</span></div>
                            <div className="flex items-center gap-3 text-primary-100"><BriefcaseBusiness className="h-4 w-4 text-primary-300" /><span>Entrenador</span></div>
                            <div className="flex items-center gap-3 text-primary-100"><CalendarRange className="h-4 w-4 text-primary-300" /><span>{temporadas.find(season => season.id === Number(form.temporada_actual_id))?.nombre || 'Temporada sin asignar'}</span></div>
                        </div>
                    </div>

                    <Surface className="overflow-hidden">
                        <div className="border-b border-slate-200 bg-slate-50 px-6 py-4">
                            <h2 className="font-bold text-slate-950">Información profesional</h2>
                            <p className="mt-1 text-sm text-slate-600">Los campos marcados con * son obligatorios.</p>
                        </div>
                        <form onSubmit={handleSubmit} className="grid gap-5 p-6 sm:grid-cols-2">
                    <div>
                        <label className="field-label">Nombre *</label>
                        <input
                            type="text"
                            value={form.nombre}
                            onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))}
                            className="field-control"
                            placeholder="Carlos"
                        />
                    </div>
                    <div>
                        <label className="field-label">Apellidos *</label>
                        <input
                            type="text"
                            value={form.apellidos}
                            onChange={e => setForm(f => ({ ...f, apellidos: e.target.value }))}
                            className="field-control"
                            placeholder="González"
                        />
                    </div>
                    <div className="sm:col-span-2">
                        <label className="field-label">Club actual</label>
                        <input
                            type="text"
                            value={form.club_actual}
                            onChange={e => setForm(f => ({ ...f, club_actual: e.target.value }))}
                            className="field-control"
                            placeholder="CD Ejemplo"
                        />
                    </div>
                    <div>
                        <label className="field-label">Cargo</label>
                        <input className="field-control" value="Entrenador" disabled aria-describedby="cargo-help" />
                        <p id="cargo-help" className="mt-1.5 text-xs text-slate-500">Rol actual de la plataforma.</p>
                    </div>
                    <div>
                        <label className="field-label">Temporada actual</label>
                        <div>
                            <select
                                value={form.temporada_actual_id}
                                onChange={e => setForm(f => ({ ...f, temporada_actual_id: e.target.value }))}
                                className="field-control"
                            >
                                <option value="">— Sin temporada —</option>
                                {temporadas.map(t => (
                                    <option key={t.id} value={t.id}>{t.nombre}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <div className="sm:col-span-2 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <label className="field-label">Crear otra temporada</label>
                        <div className="grid gap-2 sm:grid-cols-3">
                            <input
                                type="text"
                                value={nuevaTemp.nombre}
                                onChange={e => setNuevaTemp(current => ({ ...current, nombre: e.target.value }))}
                                placeholder="Nueva temporada (ej: 2026/27)"
                                className="field-control sm:col-span-3"
                            />
                            <div>
                                <label className="field-label">Fecha de inicio</label>
                                <input type="date" value={nuevaTemp.fecha_inicio} onChange={e => setNuevaTemp(current => ({ ...current, fecha_inicio: e.target.value }))} className="field-control" />
                            </div>
                            <div>
                                <label className="field-label">Fecha de fin</label>
                                <input type="date" value={nuevaTemp.fecha_fin} onChange={e => setNuevaTemp(current => ({ ...current, fecha_fin: e.target.value }))} className="field-control" />
                            </div>
                            <Button
                                type="button"
                                onClick={crearTemporada}
                                variant="secondary"
                                className="self-end"
                            >
                                <Plus className="h-4 w-4" />Crear
                            </Button>
                        </div>
                    </div>

                    {error && <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800 sm:col-span-2">{error}</p>}

                    <Button
                        type="submit"
                        disabled={saving}
                        className="sm:col-span-2 sm:ml-auto"
                    >
                        <Save className="h-4 w-4" />
                        {saving ? 'Guardando…' : isSetup ? 'Guardar y continuar' : 'Guardar cambios'}
                    </Button>
                </form>
                    </Surface>
                </div>
            </div>
        </div>
    );
};
