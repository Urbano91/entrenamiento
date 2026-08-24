import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Activity,
    AlertTriangle,
    ArrowLeft,
    CalendarDays,
    Minus,
    Plus,
    RotateCcw,
    Save,
    Trash2,
    Search,
    X,
    WandSparkles,
    Clock3,
    Coffee,
    Dumbbell,
    Eye,
    Loader2,
    Shield,
    Sparkles,
    Target,
} from 'lucide-react';

import { api } from '../services/api';
import { AppLayout } from '../components/AppLayout';
import { ExerciseDetail } from '../components/ExerciseDetail';
import { Badge, Surface } from '../components/ui';


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
    configured_training_dates: string[];

    next_match: NextMatch | null;

    recent_14_days: {
        training_count: number;
        average_score: number | null;
        level?: string;
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



type ExerciseCandidatesResponse = {
    count: number;
    candidates: ProposalExercise[];
};

type ExercisePickerState = {
    fecha: string;
    mode: 'ADD' | 'REPLACE';
    replaceExerciseId?: number;
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

        role?: {
            code: string | null;
            label: string | null;
            reason: string | null;
        };

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


type WeeklyProposalDay = {
    fecha: string;
    tipo: 'ENTRENAMIENTO' | 'DESCANSO' | 'CONFIGURADO';
    locked?: boolean;
    role?: {
        code: string | null;
        label: string | null;
        reason: string | null;
    };
    existing_training?: {
        entrenamiento_id: number;
        nombre: string;
        duracion_minutos: number | null;
        score: number;
        level: string;
    };
    proposal: TrainingProposalResponse['proposal'] | null;
};

type EditableProposalDay = WeeklyProposalDay & {
    edited?: boolean;
};

type EditableWeeklyProposalResponse = Omit<WeeklyProposalResponse, 'days'> & {
    days: EditableProposalDay[];
};

type SaveProposalResponse = {
    status: string;
    message: string;
    created_count: number;
    trainings: {
        id: number;
        fecha: string;
        nombre: string;
        duracion_minutos: number;
        exercise_count: number;
    }[];
};

type WeeklyProposalResponse = {
    status: string;
    message: string;
    reference_date: string;
    next_match: {
        partido_id: number;
        fecha: string;
        hora: string | null;
        rival: string;
        local_visitante: string;
        campo: string | null;
    } | null;
    training_dates: string[];
    rest_dates: string[];
    context: {
        weekly_average_score: number | null;
        recent_average_score: number | null;
        high_load_sessions: number;
    };
    days: WeeklyProposalDay[];
};


const loadStyle = (level: string) => {
    if (level === 'ALTA') {
        return {
            badge: 'bg-red-100 text-red-800 ring-red-200',
            bar: 'bg-red-500',
        };
    }

    if (level === 'MODERADA') {
        return {
            badge: 'bg-orange-100 text-orange-800 ring-orange-200',
            bar: 'bg-orange-500',
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

    const [weeklyProposal, setWeeklyProposal] =
        useState<EditableWeeklyProposalResponse | null>(null);

    const [originalWeeklyProposal, setOriginalWeeklyProposal] =
        useState<EditableWeeklyProposalResponse | null>(null);

    const [selectedTrainingDates, setSelectedTrainingDates] =
        useState<string[]>([]);

    const [proposalLoading, setProposalLoading] =
        useState(false);

    const [proposalError, setProposalError] =
        useState('');


    const [selectedExerciseId, setSelectedExerciseId] =
        useState<number | null>(null);

    const [exercisePicker, setExercisePicker] =
        useState<ExercisePickerState | null>(null);

    const [libraryExercises, setLibraryExercises] =
        useState<ProposalExercise[]>([]);

    const [libraryLoading, setLibraryLoading] =
        useState(false);

    const [librarySearch, setLibrarySearch] =
        useState('');

    const [recalculatingDate, setRecalculatingDate] =
        useState<string | null>(null);

    const [showAllLibrary, setShowAllLibrary] =
        useState(false);

    const [settingsChangedDates, setSettingsChangedDates] =
        useState<Set<string>>(new Set());


    const [reviewOpen, setReviewOpen] =
        useState(false);

    const [saveConfirmOpen, setSaveConfirmOpen] =
        useState(false);

    const [savingProposal, setSavingProposal] =
        useState(false);

    const [saveSuccess, setSaveSuccess] =
        useState<SaveProposalResponse | null>(null);


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


    useEffect(() => {
        if (!data?.next_match) {
            setSelectedTrainingDates([]);
            return;
        }

        

        // Las sesiones ya guardadas quedan bloqueadas: SCOUT IA no las simula.
        // El entrenador puede seleccionar únicamente días todavía libres.
        setSelectedTrainingDates([]);
    }, [data, todayIso]);


    const handleGenerateProposal = async () => {
        setProposalLoading(true);
        setProposalError('');

        try {
            const result = await api.get<WeeklyProposalResponse>(
                '/training-load/weekly-proposal',
                {
                    fecha: todayIso,
                    dias_entreno: selectedTrainingDates.join(','),
                    ejercicios: 6,
                }
            );

            const editableResult = structuredClone(result) as EditableWeeklyProposalResponse;
            setWeeklyProposal(editableResult);
            setOriginalWeeklyProposal(structuredClone(editableResult));

            window.setTimeout(() => {
                document
                    .getElementById('scout-ia-weekly-proposal')
                    ?.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start',
                    });
            }, 50);

        } catch {
            setProposalError(
                'No se pudo generar la propuesta semanal.'
            );
        } finally {
            setProposalLoading(false);
        }
    };


    const toggleTrainingDate = (fecha: string) => {
        const alreadyConfigured =
            data?.configured_training_dates.includes(fecha) ?? false;

        if (alreadyConfigured) return;

        setWeeklyProposal(null);
        setOriginalWeeklyProposal(null);

        setSelectedTrainingDates(current =>
            current.includes(fecha)
                ? current.filter(item => item !== fecha)
                : [...current, fecha].sort()
        );
    };


    const levelFromScore = (score: number) =>
        score < 40 ? 'BAJA' : score < 70 ? 'MODERADA' : 'ALTA';

    const recalculateSession = (
        proposal: TrainingProposalResponse['proposal']
    ): TrainingProposalResponse['proposal'] => {
        const exercises = proposal.exercises;

        if (exercises.length === 0) {
            return {
                ...proposal,
                estimated_proposal: {
                    ...proposal.estimated_proposal,
                    score: 0,
                    level: 'BAJA',
                    total_work_minutes: 0,
                },
            };
        }

        const baseAverage =
            exercises.reduce((sum, exercise) => sum + exercise.load_score, 0) /
            exercises.length;

        const originalDuration = Math.max(
            proposal.estimated_proposal.total_work_minutes ||
                proposal.target.duration_minutes ||
                1,
            1
        );

        const durationFactor = Math.max(
            0.55,
            Math.min(1.45, proposal.target.duration_minutes / originalDuration)
        );

        const score = Math.max(
            0,
            Math.min(100, Math.round(baseAverage * durationFactor))
        );

        return {
            ...proposal,
            estimated_proposal: {
                ...proposal.estimated_proposal,
                score,
                level: levelFromScore(score),
                total_work_minutes: proposal.target.duration_minutes,
            },
        };
    };

    const updateProposalDay = (
        fecha: string,
        updater: (
            proposal: TrainingProposalResponse['proposal']
        ) => TrainingProposalResponse['proposal']
    ) => {
        setWeeklyProposal(current => {
            if (!current) return current;

            return {
                ...current,
                days: current.days.map(day => {
                    if (day.fecha !== fecha || !day.proposal) return day;

                    return {
                        ...day,
                        edited: true,
                        proposal: recalculateSession(updater(day.proposal)),
                    };
                }),
            };
        });
    };

    const changeDuration = (fecha: string, delta: number) => {
        setSettingsChangedDates(current => {
            const next = new Set(current);
            next.add(fecha);
            return next;
        });

        updateProposalDay(fecha, proposal => ({
            ...proposal,
            target: {
                ...proposal.target,
                duration_minutes: Math.max(
                    20,
                    Math.min(150, proposal.target.duration_minutes + delta)
                ),
            },
        }));
    };

    const changeTargetLoad = (fecha: string, delta: number) => {
        setSettingsChangedDates(current => {
            const next = new Set(current);
            next.add(fecha);
            return next;
        });

        updateProposalDay(fecha, proposal => {
            const loadScore = Math.max(
                0,
                Math.min(100, proposal.target.load_score + delta)
            );

            return {
                ...proposal,
                target: {
                    ...proposal.target,
                    load_score: loadScore,
                    load_level: levelFromScore(loadScore),
                },
            };
        });
    };

    const removeExercise = (fecha: string, exerciseId: number) => {
        updateProposalDay(fecha, proposal => ({
            ...proposal,
            exercises: proposal.exercises.filter(
                exercise => exercise.exercise_id !== exerciseId
            ),
        }));
    };



    const resetProposalDay = (fecha: string) => {
        if (!originalWeeklyProposal) return;

        const originalDay = originalWeeklyProposal.days.find(
            day => day.fecha === fecha
        );

        if (!originalDay) return;

        setWeeklyProposal(current => {
            if (!current) return current;

            return {
                ...current,
                days: current.days.map(day =>
                    day.fecha === fecha
                        ? structuredClone(originalDay)
                        : day
                ),
            };
        });
    };



    const openExercisePicker = async (
        fecha: string,
        mode: 'ADD' | 'REPLACE',
        replaceExerciseId?: number
    ) => {
        setExercisePicker({
            fecha,
            mode,
            replaceExerciseId,
        });

        setLibrarySearch('');
        setShowAllLibrary(false);

        const day = weeklyProposal?.days.find(item => item.fecha === fecha);
        const targetLoad = day?.proposal?.target.load_score;

        setLibraryLoading(true);

        try {
            const result = await api.get<ExerciseCandidatesResponse>(
                '/training-load/exercise-candidates',
                {
                    carga_objetivo: targetLoad,
                    limite: 500,
                }
            );

            setLibraryExercises(result.candidates);
        } catch {
            setProposalError(
                'No se pudo cargar la biblioteca de ejercicios.'
            );
        } finally {
            setLibraryLoading(false);
        }
    };

    const chooseExerciseFromLibrary = (exercise: ProposalExercise) => {
        if (!exercisePicker) return;

        if (exercisePicker.mode === 'REPLACE' && exercisePicker.replaceExerciseId) {
            updateProposalDay(exercisePicker.fecha, proposal => ({
                ...proposal,
                exercises: proposal.exercises.map(current =>
                    current.exercise_id === exercisePicker.replaceExerciseId
                        ? structuredClone(exercise)
                        : current
                ),
            }));
        } else {
            updateProposalDay(exercisePicker.fecha, proposal => {
                if (
                    proposal.exercises.some(
                        current => current.exercise_id === exercise.exercise_id
                    )
                ) {
                    return proposal;
                }

                return {
                    ...proposal,
                    exercises: [
                        ...proposal.exercises,
                        structuredClone(exercise),
                    ],
                };
            });
        }

        setExercisePicker(null);
    };

    const recalculateDayWithScoutIA = async (fecha: string) => {
        const day = weeklyProposal?.days.find(item => item.fecha === fecha);

        if (!day?.proposal) return;

        setRecalculatingDate(fecha);
        setProposalError('');

        try {
            const session = day.proposal;

            const result = await api.get<TrainingProposalResponse['proposal']>(
                '/training-load/recalculate-session',
                {
                    fecha,
                    carga_objetivo: session.target.load_score,
                    duracion: session.target.duration_minutes,
                    ejercicios: 6,
                    role_code: session.role?.code || day.role?.code || undefined,
                    role_label: session.role?.label || day.role?.label || undefined,
                    role_reason: session.role?.reason || day.role?.reason || undefined,
                }
            );

            setWeeklyProposal(current => {
                if (!current) return current;

                return {
                    ...current,
                    days: current.days.map(currentDay =>
                        currentDay.fecha === fecha
                            ? {
                                  ...currentDay,
                                  edited: true,
                                  proposal: result,
                              }
                            : currentDay
                    ),
                };
            });

            setSettingsChangedDates(current => {
                const next = new Set(current);
                next.delete(fecha);
                return next;
            });
        } catch {
            setProposalError(
                'No se pudo recalcular esta sesión con SCOUT IA.'
            );
        } finally {
            setRecalculatingDate(null);
        }
    };

    const filteredLibraryExercises = libraryExercises.filter(exercise => {
        const search = librarySearch.trim().toLowerCase();

        if (!search) return true;

        return [
            exercise.name,
            exercise.task_type || '',
            exercise.source,
            ...(exercise.objectives || []),
        ]
            .join(' ')
            .toLowerCase()
            .includes(search);
    });


    const visibleLibraryExercises =
        librarySearch.trim() || showAllLibrary
            ? filteredLibraryExercises
            : filteredLibraryExercises.slice(0, 8);

    const proposalDates = (() => {
        if (!data?.next_match) return [];

        const start = fromIso(todayIso);
        const end = fromIso(data.next_match.fecha);
        const result: string[] = [];

        const cursor = new Date(start);

        while (cursor < end) {
            result.push(isoDate(cursor));
            cursor.setDate(cursor.getDate() + 1);
        }

        return result;
    })();



    const savableProposalDays =
        weeklyProposal?.days.filter(
            day =>
                day.tipo === 'ENTRENAMIENTO' &&
                day.proposal &&
                day.proposal.exercises.length > 0 &&
                !(data?.configured_training_dates.includes(day.fecha) ?? false)
        ) ?? [];

    const saveWeeklyProposal = async () => {
        if (savableProposalDays.length === 0) return;

        setSavingProposal(true);
        setProposalError('');

        try {
            const result = await api.post<SaveProposalResponse>(
                '/training-load/weekly-proposal/save',
                {
                    sessions: savableProposalDays.map(day => {
                        const proposal = day.proposal!;

                        return {
                            fecha: day.fecha,
                            nombre:
                                proposal.role?.label
                                    ? `SCOUT IA · ${proposal.role.label}`
                                    : 'Sesión SCOUT IA',
                            duracion_minutos: proposal.target.duration_minutes,
                            objetivo_principal:
                                proposal.context.desired_objectives.length > 0
                                    ? proposal.context.desired_objectives.join(' · ')
                                    : proposal.role?.label || null,
                            observaciones:
                                'Sesión propuesta por SCOUT IA y confirmada por el entrenador.',
                            ejercicio_ids: proposal.exercises.map(
                                exercise => exercise.exercise_id
                            ),
                        };
                    }),
                }
            );

            setSaveSuccess(result);
            setSaveConfirmOpen(false);
            setReviewOpen(false);
            setWeeklyProposal(null);
            setOriginalWeeklyProposal(null);

        } catch (caught: unknown) {
            setProposalError(
                caught instanceof Error
                    ? caught.message
                    : 'No se pudo guardar la propuesta en el calendario.'
            );
            setSaveConfirmOpen(false);
        } finally {
            setSavingProposal(false);
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
                            Carga media del periodo
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
                                No hay entrenamientos planificados en este periodo.
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

                            <div className="flex flex-wrap items-center gap-2">
                                <p className="text-3xl font-black text-slate-950">
                                    {data.recent_14_days.average_score ?? '—'}
                                </p>

                                {data.recent_14_days.average_score !== null && (
                                    <span
                                        className={`rounded-full px-2.5 py-1 text-xs font-black ring-1 ${
                                            loadStyle(
                                                data.recent_14_days.level ||
                                                levelFromScore(data.recent_14_days.average_score)
                                            ).badge
                                        }`}
                                    >
                                        {data.recent_14_days.level ||
                                            levelFromScore(data.recent_14_days.average_score)}
                                    </span>
                                )}
                            </div>

                            <p className="mt-1 text-sm font-semibold text-slate-500">
                                carga media /100
                            </p>

                        </div>

                    </div>

                </Surface>


                <Surface className="mb-5 overflow-hidden">

                    <div className="bg-primary-950 p-5 text-white sm:p-6">

                        <div className="flex flex-col gap-5">

                            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

                                <div className="max-w-2xl">

                                    <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary-200">
                                        <Sparkles className="h-4 w-4" />
                                        SCOUT IA
                                    </p>

                                    <h2 className="mt-2 text-xl font-black">
                                        Propuesta semanal hasta el partido
                                    </h2>

                                    <p className="mt-2 text-sm leading-6 text-primary-100">
                                        Indica qué días quieres entrenar. Los días no seleccionados se tratarán como descanso y SCOUT IA propondrá cada sesión hasta el próximo partido.
                                    </p>

                                    <p className="mt-2 text-xs font-semibold text-primary-300">
                                        Prioridad: ejercicios propios → favoritos → biblioteca.
                                    </p>

                                </div>

                                <button
                                    type="button"
                                    onClick={handleGenerateProposal}
                                    disabled={proposalLoading || !data.next_match}
                                    className="inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-xl bg-primary-500 px-5 py-3 text-sm font-black text-white shadow-sm transition hover:bg-primary-600 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    {proposalLoading ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                        <Sparkles className="h-4 w-4" />
                                    )}
                                    {proposalLoading ? 'Generando semana...' : 'Generar propuesta semanal'}
                                </button>

                            </div>


                            {data.next_match && proposalDates.length > 0 && (

                                <div className="rounded-2xl border border-white/15 bg-white/5 p-4">

                                    <p className="text-xs font-bold uppercase tracking-wider text-primary-200">
                                        Días disponibles antes del partido
                                    </p>

                                    <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">

                                        {proposalDates.map(fecha => {

                                            const selected = selectedTrainingDates.includes(fecha);
                                            const locked =
                                                data.configured_training_dates.includes(fecha);
                                            const parsedDate = fromIso(fecha);

                                            return (
                                                <button
                                                    key={fecha}
                                                    type="button"
                                                    onClick={() => toggleTrainingDate(fecha)}
                                                    disabled={locked}
                                                    title={
                                                        locked
                                                            ? 'Sesión ya guardada. Modifícala desde su planificación.'
                                                            : undefined
                                                    }
                                                    className={`rounded-xl border p-3 text-left transition ${
                                                        locked
                                                            ? 'cursor-not-allowed border-emerald-300/40 bg-emerald-400/10 text-emerald-50'
                                                            : selected
                                                                ? 'border-primary-300 bg-primary-500 text-white'
                                                                : 'border-white/15 bg-white/5 text-primary-100 hover:bg-white/10'
                                                    }`}
                                                >
                                                    <p className="text-xs font-bold uppercase">
                                                        {parsedDate.toLocaleDateString('es-ES', { weekday: 'short' })}
                                                    </p>

                                                    <p className="mt-1 text-lg font-black">
                                                        {parsedDate.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}
                                                    </p>

                                                    <p className="mt-1 text-xs font-semibold">
                                                        {locked
                                                            ? 'Configurado · bloqueado'
                                                            : selected
                                                                ? 'Entrenamiento'
                                                                : 'Descanso'}
                                                    </p>
                                                </button>
                                            );
                                        })}

                                    </div>

                                </div>

                            )}

                        </div>

                    </div>

                </Surface>


                {proposalError && (
                    <p className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">
                        {proposalError}
                    </p>
                )}


                {weeklyProposal && weeklyProposal.next_match && (
                    <div
                        id="scout-ia-weekly-proposal"
                        className="scroll-mt-6"
                    >

                        <Surface className="mb-5 overflow-hidden">

                            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">

                                <div>
                                    <p className="text-xs font-bold uppercase tracking-wider text-primary-700">
                                        PROPUESTA SCOUT IA
                                    </p>

                                    <h2 className="mt-1 text-xl font-black text-slate-950">
                                        Semana propuesta
                                    </h2>

                                    <p className="mt-1 text-sm text-slate-500">
                                        Hasta el partido vs {weeklyProposal.next_match.rival}
                                    </p>
                                </div>

                                <Badge className="bg-primary-100 text-primary-800 ring-primary-200">
                                    BORRADOR
                                </Badge>

                            </div>


                            <div className="divide-y divide-slate-200">

                                {weeklyProposal.days.map(day => {

                                    const parsedDate = fromIso(day.fecha);

                                    if (day.tipo === 'CONFIGURADO') {
                                        const existing = day.existing_training;
                                        const configuredStyle = loadStyle(
                                            existing?.level || 'MODERADA'
                                        );

                                        return (
                                            <div
                                                key={day.fecha}
                                                className="grid gap-3 bg-emerald-50/60 p-4 sm:grid-cols-[90px_minmax(0,1fr)_auto] sm:items-center"
                                            >
                                                <div>
                                                    <p className="text-sm font-black uppercase text-emerald-800">
                                                        {parsedDate.toLocaleDateString('es-ES', { weekday: 'short' })}
                                                    </p>
                                                    <p className="text-xs font-semibold text-emerald-700">
                                                        {parsedDate.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}
                                                    </p>
                                                </div>

                                                <div className="min-w-0">
                                                    <div className="flex flex-wrap items-center gap-2">
                                                        <Shield className="h-4 w-4 shrink-0 text-emerald-700" />
                                                        <p className="font-black text-slate-950">
                                                            {existing?.nombre || 'Entrenamiento configurado'}
                                                        </p>
                                                        <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-[11px] font-black uppercase text-emerald-800 ring-1 ring-emerald-200">
                                                            BLOQUEADO
                                                        </span>
                                                    </div>

                                                    <p className="mt-1 text-xs font-semibold text-slate-500">
                                                        {existing?.duracion_minutos || 0} min · ya guardado en calendario
                                                    </p>
                                                </div>

                                                <div className="flex flex-wrap items-center justify-end gap-2">
                                                    {existing && (
                                                        <>
                                                            <span className="text-xl font-black text-slate-950">
                                                                {Math.round(existing.score)}
                                                            </span>
                                                            <span className="text-xs font-bold text-slate-400">
                                                                /100
                                                            </span>
                                                            <span className={`rounded-full px-2.5 py-1 text-xs font-bold ring-1 ${configuredStyle.badge}`}>
                                                                {existing.level}
                                                            </span>
                                                            <Link
                                                                to={`/entrenamientos/${existing.entrenamiento_id}`}
                                                                className="ml-2 text-sm font-bold text-primary-700 hover:text-primary-900"
                                                            >
                                                                Ver planificación →
                                                            </Link>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    }

                                    if (day.tipo === 'DESCANSO') {
                                        return (
                                            <div
                                                key={day.fecha}
                                                className="grid gap-3 p-4 sm:grid-cols-[90px_minmax(0,1fr)_auto] sm:items-center"
                                            >
                                                <div>
                                                    <p className="text-sm font-black uppercase text-slate-700">
                                                        {parsedDate.toLocaleDateString('es-ES', { weekday: 'short' })}
                                                    </p>
                                                    <p className="text-xs font-semibold text-slate-500">
                                                        {parsedDate.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}
                                                    </p>
                                                </div>

                                                <div className="flex items-center gap-2 text-slate-500">
                                                    <Coffee className="h-4 w-4" />
                                                    <span className="text-sm font-bold">
                                                        Descanso
                                                    </span>
                                                </div>

                                                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
                                                    DESCANSO
                                                </span>
                                            </div>
                                        );
                                    }

                                    const session = day.proposal;

                                    if (!session) return null;

                                    const style = loadStyle(
                                        session.estimated_proposal.level
                                    );

                                    return (
                                        <div
                                            key={day.fecha}
                                            className="grid gap-3 p-4 sm:grid-cols-[90px_minmax(0,1fr)_auto] sm:items-center"
                                        >
                                            <div>
                                                <p className="text-sm font-black uppercase text-primary-800">
                                                    {parsedDate.toLocaleDateString('es-ES', { weekday: 'short' })}
                                                </p>
                                                <p className="text-xs font-semibold text-slate-500">
                                                    {parsedDate.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}
                                                </p>
                                            </div>

                                            <div className="min-w-0">

                                                <div className="flex flex-wrap items-center gap-2">
                                                    <Dumbbell className="h-4 w-4 shrink-0 text-primary-700" />

                                                    <p className="font-black text-slate-950">
                                                        Entrenamiento propuesto
                                                    </p>

                                                    {(session.role?.label || day.role?.label) && (
                                                        <span className="rounded-full bg-primary-100 px-2.5 py-1 text-[11px] font-black uppercase tracking-wide text-primary-800 ring-1 ring-primary-200">
                                                            {session.role?.label || day.role?.label}
                                                        </span>
                                                    )}

                                                    {day.edited && (
                                                        <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[11px] font-black uppercase tracking-wide text-amber-800 ring-1 ring-amber-200">
                                                            EDITADO
                                                        </span>
                                                    )}
                                                </div>

                                                <p className="mt-1 text-xs text-slate-500">
                                                    {session.target.duration_minutes} min · {session.exercises.length} ejercicios
                                                </p>

                                                <p className="mt-1 truncate text-xs font-semibold text-slate-600">
                                                    {session.exercises.map(exercise => exercise.name).join(' · ')}
                                                </p>

                                            </div>

                                            <div className="flex flex-wrap items-center justify-end gap-2">

                                                <span className="text-xl font-black text-slate-950">
                                                    {Math.round(session.estimated_proposal.score)}
                                                </span>

                                                <span className="text-xs font-bold text-slate-400">
                                                    /100
                                                </span>

                                                <span
                                                    className={`rounded-full px-2.5 py-1 text-xs font-bold ring-1 ${style.badge}`}
                                                >
                                                    {session.estimated_proposal.level}
                                                </span>

                                                <button
                                                    type="button"
                                                    className="ml-2 text-sm font-bold text-primary-700 hover:text-primary-900"
                                                    onClick={() => {
                                                        const element = document.getElementById(`proposal-${day.fecha}`);
                                                        element?.classList.toggle('hidden');
                                                    }}
                                                >
                                                    Ver planificación →
                                                </button>

                                            </div>


                                            <div
                                                id={`proposal-${day.fecha}`}
                                                className="hidden sm:col-start-2 sm:col-span-2"
                                            >
                                                <div className="mt-2 rounded-xl border border-slate-200 bg-slate-50 p-4">

                                                    {(session.role?.label || day.role?.label) && (
                                                        <div className="mb-3 flex items-center gap-2 rounded-lg bg-primary-50 px-3 py-2 text-sm">
                                                            <Target className="h-4 w-4 shrink-0 text-primary-700" />
                                                            <span className="font-black text-primary-900">
                                                                {session.role?.label || day.role?.label}
                                                            </span>
                                                            <span className="hidden text-xs text-slate-500 sm:inline">
                                                                · {session.role?.reason || day.role?.reason}
                                                            </span>
                                                        </div>
                                                    )}

                                                    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-white p-3">
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-xs font-black uppercase text-slate-500">
                                                                Carga
                                                            </span>
                                                            <button
                                                                type="button"
                                                                onClick={() => changeTargetLoad(day.fecha, -5)}
                                                                className="grid h-8 w-8 place-items-center rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50"
                                                            >
                                                                <Minus className="h-4 w-4" />
                                                            </button>
                                                            <span className="min-w-16 text-center text-lg font-black text-slate-950">
                                                                {session.target.load_score}
                                                                <span className="ml-1 text-[11px] text-slate-400">/100</span>
                                                            </span>
                                                            <span className={`rounded-full px-2 py-0.5 text-[10px] font-black ring-1 ${loadStyle(levelFromScore(session.target.load_score)).badge}`}>
                                                                {levelFromScore(session.target.load_score)}
                                                            </span>
                                                            <button
                                                                type="button"
                                                                onClick={() => changeTargetLoad(day.fecha, 5)}
                                                                className="grid h-8 w-8 place-items-center rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50"
                                                            >
                                                                <Plus className="h-4 w-4" />
                                                            </button>
                                                        </div>

                                                        <div className="h-6 w-px bg-slate-200" />

                                                        <div className="flex items-center gap-2">
                                                            <span className="text-xs font-black uppercase text-slate-500">
                                                                Tiempo
                                                            </span>
                                                            <button
                                                                type="button"
                                                                onClick={() => changeDuration(day.fecha, -5)}
                                                                className="grid h-8 w-8 place-items-center rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50"
                                                            >
                                                                <Minus className="h-4 w-4" />
                                                            </button>
                                                            <span className="min-w-16 text-center text-lg font-black text-slate-950">
                                                                {session.target.duration_minutes}
                                                                <span className="ml-1 text-[11px] text-slate-400">min</span>
                                                            </span>
                                                            <button
                                                                type="button"
                                                                onClick={() => changeDuration(day.fecha, 5)}
                                                                className="grid h-8 w-8 place-items-center rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50"
                                                            >
                                                                <Plus className="h-4 w-4" />
                                                            </button>
                                                        </div>

                                                        <div className="ml-auto flex items-center gap-2">
                                                            <span className={`rounded-full px-2.5 py-1 text-xs font-black ring-1 ${loadStyle(session.estimated_proposal.level).badge}`}>
                                                                Estimada {Math.round(session.estimated_proposal.score)}/100 · {session.estimated_proposal.level}
                                                            </span>

                                                            {settingsChangedDates.has(day.fecha) && (
                                                                <button
                                                                    type="button"
                                                                    onClick={() => recalculateDayWithScoutIA(day.fecha)}
                                                                    disabled={recalculatingDate === day.fecha}
                                                                    className="inline-flex items-center gap-1.5 rounded-lg bg-primary-700 px-3 py-2 text-xs font-black text-white hover:bg-primary-800 disabled:cursor-wait disabled:opacity-60"
                                                                >
                                                                    {recalculatingDate === day.fecha ? (
                                                                        <Loader2 className="h-4 w-4 animate-spin" />
                                                                    ) : (
                                                                        <WandSparkles className="h-4 w-4" />
                                                                    )}
                                                                    {recalculatingDate === day.fecha ? 'Ajustando...' : 'Aplicar'}
                                                                </button>
                                                            )}
                                                        </div>
                                                    </div>

                                                    {session.target.load_score + 20 < session.estimated_proposal.score && (
                                                        <div className="mt-3 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs font-semibold leading-5 text-amber-900">
                                                            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                                                            La carga estimada está bastante por encima del objetivo de SCOUT IA. Puedes mantenerla si esa es tu decisión.
                                                        </div>
                                                    )}

                                                    <div className="mt-4 flex flex-wrap items-center justify-between gap-2">
                                                        <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                                                            Ejercicios
                                                        </p>

                                                        <div className="flex flex-wrap gap-2">
                                                            {day.edited && (
                                                                <button
                                                                    type="button"
                                                                    onClick={() => resetProposalDay(day.fecha)}
                                                                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50"
                                                                >
                                                                    <RotateCcw className="h-3.5 w-3.5" />
                                                                    Restaurar IA
                                                                </button>
                                                            )}

                                                            <button
                                                                type="button"
                                                                onClick={() => openExercisePicker(day.fecha, 'ADD')}
                                                                className="inline-flex items-center gap-1.5 rounded-lg bg-primary-700 px-3 py-2 text-xs font-black text-white hover:bg-primary-800"
                                                            >
                                                                <Plus className="h-4 w-4" />
                                                                Añadir ejercicio
                                                            </button>
                                                        </div>
                                                    </div>

                                                    <div className="mt-3 space-y-3">
                                                        {session.exercises.map((exercise, index) => (
                                                            <div
                                                                key={`${day.fecha}-${exercise.exercise_id}-${index}`}
                                                                className="rounded-xl border border-slate-200 bg-white p-4"
                                                            >
                                                                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => setSelectedExerciseId(exercise.exercise_id)}
                                                                        className="group min-w-0 flex-1 text-left"
                                                                    >
                                                                        <div className="flex flex-wrap items-center gap-2">
                                                                            <span className="grid h-7 w-7 place-items-center rounded-lg bg-primary-950 text-xs font-black text-white">
                                                                                {index + 1}
                                                                            </span>

                                                                            <p className="font-black text-slate-950 transition group-hover:text-primary-700">
                                                                                {exercise.name}
                                                                            </p>

                                                                            <span
                                                                                className={`rounded-full px-2 py-0.5 text-[10px] font-black ring-1 ${sourceStyle(exercise.source)}`}
                                                                            >
                                                                                {exercise.source}
                                                                            </span>

                                                                            <span
                                                                                className={`rounded-full px-2 py-0.5 text-[10px] font-black ring-1 ${loadStyle(exercise.load_level).badge}`}
                                                                            >
                                                                                {exercise.load_level}
                                                                            </span>
                                                                        </div>

                                                                        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                                                                            {exercise.task_type && (
                                                                                <span>{exercise.task_type}</span>
                                                                            )}

                                                                            {exercise.players && (
                                                                                <span>{exercise.players} jug.</span>
                                                                            )}

                                                                            {exercise.time_description && (
                                                                                <span>{exercise.time_description}</span>
                                                                            )}

                                                                            <span className="font-bold text-slate-700">
                                                                                Carga {exercise.load_score}/100
                                                                            </span>
                                                                        </div>

                                                                        {exercise.objectives.length > 0 && (
                                                                            <p className="mt-2 text-xs font-semibold text-slate-600">
                                                                                {exercise.objectives.join(' · ')}
                                                                            </p>
                                                                        )}

                                                                        <span className="mt-2 inline-flex items-center gap-1.5 text-xs font-black text-primary-700 opacity-80 transition group-hover:opacity-100">
                                                                            <Eye className="h-3.5 w-3.5" />
                                                                            Ver ficha
                                                                        </span>
                                                                    </button>

                                                                    <div className="flex shrink-0 gap-2">
                                                                        <button
                                                                            type="button"
                                                                            onClick={() =>
                                                                                openExercisePicker(
                                                                                    day.fecha,
                                                                                    'REPLACE',
                                                                                    exercise.exercise_id
                                                                                )
                                                                            }
                                                                            className="rounded-lg border border-primary-200 bg-primary-50 px-3 py-2 text-xs font-black text-primary-800 hover:bg-primary-100"
                                                                        >
                                                                            Cambiar
                                                                        </button>

                                                                        <button
                                                                            type="button"
                                                                            onClick={() =>
                                                                                removeExercise(
                                                                                    day.fecha,
                                                                                    exercise.exercise_id
                                                                                )
                                                                            }
                                                                            className="grid h-9 w-9 place-items-center rounded-lg border border-slate-200 text-slate-400 hover:border-red-200 hover:bg-red-50 hover:text-red-700"
                                                                            title="Eliminar ejercicio"
                                                                        >
                                                                            <Trash2 className="h-4 w-4" />
                                                                        </button>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ))}

                                                        {session.exercises.length === 0 && (
                                                            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-5 text-center">
                                                                <p className="text-sm font-bold text-slate-700">
                                                                    Esta sesión no tiene ejercicios.
                                                                </p>

                                                                <button
                                                                    type="button"
                                                                    onClick={() => openExercisePicker(day.fecha, 'ADD')}
                                                                    className="mt-3 inline-flex items-center gap-2 rounded-lg bg-primary-700 px-4 py-2 text-xs font-black text-white"
                                                                >
                                                                    <Plus className="h-4 w-4" />
                                                                    Añadir ejercicio
                                                                </button>
                                                            </div>
                                                        )}
                                                    </div>

                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}


                                <div className="grid gap-3 bg-orange-50 p-4 sm:grid-cols-[90px_minmax(0,1fr)_auto] sm:items-center">

                                    <div>
                                        <p className="text-sm font-black uppercase text-orange-800">
                                            {fromIso(weeklyProposal.next_match.fecha).toLocaleDateString('es-ES', { weekday: 'short' })}
                                        </p>

                                        <p className="text-xs font-semibold text-orange-700">
                                            {fromIso(weeklyProposal.next_match.fecha).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}
                                        </p>
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <Shield className="h-4 w-4 text-orange-700" />

                                        <div>
                                            <p className="font-black text-slate-950">
                                                Partido vs {weeklyProposal.next_match.rival}
                                            </p>

                                            <p className="text-xs font-semibold text-slate-500">
                                                {weeklyProposal.next_match.hora || 'Sin hora'}
                                            </p>
                                        </div>
                                    </div>

                                    <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-bold text-orange-800">
                                        PARTIDO
                                    </span>

                                </div>

                            </div>

                        </Surface>


                        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:justify-end">

                            <button
                                type="button"
                                onClick={() => setReviewOpen(true)}
                                disabled={savableProposalDays.length === 0}
                                className="min-h-11 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                Revisar propuesta
                            </button>

                            <button
                                type="button"
                                onClick={() => setSaveConfirmOpen(true)}
                                disabled={savableProposalDays.length === 0 || savingProposal}
                                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-primary-700 px-5 py-2 text-sm font-black text-white hover:bg-primary-800 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                <Save className="h-4 w-4" />
                                Guardar en calendario
                            </button>

                        </div>


                        <p className="mb-5 text-center text-xs font-semibold text-slate-500">
                            Borrador: solo se guardará cuando tú lo confirmes.
                        </p>

                    </div>
                )}

                {reviewOpen && weeklyProposal && (
                    <div
                        className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/55 p-3 sm:p-6"
                        onClick={() => setReviewOpen(false)}
                    >
                        <div
                            className="mx-auto flex max-h-[calc(100dvh-1.5rem)] w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl sm:max-h-[calc(100dvh-3rem)]"
                            onClick={event => event.stopPropagation()}
                        >
                            <div className="flex shrink-0 items-start justify-between gap-4 border-b border-slate-200 p-4 sm:p-5">
                                <div>
                                    <p className="text-xs font-black uppercase tracking-wider text-primary-700">
                                        Revisión final
                                    </p>
                                    <h2 className="mt-1 text-xl font-black text-slate-950">
                                        {savableProposalDays.length}{' '}
                                        {savableProposalDays.length === 1
                                            ? 'sesión nueva'
                                            : 'sesiones nuevas'}
                                    </h2>
                                    <p className="mt-1 text-sm text-slate-500">
                                        Esto es lo que se añadirá a tu calendario.
                                    </p>
                                </div>

                                <button
                                    type="button"
                                    onClick={() => setReviewOpen(false)}
                                    className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-50"
                                >
                                    <X className="h-5 w-5" />
                                </button>
                            </div>

                            <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-5">
                                <div className="space-y-3">
                                    {savableProposalDays.map(day => {
                                        const proposal = day.proposal!;

                                        return (
                                            <div
                                                key={`review-${day.fecha}`}
                                                className="rounded-xl border border-slate-200 bg-white p-4"
                                            >
                                                <div className="flex flex-wrap items-start justify-between gap-3">
                                                    <div>
                                                        <p className="text-xs font-black uppercase tracking-wider text-primary-700">
                                                            {fromIso(day.fecha).toLocaleDateString(
                                                                'es-ES',
                                                                {
                                                                    weekday: 'long',
                                                                    day: 'numeric',
                                                                    month: 'long',
                                                                }
                                                            )}
                                                        </p>

                                                        <h3 className="mt-1 font-black text-slate-950">
                                                            {proposal.role?.label || 'Sesión SCOUT IA'}
                                                        </h3>
                                                    </div>

                                                    <div className="flex flex-wrap gap-2">
                                                        <span className={`rounded-full px-2.5 py-1 text-xs font-black ring-1 ${loadStyle(proposal.estimated_proposal.level).badge}`}>
                                                            {Math.round(proposal.estimated_proposal.score)}/100 · {proposal.estimated_proposal.level}
                                                        </span>

                                                        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-black text-slate-700 ring-1 ring-slate-200">
                                                            {proposal.target.duration_minutes} min
                                                        </span>
                                                    </div>
                                                </div>

                                                <div className="mt-3 space-y-2">
                                                    {proposal.exercises.map((exercise, index) => (
                                                        <button
                                                            key={`review-${day.fecha}-${exercise.exercise_id}-${index}`}
                                                            type="button"
                                                            onClick={() => setSelectedExerciseId(exercise.exercise_id)}
                                                            className="flex w-full items-center justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2 text-left hover:bg-primary-50"
                                                        >
                                                            <span className="min-w-0 text-sm font-bold text-slate-800">
                                                                {index + 1}. {exercise.name}
                                                            </span>

                                                            <span className="shrink-0 text-xs font-black text-primary-700">
                                                                Ver ficha
                                                            </span>
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            <div className="flex shrink-0 flex-col gap-2 border-t border-slate-200 bg-slate-50 p-4 sm:flex-row sm:justify-end">
                                <button
                                    type="button"
                                    onClick={() => setReviewOpen(false)}
                                    className="min-h-10 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-700 hover:bg-slate-50"
                                >
                                    Seguir editando
                                </button>

                                <button
                                    type="button"
                                    onClick={() => {
                                        setReviewOpen(false);
                                        setSaveConfirmOpen(true);
                                    }}
                                    className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl bg-primary-700 px-4 py-2 text-sm font-black text-white hover:bg-primary-800"
                                >
                                    <Save className="h-4 w-4" />
                                    Guardar en calendario
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {saveConfirmOpen && (
                    <div
                        className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/55 p-4"
                        onClick={() => !savingProposal && setSaveConfirmOpen(false)}
                    >
                        <div
                            className="w-full max-w-md rounded-2xl bg-white p-5 shadow-2xl"
                            onClick={event => event.stopPropagation()}
                        >
                            <p className="text-xs font-black uppercase tracking-wider text-primary-700">
                                Confirmar planificación
                            </p>

                            <h2 className="mt-2 text-xl font-black text-slate-950">
                                Añadir {savableProposalDays.length}{' '}
                                {savableProposalDays.length === 1
                                    ? 'sesión'
                                    : 'sesiones'} al calendario
                            </h2>

                            <p className="mt-2 text-sm leading-6 text-slate-600">
                                A partir de ese momento serán entrenamientos normales.
                                Podrás modificarlos desde su planificación, pero SCOUT IA
                                ya no los regenerará.
                            </p>

                            <div className="mt-4 space-y-2">
                                {savableProposalDays.map(day => (
                                    <div
                                        key={`confirm-${day.fecha}`}
                                        className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2"
                                    >
                                        <span className="text-sm font-bold capitalize text-slate-800">
                                            {fromIso(day.fecha).toLocaleDateString(
                                                'es-ES',
                                                {
                                                    weekday: 'short',
                                                    day: 'numeric',
                                                    month: 'short',
                                                }
                                            )}
                                        </span>

                                        <span className="text-xs font-bold text-slate-500">
                                            {day.proposal?.target.duration_minutes} min
                                        </span>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-5 flex flex-col gap-2 sm:flex-row sm:justify-end">
                                <button
                                    type="button"
                                    disabled={savingProposal}
                                    onClick={() => setSaveConfirmOpen(false)}
                                    className="min-h-10 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-700 disabled:opacity-50"
                                >
                                    Cancelar
                                </button>

                                <button
                                    type="button"
                                    disabled={savingProposal}
                                    onClick={saveWeeklyProposal}
                                    className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl bg-primary-700 px-4 py-2 text-sm font-black text-white hover:bg-primary-800 disabled:cursor-wait disabled:opacity-60"
                                >
                                    {savingProposal ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                        <Save className="h-4 w-4" />
                                    )}
                                    {savingProposal
                                        ? 'Guardando...'
                                        : 'Confirmar y guardar'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {saveSuccess && (
                    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/55 p-4">
                        <div className="w-full max-w-md rounded-2xl bg-white p-5 text-center shadow-2xl">
                            <div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-emerald-100 text-emerald-700">
                                <Save className="h-6 w-6" />
                            </div>

                            <h2 className="mt-4 text-xl font-black text-slate-950">
                                Planificación guardada
                            </h2>

                            <p className="mt-2 text-sm leading-6 text-slate-600">
                                {saveSuccess.message}
                            </p>

                            <div className="mt-5 grid gap-2">
                                <Link
                                    to="/dashboard"
                                    className="inline-flex min-h-11 items-center justify-center rounded-xl bg-primary-700 px-4 py-2 text-sm font-black text-white hover:bg-primary-800"
                                >
                                    Ver en Agenda
                                </Link>

                                <button
                                    type="button"
                                    onClick={() => setSaveSuccess(null)}
                                    className="min-h-10 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-700"
                                >
                                    Cerrar
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {selectedExerciseId && (
                    <ExerciseDetail
                        id={selectedExerciseId}
                        onClose={() => setSelectedExerciseId(null)}
                    />
                )}

                {exercisePicker && (
                    <div
                        className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/55 p-3 sm:p-6"
                        onClick={() => setExercisePicker(null)}
                    >
                        <div
                            className="mx-auto flex max-h-[calc(100dvh-1.5rem)] w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl sm:max-h-[calc(100dvh-3rem)]"
                            onClick={event => event.stopPropagation()}
                        >
                            <div className="shrink-0 border-b border-slate-200 bg-white p-4 sm:p-5">
                                <div className="flex items-start justify-between gap-4">
                                    <div>
                                        <p className="text-xs font-black uppercase tracking-wider text-primary-700">
                                            {exercisePicker.mode === 'REPLACE'
                                                ? 'Cambiar ejercicio'
                                                : 'Añadir ejercicio'}
                                        </p>

                                        <h2 className="mt-1 text-xl font-black text-slate-950">
                                            SCOUT IA te recomienda
                                        </h2>

                                        <p className="mt-1 text-sm text-slate-500">
                                            Elige una tarjeta. Primero aparecen tus mejores opciones.
                                        </p>
                                    </div>

                                    <button
                                        type="button"
                                        onClick={() => setExercisePicker(null)}
                                        className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-50"
                                    >
                                        <X className="h-5 w-5" />
                                    </button>
                                </div>

                                <div className="relative mt-4">
                                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                                    <input
                                        value={librarySearch}
                                        onChange={event => setLibrarySearch(event.target.value)}
                                        placeholder="Buscar otro ejercicio..."
                                        className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm font-semibold text-slate-800 outline-none focus:border-primary-400 focus:bg-white"
                                    />
                                </div>
                            </div>

                            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4 sm:p-5">
                                {libraryLoading ? (
                                    <div className="py-14 text-center text-sm font-bold text-primary-700">
                                        Buscando las mejores opciones…
                                    </div>
                                ) : visibleLibraryExercises.length === 0 ? (
                                    <div className="py-14 text-center text-sm font-semibold text-slate-500">
                                        No se encontraron ejercicios.
                                    </div>
                                ) : (
                                    <>
                                        <div className="grid gap-3 sm:grid-cols-2">
                                            {visibleLibraryExercises.map(exercise => (
                                                <div
                                                    key={exercise.exercise_id}
                                                    className="rounded-xl border border-slate-200 bg-white p-4 transition hover:border-primary-300"
                                                >
                                                    <div className="flex items-start justify-between gap-3">
                                                        <div className="min-w-0">
                                                            <div className="flex flex-wrap items-center gap-2">
                                                                <p className="font-black text-slate-950">
                                                                    {exercise.name}
                                                                </p>

                                                                <span className={`rounded-full px-2 py-0.5 text-[10px] font-black ring-1 ${sourceStyle(exercise.source)}`}>
                                                                    {exercise.source}
                                                                </span>
                                                            </div>

                                                            <p className="mt-2 text-xs text-slate-500">
                                                                {exercise.task_type || 'Sin tipo'}
                                                                {exercise.players ? ` · ${exercise.players} jug.` : ''}
                                                                {exercise.time_description ? ` · ${exercise.time_description}` : ''}
                                                            </p>

                                                            {exercise.objectives.length > 0 && (
                                                                <p className="mt-2 line-clamp-2 text-xs font-semibold text-slate-600">
                                                                    {exercise.objectives.join(' · ')}
                                                                </p>
                                                            )}
                                                        </div>

                                                        <div className="shrink-0 text-right">
                                                            <p className="text-lg font-black text-slate-950">
                                                                {Math.round(exercise.load_score)}
                                                                <span className="ml-1 text-[11px] text-slate-400">/100</span>
                                                            </p>

                                                            <span className={`mt-1 inline-flex rounded-full px-2 py-0.5 text-[10px] font-black ring-1 ${loadStyle(exercise.load_level).badge}`}>
                                                                {exercise.load_level}
                                                            </span>
                                                        </div>
                                                    </div>

                                                    <div className="mt-4 flex gap-2">
                                                        <button
                                                            type="button"
                                                            onClick={() => setSelectedExerciseId(exercise.exercise_id)}
                                                            className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-black text-primary-700 hover:bg-slate-50"
                                                        >
                                                            <Eye className="h-4 w-4" />
                                                            Ver ficha
                                                        </button>

                                                        <button
                                                            type="button"
                                                            onClick={() => chooseExerciseFromLibrary(exercise)}
                                                            className="inline-flex flex-1 items-center justify-center rounded-lg bg-primary-700 px-3 py-2 text-xs font-black text-white hover:bg-primary-800"
                                                        >
                                                            Elegir
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>

                                        {!librarySearch.trim() && !showAllLibrary && filteredLibraryExercises.length > 8 && (
                                            <div className="mt-4 text-center">
                                                <button
                                                    type="button"
                                                    onClick={() => setShowAllLibrary(true)}
                                                    className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-black text-primary-700 hover:bg-slate-50"
                                                >
                                                    Ver más ejercicios
                                                </button>
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                )}

            </div>

        </AppLayout>
    );
};