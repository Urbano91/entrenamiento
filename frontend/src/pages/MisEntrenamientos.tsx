import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { AppLayout } from '../components/AppLayout';
import { TemporalNavigation } from '../components/TemporalNavigation';
import { changeFocusDate, datesForView, isoDate, TemporalView } from '../components/temporal';
import { ActionLink, Badge, Button, Modal, PageHeader, Surface } from '../components/ui';
import { EntrenamientoDetail, EntrenamientoList, Temporada } from '../types/fase2';
import { Clock3, Copy, Dumbbell, Edit3, Eye, Plus, Target, Trash2, UserRound } from 'lucide-react';

const todayIso = () => {
    const date = new Date();
    const pad = (value: number) => String(value).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
};

export const MisEntrenamientos: React.FC = () => {
    const navigate = useNavigate();
    const [entrenamientos, setEntrenamientos] = useState<EntrenamientoList[]>([]);
    const [loading, setLoading] = useState(true);
    const today = useMemo(() => new Date(), []);
    const todayKey = isoDate(today);
    const [focusDate, setFocusDate] = useState(() => today);
    const [view, setView] = useState<TemporalView>('day');
    const [confirmId, setConfirmId] = useState<number | null>(null);
    const [reutId, setReutId] = useState<number | null>(null);
    const [reutNombre, setReutNombre] = useState('');
    const [reutFecha, setReutFecha] = useState('');
    const [error, setError] = useState('');
    const [selectedSeasonId, setSelectedSeasonId] = useState<number | null>(null);

    useEffect(() => {
        api.get<Temporada[]>('/temporadas').then(items => {
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

    const visibleDates = useMemo(() => datesForView(focusDate, view), [focusDate, view]);
    const trainingsByDate = useMemo(
        () => entrenamientos.reduce<Record<string, EntrenamientoList[]>>(
            (groups, training) => {
                (groups[training.fecha] ||= []).push(training);
                return groups;
            },
            {},
        ),
        [entrenamientos],
    );

    const changePeriod = (direction: -1 | 1) => {
        setFocusDate(changeFocusDate(focusDate, view, direction));
    };

    const goToday = () => setFocusDate(today);

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
        if (reutFecha < todayIso()) {
            setError('No puedes crear un entrenamiento en una fecha pasada.');
            return;
        }
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
                actions={<ActionLink to="/entrenamientos/nuevo"><Plus className="h-4 w-4" />Nuevo entrenamiento</ActionLink>}
            />

            <Surface className="mb-4 p-3 sm:p-4">
                <TemporalNavigation
                    focusDate={focusDate}
                    view={view}
                    onChangeView={setView}
                    onChangePeriod={changePeriod}
                    onToday={goToday}
                    ariaLabel="Vista de entrenamientos"
                />
            </Surface>

            {error && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</div>}

            <Surface className="overflow-hidden">
                {loading ? (
                    <p className="px-6 py-16 text-center text-sm font-semibold text-slate-500">Cargando entrenamientos…</p>
                ) : (
                    <div className="divide-y divide-slate-200">
                        {visibleDates.map(date => {
                            const dateKey = isoDate(date);
                            const dayTrainings = trainingsByDate[dateKey] || [];
                            return (
                                <section key={dateKey} className="grid gap-3 p-3 sm:grid-cols-[90px_minmax(0,1fr)] sm:p-4">
                                    <div>
                                        <p className="text-sm font-black uppercase tracking-wide text-primary-800">{date.toLocaleDateString('es-ES', { weekday: 'short' }).replace('.', '')} {date.getDate()}</p>
                                        <p className="mt-0.5 text-xs font-semibold capitalize text-slate-500">{date.toLocaleDateString('es-ES', { month: 'long' })}</p>
                                    </div>
                                    {dayTrainings.length === 0 ? (
                                        <p className="rounded-xl bg-slate-50 px-3 py-4 text-sm text-slate-500">Sin entrenamientos.</p>
                                    ) : (
                                        <div className="space-y-2">
                                            {dayTrainings.map(training => (
                                                <article key={training.id} className="rounded-xl border border-primary-200 bg-primary-50/40 p-3 sm:p-4">
                                                    <div className="flex items-start justify-between gap-3">
                                                        <ActionLink to={`/entrenamientos/${training.id}`} variant="ghost" className="min-w-0 flex-1 !justify-start !p-0 text-left hover:bg-transparent">
                                                            <span className="min-w-0">
                                                                <span className="flex flex-wrap items-center gap-2"><strong className="break-words text-slate-950">{training.nombre}</strong>{training.fecha >= todayKey && <Badge tone="green">Planificado</Badge>}</span>
                                                                <span className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs leading-5 text-slate-600 sm:text-sm">
                                                                    <span className="flex items-center gap-1.5"><Clock3 className="h-4 w-4" />{training.hora ? training.hora.slice(0, 5) : 'Sin hora'}</span>
                                                                    {training.duracion_minutos && <span>{training.duracion_minutos} min</span>}
                                                                    <span className="flex items-center gap-1.5"><Dumbbell className="h-4 w-4" />{training.num_ejercicios} ejercicios</span>
                                                                    {training.objetivo_principal && <span className="flex min-w-0 w-full items-start gap-1.5 text-xs leading-5 sm:w-auto sm:text-sm"><Target className="hidden h-4 w-4 shrink-0 sm:block" /><span className="break-words [overflow-wrap:anywhere]">{training.objetivo_principal}</span></span>}
                                                                </span>
                                                            </span>
                                                        </ActionLink>
                                                    </div>
                                                </article>
                                            ))}
                                        </div>
                                    )}
                                </section>
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
                    description={`Crea una copia independiente de “${reusable.nombre}”.`}
                    onClose={() => setReutId(null)}
                    footer={<div className="flex justify-end gap-3"><Button variant="secondary" onClick={() => setReutId(null)}>Cancelar</Button><Button onClick={handleReutilizar} disabled={!reutFecha || reutFecha < todayIso()}><Copy className="h-4 w-4" />Crear copia</Button></div>}
                >
                    <div className="space-y-3">
                        <div>
                            <label className="field-label">Nueva fecha *</label>
                            <input className="field-control" type="date" min={todayIso()} value={reutFecha} onChange={event => setReutFecha(event.target.value)} />
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
