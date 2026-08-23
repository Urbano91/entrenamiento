import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
    Activity, ArrowLeft, CalendarDays, Clock3, Copy, Dumbbell, Edit3,
    FileText, Info, Maximize2, Target, Trash2, Users,
} from 'lucide-react';
import { api, imageUrl } from '../services/api';
import { AppLayout } from '../components/AppLayout';
import { ExerciseDetail } from '../components/ExerciseDetail';
import { ActionLink, Badge, Button, EmptyState, Modal, Surface } from '../components/ui';
import { EntrenamientoDetail } from '../types/fase2';
import { useToast } from '../utils/useToast';

const todayIso = () => {
    const today = new Date();
    const pad = (value: number) => String(value).padStart(2, '0');
    return `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
};


type TrainingLoadExercise = {
    name: string;
    score: number;
    level: string;
    work_minutes: number;
    rest_minutes: number;
    density: number;
    area_per_player: number | null;
    components: {
        duration_density: number;
        task_type: number;
        space: number;
        objectives: number;
    };
    reasons: string[];
};

type TrainingLoadResponse = {
    entrenamiento_id: number;
    nombre: string;
    fecha: string;
    duracion_minutos: number | null;
    score: number;
    level: string;
    total_work_minutes?: number;
    training_duration_minutes?: number | null;
    exercise_loads?: TrainingLoadExercise[];
    reasons: string[];
};

const loadPresentation = (level: string) => {
    if (level === 'ALTA') {
        return {
            labelClass: 'bg-orange-100 text-orange-800 ring-orange-200',
            barClass: 'bg-orange-500',
        };
    }

    if (level === 'MODERADA') {
        return {
            labelClass: 'bg-amber-100 text-amber-800 ring-amber-200',
            barClass: 'bg-amber-500',
        };
    }

    return {
        labelClass: 'bg-emerald-100 text-emerald-800 ring-emerald-200',
        barClass: 'bg-emerald-500',
    };
};

export const DetalleEntrenamiento: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [training, setTraining] = useState<EntrenamientoDetail | null>(null);
    const [trainingLoad, setTrainingLoad] = useState<TrainingLoadResponse | null>(null);
    const [trainingLoadError, setTrainingLoadError] = useState('');
    const [loading, setLoading] = useState(true);
    const [selectedExerciseId, setSelectedExerciseId] = useState<number | null>(null);
    const [showReuse, setShowReuse] = useState(false);
    const [reuseForm, setReuseForm] = useState({ fecha: '', nombre: '' });
    const [showDelete, setShowDelete] = useState(false);
    const [error, setError] = useState('');
    const [isReusing, setIsReusing] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const { success, error: toastError } = useToast();

    useEffect(() => {
        if (!id) return;

        setLoading(true);
        setTrainingLoadError('');

        Promise.all([
            api.get<EntrenamientoDetail>(`/entrenamientos/${id}`),
            api.get<TrainingLoadResponse>(`/training-load/${id}`)
                .then(result => {
                    setTrainingLoad(result);
                    return result;
                })
                .catch(() => {
                    setTrainingLoad(null);
                    setTrainingLoadError('No se pudo calcular la carga estimada de esta sesión.');
                    return null;
                }),
        ])
            .then(([trainingResult]) => {
                setTraining(trainingResult);
            })
            .catch(() => navigate('/entrenamientos'))
            .finally(() => setLoading(false));
    }, [id, navigate]);

    const handleReuse = async () => {
        if (!reuseForm.fecha) return;
        if (reuseForm.fecha < todayIso()) {
            setError('No puedes crear un entrenamiento en una fecha pasada.');
            return;
        }
        setIsReusing(true);
        try {
            const copy = await api.post<EntrenamientoDetail>(`/entrenamientos/${id}/reutilizar`, {
                fecha: reuseForm.fecha,
                nombre: reuseForm.nombre || undefined,
            });
            success('Copia creada con éxito');
            navigate(`/entrenamientos/${copy.id}`);
        } catch (caught: unknown) {
            toastError(caught instanceof Error ? caught.message : 'No se pudo duplicar el entrenamiento.');
            setShowReuse(false);
        } finally {
            setIsReusing(false);
        }
    };

    const handleDelete = async () => {
        setIsDeleting(true);
        try {
            await api.delete(`/entrenamientos/${id}`);
            success('Entrenamiento eliminado');
            navigate('/entrenamientos');
        } catch (caught: unknown) {
            toastError(caught instanceof Error ? caught.message : 'No se pudo eliminar el entrenamiento.');
            setShowDelete(false);
        } finally {
            setIsDeleting(false);
        }
    };

    if (loading) return <AppLayout><div className="py-20 text-center font-semibold text-primary-700">Cargando entrenamiento…</div></AppLayout>;
    if (!training) return null;

    const date = new Date(`${training.fecha}T00:00:00`);

    return (
        <AppLayout>
            <div className="mx-auto max-w-5xl">
                <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="mb-3"><ArrowLeft className="h-4 w-4" />Volver</Button>

                <div className="relative mb-5 overflow-hidden rounded-2xl bg-primary-950 p-5 text-white shadow-panel sm:p-6">
                    <div className="absolute -right-20 -top-24 h-64 w-64 rounded-full border-[42px] border-primary-800/40" />
                    <div className="relative">
                        <p className="flex items-center gap-2 text-sm font-semibold capitalize text-primary-200"><CalendarDays className="h-4 w-4" />{date.toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</p>
                        <h1 className="mt-2 max-w-3xl break-words text-2xl font-bold leading-tight tracking-tight [overflow-wrap:anywhere] sm:text-[28px]">{training.nombre}</h1>
                        <div className="mt-4 flex flex-wrap gap-2">
                            {training.hora && <Badge className="bg-white/10 text-white ring-white/20"><Clock3 className="mr-1 h-3.5 w-3.5" />{training.hora.slice(0, 5)}</Badge>}
                            {training.duracion_minutos && <Badge className="bg-white/10 text-white ring-white/20"><Clock3 className="mr-1 h-3.5 w-3.5" />{training.duracion_minutos} minutos</Badge>}
                            <Badge className="bg-white/10 text-white ring-white/20"><Dumbbell className="mr-1 h-3.5 w-3.5" />{training.ejercicios.length} ejercicios</Badge>
                        </div>
                    </div>
                </div>

                {error && <p className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</p>}

                <Surface className="mb-5 overflow-hidden">
                    <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">
                        <div><p className="text-xs font-bold uppercase tracking-wider text-primary-700">Secuencia de trabajo</p><h2 className="mt-1 text-lg font-bold text-slate-950">Ejercicios</h2></div>
                        <Badge tone="green">{training.ejercicios.length} total</Badge>
                    </div>
                    {training.ejercicios.length === 0 ? (
                        <EmptyState icon={Dumbbell} title="Sesión sin ejercicios" description="Edita el entrenamiento para añadir ejercicios de la biblioteca." />
                    ) : (
                        <div className="divide-y divide-slate-200">
                            {training.ejercicios.map((exercise, index) => (
                                <button
                                    key={exercise.id}
                                    onClick={() => setSelectedExerciseId(exercise.ejercicio_id)}
                                    className="grid min-h-11 w-full grid-cols-[auto_minmax(0,1fr)] items-center gap-3 p-3 text-left transition hover:bg-primary-50 sm:grid-cols-[48px_minmax(0,1fr)_auto] sm:px-4"
                                >
                                    <div className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-xl bg-primary-950 text-sm font-bold text-white">
                                        {exercise.imagen_principal ? <img src={imageUrl(exercise.imagen_principal)} alt="" className="h-full w-full object-cover" /> : String(index + 1).padStart(2, '0')}
                                    </div>
                                    <div className="min-w-0">
                                        <p className="break-words font-bold text-slate-950 [overflow-wrap:anywhere]">{exercise.nombre}</p>
                                        <div className="mt-1 flex flex-wrap gap-x-2 gap-y-1 text-xs font-normal text-slate-600">
                                            <span className="min-w-0 break-words [overflow-wrap:anywhere]">{exercise.tipo}</span>
                                            <span className="flex min-w-0 items-start gap-1"><Users className="h-3.5 w-3.5 shrink-0" /><span className="break-words [overflow-wrap:anywhere]">{exercise.jugadores} jug.</span></span>
                                            <span className="flex min-w-0 items-start gap-1"><Maximize2 className="h-3.5 w-3.5 shrink-0" /><span className="break-words [overflow-wrap:anywhere]">{exercise.espacio}</span></span>
                                            <span className="flex min-w-0 items-start gap-1"><Clock3 className="h-3.5 w-3.5 shrink-0" /><span className="break-words [overflow-wrap:anywhere]">{exercise.tiempo}</span></span>
                                        </div>
                                    </div>
                                    <span className="hidden text-sm font-bold text-primary-700 sm:block">Ver ficha</span>
                                </button>
                            ))}
                        </div>
                    )}
                </Surface>

                {trainingLoad && (
                    <Surface className="mb-5 overflow-hidden">
                        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">
                            <div className="flex items-center gap-3">
                                <span className="rounded-xl bg-primary-100 p-2 text-primary-800">
                                    <Activity className="h-5 w-5" />
                                </span>
                                <div>
                                    <p className="text-xs font-bold uppercase tracking-wider text-primary-700">
                                        Análisis SCOUT IA
                                    </p>
                                    <h2 className="mt-1 text-lg font-bold text-slate-950">
                                        Carga estimada de la sesión
                                    </h2>
                                </div>
                            </div>
                            <Badge className="bg-primary-100 text-primary-800 ring-primary-200">
                                BETA
                            </Badge>
                        </div>

                        <div className="grid gap-6 p-4 sm:p-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
                            <div>
                                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                                    Carga estimada
                                </p>

                                <div className="mt-3 flex flex-wrap items-end gap-3">
                                    <span className="text-5xl font-black tracking-tight text-slate-950">
                                        {Math.round(trainingLoad.score)}
                                    </span>
                                    <span className="pb-1 text-xl font-bold text-slate-400">/ 100</span>
                                    <span
                                        className={`mb-1 rounded-full px-3 py-1 text-xs font-bold ring-1 ${loadPresentation(trainingLoad.level).labelClass}`}
                                    >
                                        {trainingLoad.level}
                                    </span>
                                </div>

                                <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-200">
                                    <div
                                        className={`h-full rounded-full transition-all ${loadPresentation(trainingLoad.level).barClass}`}
                                        style={{ width: `${Math.max(0, Math.min(trainingLoad.score, 100))}%` }}
                                    />
                                </div>

                                <div className="mt-2 flex justify-between text-xs font-semibold text-slate-400">
                                    <span>0</span>
                                    <span>25</span>
                                    <span>50</span>
                                    <span>75</span>
                                    <span>100</span>
                                </div>

                                <div className="mt-5 rounded-xl border border-primary-100 bg-primary-50 p-3">
                                    <div className="flex items-start gap-2">
                                        <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary-700" />
                                        <p className="text-xs leading-5 text-slate-600">
                                            Estimación previa de la sesión calculada a partir de su duración,
                                            composición y características de los ejercicios. No representa la
                                            carga física real de cada jugador.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                                    ¿Por qué esta carga?
                                </p>

                                <div className="mt-3 space-y-2">
                                    {trainingLoad.reasons.map((reason, index) => (
                                        <div
                                            key={`${reason}-${index}`}
                                            className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2.5"
                                        >
                                            <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary-600" />
                                            <p className="text-sm leading-5 text-slate-700">{reason}</p>
                                        </div>
                                    ))}
                                </div>

                                {typeof trainingLoad.total_work_minutes === 'number' && (
                                    <p className="mt-4 text-xs font-semibold text-slate-500">
                                        Trabajo efectivo detectado en ejercicios: {trainingLoad.total_work_minutes} min
                                    </p>
                                )}
                            </div>
                        </div>
                    </Surface>
                )}

                {trainingLoadError && (
                    <div className="mb-5 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                        <span className="font-semibold">SCOUT IA:</span> {trainingLoadError}
                    </div>
                )}

                <div className="mb-5 grid gap-3 lg:grid-cols-2">
                    <Surface className="p-4">
                        <div className="flex items-start gap-3">
                            <span className="rounded-xl bg-primary-100 p-2 text-primary-800"><Target className="h-5 w-5" /></span>
                            <div className="min-w-0"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Objetivo principal</p><p className="mt-1.5 break-words text-sm leading-5 text-slate-700 [overflow-wrap:anywhere]">{training.objetivo_principal || 'Sin objetivo definido'}</p></div>
                        </div>
                    </Surface>
                    <Surface className="p-4">
                        <div className="flex items-start gap-3">
                            <span className="rounded-xl bg-blue-100 p-2 text-blue-700"><FileText className="h-5 w-5" /></span>
                            <div className="min-w-0"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Observaciones</p><p className="mt-1.5 whitespace-pre-wrap break-words text-sm leading-5 text-slate-700 [overflow-wrap:anywhere]">{training.observaciones || 'Sin observaciones'}</p></div>
                        </div>
                    </Surface>
                </div>

                <div className="flex flex-wrap gap-2">
                    <ActionLink to={`/entrenamientos/${id}/editar`}><Edit3 className="h-4 w-4" />Editar</ActionLink>
                    <Button variant="secondary" onClick={() => setShowReuse(true)}><Copy className="h-4 w-4" />Duplicar</Button>
                    <Button variant="secondary" onClick={() => setShowDelete(true)} className="border-red-200 text-red-700 hover:bg-red-50 hover:text-red-800"><Trash2 className="h-4 w-4" />Eliminar</Button>
                </div>
            </div>

            {selectedExerciseId && <ExerciseDetail id={selectedExerciseId} onClose={() => setSelectedExerciseId(null)} />}

            {showReuse && (
                <Modal
                    title="Duplicar entrenamiento"
                    description="Se creará una copia independiente y el original permanecerá intacto."
                    onClose={() => setShowReuse(false)}
                    footer={<div className="flex justify-end gap-3"><Button variant="secondary" onClick={() => setShowReuse(false)}>Cancelar</Button><Button onClick={handleReuse} disabled={!reuseForm.fecha || reuseForm.fecha < todayIso()} loading={isReusing} loadingText="Creando..."><Copy className="h-4 w-4" />Crear copia</Button></div>}
                >
                    <div className="space-y-3">
                        <div><label className="field-label">Nueva fecha *</label><input type="date" min={todayIso()} value={reuseForm.fecha} onChange={event => setReuseForm(current => ({ ...current, fecha: event.target.value }))} className="field-control" /></div>
                        <div><label className="field-label">Nombre de la copia</label><input value={reuseForm.nombre} onChange={event => setReuseForm(current => ({ ...current, nombre: event.target.value }))} className="field-control" placeholder={training.nombre} /></div>
                    </div>
                </Modal>
            )}

            {showDelete && (
                <Modal
                    title="Eliminar entrenamiento"
                    description={`Se eliminará “${training.nombre}”. Los ejercicios de la biblioteca no se verán afectados.`}
                    onClose={() => setShowDelete(false)}
                    footer={<div className="flex justify-end gap-3"><Button variant="secondary" onClick={() => setShowDelete(false)}>Cancelar</Button><Button variant="danger" onClick={handleDelete} loading={isDeleting} loadingText="Eliminando...">Eliminar</Button></div>}
                >
                    <p className="text-sm leading-6 text-slate-700">Esta acción no se puede deshacer.</p>
                </Modal>
            )}
        </AppLayout>
    );
};