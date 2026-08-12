import React, { useEffect, useMemo, useState } from 'react';
import {
    CalendarDays, ChevronLeft, ChevronRight, Copy, Dumbbell, Eye,
    Download, EyeOff, FileText, Loader2, LogOut, Plus, Shield, StickyNote,
    Users,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../components/AuthContext';
import { Button, Modal, PageHeader, Surface } from '../components/ui';
import { api } from '../services/api';
import { Temporada } from '../types/fase2';

interface ClubInfo { id: number; nombre: string; owner_user_id: number }
interface ClubTrainer {
    assignment_id: number;
    user_id: number;
    usuario: string;
    nombre: string;
    apellidos: string;
    categoria: string;
    temporada_id: number;
    temporada: string;
    training_count: number;
    match_count: number;
    color: string;
    visible: boolean;
    provisional_password?: string | null;
}
interface Activity {
    type: 'ENTRENAMIENTO' | 'PARTIDO';
    id: number;
    fecha: string;
    hora?: string | null;
    trainer_user_id: number;
    trainer: string;
    categoria: string;
    title: string;
    duration?: number | null;
    objective?: string | null;
    notes?: string | null;
    color: string;
    exercises: { id: number; nombre: string }[];
}
interface Planning {
    trainer_user_id: number;
    trainer: string;
    fecha: string;
    note?: string | null;
    documents: string[];
    color: string;
}
interface Coordination {
    trainers: { user_id: number; display_name: string; categoria: string; color: string }[];
    activities: Activity[];
    planning: Planning[];
}
type Period = 'day' | 'week' | 'month';

const pad = (value: number) => String(value).padStart(2, '0');
const iso = (date: Date) => (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
);
const fromIso = (value: string) => new Date(`${value}T00:00:00`);
const addDays = (date: Date, amount: number) => {
    const result = new Date(date);
    result.setDate(result.getDate() + amount);
    return result;
};
const range = (anchor: Date, period: Period) => {
    if (period === 'day') return [anchor, anchor] as const;
    if (period === 'week') {
        const start = addDays(anchor, anchor.getDay() === 0 ? -6 : 1 - anchor.getDay());
        return [start, addDays(start, 6)] as const;
    }
    return [
        new Date(anchor.getFullYear(), anchor.getMonth(), 1),
        new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0),
    ] as const;
};

export const ClubDashboard: React.FC = () => {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const [club, setClub] = useState<ClubInfo | null>(null);
    const [seasons, setSeasons] = useState<Temporada[]>([]);
    const [trainers, setTrainers] = useState<ClubTrainer[]>([]);
    const [seasonId, setSeasonId] = useState<number | null>(null);
    const [trainerId, setTrainerId] = useState<number | null>(null);
    const [period, setPeriod] = useState<Period>('week');
    const [anchor, setAnchor] = useState(new Date());
    const [coordination, setCoordination] = useState<Coordination>({ trainers: [], activities: [], planning: [] });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [updatingVisibilityId, setUpdatingVisibilityId] = useState<number | null>(null);
    const [exporting, setExporting] = useState(false);
    const [success, setSuccess] = useState('');
    const [assignmentOpen, setAssignmentOpen] = useState(false);
    const [newTrainer, setNewTrainer] = useState({
        nombre: '', apellidos: '', categoria: '',
    });
    const [createdTrainer, setCreatedTrainer] = useState<ClubTrainer | null>(null);
    const [credentialsCopied, setCredentialsCopied] = useState(false);
    const [assigning, setAssigning] = useState(false);
    const [start, end] = useMemo(() => range(anchor, period), [anchor, period]);

    useEffect(() => {
        Promise.all([
            api.get<ClubInfo>('/club'),
            api.get<Temporada[]>('/temporadas'),
            api.get<ClubTrainer[]>('/club/entrenadores'),
        ]).then(([clubData, seasonData, trainerData]) => {
            setClub(clubData);
            setSeasons(seasonData);
            setTrainers(trainerData);
            setSeasonId(trainerData[0]?.temporada_id ?? seasonData[0]?.id ?? null);
            setError('');
        }).catch(() => {
            setError('No se ha podido cargar la información del club.');
        });
    }, []);

    useEffect(() => {
        if (!seasonId) {
            setLoading(false);
            return;
        }
        let active = true;
        setLoading(true);
        api.get<Coordination>('/club/coordination', {
            temporada_id: seasonId,
            coach_user_id: trainerId,
            desde: iso(start),
            hasta: iso(end),
        }).then(data => {
            if (!active) return;
            setCoordination(data);
            setError('');
        }).catch(() => {
            if (!active) return;
            setError('No se ha podido cargar la actividad del club.');
        }).finally(() => {
            if (active) setLoading(false);
        });
        return () => { active = false; };
    }, [seasonId, trainerId, start, end]);

    const seasonTrainers = useMemo(
        () => trainers.filter(item => item.temporada_id === seasonId),
        [trainers, seasonId],
    );
    const visibleSeasonTrainers = useMemo(
        () => seasonTrainers.filter(item => item.visible),
        [seasonTrainers],
    );

    const move = (direction: number) => {
        setAnchor(current => {
            if (period === 'month') {
                return new Date(current.getFullYear(), current.getMonth() + direction, 1);
            }
            return addDays(current, direction * (period === 'day' ? 1 : 7));
        });
    };

    const closeAssignment = () => {
        setAssignmentOpen(false);
        setCreatedTrainer(null);
        setCredentialsCopied(false);
        setNewTrainer({ nombre: '', apellidos: '', categoria: '' });
    };

    const openAssignment = () => {
        setNewTrainer({
            nombre: '', apellidos: '', categoria: '',
        });
        setCreatedTrainer(null);
        setCredentialsCopied(false);
        setAssignmentOpen(true);
        setError('');
    };

    const assignTrainer = async () => {
        if (!seasonId || !newTrainer.nombre.trim() || !newTrainer.apellidos.trim() || !newTrainer.categoria.trim()) return;
        setAssigning(true);
        setError('');
        try {
            const assigned = await api.post<ClubTrainer>('/club/entrenadores', {
                ...newTrainer,
                temporada_id: seasonId,
            });
            setTrainers(await api.get<ClubTrainer[]>('/club/entrenadores'));
            setCreatedTrainer(assigned);
            setSuccess(`${assigned.nombre} ${assigned.apellidos} se ha añadido al club.`);
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : 'No se pudo crear el entrenador.');
        } finally {
            setAssigning(false);
        }
    };

    const copyCredentials = async () => {
        if (!createdTrainer?.provisional_password) return;
        try {
            await navigator.clipboard.writeText(
                `Usuario: ${createdTrainer.usuario}\nContraseña temporal: ${createdTrainer.provisional_password}`,
            );
            setCredentialsCopied(true);
        } catch {
            setError('No se pudieron copiar las credenciales. Copia los datos manualmente.');
        }
    };

    const exportCalendar = async () => {
        if (!seasonId) return;
        setExporting(true);
        setError('');
        try {
            const result = await api.download('/club/coordination/export.xlsx', {
                temporada_id: seasonId,
                coach_user_id: trainerId,
                desde: iso(start),
                hasta: iso(end),
            });
            const url = URL.createObjectURL(result.blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = result.filename;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : 'No se pudo exportar el calendario.');
        } finally {
            setExporting(false);
        }
    };

    const setTrainerVisibility = async (trainer: ClubTrainer) => {
        setUpdatingVisibilityId(trainer.user_id);
        setError('');
        try {
            await api.put(`/club/entrenadores/${trainer.user_id}/visibilidad`, {
                visible: !trainer.visible,
            });
            const nextTrainerId = trainer.visible && trainerId === trainer.user_id
                ? null
                : trainerId;
            const [updatedTrainers, updatedCoordination] = await Promise.all([
                api.get<ClubTrainer[]>('/club/entrenadores'),
                api.get<Coordination>('/club/coordination', {
                    temporada_id: seasonId,
                    coach_user_id: nextTrainerId,
                    desde: iso(start),
                    hasta: iso(end),
                }),
            ]);
            setTrainers(updatedTrainers);
            setCoordination(updatedCoordination);
            setTrainerId(nextTrainerId);
            setSuccess(
                trainer.visible
                    ? `${trainer.nombre} se ha ocultado del calendario del club.`
                    : `${trainer.nombre} vuelve a mostrarse en el calendario del club.`,
            );
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : 'No se pudo actualizar la visibilidad.');
        } finally {
            setUpdatingVisibilityId(null);
        }
    };

    const title = period === 'day'
        ? start.toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })
        : period === 'month'
        ? start.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' })
        : `${start.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })} — ${end.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}`;
    const trainingActivities = coordination.activities.filter(item => item.type === 'ENTRENAMIENTO');
    const matchActivities = coordination.activities.filter(item => item.type === 'PARTIDO');
    const activitiesWithDuration = trainingActivities.filter(item => item.duration != null);
    const plannedMinutes = activitiesWithDuration.reduce((total, item) => total + (item.duration || 0), 0);

    const visibleDays = useMemo(() => {
        if (period === 'day' || period === 'week') {
            const length = period === 'day' ? 1 : 7;
            return Array.from({ length }, (_, index) => iso(addDays(start, index)));
        }
        return [...new Set([
            ...coordination.activities.map(item => item.fecha),
            ...coordination.planning.map(item => item.fecha),
        ])].sort();
    }, [coordination.activities, coordination.planning, period, start]);

    return (
        <div className="min-h-screen bg-slate-100 p-4 sm:p-6">
            <div className="mx-auto max-w-6xl">
                <PageHeader
                    eyebrow="Club"
                    title={club?.nombre || 'Coordinación'}
                    actions={<Button variant="secondary" onClick={async () => { await logout(); navigate('/login'); }}><LogOut className="h-4 w-4" />Salir</Button>}
                />

                {error && <p className="mb-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-800">{error}</p>}
                {success && <p className="mb-4 rounded-xl border border-green-200 bg-green-50 p-3 text-sm font-semibold text-green-800">{success}</p>}

                <Surface className="mb-4 p-3 sm:p-4">
                    <div className="grid gap-3 md:grid-cols-[220px_minmax(0,1fr)]">
                        <div>
                            <label className="field-label">Temporada</label>
                            <select
                                className="field-control"
                                value={seasonId ?? ''}
                                onChange={event => {
                                    setTrainerId(null);
                                    setSeasonId(Number(event.target.value));
                                }}
                            >
                                {seasons.map(season => <option key={season.id} value={season.id}>{season.nombre}</option>)}
                            </select>
                        </div>
                        <div>
                            <p className="field-label">Entrenadores</p>
                            <div className="flex gap-2 overflow-x-auto pb-1">
                                <Filter active={trainerId === null} onClick={() => setTrainerId(null)}>Todos</Filter>
                                {visibleSeasonTrainers.map(trainer => (
                                    <Filter key={trainer.assignment_id} active={trainerId === trainer.user_id} onClick={() => setTrainerId(trainer.user_id)}>
                                        <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: trainer.color }} />
                                        {trainer.nombre} · {trainer.categoria}
                                    </Filter>
                                ))}
                            </div>
                        </div>
                    </div>
                </Surface>

                <div className="mb-4 grid grid-cols-3 gap-2">
                    <Summary label="Entrenos" value={trainingActivities.length} />
                    <Summary label="Partidos" value={matchActivities.length} />
                    <Summary
                        label="Minutos"
                        value={trainingActivities.length > 0 && activitiesWithDuration.length === 0 ? '—' : plannedMinutes}
                    />
                </div>

                <Surface className="overflow-hidden">
                    <div className="flex flex-col gap-3 border-b border-slate-200 bg-slate-50 p-3 sm:flex-row sm:items-center sm:justify-between">
                        <div className="flex items-center gap-2">
                            <CalendarDays className="h-5 w-5 text-primary-700" />
                            <h2 className="font-bold capitalize text-slate-950">{title}</h2>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                            <Button variant="secondary" size="sm" onClick={() => { void exportCalendar(); }} disabled={exporting || !seasonId}>
                                {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                                Exportar Excel
                            </Button>
                            <div className="grid grid-cols-3 rounded-xl bg-slate-200 p-1">
                                {(['day', 'week', 'month'] as Period[]).map(value => (
                                    <button
                                        key={value}
                                        onClick={() => setPeriod(value)}
                                        className={`min-h-10 rounded-lg px-3 text-sm font-semibold ${period === value ? 'bg-white text-primary-800 shadow-sm' : 'text-slate-600'}`}
                                    >
                                        {value === 'day' ? 'Día' : value === 'week' ? 'Semana' : 'Mes'}
                                    </button>
                                ))}
                            </div>
                            <Button variant="ghost" size="sm" onClick={() => move(-1)} aria-label="Periodo anterior"><ChevronLeft className="h-4 w-4" /></Button>
                            <Button variant="ghost" size="sm" onClick={() => move(1)} aria-label="Periodo siguiente"><ChevronRight className="h-4 w-4" /></Button>
                        </div>
                    </div>

                    {coordination.trainers.length > 0 && (
                        <div className="flex flex-wrap gap-x-4 gap-y-2 border-b border-slate-200 bg-white px-3 py-3 sm:px-4" aria-label="Leyenda de entrenadores">
                            {coordination.trainers.map(trainer => (
                                <span key={`${trainer.user_id}-${trainer.categoria}`} className="inline-flex items-center gap-2 text-xs font-semibold text-slate-700">
                                    <span className="h-3 w-3 rounded-full" style={{ backgroundColor: trainer.color }} />
                                    {trainer.display_name} · {trainer.categoria}
                                </span>
                            ))}
                        </div>
                    )}

                    {loading ? (
                        <p className="p-8 text-center text-sm font-semibold text-slate-600">Cargando actividad…</p>
                    ) : coordination.activities.length === 0 && coordination.planning.length === 0 ? (
                        <p className="p-8 text-center text-sm text-slate-600">Sin actividad en este periodo.</p>
                    ) : visibleDays.length === 0 ? (
                        <p className="p-8 text-center text-sm text-slate-600">No hay actividad ni planificación en este periodo.</p>
                    ) : (
                        <div className="divide-y divide-slate-200">
                            {visibleDays.map(day => (
                                <DayGroup
                                    key={day}
                                    date={day}
                                    activities={coordination.activities.filter(item => item.fecha === day)}
                                    planning={coordination.planning.filter(item => item.fecha === day)}
                                />
                            ))}
                        </div>
                    )}
                </Surface>

                <div className="mt-4 flex items-center justify-between gap-3">
                    <h2 className="text-lg font-bold text-slate-950">Entrenadores del club</h2>
                    <Button onClick={openAssignment}><Plus className="h-4 w-4" />Añadir</Button>
                </div>
                <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {seasonTrainers.map(trainer => (
                        <Surface key={trainer.assignment_id} className={`p-4 ${trainer.visible ? '' : 'opacity-70'}`}>
                            <Users className="h-5 w-5" style={{ color: trainer.color }} />
                            <div className="mt-2 flex items-center justify-between gap-3">
                                <h3 className="font-bold text-slate-950">{trainer.nombre} {trainer.apellidos}</h3>
                                <button
                                    onClick={() => { setSuccess(''); void setTrainerVisibility(trainer); }}
                                    disabled={updatingVisibilityId === trainer.user_id}
                                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-slate-700 hover:bg-slate-100 disabled:opacity-60"
                                    aria-label={`${trainer.visible ? 'Ocultar' : 'Mostrar'} a ${trainer.nombre} ${trainer.apellidos}`}
                                    title={trainer.visible ? 'Ocultar del calendario' : 'Mostrar en el calendario'}
                                >
                                    {updatingVisibilityId === trainer.user_id
                                        ? <Loader2 className="h-4 w-4 animate-spin" />
                                        : trainer.visible ? <Eye className="h-5 w-5" /> : <EyeOff className="h-5 w-5" />}
                                </button>
                            </div>
                            <p className="text-sm text-slate-600">{trainer.categoria} · {trainer.temporada}</p>
                            <p className="mt-2 text-sm font-semibold text-slate-800">
                                {trainer.training_count} entrenamientos · {trainer.match_count} partidos en la temporada
                            </p>
                        </Surface>
                    ))}
                </div>
            </div>

            {assignmentOpen && (
                <Modal
                    title="Añadir entrenador"
                    description={createdTrainer
                        ? 'Cuenta creada correctamente. Entrega estas credenciales temporales al entrenador.'
                        : 'Crea una cuenta nueva y asóciala directamente al club.'}
                    onClose={() => { if (!assigning) closeAssignment(); }}
                    footer={(
                        <div className="flex justify-end gap-3">
                            {createdTrainer ? (
                                <Button onClick={closeAssignment}>Cerrar</Button>
                            ) : (
                                <>
                                    <Button variant="secondary" onClick={closeAssignment} disabled={assigning}>Cancelar</Button>
                                    <Button onClick={() => { void assignTrainer(); }} disabled={assigning || !newTrainer.nombre.trim() || !newTrainer.apellidos.trim() || !newTrainer.categoria.trim()}>
                                        {assigning && <Loader2 className="h-4 w-4 animate-spin" />}Crear entrenador
                                    </Button>
                                </>
                            )}
                        </div>
                    )}
                >
                    {createdTrainer ? (
                        <section className="rounded-2xl border border-orange-200 bg-orange-50 p-4 text-orange-950">
                            <p className="text-xs font-black uppercase tracking-wide text-orange-800">Credenciales temporales</p>
                            <dl className="mt-4 space-y-3">
                                <div><dt className="text-sm font-semibold text-orange-800">Usuario</dt><dd className="mt-1 break-all font-mono font-bold">{createdTrainer.usuario}</dd></div>
                                <div><dt className="text-sm font-semibold text-orange-800">Contraseña temporal</dt><dd className="mt-1 break-all font-mono font-bold">{createdTrainer.provisional_password}</dd></div>
                            </dl>
                            <Button variant="secondary" className="mt-4 border-orange-300 text-orange-900" onClick={() => { void copyCredentials(); }}>
                                <Copy className="h-4 w-4" />{credentialsCopied ? 'Credenciales copiadas' : 'Copiar credenciales'}
                            </Button>
                        </section>
                    ) : (
                        <div className="space-y-4">
                            <div className="grid gap-4 sm:grid-cols-2">
                                <div><label className="field-label">Nombre *</label><input className="field-control" value={newTrainer.nombre} onChange={event => setNewTrainer(current => ({ ...current, nombre: event.target.value }))} /></div>
                                <div><label className="field-label">Apellidos *</label><input className="field-control" value={newTrainer.apellidos} onChange={event => setNewTrainer(current => ({ ...current, apellidos: event.target.value }))} /></div>
                            </div>
                            <div>
                                <label className="field-label">Categoría *</label>
                                <input className="field-control" value={newTrainer.categoria} placeholder="Introducir categoría" onChange={event => setNewTrainer(current => ({ ...current, categoria: event.target.value }))} />
                            </div>
                            <p className="text-sm text-slate-600">Temporada: {seasons.find(item => item.id === seasonId)?.nombre || 'Seleccionada'}</p>
                        </div>
                    )}
                </Modal>
            )}
        </div>
    );
};

const DayGroup: React.FC<{ date: string; activities: Activity[]; planning: Planning[] }> = ({ date, activities, planning }) => {
    const parsed = fromIso(date);
    return (
        <section className="grid gap-3 p-3 sm:grid-cols-[90px_minmax(0,1fr)] sm:p-4">
            <div>
                <p className="text-sm font-black uppercase tracking-wide text-primary-800">
                    {parsed.toLocaleDateString('es-ES', { weekday: 'short' })} {parsed.getDate()}
                </p>
                <p className="text-xs font-semibold capitalize text-slate-500">
                    {parsed.toLocaleDateString('es-ES', { month: 'long' })}
                </p>
            </div>
            <div className="space-y-2">
                {activities.map(activity => <ActivityCard key={`${activity.type}-${activity.id}`} activity={activity} />)}
                {planning.map((item, index) => <PlanningCard key={`${item.trainer_user_id}-${index}`} planning={item} />)}
                {activities.length === 0 && planning.length === 0 && (
                    <p className="rounded-xl bg-slate-50 px-3 py-4 text-sm text-slate-500">Sin actividad.</p>
                )}
            </div>
        </section>
    );
};

const ActivityCard: React.FC<{ activity: Activity }> = ({ activity }) => (
    <article className="rounded-xl border border-slate-200 bg-white p-3" style={{ borderLeftColor: activity.color, borderLeftWidth: 5 }}>
        <div className="flex items-start gap-3">
            <span className={`rounded-xl p-2 ${activity.type === 'PARTIDO' ? 'bg-orange-100 text-orange-800' : 'bg-primary-100 text-primary-800'}`}>
                {activity.type === 'PARTIDO' ? <Shield className="h-5 w-5" /> : <Dumbbell className="h-5 w-5" />}
            </span>
            <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                        <p className="font-bold" style={{ color: activity.color }}>{activity.trainer} · {activity.categoria}</p>
                        <h3 className="mt-0.5 break-words font-semibold text-slate-950">{activity.title}</h3>
                    </div>
                    {activity.hora && <time className="text-sm font-bold text-slate-600">{activity.hora}</time>}
                </div>
                <p className="mt-1 text-xs font-bold uppercase tracking-wide text-slate-500">
                    {activity.type === 'PARTIDO' ? 'Partido' : 'Entrenamiento'}
                    {activity.duration ? ` · ${activity.duration} min` : ''}
                </p>
                {activity.objective && <p className="mt-2 text-sm text-slate-600">{activity.objective}</p>}
                {activity.exercises.length > 0 && (
                    <p className="mt-2 text-xs text-slate-500">Ejercicios: {activity.exercises.map(item => item.nombre).join(' · ')}</p>
                )}
            </div>
        </div>
    </article>
);

const PlanningCard: React.FC<{ planning: Planning }> = ({ planning }) => (
    <article className="rounded-xl border border-blue-200 bg-blue-50 p-3" style={{ borderLeftColor: planning.color, borderLeftWidth: 5 }}>
        <p className="flex items-center gap-2 text-sm font-bold text-blue-950">
            <StickyNote className="h-4 w-4" />{planning.trainer} · Planificación
        </p>
        {planning.note && <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{planning.note}</p>}
        {planning.documents.length > 0 && (
            <p className="mt-2 flex items-start gap-1 text-xs text-slate-600">
                <FileText className="mt-0.5 h-3.5 w-3.5 shrink-0" />{planning.documents.join(' · ')}
            </p>
        )}
    </article>
);

const Filter: React.FC<{ active: boolean; onClick: () => void; children: React.ReactNode }> = ({ active, onClick, children }) => (
    <button onClick={onClick} className={`inline-flex min-h-11 shrink-0 items-center gap-2 rounded-xl px-3 text-sm font-semibold ${active ? 'bg-primary-700 text-white' : 'bg-slate-100 text-slate-700'}`}>
        {children}
    </button>
);

const Summary: React.FC<{ label: string; value: number | string }> = ({ label, value }) => (
    <Surface className="p-3 text-center">
        <p className="text-xl font-bold text-slate-950">{value}</p>
        <p className="text-xs font-semibold text-slate-500">{label}</p>
    </Surface>
);
