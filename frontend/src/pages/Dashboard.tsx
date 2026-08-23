import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Activity,
    AlertTriangle,
    ArrowRight,
    CalendarDays,
    Clock3,
    Dumbbell,
    Plus,
    Shield,
} from 'lucide-react';

import { api } from '../services/api';
import { AppLayout } from '../components/AppLayout';
import {
    ActionLink,
    Badge,
    EmptyState,
    PageHeader,
    Surface,
} from '../components/ui';
import { AgendaDia, Perfil } from '../types/fase2';
import { useAuth } from '../components/AuthContext';


const isoDate = (date: Date) => {
    const pad = (value: number) => String(value).padStart(2, '0');

    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(
        date.getDate()
    )}`;
};


const fromIso = (value: string) =>
    new Date(`${value}T00:00:00`);


type WeeklyTraining = {
    entrenamiento_id: number;
    nombre: string;
    fecha: string;
    hora: string | null;
    duracion_minutos: number | null;
    score: number;
    level: string;
};


type NextMatch = {
    partido_id: number;
    fecha: string;
    hora: string | null;
    rival: string;
    local_visitante: string;
    campo: string | null;
    dias_desde_referencia: number;
};


type WeeklyLoadResponse = {
    reference_date: string;
    week_start: string;
    week_end: string;

    summary: {
        training_count: number;
        total_minutes: number;
        average_score: number | null;
        high_load_sessions: number;
        moderate_load_sessions: number;
        low_load_sessions: number;
    };

    trainings: WeeklyTraining[];

    next_match: NextMatch | null;

    recent_14_days: {
        training_count: number;
        average_score: number | null;
    };

    alerts: string[];
};


const loadLevel = (score: number | null) => {
    if (score === null) return 'SIN DATOS';
    if (score < 40) return 'BAJA';
    if (score < 70) return 'MODERADA';

    return 'ALTA';
};


const loadStyle = (level: string) => {
    if (level === 'ALTA') {
        return {
            badge: 'bg-orange-100 text-orange-800 ring-orange-200',
            bar: 'bg-orange-500',
        };
    }

    if (level === 'MODERADA') {
        return {
            badge: 'bg-amber-100 text-amber-800 ring-amber-200',
            bar: 'bg-amber-500',
        };
    }

    return {
        badge: 'bg-emerald-100 text-emerald-800 ring-emerald-200',
        bar: 'bg-emerald-500',
    };
};


export const Dashboard: React.FC = () => {
    const { user } = useAuth();

    const today = useMemo(() => new Date(), []);
    const todayIso = isoDate(today);

    const [perfil, setPerfil] = useState<Perfil | null>(null);
    const [agenda, setAgenda] = useState<AgendaDia[]>([]);

    const [weeklyLoad, setWeeklyLoad] =
        useState<WeeklyLoadResponse | null>(null);

    const [weeklyLoadError, setWeeklyLoadError] =
        useState(false);


    useEffect(() => {
        Promise.all([
            api.get<Perfil>('/perfil'),

            api.get<AgendaDia[]>(
                '/planificaciones/agenda',
                {
                    desde: todayIso,
                    limite: 7,
                }
            ),

            api.get<WeeklyLoadResponse>(
                '/training-load/week',
                {
                    fecha: todayIso,
                }
            )
                .then(result => {
                    setWeeklyLoad(result);
                    setWeeklyLoadError(false);

                    return result;
                })
                .catch(() => {
                    setWeeklyLoad(null);
                    setWeeklyLoadError(true);

                    return null;
                }),
        ])
            .then(([profile, upcomingDays]) => {
                setPerfil(profile);
                setAgenda(upcomingDays);
            })
            .catch(() => {
                setAgenda([]);
            });
    }, [todayIso]);


    const greeting =
        today.getHours() < 12
            ? 'Buenos días'
            : today.getHours() < 20
                ? 'Buenas tardes'
                : 'Buenas noches';


    const averageScore =
        weeklyLoad?.summary.average_score ?? null;

    const currentLevel =
        loadLevel(averageScore);

    const currentStyle =
        loadStyle(currentLevel);


    return (
        <AppLayout>

            {/* ======================================================
                CABECERA
            ====================================================== */}

            <div className="mb-5 overflow-hidden rounded-2xl bg-primary-950 text-white shadow-panel">

                <div className="relative px-5 py-5 sm:px-6 sm:py-6">

                    <div className="absolute -right-16 -top-24 h-64 w-64 rounded-full border-[40px] border-primary-800/40" />

                    <div className="relative flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">

                        <div>

                            <p className="text-sm font-semibold text-primary-300">
                                Panel del cuerpo técnico
                            </p>

                            <h1 className="mt-1.5 text-2xl font-bold tracking-tight sm:text-[28px]">
                                {greeting},{' '}
                                {perfil?.nombre || user?.usuario}
                            </h1>

                            <div className="mt-3 flex flex-wrap items-center gap-2">

                                {perfil?.club_actual && (
                                    <Badge
                                        tone="green"
                                        className="bg-white/10 text-white ring-white/20"
                                    >
                                        {perfil.club_actual}
                                    </Badge>
                                )}

                                <Badge
                                    tone="green"
                                    className="bg-white/10 text-white ring-white/20"
                                >
                                    Temporada{' '}
                                    {perfil?.temporada_actual?.nombre ||
                                        'sin asignar'}
                                </Badge>

                            </div>

                        </div>

                        <ActionLink
                            to="/entrenamientos/nuevo"
                            className="bg-primary-500 text-primary-950 hover:bg-primary-400"
                        >
                            <Plus className="h-5 w-5" />
                            Nueva sesión
                        </ActionLink>

                    </div>

                </div>

            </div>


            {/* ======================================================
                SCOUT IA - RESUMEN SEMANAL
            ====================================================== */}

            {weeklyLoad && (

                <Surface className="mb-6 overflow-hidden">

                    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">

                        <div className="flex items-center gap-3">

                            <span className="rounded-xl bg-primary-100 p-2 text-primary-800">
                                <Activity className="h-5 w-5" />
                            </span>

                            <div>

                                <p className="text-xs font-bold uppercase tracking-wider text-primary-700">
                                    SCOUT IA · ESTA SEMANA
                                </p>

                                <h2 className="mt-1 text-lg font-bold text-slate-950">
                                    Análisis de carga
                                </h2>

                            </div>

                        </div>

                        <div className="flex items-center gap-3">

                            <Badge className="bg-primary-100 text-primary-800 ring-primary-200">
                                BETA
                            </Badge>

                            <Link
                                to={`/analisis-semanal?fecha=${todayIso}`}
                                className="group flex items-center gap-1 text-sm font-bold text-primary-700 transition hover:text-primary-900"
                            >
                                Ver análisis semanal
                                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                            </Link>

                        </div>

                    </div>


                    <div className="grid gap-5 p-4 sm:p-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">

                        {/* CARGA SEMANAL */}

                        <div>

                            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                                Carga semanal media
                            </p>

                            <div className="mt-3 flex flex-wrap items-end gap-3">

                                <span className="text-5xl font-black tracking-tight text-slate-950">
                                    {averageScore !== null
                                        ? Math.round(averageScore)
                                        : '—'}
                                </span>

                                <span className="pb-1 text-xl font-bold text-slate-400">
                                    / 100
                                </span>

                                {averageScore !== null && (
                                    <span
                                        className={`mb-1 rounded-full px-3 py-1 text-xs font-bold ring-1 ${currentStyle.badge}`}
                                    >
                                        {currentLevel}
                                    </span>
                                )}

                            </div>


                            {averageScore !== null && (

                                <div className="mt-4">

                                    <div className="h-3 overflow-hidden rounded-full bg-slate-200">

                                        <div
                                            className={`h-full rounded-full ${currentStyle.bar}`}
                                            style={{
                                                width: `${Math.max(
                                                    0,
                                                    Math.min(
                                                        averageScore,
                                                        100
                                                    )
                                                )}%`,
                                            }}
                                        />

                                    </div>

                                </div>

                            )}


                            <div className="mt-5 grid grid-cols-2 gap-3">

                                <div className="rounded-xl border border-slate-200 p-3">

                                    <p className="text-2xl font-black text-slate-950">
                                        {weeklyLoad.summary.training_count}
                                    </p>

                                    <p className="mt-1 text-xs font-semibold text-slate-500">
                                        Entrenamientos
                                    </p>

                                </div>

                                <div className="rounded-xl border border-slate-200 p-3">

                                    <p className="text-2xl font-black text-slate-950">
                                        {weeklyLoad.summary.total_minutes}
                                    </p>

                                    <p className="mt-1 text-xs font-semibold text-slate-500">
                                        Minutos
                                    </p>

                                </div>

                            </div>


                            <div className="mt-4 flex flex-wrap gap-2">

                                {weeklyLoad.summary.high_load_sessions > 0 && (
                                    <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-bold text-orange-800">
                                        {weeklyLoad.summary.high_load_sessions}{' '}
                                        carga
                                        {weeklyLoad.summary.high_load_sessions ===
                                        1
                                            ? ''
                                            : 's'}{' '}
                                        alta
                                        {weeklyLoad.summary.high_load_sessions ===
                                        1
                                            ? ''
                                            : 's'}
                                    </span>
                                )}

                                {weeklyLoad.summary
                                    .moderate_load_sessions > 0 && (
                                    <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800">
                                        {
                                            weeklyLoad.summary
                                                .moderate_load_sessions
                                        }{' '}
                                        moderada
                                        {weeklyLoad.summary
                                            .moderate_load_sessions === 1
                                            ? ''
                                            : 's'}
                                    </span>
                                )}

                                {weeklyLoad.summary.low_load_sessions > 0 && (
                                    <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800">
                                        {
                                            weeklyLoad.summary
                                                .low_load_sessions
                                        }{' '}
                                        baja
                                        {weeklyLoad.summary
                                            .low_load_sessions === 1
                                            ? ''
                                            : 's'}
                                    </span>
                                )}

                            </div>

                        </div>


                        {/* PARTIDO + AVISOS */}

                        <div className="space-y-4">

                            {weeklyLoad.next_match && (

                                <div className="rounded-2xl border border-orange-200 bg-orange-50 p-4">

                                    <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-orange-700">

                                        <Shield className="h-4 w-4" />

                                        Próximo partido

                                    </div>

                                    <p className="mt-2 text-xl font-black text-slate-950">
                                        vs {weeklyLoad.next_match.rival}
                                    </p>

                                    <div className="mt-2 flex flex-wrap gap-3 text-sm font-semibold text-slate-600">

                                        <span className="flex items-center gap-1">

                                            <CalendarDays className="h-4 w-4" />

                                            {fromIso(
                                                weeklyLoad.next_match.fecha
                                            ).toLocaleDateString(
                                                'es-ES',
                                                {
                                                    weekday: 'short',
                                                    day: 'numeric',
                                                    month: 'short',
                                                }
                                            )}

                                        </span>

                                        {weeklyLoad.next_match.hora && (

                                            <span className="flex items-center gap-1">

                                                <Clock3 className="h-4 w-4" />

                                                {
                                                    weeklyLoad.next_match
                                                        .hora
                                                }

                                            </span>

                                        )}

                                    </div>

                                    <p className="mt-3 text-xs font-semibold text-orange-800">

                                        {weeklyLoad.next_match
                                            .dias_desde_referencia === 0
                                            ? 'El partido es hoy.'
                                            : weeklyLoad.next_match
                                                  .dias_desde_referencia === 1
                                                ? 'El partido es mañana.'
                                                : `Faltan ${weeklyLoad.next_match.dias_desde_referencia} días para competir.`}

                                    </p>

                                </div>

                            )}


                            {weeklyLoad.alerts.length > 0 && (

                                <div className="rounded-2xl border border-slate-200 bg-white p-4">

                                    <div className="flex items-center gap-2">

                                        <AlertTriangle className="h-4 w-4 text-primary-700" />

                                        <p className="text-sm font-bold text-slate-950">
                                            SCOUT IA ha detectado{' '}
                                            {weeklyLoad.alerts.length}{' '}
                                            {weeklyLoad.alerts.length === 1
                                                ? 'aspecto'
                                                : 'aspectos'}{' '}
                                            a revisar
                                        </p>

                                    </div>

                                    <div className="mt-3 space-y-2">

                                        {weeklyLoad.alerts.map(
                                            (alert, index) => (

                                                <div
                                                    key={`${alert}-${index}`}
                                                    className="flex items-start gap-2 text-sm leading-5 text-slate-600"
                                                >

                                                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary-600" />

                                                    <span>
                                                        {alert}
                                                    </span>

                                                </div>

                                            )
                                        )}

                                    </div>

                                </div>

                            )}

                        </div>

                    </div>


                    {/* ÚLTIMOS 14 DÍAS */}

                    {weeklyLoad.recent_14_days.average_score !==
                        null && (

                        <div className="border-t border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">

                            <p className="text-xs text-slate-500">

                                Contexto reciente:{' '}

                                <span className="font-bold text-slate-700">
                                    {
                                        weeklyLoad.recent_14_days
                                            .training_count
                                    }{' '}
                                    entrenamientos
                                </span>{' '}

                                en los últimos 14 días · carga media{' '}

                                <span className="font-bold text-slate-700">
                                    {
                                        weeklyLoad.recent_14_days
                                            .average_score
                                    }
                                    /100
                                </span>

                            </p>

                        </div>

                    )}

                </Surface>

            )}


            {weeklyLoadError && (

                <div className="mb-5 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">

                    <span className="font-semibold">
                        SCOUT IA:
                    </span>{' '}

                    No se pudo cargar el análisis semanal.

                </div>

            )}


            {/* ======================================================
                AGENDA
            ====================================================== */}

            <PageHeader title="Agenda" />


            <Surface className="overflow-hidden">

                {agenda.length === 0 ? (

                    <EmptyState
                        icon={Dumbbell}
                        title="Sin planificación próxima"
                        description="Crea una sesión o añade un partido para empezar a organizar la agenda."
                        action={
                            <ActionLink
                                to="/entrenamientos/nuevo"
                                size="sm"
                            >
                                <Plus className="h-4 w-4" />
                                Crear sesión
                            </ActionLink>
                        }
                    />

                ) : (

                    <div className="divide-y divide-slate-200">

                        {agenda.map(day => (

                            <Link
                                key={day.fecha}
                                to={day.url_calendario}
                                className="group grid gap-3 p-3 transition hover:bg-slate-50 sm:grid-cols-[76px_minmax(0,1fr)_auto] sm:items-center sm:px-4 sm:py-3"
                            >

                                <div className="rounded-xl bg-primary-50 px-3 py-2 text-center ring-1 ring-inset ring-primary-100">

                                    <p className="text-xl font-bold text-primary-900">
                                        {fromIso(day.fecha).getDate()}
                                    </p>

                                    <p className="text-xs font-bold uppercase tracking-wider text-primary-700">

                                        {fromIso(
                                            day.fecha
                                        ).toLocaleDateString(
                                            'es-ES',
                                            {
                                                month: 'short',
                                            }
                                        )}

                                    </p>

                                </div>


                                <div className="min-w-0">

                                    <div className="flex flex-col items-start gap-1 text-sm">

                                        {day.entrenamiento.cantidad > 0 && (

                                            <span className="flex items-center gap-2 rounded-lg bg-primary-100 px-2.5 py-1 font-semibold text-primary-900">

                                                <Dumbbell className="h-4 w-4" />

                                                Entrenamiento ·{' '}

                                                {
                                                    day.entrenamiento
                                                        .sesiones
                                                }{' '}

                                                {day.entrenamiento
                                                    .sesiones === 1
                                                    ? 'sesión'
                                                    : 'sesiones'}

                                                {day.entrenamiento
                                                    .duracion_total >
                                                0
                                                    ? ` · ${day.entrenamiento.duracion_total} min`
                                                    : ''}

                                            </span>

                                        )}


                                        {day.partidos.map(match => (

                                            <span
                                                key={match.id}
                                                className="flex items-center gap-2 rounded-lg bg-orange-100 px-2.5 py-1 font-semibold text-orange-950"
                                            >

                                                <Shield className="h-4 w-4" />

                                                Partido ·{' '}

                                                {match.hora ||
                                                    'Sin hora'}{' '}

                                                vs {match.rival}

                                            </span>

                                        ))}

                                    </div>

                                </div>


                                <span className="flex items-center gap-1 text-sm font-bold text-primary-700">

                                    Ver planificación

                                    <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />

                                </span>

                            </Link>

                        ))}

                    </div>

                )}

            </Surface>

        </AppLayout>
    );
};