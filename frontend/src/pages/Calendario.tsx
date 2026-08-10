import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
    CalendarDays, CalendarRange, ChevronLeft, ChevronRight,
    Edit3, List, MapPin, Plus, Target,
} from 'lucide-react';
import { AppLayout } from '../components/AppLayout';
import { DailyResources } from '../components/DailyResources';
import { PartidoFormModal } from '../components/PartidoFormModal';
import { ActionLink, Badge, Button, EmptyState, Modal, PageHeader, Surface } from '../components/ui';
import { api } from '../services/api';
import {
    CalendarioResponse, Partido, PlanificacionDia, Temporada,
} from '../types/fase2';

type CalendarView = 'month' | 'week' | 'list';

const MONTHS = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
const DAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
const pad = (value: number) => String(value).padStart(2, '0');
const isoDate = (date: Date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
const fromIso = (value: string) => new Date(`${value}T00:00:00`);
const displayTime = (value?: string | null) => value ? value.slice(0, 5) : 'Sin hora';

const startOfWeek = (date: Date) => {
    const result = new Date(date);
    const offset = result.getDay() === 0 ? -6 : 1 - result.getDay();
    result.setDate(result.getDate() + offset);
    result.setHours(0, 0, 0, 0);
    return result;
};

const addDays = (date: Date, amount: number) => {
    const result = new Date(date);
    result.setDate(result.getDate() + amount);
    return result;
};

const emptyPlanning = (fecha: string): PlanificacionDia => ({
    fecha,
    entrenamientos: [],
    resumen_entrenamiento: {
        entrenamientos_planificados: 0, sesiones: 0,
        duracion_total: 0, num_ejercicios_total: 0,
    },
    partidos: [],
});

const TrainingIndicator: React.FC<{
    day: PlanificacionDia;
    onClick: () => void;
    compact?: boolean;
}> = ({ day, onClick, compact = false }) => {
    const summary = day.resumen_entrenamiento;
    if (summary.sesiones === 0) return null;
    return (
        <button
            type="button"
            onClick={event => { event.stopPropagation(); onClick(); }}
            className={`w-full rounded-lg border-l-4 border-primary-700 bg-primary-100 text-left text-primary-950 transition hover:bg-primary-200 ${compact ? 'px-2 py-1.5' : 'px-3 py-2.5'}`}
        >
            <span className="block truncate text-[11px] font-extrabold uppercase tracking-wide">Entrenamiento</span>
            <span className="mt-0.5 block truncate text-xs font-semibold">
                {summary.sesiones} {summary.sesiones === 1 ? 'sesión' : 'sesiones'}
                {summary.duracion_total > 0 ? ` · ${summary.duracion_total} min` : ''}
            </span>
        </button>
    );
};

const MatchIndicator: React.FC<{
    match: Partido;
    onClick: () => void;
    compact?: boolean;
}> = ({ match, onClick, compact = false }) => (
    <button
        type="button"
        onClick={event => { event.stopPropagation(); onClick(); }}
        className={`w-full rounded-lg border-l-4 border-orange-600 bg-orange-100 text-left text-orange-950 transition hover:bg-orange-200 ${compact ? 'px-2 py-1.5' : 'px-3 py-2.5'}`}
    >
        <span className="flex items-center gap-1 text-[11px] font-extrabold uppercase tracking-wide">
            <span className="flex h-4 w-4 items-center justify-center rounded bg-orange-700 text-[10px] text-white">P</span>
            Partido {match.hora ? `· ${displayTime(match.hora)}` : ''}
        </span>
        <span className="mt-0.5 block truncate text-xs font-semibold">vs {match.rival}</span>
    </button>
);

interface DayPlanningProps {
    day: PlanificacionDia;
    temporadaId: number;
    canCreate: boolean;
    onAddMatch: () => void;
    onEditMatch: (match: Partido) => void;
}

const DayPlanning: React.FC<DayPlanningProps> = ({
    day, temporadaId, canCreate, onAddMatch, onEditMatch,
}) => {
    const hasContent = day.entrenamientos.length > 0 || day.partidos.length > 0;
    if (!hasContent) {
        return (
            <div>
                <EmptyState
                    icon={CalendarDays}
                    title="Día disponible"
                    description="No hay entrenamientos ni partidos planificados."
                    action={canCreate ? (
                        <div className="flex flex-wrap justify-center gap-2">
                            <ActionLink to={`/entrenamientos/nuevo?fecha=${day.fecha}`} size="sm"><Plus className="h-4 w-4" />Entrenamiento</ActionLink>
                            <Button type="button" variant="secondary" size="sm" onClick={onAddMatch}><Plus className="h-4 w-4" />Partido</Button>
                        </div>
                    ) : undefined}
                />
                <DailyResources fecha={day.fecha} partidos={day.partidos} temporadaId={temporadaId} />
            </div>
        );
    }
    return (
        <div className="space-y-7">
            {day.entrenamientos.length > 0 && (
                <section>
                    <div className="mb-3 flex items-center justify-between gap-3">
                        <div>
                            <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-primary-800">Entrenamiento planificado</p>
                            <p className="mt-1 text-sm text-slate-600">Sesiones del día</p>
                        </div>
                        <Badge tone="green">{day.resumen_entrenamiento.sesiones} {day.resumen_entrenamiento.sesiones === 1 ? 'sesión' : 'sesiones'}</Badge>
                    </div>
                    <div className="overflow-hidden rounded-2xl border border-primary-200 bg-primary-50/40">
                        <div className="divide-y divide-primary-100">
                            {day.entrenamientos.map(training => (
                                <Link key={training.id} to={`/entrenamientos/${training.id}`} className="grid gap-3 p-4 transition hover:bg-primary-100 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
                                    <div className="min-w-0">
                                        <p className="truncate font-bold text-slate-950">{training.nombre}</p>
                                        <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs font-medium text-slate-600">
                                            <span>{training.duracion_minutos ? `${training.duracion_minutos} min` : 'Duración sin definir'}</span>
                                            <span>{training.num_ejercicios} ejercicios</span>
                                            {training.objetivo_principal && <span className="flex min-w-0 items-center gap-1"><Target className="h-3.5 w-3.5" /><span className="truncate">{training.objetivo_principal}</span></span>}
                                        </div>
                                    </div>
                                    <span className="text-xs font-bold text-primary-800">Ver sesión</span>
                                </Link>
                            ))}
                        </div>
                        <div className="flex flex-wrap justify-between gap-2 border-t border-primary-200 bg-primary-100 px-4 py-3 text-sm font-bold text-primary-950">
                            <span>Total entrenamiento</span>
                            <span>{day.resumen_entrenamiento.duracion_total} min · {day.resumen_entrenamiento.num_ejercicios_total} ejercicios</span>
                        </div>
                    </div>
                </section>
            )}

            {day.partidos.length > 0 && (
                <section>
                    <div className="mb-3 flex items-center justify-between gap-3">
                        <div>
                            <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-orange-800">Partido</p>
                            <p className="mt-1 text-sm text-slate-600">Compromisos del día</p>
                        </div>
                        <Badge tone="amber">{day.partidos.length} {day.partidos.length === 1 ? 'partido' : 'partidos'}</Badge>
                    </div>
                    <div className="space-y-3">
                        {day.partidos.map(match => (
                            <article key={match.id} className="rounded-2xl border border-orange-300 bg-orange-50 p-4 text-orange-950 sm:p-5">
                                <div className="flex items-start justify-between gap-4">
                                    <div>
                                        <p className="text-sm font-extrabold uppercase tracking-wide text-orange-800">{displayTime(match.hora)} · {match.local_visitante === 'local' ? 'Local' : 'Visitante'}</p>
                                        <h3 className="mt-1 text-xl font-bold">vs {match.rival}</h3>
                                    </div>
                                    <Button type="button" variant="secondary" size="sm" className="border-orange-300 text-orange-900 hover:bg-orange-100" onClick={() => onEditMatch(match)}><Edit3 className="h-4 w-4" />Editar</Button>
                                </div>
                                {match.campo && <p className="mt-3 flex items-center gap-2 text-sm font-semibold"><MapPin className="h-4 w-4" />{match.campo}</p>}
                                {match.observaciones && <p className="mt-3 whitespace-pre-wrap rounded-xl bg-white/70 p-3 text-sm leading-6 text-slate-800">{match.observaciones}</p>}
                            </article>
                        ))}
                    </div>
                </section>
            )}

            {canCreate && (
                <div className="flex flex-wrap gap-2 border-t border-slate-200 pt-5">
                    <ActionLink to={`/entrenamientos/nuevo?fecha=${day.fecha}`} size="sm"><Plus className="h-4 w-4" />Añadir sesión</ActionLink>
                    <Button type="button" variant="secondary" size="sm" onClick={onAddMatch}><Plus className="h-4 w-4" />Añadir partido</Button>
                </div>
            )}
            <DailyResources fecha={day.fecha} partidos={day.partidos} temporadaId={temporadaId} />
        </div>
    );
};

export const Calendario: React.FC = () => {
    const [searchParams] = useSearchParams();
    const initialDate = searchParams.get('fecha') || searchParams.get('d');
    const today = useMemo(() => new Date(), []);
    const [focusDate, setFocusDate] = useState(() => initialDate ? fromIso(initialDate) : today);
    const [selected, setSelected] = useState(() => initialDate || isoDate(today));
    const [view, setView] = useState<CalendarView>('month');
    const [planning, setPlanning] = useState<Record<string, PlanificacionDia>>({});
    const [numDays, setNumDays] = useState(new Date(focusDate.getFullYear(), focusDate.getMonth() + 1, 0).getDate());
    const [loading, setLoading] = useState(true);
    const [dayOpen, setDayOpen] = useState(Boolean(initialDate));
    const [matchEditor, setMatchEditor] = useState<Partido | 'new' | null>(null);
    const [temporadas, setTemporadas] = useState<Temporada[]>([]);
    const [selectedSeasonId, setSelectedSeasonId] = useState<number | null>(null);

    useEffect(() => {
        api.get<Temporada[]>('/temporadas').then(items => {
            setTemporadas(items);
            const active = items.find(item => item.activa);
            setSelectedSeasonId(current => current ?? active?.id ?? items[0]?.id ?? null);
        }).catch(() => setTemporadas([]));
    }, []);

    const year = focusDate.getFullYear();
    const month = focusDate.getMonth() + 1;
    const weekStart = useMemo(() => startOfWeek(focusDate), [focusDate]);
    const weekDays = useMemo(() => Array.from({ length: 7 }, (_, index) => addDays(weekStart, index)), [weekStart]);

    const loadCalendar = useCallback(async () => {
        setLoading(true);
        const requests = new Map<string, { year: number; month: number; temporada_id?: number }>();
        const seasonParams = selectedSeasonId ? { temporada_id: selectedSeasonId } : {};
        requests.set(`${year}-${month}`, { year, month, ...seasonParams });
        if (view === 'week') {
            weekDays.forEach(date => requests.set(`${date.getFullYear()}-${date.getMonth() + 1}`, {
                year: date.getFullYear(), month: date.getMonth() + 1, ...seasonParams,
            }));
        }
        try {
            const responses = await Promise.all(
                [...requests.values()].map(item => api.get<CalendarioResponse>('/calendario', item))
            );
            setPlanning(Object.assign({}, ...responses.map(response => response.planificacion)));
            const primary = responses.find(response => response.year === year && response.month === month);
            if (primary) setNumDays(primary.num_days);
        } catch {
            setPlanning({});
        } finally {
            setLoading(false);
        }
    }, [month, selectedSeasonId, view, weekDays, year]);

    useEffect(() => { void loadCalendar(); }, [loadCalendar]);

    const openDay = (date: string) => {
        setSelected(date);
        setDayOpen(true);
    };
    const openNewMatch = (date = selected) => {
        setSelected(date);
        setDayOpen(false);
        setMatchEditor('new');
    };
    const openEditMatch = (match: Partido) => {
        setDayOpen(false);
        setMatchEditor(match);
    };
    const finishMatchChange = async (date?: string) => {
        setMatchEditor(null);
        if (date) setSelected(date);
        await loadCalendar();
    };

    const monthPlans = useMemo(() => Object.values(planning)
        .filter(day => {
            const date = fromIso(day.fecha);
            return date.getFullYear() === year && date.getMonth() + 1 === month;
        })
        .sort((a, b) => a.fecha.localeCompare(b.fecha)), [month, planning, year]);

    const selectedDay = planning[selected] || emptyPlanning(selected);
    const activeSeasonId = temporadas.find(item => item.activa)?.id ?? null;
    const canCreate = selectedSeasonId !== null && selectedSeasonId === activeSeasonId;
    const firstWeekday = new Date(year, month - 1, 1).getDay();
    const offset = firstWeekday === 0 ? 6 : firstWeekday - 1;
    const trailing = (7 - ((offset + numDays) % 7)) % 7;

    const changePeriod = (direction: -1 | 1) => {
        const next = new Date(focusDate);
        if (view === 'week') next.setDate(next.getDate() + direction * 7);
        else next.setMonth(next.getMonth() + direction, 1);
        setFocusDate(next);
        setSelected(isoDate(next));
    };
    const goToday = () => {
        setFocusDate(today);
        setSelected(isoDate(today));
    };
    const periodTitle = view === 'week'
        ? `${weekStart.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })} — ${weekDays[6].toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })}`
        : `${MONTHS[month - 1]} ${year}`;

    const AgendaList = () => (
        <Surface className="overflow-hidden">
            {monthPlans.length === 0 ? (
                <EmptyState
                    icon={CalendarDays}
                    title="Sin planificación este mes"
                    description="No hay entrenamientos ni partidos en esta temporada."
                    action={canCreate ? <ActionLink to={`/entrenamientos/nuevo?fecha=${selected}`} size="sm"><Plus className="h-4 w-4" />Nuevo entrenamiento</ActionLink> : undefined}
                />
            ) : (
                <div className="divide-y divide-slate-200">
                    {monthPlans.map(day => (
                        <button key={day.fecha} type="button" onClick={() => openDay(day.fecha)} className="grid w-full gap-3 p-4 text-left transition hover:bg-slate-50 sm:grid-cols-[90px_minmax(0,1fr)_auto] sm:items-center sm:px-5">
                            <div>
                                <p className="text-xl font-bold text-slate-950">{fromIso(day.fecha).getDate()}</p>
                                <p className="text-xs font-bold uppercase tracking-wider text-primary-700">{MONTHS[fromIso(day.fecha).getMonth()].slice(0, 3)}</p>
                            </div>
                            <div className="flex min-w-0 flex-wrap gap-2">
                                {day.partidos.map(match => <Badge key={match.id} tone="amber">P · {match.rival} · {displayTime(match.hora)}</Badge>)}
                                {day.resumen_entrenamiento.sesiones > 0 && <Badge tone="green">Entrenamiento · {day.resumen_entrenamiento.sesiones} {day.resumen_entrenamiento.sesiones === 1 ? 'sesión' : 'sesiones'} · {day.resumen_entrenamiento.duracion_total} min</Badge>}
                            </div>
                            <span className="text-sm font-bold text-primary-800">Ver planificación</span>
                        </button>
                    ))}
                </div>
            )}
        </Surface>
    );

    return (
        <AppLayout>
            <PageHeader
                eyebrow="Planificación deportiva"
                title="Calendario"
                description="Consulta la carga diaria y los partidos sin saturar la vista mensual."
                actions={
                    canCreate ? <>
                        <Button type="button" variant="secondary" onClick={() => openNewMatch()} className="border-orange-300 text-orange-900 hover:bg-orange-100"><Plus className="h-4 w-4" />Añadir partido</Button>
                        <ActionLink to={`/entrenamientos/nuevo?fecha=${selected}`}><Plus className="h-4 w-4" />Nuevo entrenamiento</ActionLink>
                    </> : undefined
                }
            />

            <Surface className="mb-5 p-3 sm:p-4">
                <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
                    <div className="min-w-[220px]">
                        <label htmlFor="calendar-season" className="field-label">Temporada del calendario</label>
                        <select
                            id="calendar-season"
                            className="field-control"
                            value={selectedSeasonId ?? ''}
                            onChange={event => setSelectedSeasonId(Number(event.target.value))}
                        >
                            {temporadas.map(season => (
                                <option key={season.id} value={season.id}>
                                    {season.nombre}{season.activa ? ' · activa' : ''}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button variant="secondary" size="sm" onClick={() => changePeriod(-1)} aria-label="Periodo anterior"><ChevronLeft className="h-4 w-4" /></Button>
                        <h2 className="min-w-0 flex-1 text-center text-lg font-bold capitalize text-slate-950 sm:min-w-[260px]">{periodTitle}</h2>
                        <Button variant="secondary" size="sm" onClick={() => changePeriod(1)} aria-label="Periodo siguiente"><ChevronRight className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={goToday}>Hoy</Button>
                    </div>
                    <div className="grid grid-cols-3 rounded-xl bg-slate-100 p-1" aria-label="Vista de calendario">
                        {([
                            ['month', CalendarDays, 'Mes'],
                            ['week', CalendarRange, 'Semana'],
                            ['list', List, 'Lista'],
                        ] as const).map(([value, Icon, label]) => (
                            <button key={value} type="button" onClick={() => setView(value)} className={`flex min-h-9 items-center justify-center gap-1.5 rounded-lg px-3 text-sm font-semibold transition ${view === value ? 'bg-white text-primary-800 shadow-sm' : 'text-slate-600 hover:bg-slate-200 hover:text-slate-950'}`}>
                                <Icon className="h-4 w-4" />{label}
                            </button>
                        ))}
                    </div>
                </div>
            </Surface>

            {view === 'list' ? <AgendaList /> : (
                <>
                    <div className="md:hidden"><AgendaList /></div>
                    {view === 'month' && (
                        <Surface className="hidden overflow-hidden md:block">
                            <div className="grid grid-cols-7 border-b border-slate-200 bg-slate-50">
                                {DAYS.map(day => <div key={day} className="px-2 py-3 text-center text-xs font-bold uppercase tracking-wider text-slate-600">{day.slice(0, 3)}</div>)}
                            </div>
                            <div className="grid grid-cols-7 gap-px bg-slate-200">
                                {Array.from({ length: offset }, (_, index) => <div key={`before-${index}`} className="min-h-[150px] bg-slate-50" />)}
                                {Array.from({ length: numDays }, (_, index) => {
                                    const dayNumber = index + 1;
                                    const key = `${year}-${pad(month)}-${pad(dayNumber)}`;
                                    const day = planning[key] || emptyPlanning(key);
                                    const isToday = key === isoDate(today);
                                    const isSelected = key === selected;
                                    return (
                                        <div key={key} onClick={() => openDay(key)} className={`min-h-[150px] cursor-pointer bg-white p-2 transition hover:bg-slate-50 ${isSelected ? 'relative z-10 ring-2 ring-inset ring-primary-600' : ''}`}>
                                            <div className="mb-2 flex items-center justify-between">
                                                <span className={`flex h-7 w-7 items-center justify-center rounded-lg text-sm font-bold ${isToday ? 'bg-primary-800 text-white' : 'text-slate-700'}`}>{dayNumber}</span>
                                                {(day.partidos.length > 0 || day.entrenamientos.length > 0) && <span className="text-[10px] font-bold uppercase text-slate-500">Planificado</span>}
                                            </div>
                                            <div className="space-y-1.5">
                                                {day.partidos.map(match => <MatchIndicator key={match.id} match={match} onClick={() => openDay(key)} compact />)}
                                                <TrainingIndicator day={day} onClick={() => openDay(key)} compact />
                                            </div>
                                        </div>
                                    );
                                })}
                                {Array.from({ length: trailing }, (_, index) => <div key={`after-${index}`} className="min-h-[150px] bg-slate-50" />)}
                            </div>
                        </Surface>
                    )}

                    {view === 'week' && (
                        <Surface className="hidden overflow-x-auto md:block">
                            <div className="grid min-w-[980px] grid-cols-7 gap-px bg-slate-200">
                                {weekDays.map(date => {
                                    const key = isoDate(date);
                                    const day = planning[key] || emptyPlanning(key);
                                    const isToday = key === isoDate(today);
                                    return (
                                        <div key={key} className="min-h-[420px] bg-white">
                                            <button type="button" onClick={() => openDay(key)} className={`w-full border-b border-slate-200 px-3 py-4 text-left ${selected === key ? 'bg-primary-50' : 'bg-slate-50 hover:bg-slate-100'}`}>
                                                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">{DAYS[(date.getDay() + 6) % 7]}</p>
                                                <p className={`mt-1 text-2xl font-bold ${isToday ? 'text-primary-700' : 'text-slate-950'}`}>{date.getDate()}</p>
                                            </button>
                                            <div className="space-y-2 p-2.5">
                                                {day.partidos.map(match => <MatchIndicator key={match.id} match={match} onClick={() => openDay(key)} />)}
                                                <TrainingIndicator day={day} onClick={() => openDay(key)} />
                                                {day.partidos.length === 0 && day.entrenamientos.length === 0 && <p className="px-1 py-5 text-center text-xs font-medium text-slate-500">Día disponible</p>}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </Surface>
                    )}
                </>
            )}

            {loading && <p className="mt-4 text-center text-sm font-medium text-slate-600">Actualizando calendario…</p>}

            {dayOpen && selectedSeasonId !== null && (
                <Modal
                    title={`Planificación — ${fromIso(selected).toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}`}
                    description="Entrenamientos y partidos previstos para este día."
                    onClose={() => setDayOpen(false)}
                    size="lg"
                >
                    <DayPlanning
                        day={selectedDay}
                        temporadaId={selectedSeasonId}
                        canCreate={canCreate}
                        onAddMatch={() => openNewMatch(selected)}
                        onEditMatch={openEditMatch}
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
