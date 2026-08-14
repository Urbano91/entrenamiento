import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
    CalendarDays, Dumbbell, Edit3,
    MapPin, Plus, Shield, StickyNote, Target,
} from 'lucide-react';
import { AppLayout } from '../components/AppLayout';
import { DailyResources } from '../components/DailyResources';
import { PartidoFormModal } from '../components/PartidoFormModal';
import { TemporalNavigation } from '../components/TemporalNavigation';
import { changeFocusDate, datesForView, fromIso, isoDate, TemporalView } from '../components/temporal';
import { ActionLink, Badge, Button, EmptyState, Modal, PageHeader, Surface } from '../components/ui';
import { api } from '../services/api';
import { CalendarioResponse, Partido, PlanificacionDia, Temporada } from '../types/fase2';

const displayTime = (value?: string | null) => value ? value.slice(0, 5) : 'Sin hora';

const emptyPlanning = (fecha: string): PlanificacionDia => ({
    fecha,
    nota: null,
    entrenamientos: [],
    resumen_entrenamiento: {
        entrenamientos_planificados: 0,
        sesiones: 0,
        duracion_total: 0,
        num_ejercicios_total: 0,
    },
    partidos: [],
});

interface DayPlanningProps {
    day: PlanificacionDia;
    temporadaId: number;
    canManage: boolean;
    canCreateTraining: boolean;
    onAddMatch: () => void;
    onEditMatch: (match: Partido) => void;
    onResourcesChanged: () => void;
}

const DayPlanning: React.FC<DayPlanningProps> = ({
    day, temporadaId, canManage, canCreateTraining,
    onAddMatch, onEditMatch, onResourcesChanged,
}) => {
    const hasContent = day.entrenamientos.length > 0 || day.partidos.length > 0;
    return (
        <div className="space-y-5">
            {!hasContent && (
                <EmptyState
                    icon={CalendarDays}
                    title="Sin actividad"
                    description="No hay entrenamientos ni partidos planificados. Puedes añadir una nota a este día."
                    action={canManage ? (
                        <div className="flex flex-wrap justify-center gap-2">
                            {canCreateTraining && (
                                <ActionLink to={`/entrenamientos/nuevo?fecha=${day.fecha}`} size="sm" className="h-11">
                                    <Plus className="h-4 w-4" />Entrenamiento
                                </ActionLink>
                            )}
                            <Button type="button" variant="secondary" size="sm" className="h-11" onClick={onAddMatch}>
                                <Plus className="h-4 w-4" />Partido
                            </Button>
                        </div>
                    ) : undefined}
                />
            )}

            {day.entrenamientos.length > 0 && (
                <section>
                    <div className="mb-3 flex items-center justify-between gap-3">
                        <h3 className="text-sm font-extrabold uppercase tracking-wide text-primary-800">Entrenamientos</h3>
                        <Badge tone="green">{day.entrenamientos.length}</Badge>
                    </div>
                    <div className="divide-y divide-primary-100 overflow-hidden rounded-2xl border border-primary-200 bg-primary-50/40">
                        {day.entrenamientos.map(training => (
                            <Link key={training.id} to={`/entrenamientos/${training.id}`} className="block p-3 transition hover:bg-primary-100 sm:px-4">
                                <p className="break-words font-bold text-slate-950">{training.nombre}</p>
                                <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-600">
                                    <span>{displayTime(training.hora)}</span>
                                    <span>{training.duracion_minutos ? `${training.duracion_minutos} min` : 'Duración sin definir'}</span>
                                    <span>{training.num_ejercicios} ejercicios</span>
                                    {training.objetivo_principal && (
                                        <span className="flex items-start gap-1"><Target className="h-3.5 w-3.5 shrink-0" />{training.objetivo_principal}</span>
                                    )}
                                </div>
                            </Link>
                        ))}
                    </div>
                </section>
            )}

            {day.partidos.length > 0 && (
                <section>
                    <div className="mb-3 flex items-center justify-between gap-3">
                        <h3 className="text-sm font-extrabold uppercase tracking-wide text-orange-800">Partidos</h3>
                        <Badge tone="amber">{day.partidos.length}</Badge>
                    </div>
                    <div className="space-y-2">
                        {day.partidos.map(match => (
                            <article key={match.id} className="rounded-2xl border border-orange-300 bg-orange-50 p-3 text-orange-950 sm:p-4">
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <p className="text-xs font-semibold uppercase tracking-wide text-orange-800">{displayTime(match.hora)} · {match.local_visitante === 'local' ? 'Local' : 'Visitante'}</p>
                                        <h4 className="mt-1 text-lg font-bold">vs {match.rival}</h4>
                                    </div>
                                    {canManage && (
                                        <Button type="button" variant="secondary" size="sm" className="h-11 border-orange-300 text-orange-900" onClick={() => onEditMatch(match)}>
                                            <Edit3 className="h-4 w-4" />Editar
                                        </Button>
                                    )}
                                </div>
                                {match.campo && <p className="mt-2 flex items-center gap-2 text-sm"><MapPin className="h-4 w-4" />{match.campo}</p>}
                                {match.observaciones && <p className="mt-2 whitespace-pre-wrap rounded-xl bg-white/70 p-2.5 text-sm text-slate-700">{match.observaciones}</p>}
                            </article>
                        ))}
                    </div>
                </section>
            )}

            {hasContent && canManage && (
                <div className="flex flex-wrap gap-2 border-t border-slate-200 pt-4">
                    {canCreateTraining && (
                        <ActionLink to={`/entrenamientos/nuevo?fecha=${day.fecha}`} size="sm" className="h-11">
                            <Plus className="h-4 w-4" />Entrenamiento
                        </ActionLink>
                    )}
                    <Button type="button" variant="secondary" size="sm" className="h-11" onClick={onAddMatch}>
                        <Plus className="h-4 w-4" />Partido
                    </Button>
                </div>
            )}

            <DailyResources
                fecha={day.fecha}
                partidos={day.partidos}
                temporadaId={temporadaId}
                onChanged={onResourcesChanged}
            />
        </div>
    );
};

export const Calendario: React.FC = () => {
    const [searchParams] = useSearchParams();
    const initialDate = searchParams.get('fecha') || searchParams.get('d');
    const today = useMemo(() => new Date(), []);
    const todayKey = isoDate(today);
    const [focusDate, setFocusDate] = useState(() => initialDate ? fromIso(initialDate) : today);
    const [selected, setSelected] = useState(() => initialDate || todayKey);
    const [view, setView] = useState<TemporalView>('day');
    const [planning, setPlanning] = useState<Record<string, PlanificacionDia>>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [dayOpen, setDayOpen] = useState(Boolean(initialDate));
    const [matchEditor, setMatchEditor] = useState<Partido | 'new' | null>(null);
    const [temporadas, setTemporadas] = useState<Temporada[]>([]);
    const [selectedSeasonId, setSelectedSeasonId] = useState<number | null>(null);

    useEffect(() => {
        api.get<Temporada[]>('/temporadas').then(items => {
            setTemporadas(items);
            const active = items.find(item => item.activa);
            setSelectedSeasonId(current => current ?? active?.id ?? items[0]?.id ?? null);
        }).catch(() => {
            setTemporadas([]);
            setError('No se ha podido cargar el calendario.');
        });
    }, []);

    const visibleDates = useMemo(() => datesForView(focusDate, view), [focusDate, view]);

    const loadCalendar = useCallback(async () => {
        if (selectedSeasonId === null) return;
        setLoading(true);
        const requests = new Map<string, { year: number; month: number; temporada_id: number }>();
        visibleDates.forEach(date => {
            requests.set(`${date.getFullYear()}-${date.getMonth() + 1}`, {
                year: date.getFullYear(),
                month: date.getMonth() + 1,
                temporada_id: selectedSeasonId,
            });
        });
        try {
            const responses = await Promise.all(
                [...requests.values()].map(params => api.get<CalendarioResponse>('/calendario', params)),
            );
            setPlanning(Object.assign({}, ...responses.map(response => response.planificacion)));
            setError('');
        } catch {
            setPlanning({});
            setError('No se ha podido cargar el calendario.');
        } finally {
            setLoading(false);
        }
    }, [selectedSeasonId, visibleDates]);

    useEffect(() => { void loadCalendar(); }, [loadCalendar]);

    const selectedDay = planning[selected] || emptyPlanning(selected);
    const activeSeasonId = temporadas.find(item => item.activa)?.id ?? null;
    const canManage = selectedSeasonId !== null && selectedSeasonId === activeSeasonId;
    const canCreateTraining = canManage && selected >= todayKey;

    const openDay = (date: string) => {
        setSelected(date);
        setDayOpen(true);
    };
    const openNewMatch = (date = selected) => {
        setSelected(date);
        setDayOpen(false);
        setMatchEditor('new');
    };
    const finishMatchChange = async (date?: string) => {
        setMatchEditor(null);
        if (date) setSelected(date);
        await loadCalendar();
    };
    const changePeriod = (direction: -1 | 1) => {
        const next = changeFocusDate(focusDate, view, direction);
        setFocusDate(next);
        setSelected(isoDate(next));
    };
    const goToday = () => {
        setFocusDate(today);
        setSelected(todayKey);
    };

    return (
        <AppLayout>
            <PageHeader
                eyebrow="Planificación deportiva"
                title="Calendario"
                actions={canManage ? (
                    <div className="grid w-full grid-cols-2 gap-2 sm:flex sm:w-auto">
                        <Button type="button" variant="secondary" onClick={() => openNewMatch()} className="w-full border-orange-300 text-orange-900 sm:w-auto">
                            <Plus className="h-4 w-4" />Partido
                        </Button>
                        {canCreateTraining && (
                            <ActionLink to={`/entrenamientos/nuevo?fecha=${selected}`} className="w-full sm:w-auto">
                                <Plus className="h-4 w-4" />Entrenamiento
                            </ActionLink>
                        )}
                    </div>
                ) : undefined}
            />

            {error && (
                <p className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">
                    {error}
                </p>
            )}

            <Surface className="mb-4 p-3 sm:p-4">
                <TemporalNavigation focusDate={focusDate} view={view} onChangeView={setView} onChangePeriod={changePeriod} onToday={goToday} ariaLabel="Vista de calendario" />
            </Surface>

            <Surface className="overflow-hidden">
                <div className="divide-y divide-slate-200">
                    {visibleDates.map(date => {
                        const key = isoDate(date);
                        const day = planning[key] || emptyPlanning(key);
                        return <CalendarDayRow key={key} day={day} onClick={() => openDay(key)} />;
                    })}
                </div>
            </Surface>

            {loading && <p className="mt-4 text-center text-sm font-medium text-slate-600">Actualizando calendario…</p>}

            {dayOpen && selectedSeasonId !== null && (
                <Modal
                    title={`Planificación — ${fromIso(selected).toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}`}
                    description="Entrenamientos, partidos y notas de este día."
                    onClose={() => setDayOpen(false)}
                    size="lg"
                >
                    <DayPlanning
                        day={selectedDay}
                        temporadaId={selectedSeasonId}
                        canManage={canManage}
                        canCreateTraining={canCreateTraining}
                        onAddMatch={() => openNewMatch(selected)}
                        onEditMatch={match => { setDayOpen(false); setMatchEditor(match); }}
                        onResourcesChanged={() => { void loadCalendar(); }}
                    />
                </Modal>
            )}

            {matchEditor && (
                <PartidoFormModal
                    key={matchEditor === 'new' ? `new-${selected}` : `edit-${matchEditor.id}`}
                    fecha={selected}
                    partido={matchEditor === 'new' ? undefined : matchEditor}
                    onClose={() => setMatchEditor(null)}
                    onSaved={saved => { void finishMatchChange(saved.fecha); }}
                    onDeleted={() => { void finishMatchChange(); }}
                />
            )}
        </AppLayout>
    );
};

const CalendarDayRow: React.FC<{ day: PlanificacionDia; onClick: () => void }> = ({ day, onClick }) => {
    const date = fromIso(day.fecha);
    const hasActivity = day.entrenamientos.length > 0 || day.partidos.length > 0 || Boolean(day.nota);
    return (
        <button type="button" onClick={onClick} className="grid min-h-20 w-full gap-3 p-3 text-left transition hover:bg-slate-50 sm:grid-cols-[90px_minmax(0,1fr)] sm:p-4">
            <span>
                <span className="block text-sm font-black uppercase tracking-wide text-primary-800">
                    {date.toLocaleDateString('es-ES', { weekday: 'short' }).replace('.', '')} {date.getDate()}
                </span>
                <span className="mt-0.5 block text-xs font-semibold capitalize text-slate-500">
                    {date.toLocaleDateString('es-ES', { month: 'long' })}
                </span>
            </span>
            <span className="min-w-0 space-y-2">
                {day.entrenamientos.map(training => (
                    <span key={training.id} className="flex min-w-0 items-start gap-2 rounded-xl bg-primary-50 px-3 py-2 text-sm text-primary-950">
                        <Dumbbell className="mt-0.5 h-4 w-4 shrink-0" />
                        <span className="min-w-0"><strong className="block break-words">{training.nombre}</strong><span className="text-xs">{displayTime(training.hora)}{training.duracion_minutos ? ` · ${training.duracion_minutos} min` : ''}</span></span>
                    </span>
                ))}
                {day.partidos.map(match => (
                    <span key={match.id} className="flex min-w-0 items-start gap-2 rounded-xl bg-orange-50 px-3 py-2 text-sm text-orange-950">
                        <Shield className="mt-0.5 h-4 w-4 shrink-0" />
                        <span className="min-w-0"><strong className="block break-words">Partido vs {match.rival}</strong><span className="text-xs">{displayTime(match.hora)}</span></span>
                    </span>
                ))}
                {day.nota && (
                    <span className="flex min-w-0 items-start gap-2 rounded-xl bg-blue-50 px-3 py-2 text-sm text-blue-950">
                        <StickyNote className="mt-0.5 h-4 w-4 shrink-0" />
                        <span className="min-w-0"><strong className="block">Nota</strong><span className="block break-words whitespace-pre-wrap text-xs">{day.nota}</span></span>
                    </span>
                )}
                {!hasActivity && <span className="block rounded-xl bg-slate-50 px-3 py-3 text-sm text-slate-500">Sin actividad.</span>}
            </span>
        </button>
    );
};
