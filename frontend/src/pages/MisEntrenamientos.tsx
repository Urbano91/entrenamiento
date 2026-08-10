import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { AppLayout } from '../components/AppLayout';
import { ActionLink, Badge, Button, EmptyState, Modal, PageHeader, Surface } from '../components/ui';
import { EntrenamientoDetail, EntrenamientoList, Temporada } from '../types/fase2';
import { CalendarRange, Clock3, Copy, Dumbbell, Edit3, Eye, Plus, Target, Trash2 } from 'lucide-react';

type Filter = 'all' | 'week' | 'month';
const fromIso = (value: string) => new Date(`${value}T00:00:00`);
const todayIso = () => {
    const date = new Date();
    const pad = (value: number) => String(value).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
};

export const MisEntrenamientos: React.FC = () => {
    const navigate = useNavigate();
    const [entrenamientos, setEntrenamientos] = useState<EntrenamientoList[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<Filter>('all');
    const [confirmId, setConfirmId] = useState<number | null>(null);
    const [reutId, setReutId] = useState<number | null>(null);
    const [reutNombre, setReutNombre] = useState('');
    const [reutFecha, setReutFecha] = useState('');
    const [error, setError] = useState('');
    const [temporadas, setTemporadas] = useState<Temporada[]>([]);
    const [selectedSeasonId, setSelectedSeasonId] = useState<number | null>(null);

    useEffect(() => {
        api.get<Temporada[]>('/temporadas').then(items => {
            setTemporadas(items);
            setSelectedSeasonId(items.find(item => item.activa)?.id ?? items[0]?.id ?? null);
        }).catch(() => {
            setError('No se pudieron cargar las temporadas.');
            setLoading(false);
        });
    }, []);

    useEffect(() => {
        if (selectedSeasonId === null) return;
        setLoading(true);
        api.get<EntrenamientoList[]>('/entrenamientos', { temporada_id: selectedSeasonId })
            .then(setEntrenamientos)
            .catch(() => setError('No se pudieron cargar los entrenamientos.'))
            .finally(() => setLoading(false));
    }, [selectedSeasonId]);

    const filtered = useMemo(() => {
        const today = new Date();
        const weekStart = new Date(today);
        weekStart.setDate(today.getDate() - (today.getDay() === 0 ? 6 : today.getDay() - 1));
        weekStart.setHours(0, 0, 0, 0);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);

        return entrenamientos.filter(training => {
            const date = fromIso(training.fecha);
            if (filter === 'week') return date >= weekStart && date <= weekEnd;
            if (filter === 'month') return date.getMonth() === today.getMonth() && date.getFullYear() === today.getFullYear();
            return true;
        });
    }, [entrenamientos, filter]);

    const handleEliminar = async (id: number) => {
        try {
            await api.delete(`/entrenamientos/${id}`);
            setEntrenamientos(previous => previous.filter(training => training.id !== id));
            setConfirmId(null);
        } catch (caught: unknown) {
            setError(caught instanceof Error ? caught.message : 'No se pudo eliminar el entrenamiento.');
        }
    };

    const handleReutilizar = async () => {
        if (!reutId || !reutFecha) return;
        try {
            const copy = await api.post<EntrenamientoDetail>(`/entrenamientos/${reutId}/reutilizar`, {
                fecha: reutFecha,
                nombre: reutNombre || undefined,
            });
            setReutId(null);
            navigate(`/entrenamientos/${copy.id}`);
        } catch (caught: unknown) {
            setError(caught instanceof Error ? caught.message : 'No se pudo duplicar el entrenamiento.');
        }
    };

    const reusable = reutId ? entrenamientos.find(training => training.id === reutId) : null;

    return (
        <AppLayout>
            <PageHeader
                eyebrow="Planificación"
                title="Mis entrenamientos"
                description="Consulta, ajusta y reutiliza las sesiones de tu planificación."
                actions={<ActionLink to="/entrenamientos/nuevo"><Plus className="h-4 w-4" />Nuevo entrenamiento</ActionLink>}
            />

            <Surface className="mb-5 flex flex-col gap-3 p-3 lg:flex-row lg:items-end lg:justify-between sm:p-4">
                <div className="min-w-[220px]">
                    <label htmlFor="training-season" className="field-label"><CalendarRange className="mr-1 inline h-4 w-4" />Temporada</label>
                    <select id="training-season" className="field-control" value={selectedSeasonId ?? ''} onChange={event => setSelectedSeasonId(Number(event.target.value))}>
                        {temporadas.map(season => <option key={season.id} value={season.id}>{season.nombre}{season.activa ? ' · activa' : ''}</option>)}
                    </select>
                </div>
                <div className="grid grid-cols-3 rounded-xl bg-slate-100 p-1">
                    {([
                        ['all', 'Todos'],
                        ['week', 'Esta semana'],
                        ['month', 'Este mes'],
                    ] as const).map(([value, label]) => (
                        <button
                            key={value}
                            onClick={() => setFilter(value)}
                            className={`min-h-9 rounded-lg px-3 text-sm font-semibold transition ${filter === value ? 'bg-white text-primary-800 shadow-sm' : 'text-slate-600 hover:bg-slate-200 hover:text-slate-950'}`}
                        >
                            {label}
                        </button>
                    ))}
                </div>
                <p className="px-1 text-sm font-medium text-slate-600">{filtered.length} {filtered.length === 1 ? 'entrenamiento' : 'entrenamientos'}</p>
            </Surface>

            {error && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</div>}

            <Surface className="overflow-hidden">
                {loading ? (
                    <p className="px-6 py-16 text-center text-sm font-semibold text-slate-500">Cargando entrenamientos…</p>
                ) : filtered.length === 0 ? (
                    <EmptyState
                        icon={Dumbbell}
                        title="No hay entrenamientos en este periodo"
                        description="Cambia el filtro o crea una nueva sesión para tu equipo."
                        action={<ActionLink to="/entrenamientos/nuevo" size="sm"><Plus className="h-4 w-4" />Crear entrenamiento</ActionLink>}
                    />
                ) : (
                    <div className="divide-y divide-slate-200">
                        {filtered.map(training => {
                            const date = fromIso(training.fecha);
                            return (
                                <article key={training.id} className="grid gap-4 p-4 sm:grid-cols-[86px_minmax(0,1fr)] sm:p-5 xl:grid-cols-[86px_minmax(0,1fr)_auto] xl:items-center">
                                    <div className="rounded-xl bg-slate-950 px-3 py-2.5 text-center text-white">
                                        <p className="text-2xl font-bold">{date.getDate()}</p>
                                        <p className="text-[11px] font-bold uppercase tracking-wider text-primary-300">{date.toLocaleDateString('es-ES', { month: 'short' })}</p>
                                        <p className="mt-0.5 text-[10px] font-medium text-slate-300">{date.toLocaleDateString('es-ES', { weekday: 'short' })}</p>
                                    </div>
                                    <div className="min-w-0">
                                        <div className="flex flex-wrap items-center gap-2">
                                            <h2 className="truncate text-base font-bold text-slate-950">{training.nombre}</h2>
                                            {training.fecha >= todayIso() && <Badge tone="green">Planificado</Badge>}
                                        </div>
                                        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-2 text-sm text-slate-600">
                                            {training.duracion_minutos && <span className="flex items-center gap-1.5"><Clock3 className="h-4 w-4" />{training.duracion_minutos} min</span>}
                                            <span className="flex items-center gap-1.5"><Dumbbell className="h-4 w-4" />{training.num_ejercicios} ejercicios</span>
                                            {training.objetivo_principal && <span className="flex min-w-0 items-center gap-1.5"><Target className="h-4 w-4 shrink-0" /><span className="truncate">{training.objetivo_principal}</span></span>}
                                        </div>
                                    </div>
                                    <div className="flex flex-wrap gap-2 sm:col-start-2 xl:col-start-auto">
                                        <ActionLink to={`/entrenamientos/${training.id}`} variant="secondary" size="sm" title="Ver entrenamiento"><Eye className="h-4 w-4" />Ver</ActionLink>
                                        <ActionLink to={`/entrenamientos/${training.id}/editar`} variant="ghost" size="sm" title="Editar entrenamiento"><Edit3 className="h-4 w-4" />Editar</ActionLink>
                                        <Button variant="ghost" size="sm" onClick={() => { setReutId(training.id); setReutNombre(''); setReutFecha(''); }} title="Duplicar entrenamiento"><Copy className="h-4 w-4" />Duplicar</Button>
                                        <Button variant="ghost" size="sm" onClick={() => setConfirmId(training.id)} className="text-red-700 hover:bg-red-50 hover:text-red-800" title="Eliminar entrenamiento"><Trash2 className="h-4 w-4" />Eliminar</Button>
                                    </div>
                                </article>
                            );
                        })}
                    </div>
                )}
            </Surface>

            {confirmId && (
                <Modal
                    title="Eliminar entrenamiento"
                    description="Se eliminará la sesión y sus relaciones. La biblioteca de ejercicios no se verá afectada."
                    onClose={() => setConfirmId(null)}
                    footer={<div className="flex justify-end gap-3"><Button variant="secondary" onClick={() => setConfirmId(null)}>Cancelar</Button><Button variant="danger" onClick={() => handleEliminar(confirmId)}>Eliminar</Button></div>}
                >
                    <p className="text-sm leading-6 text-slate-700">Esta acción no se puede deshacer.</p>
                </Modal>
            )}

            {reutId && reusable && (
                <Modal
                    title="Duplicar entrenamiento"
                    description={`Crea una copia independiente de “${reusable.nombre}” en la temporada activa.`}
                    onClose={() => setReutId(null)}
                    footer={<div className="flex justify-end gap-3"><Button variant="secondary" onClick={() => setReutId(null)}>Cancelar</Button><Button onClick={handleReutilizar} disabled={!reutFecha}><Copy className="h-4 w-4" />Crear copia</Button></div>}
                >
                    <div className="space-y-4">
                        <div>
                            <label className="field-label">Nueva fecha *</label>
                            <input className="field-control" type="date" value={reutFecha} onChange={event => setReutFecha(event.target.value)} />
                        </div>
                        <div>
                            <label className="field-label">Nombre de la copia</label>
                            <input className="field-control" value={reutNombre} onChange={event => setReutNombre(event.target.value)} placeholder={reusable.nombre} />
                        </div>
                    </div>
                </Modal>
            )}
        </AppLayout>
    );
};
