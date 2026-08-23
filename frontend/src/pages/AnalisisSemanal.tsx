import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Activity,
    AlertTriangle,
    ArrowLeft,
    CalendarDays,
    Clock3,
    Dumbbell,
    Shield,
    Sparkles,
} from 'lucide-react';

import { api } from '../services/api';
import { AppLayout } from '../components/AppLayout';
import { Badge, Button, Surface } from '../components/ui';


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


type ProposalExercise = {
    exercise_id: number;
    name: string;
    source: 'PROPIO' | 'FAVORITO' | 'BIBLIOTECA';
    source_priority: number;
    task_type: string | null;
    players: number | null;
    space: string | null;
    time_description: string | null;
    objectives: string[];
    matched_objectives: string[];
    objective_match_count: number;
    load_score: number;
    load_level: string;
    load_distance: number;
    reasons: string[];
};


type TrainingProposalResponse = {
    reference_date: string;

    next_match: NextMatch | null;

    weekly_context: {
        week_start: string;
        week_end: string;
        training_count: number;
        average_score: number | null;
        high_load_sessions: number;
    };

    recent_14_days: {
        training_count: number;
        average_score: number | null;
    };

    proposal: {
        status: string;
        message: string;

        target: {
            load_score: number;
            load_level: string;
            duration_minutes: number;
        };

        context: {
            days_to_match: number | null;
            weekly_average_score: number | null;
            recent_average_score: number | null;
            high_load_sessions: number;
            desired_objectives: string[];
        };

        selection_rule: string[];

        source_counts: {
            PROPIO: number;
            FAVORITO: number;
            BIBLIOTECA: number;
        };

        exercises: ProposalExercise[];

        estimated_proposal: {
            score: number;
            level: string;
            total_work_minutes: number | null;
            reasons: string[];
        };

        reasons: string[];
    };
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


const sourceStyle = (source: ProposalExercise['source']) => {
    if (source === 'PROPIO') {
        return 'bg-primary-100 text-primary-800 ring-primary-200';
    }

    if (source === 'FAVORITO') {
        return 'bg-amber-100 text-amber-800 ring-amber-200';
    }

    return 'bg-slate-100 text-slate-700 ring-slate-200';
};


export const AnalisisSemanal: React.FC = () => {
    const today = useMemo(() => new Date(), []);
    const todayIso = isoDate(today);

    const [data, setData] = useState<WeeklyLoadResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const [proposal, setProposal] =
        useState<TrainingProposalResponse | null>(null);

    const [proposalLoading, setProposalLoading] =
        useState(false);

    const [proposalError, setProposalError] =
        useState('');


    useEffect(() => {
        api.get<WeeklyLoadResponse>(
            '/training-load/week',
            {
                fecha: todayIso,
            }
        )
            .then(result => {
                setData(result);
                setError('');
            })
            .catch(() => {
                setError('No se pudo cargar el análisis semanal.');
            })
            .finally(() => {
                setLoading(false);
            });
    }, [todayIso]);


    const handleGenerateProposal = async () => {
        setProposalLoading(true);
        setProposalError('');

        try {
            const result = await api.get<TrainingProposalResponse>(
                '/training-load/proposal',
                {
                    fecha: todayIso,
                    ejercicios: 4,
                }
            );

            setProposal(result);

            window.setTimeout(() => {
                document
                    .getElementById('scout-ia-proposal')
                    ?.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start',
                    });
            }, 50);

        } catch {
            setProposalError(
                'No se pudo generar la propuesta de sesión.'
            );
        } finally {
            setProposalLoading(false);
        }
    };


    if (loading) {
        return (
            <AppLayout>
                <div className="py-20 text-center font-semibold text-primary-700">
                    Analizando planificación…
                </div>
            </AppLayout>
        );
    }


    if (!data) {
        return (
            <AppLayout>
                <div className="mx-auto max-w-5xl">
                    <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">
                        {error || 'No se pudo cargar el análisis.'}
                    </p>
                </div>
            </AppLayout>
        );
    }


    const averageScore = data.summary.average_score;

    const averageLevel =
        averageScore === null
            ? 'SIN DATOS'
            : averageScore < 40
                ? 'BAJA'
                : averageScore < 70
                    ? 'MODERADA'
                    : 'ALTA';

    const averageStyle = loadStyle(averageLevel);


    return (
        <AppLayout>

            <div className="mx-auto max-w-6xl">

                <Link
                    to="/dashboard"
                    className="mb-4 inline-flex items-center gap-2 text-sm font-bold text-primary-700 hover:text-primary-900"
                >
                    <ArrowLeft className="h-4 w-4" />
                    Volver al inicio
                </Link>


                <div className="mb-5 overflow-hidden rounded-2xl bg-primary-950 text-white shadow-panel">

                    <div className="relative p-5 sm:p-6">

                        <div className="absolute -right-20 -top-24 h-64 w-64 rounded-full border-[42px] border-primary-800/40" />

                        <div className="relative">

                            <p className="flex items-center gap-2 text-sm font-semibold text-primary-200">
                                <Activity className="h-4 w-4" />
                                SCOUT IA
                            </p>

                            <h1 className="mt-2 text-2xl font-black tracking-tight sm:text-[30px]">
                                Análisis semanal
                            </h1>

                            <p className="mt-2 max-w-2xl text-sm leading-6 text-primary-100">
                                Distribución de carga, contexto reciente y proximidad del próximo partido.
                            </p>

                            <div className="mt-4 flex flex-wrap gap-2">

                                <Badge className="bg-white/10 text-white ring-white/20">
                                    {fromIso(data.week_start).toLocaleDateString(
                                        'es-ES',
                                        {
                                            day: 'numeric',
                                            month: 'short',
                                        }
                                    )}
                                    {' – '}
                                    {fromIso(data.week_end).toLocaleDateString(
                                        'es-ES',
                                        {
                                            day: 'numeric',
                                            month: 'short',
                                        }
                                    )}
                                </Badge>

                                <Badge className="bg-white/10 text-white ring-white/20">
                                    {data.summary.training_count} entrenamientos
                                </Badge>

                            </div>

                        </div>

                    </div>

                </div>


                <div className="mb-5 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">

                    <Surface className="p-5">

                        <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                            Carga media semanal
                        </p>

                        <div className="mt-3 flex flex-wrap items-end gap-3">

                            <span className="text-5xl font-black text-slate-950">
                                {averageScore !== null
                                    ? Math.round(averageScore)
                                    : '—'}
                            </span>

                            <span className="pb-1 text-xl font-bold text-slate-400">
                                / 100
                            </span>

                            {averageScore !== null && (
                                <span
                                    className={`mb-1 rounded-full px-3 py-1 text-xs font-bold ring-1 ${averageStyle.badge}`}
                                >
                                    {averageLevel}
                                </span>
                            )}

                        </div>


                        {averageScore !== null && (
                            <div className="mt-4">

                                <div className="h-3 overflow-hidden rounded-full bg-slate-200">

                                    <div
                                        className={`h-full rounded-full ${averageStyle.bar}`}
                                        style={{
                                            width: `${Math.max(
                                                0,
                                                Math.min(averageScore, 100)
                                            )}%`,
                                        }}
                                    />

                                </div>

                            </div>
                        )}


                        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">

                            <div className="rounded-xl border border-slate-200 p-3">

                                <p className="text-2xl font-black text-slate-950">
                                    {data.summary.training_count}
                                </p>

                                <p className="mt-1 text-xs font-semibold text-slate-500">
                                    Entrenos
                                </p>

                            </div>

                            <div className="rounded-xl border border-slate-200 p-3">

                                <p className="text-2xl font-black text-slate-950">
                                    {data.summary.total_minutes}
                                </p>

                                <p className="mt-1 text-xs font-semibold text-slate-500">
                                    Minutos
                                </p>

                            </div>

                            <div className="rounded-xl border border-orange-200 bg-orange-50 p-3">

                                <p className="text-2xl font-black text-orange-800">
                                    {data.summary.high_load_sessions}
                                </p>

                                <p className="mt-1 text-xs font-semibold text-orange-700">
                                    Altas
                                </p>

                            </div>

                            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3">

                                <p className="text-2xl font-black text-amber-800">
                                    {data.summary.moderate_load_sessions}
                                </p>

                                <p className="mt-1 text-xs font-semibold text-amber-700">
                                    Moderadas
                                </p>

                            </div>

                        </div>

                    </Surface>


                    <Surface className="p-5">

                        <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-orange-700">
                            <Shield className="h-4 w-4" />
                            Próximo partido
                        </p>

                        {data.next_match ? (
                            <>

                                <h2 className="mt-3 text-2xl font-black text-slate-950">
                                    vs {data.next_match.rival}
                                </h2>

                                <div className="mt-3 flex flex-wrap gap-4 text-sm font-semibold text-slate-600">

                                    <span className="flex items-center gap-1.5">
                                        <CalendarDays className="h-4 w-4" />

                                        {fromIso(
                                            data.next_match.fecha
                                        ).toLocaleDateString(
                                            'es-ES',
                                            {
                                                weekday: 'long',
                                                day: 'numeric',
                                                month: 'long',
                                            }
                                        )}

                                    </span>

                                    {data.next_match.hora && (
                                        <span className="flex items-center gap-1.5">
                                            <Clock3 className="h-4 w-4" />
                                            {data.next_match.hora}
                                        </span>
                                    )}

                                </div>


                                <div className="mt-5 rounded-xl border border-orange-200 bg-orange-50 p-3">

                                    <p className="text-sm font-bold text-orange-900">

                                        {data.next_match.dias_desde_referencia === 0
                                            ? 'El partido es hoy.'
                                            : data.next_match.dias_desde_referencia === 1
                                                ? 'El partido es mañana.'
                                                : `Faltan ${data.next_match.dias_desde_referencia} días para competir.`}

                                    </p>

                                </div>

                            </>
                        ) : (

                            <p className="mt-3 text-sm text-slate-500">
                                No hay ningún partido próximo registrado.
                            </p>

                        )}

                    </Surface>

                </div>


                <Surface className="mb-5 overflow-hidden">

                    <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">

                        <p className="text-xs font-bold uppercase tracking-wider text-primary-700">
                            Distribución semanal
                        </p>

                        <h2 className="mt-1 text-lg font-bold text-slate-950">
                            Entrenamientos y carga
                        </h2>

                    </div>


                    <div className="divide-y divide-slate-200">

                        {data.trainings.length === 0 ? (

                            <div className="p-5 text-sm text-slate-500">
                                No hay entrenamientos planificados esta semana.
                            </div>

                        ) : (

                            data.trainings.map(training => {

                                const style = loadStyle(training.level);

                                return (

                                    <Link
                                        key={training.entrenamiento_id}
                                        to={`/entrenamientos/${training.entrenamiento_id}`}
                                        className="grid gap-3 p-4 transition hover:bg-slate-50 sm:grid-cols-[90px_minmax(0,1fr)_auto] sm:items-center"
                                    >

                                        <div>

                                            <p className="text-sm font-black uppercase text-primary-800">
                                                {fromIso(training.fecha).toLocaleDateString(
                                                    'es-ES',
                                                    {
                                                        weekday: 'short',
                                                    }
                                                )}
                                            </p>

                                            <p className="text-xs font-semibold text-slate-500">
                                                {fromIso(training.fecha).toLocaleDateString(
                                                    'es-ES',
                                                    {
                                                        day: 'numeric',
                                                        month: 'short',
                                                    }
                                                )}
                                            </p>

                                        </div>


                                        <div className="min-w-0">

                                            <div className="flex items-center gap-2">

                                                <Dumbbell className="h-4 w-4 shrink-0 text-primary-700" />

                                                <p className="truncate font-bold text-slate-950">
                                                    {training.nombre}
                                                </p>

                                            </div>

                                            <p className="mt-1 text-xs text-slate-500">
                                                {training.duracion_minutos || 0} min
                                            </p>

                                        </div>


                                        <div className="flex items-center gap-3">

                                            <span className="text-xl font-black text-slate-950">
                                                {Math.round(training.score)}
                                            </span>

                                            <span className="text-xs font-bold text-slate-400">
                                                /100
                                            </span>

                                            <span
                                                className={`rounded-full px-2.5 py-1 text-xs font-bold ring-1 ${style.badge}`}
                                            >
                                                {training.level}
                                            </span>

                                        </div>

                                    </Link>

                                );
                            })

                        )}

                    </div>

                </Surface>


                <Surface className="mb-5 p-5">

                    <div className="flex items-center gap-3">

                        <span className="rounded-xl bg-primary-100 p-2 text-primary-800">
                            <AlertTriangle className="h-5 w-5" />
                        </span>

                        <div>

                            <p className="text-xs font-bold uppercase tracking-wider text-primary-700">
                                SCOUT IA
                            </p>

                            <h2 className="text-lg font-black text-slate-950">
                                Aspectos a revisar
                            </h2>

                        </div>

                    </div>


                    <div className="mt-4 space-y-3">

                        {data.alerts.map((alert, index) => (

                            <div
                                key={`${alert}-${index}`}
                                className="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3"
                            >

                                <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-primary-600" />

                                <p className="text-sm leading-6 text-slate-700">
                                    {alert}
                                </p>

                            </div>

                        ))}

                    </div>

                </Surface>


                <Surface className="mb-5 p-5">

                    <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                        Contexto reciente
                    </p>

                    <h2 className="mt-1 text-lg font-black text-slate-950">
                        Últimos 14 días
                    </h2>


                    <div className="mt-4 grid gap-3 sm:grid-cols-2">

                        <div className="rounded-xl border border-slate-200 p-4">

                            <p className="text-3xl font-black text-slate-950">
                                {data.recent_14_days.training_count}
                            </p>

                            <p className="mt-1 text-sm font-semibold text-slate-500">
                                entrenamientos
                            </p>

                        </div>


                        <div className="rounded-xl border border-slate-200 p-4">

                            <p className="text-3xl font-black text-slate-950">
                                {data.recent_14_days.average_score ?? '—'}
                            </p>

                            <p className="mt-1 text-sm font-semibold text-slate-500">
                                carga media /100
                            </p>

                        </div>

                    </div>

                </Surface>


                <Surface className="mb-5 overflow-hidden">

                    <div className="bg-primary-950 p-5 text-white sm:p-6">

                        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

                            <div className="max-w-2xl">

                                <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary-200">
                                    <Sparkles className="h-4 w-4" />
                                    SCOUT IA
                                </p>

                                <h2 className="mt-2 text-xl font-black">
                                    Propuesta de próxima sesión
                                </h2>

                                <p className="mt-2 text-sm leading-6 text-primary-100">
                                    Utiliza la carga reciente, la semana actual y el próximo partido para preparar una propuesta con ejercicios reales de tu biblioteca.
                                </p>

                                <p className="mt-2 text-xs font-semibold text-primary-300">
                                    Prioridad: ejercicios propios → favoritos → biblioteca.
                                </p>

                            </div>


                            <Button
                                onClick={handleGenerateProposal}
                                loading={proposalLoading}
                                loadingText="Analizando..."
                                className="shrink-0 bg-white text-primary-950 hover:bg-primary-50"
                            >
                                <Sparkles className="h-4 w-4" />
                                Generar propuesta
                            </Button>

                        </div>

                    </div>

                </Surface>


                {proposalError && (
                    <p className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">
                        {proposalError}
                    </p>
                )}


                {proposal && (
                    <div
                        id="scout-ia-proposal"
                        className="scroll-mt-6"
                    >

                        <Surface className="mb-5 overflow-hidden">

                            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">

                                <div>

                                    <p className="text-xs font-bold uppercase tracking-wider text-primary-700">
                                        PROPUESTA SCOUT IA
                                    </p>

                                    <h2 className="mt-1 text-xl font-black text-slate-950">
                                        Próxima sesión
                                    </h2>

                                </div>

                                <Badge className="bg-primary-100 text-primary-800 ring-primary-200">
                                    BORRADOR
                                </Badge>

                            </div>


                            <div className="p-4 sm:p-5">

                                <div className="grid gap-3 sm:grid-cols-3">

                                    <div className="rounded-xl border border-slate-200 p-4">

                                        <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                                            Carga objetivo
                                        </p>

                                        <div className="mt-2 flex items-end gap-2">

                                            <span className="text-3xl font-black text-slate-950">
                                                {Math.round(
                                                    proposal.proposal.target.load_score
                                                )}
                                            </span>

                                            <span className="pb-1 text-sm font-bold text-slate-400">
                                                /100
                                            </span>

                                        </div>

                                        <span
                                            className={`mt-2 inline-flex rounded-full px-2.5 py-1 text-xs font-bold ring-1 ${
                                                loadStyle(
                                                    proposal.proposal.target.load_level
                                                ).badge
                                            }`}
                                        >
                                            {proposal.proposal.target.load_level}
                                        </span>

                                    </div>


                                    <div className="rounded-xl border border-slate-200 p-4">

                                        <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                                            Duración objetivo
                                        </p>

                                        <p className="mt-2 text-3xl font-black text-slate-950">
                                            {proposal.proposal.target.duration_minutes}
                                        </p>

                                        <p className="mt-1 text-sm font-semibold text-slate-500">
                                            minutos
                                        </p>

                                    </div>


                                    <div className="rounded-xl border border-slate-200 p-4">

                                        <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                                            Carga estimada propuesta
                                        </p>

                                        <div className="mt-2 flex items-end gap-2">

                                            <span className="text-3xl font-black text-slate-950">
                                                {Math.round(
                                                    proposal.proposal.estimated_proposal.score
                                                )}
                                            </span>

                                            <span className="pb-1 text-sm font-bold text-slate-400">
                                                /100
                                            </span>

                                        </div>

                                        <span
                                            className={`mt-2 inline-flex rounded-full px-2.5 py-1 text-xs font-bold ring-1 ${
                                                loadStyle(
                                                    proposal.proposal.estimated_proposal.level
                                                ).badge
                                            }`}
                                        >
                                            {proposal.proposal.estimated_proposal.level}
                                        </span>

                                    </div>

                                </div>


                                <div className="mt-6">

                                    <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                                        ¿Por qué esta propuesta?
                                    </p>

                                    <div className="mt-3 space-y-2">

                                        {proposal.proposal.reasons.map(
                                            (reason, index) => (
                                                <div
                                                    key={`${reason}-${index}`}
                                                    className="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3"
                                                >
                                                    <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-primary-600" />

                                                    <p className="text-sm leading-6 text-slate-700">
                                                        {reason}
                                                    </p>
                                                </div>
                                            )
                                        )}

                                    </div>

                                </div>

                            </div>

                        </Surface>


                        <Surface className="mb-5 overflow-hidden">

                            <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">

                                <p className="text-xs font-bold uppercase tracking-wider text-primary-700">
                                    Ejercicios seleccionados
                                </p>

                                <h2 className="mt-1 text-lg font-black text-slate-950">
                                    Propuesta de trabajo
                                </h2>

                            </div>


                            <div className="divide-y divide-slate-200">

                                {proposal.proposal.exercises.map(
                                    (exercise, index) => {

                                        const style = loadStyle(
                                            exercise.load_level
                                        );

                                        return (
                                            <div
                                                key={exercise.exercise_id}
                                                className="grid gap-3 p-4 sm:grid-cols-[48px_minmax(0,1fr)_auto] sm:items-center"
                                            >

                                                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary-950 text-sm font-black text-white">
                                                    {String(index + 1).padStart(2, '0')}
                                                </div>


                                                <div className="min-w-0">

                                                    <div className="flex flex-wrap items-center gap-2">

                                                        <p className="font-black text-slate-950">
                                                            {exercise.name}
                                                        </p>

                                                        <span
                                                            className={`rounded-full px-2.5 py-1 text-[11px] font-bold ring-1 ${sourceStyle(exercise.source)}`}
                                                        >
                                                            {exercise.source}
                                                        </span>

                                                    </div>


                                                    <p className="mt-1 text-xs text-slate-500">
                                                        {exercise.task_type || 'Sin tipo'}
                                                        {' · '}
                                                        {exercise.players || '—'} jug.
                                                        {' · '}
                                                        {exercise.time_description || 'Sin tiempo'}
                                                    </p>


                                                    {exercise.objectives.length > 0 && (
                                                        <p className="mt-1 text-xs font-semibold text-slate-600">
                                                            {exercise.objectives.join(' · ')}
                                                        </p>
                                                    )}

                                                </div>


                                                <div className="flex items-center gap-2">

                                                    <span className="text-xl font-black text-slate-950">
                                                        {Math.round(exercise.load_score)}
                                                    </span>

                                                    <span className="text-xs font-bold text-slate-400">
                                                        /100
                                                    </span>

                                                    <span
                                                        className={`rounded-full px-2.5 py-1 text-xs font-bold ring-1 ${style.badge}`}
                                                    >
                                                        {exercise.load_level}
                                                    </span>

                                                </div>

                                            </div>
                                        );
                                    }
                                )}

                            </div>

                        </Surface>


                        <Surface className="mb-5 p-5">

                            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                                Origen de los ejercicios
                            </p>

                            <div className="mt-3 flex flex-wrap gap-2">

                                <span className="rounded-full bg-primary-100 px-3 py-1 text-xs font-bold text-primary-800">
                                    {proposal.proposal.source_counts.PROPIO} propios
                                </span>

                                <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800">
                                    {proposal.proposal.source_counts.FAVORITO} favoritos
                                </span>

                                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
                                    {proposal.proposal.source_counts.BIBLIOTECA} biblioteca
                                </span>

                            </div>


                            <p className="mt-4 text-sm font-semibold text-primary-800">
                                {proposal.proposal.message}
                            </p>

                            <p className="mt-1 text-xs leading-5 text-slate-500">
                                Esta propuesta todavía no crea ni modifica ningún entrenamiento.
                            </p>

                        </Surface>

                    </div>
                )}

            </div>

        </AppLayout>
    );
};