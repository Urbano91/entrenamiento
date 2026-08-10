import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
    ArrowLeft, CalendarDays, Clock3, Copy, Dumbbell, Edit3,
    FileText, Maximize2, Target, Trash2, Users,
} from 'lucide-react';
import { api } from '../services/api';
import { AppLayout } from '../components/AppLayout';
import { ExerciseDetail } from '../components/ExerciseDetail';
import { ActionLink, Badge, Button, EmptyState, Modal, Surface } from '../components/ui';
import { EntrenamientoDetail } from '../types/fase2';

export const DetalleEntrenamiento: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [training, setTraining] = useState<EntrenamientoDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedExerciseId, setSelectedExerciseId] = useState<number | null>(null);
    const [showReuse, setShowReuse] = useState(false);
    const [reuseForm, setReuseForm] = useState({ fecha: '', nombre: '' });
    const [showDelete, setShowDelete] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!id) return;
        api.get<EntrenamientoDetail>(`/entrenamientos/${id}`)
            .then(setTraining)
            .catch(() => navigate('/entrenamientos'))
            .finally(() => setLoading(false));
    }, [id, navigate]);

    const handleReuse = async () => {
        if (!reuseForm.fecha) return;
        try {
            const copy = await api.post<EntrenamientoDetail>(`/entrenamientos/${id}/reutilizar`, {
                fecha: reuseForm.fecha,
                nombre: reuseForm.nombre || undefined,
            });
            navigate(`/entrenamientos/${copy.id}`);
        } catch (caught: unknown) {
            setError(caught instanceof Error ? caught.message : 'No se pudo duplicar el entrenamiento.');
            setShowReuse(false);
        }
    };

    const handleDelete = async () => {
        try {
            await api.delete(`/entrenamientos/${id}`);
            navigate('/entrenamientos');
        } catch (caught: unknown) {
            setError(caught instanceof Error ? caught.message : 'No se pudo eliminar el entrenamiento.');
            setShowDelete(false);
        }
    };

    if (loading) return <AppLayout><div className="py-20 text-center font-semibold text-primary-700">Cargando entrenamiento…</div></AppLayout>;
    if (!training) return null;

    const date = new Date(`${training.fecha}T00:00:00`);

    return (
        <AppLayout>
            <div className="mx-auto max-w-5xl">
                <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="mb-4"><ArrowLeft className="h-4 w-4" />Volver</Button>

                <div className="relative mb-6 overflow-hidden rounded-3xl bg-primary-950 p-6 text-white shadow-panel sm:p-8">
                    <div className="absolute -right-20 -top-24 h-64 w-64 rounded-full border-[42px] border-primary-800/40" />
                    <div className="relative">
                        <p className="flex items-center gap-2 text-sm font-semibold capitalize text-primary-200"><CalendarDays className="h-4 w-4" />{date.toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</p>
                        <h1 className="mt-3 max-w-3xl text-3xl font-bold tracking-tight sm:text-4xl">{training.nombre}</h1>
                        <div className="mt-5 flex flex-wrap gap-2">
                            {training.duracion_minutos && <Badge className="bg-white/10 text-white ring-white/20"><Clock3 className="mr-1 h-3.5 w-3.5" />{training.duracion_minutos} minutos</Badge>}
                            <Badge className="bg-white/10 text-white ring-white/20"><Dumbbell className="mr-1 h-3.5 w-3.5" />{training.ejercicios.length} ejercicios</Badge>
                        </div>
                    </div>
                </div>

                {error && <p className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</p>}

                <div className="mb-6 grid gap-5 lg:grid-cols-2">
                    <Surface className="p-5">
                        <div className="flex items-start gap-3">
                            <span className="rounded-xl bg-primary-100 p-2.5 text-primary-800"><Target className="h-5 w-5" /></span>
                            <div><p className="text-xs font-bold uppercase tracking-wider text-slate-500">Objetivo principal</p><p className="mt-2 text-sm leading-6 text-slate-800">{training.objetivo_principal || 'Sin objetivo definido'}</p></div>
                        </div>
                    </Surface>
                    <Surface className="p-5">
                        <div className="flex items-start gap-3">
                            <span className="rounded-xl bg-blue-100 p-2.5 text-blue-700"><FileText className="h-5 w-5" /></span>
                            <div><p className="text-xs font-bold uppercase tracking-wider text-slate-500">Observaciones</p><p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-800">{training.observaciones || 'Sin observaciones'}</p></div>
                        </div>
                    </Surface>
                </div>

                <Surface className="mb-6 overflow-hidden">
                    <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-5 py-4 sm:px-6">
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
                                    className="grid w-full grid-cols-[auto_minmax(0,1fr)] items-center gap-4 p-4 text-left transition hover:bg-primary-50 sm:grid-cols-[56px_minmax(0,1fr)_auto] sm:px-6"
                                >
                                    <div className="flex h-12 w-12 items-center justify-center overflow-hidden rounded-xl bg-primary-950 font-bold text-white">
                                        {exercise.imagen_principal ? <img src={`http://localhost:8000/api/imagenes/${exercise.imagen_principal}`} alt="" className="h-full w-full object-cover" /> : String(index + 1).padStart(2, '0')}
                                    </div>
                                    <div className="min-w-0">
                                        <p className="truncate font-bold text-slate-950">{exercise.nombre}</p>
                                        <div className="mt-2 flex flex-wrap gap-2 text-xs font-medium text-slate-600">
                                            <span>{exercise.codigo} · {exercise.tipo}</span>
                                            <span className="flex items-center gap-1"><Users className="h-3.5 w-3.5" />{exercise.jugadores} jug.</span>
                                            <span className="flex items-center gap-1"><Maximize2 className="h-3.5 w-3.5" />{exercise.espacio}</span>
                                            <span className="flex items-center gap-1"><Clock3 className="h-3.5 w-3.5" />{exercise.tiempo}</span>
                                        </div>
                                    </div>
                                    <span className="hidden text-sm font-bold text-primary-700 sm:block">Ver ficha</span>
                                </button>
                            ))}
                        </div>
                    )}
                </Surface>

                <div className="flex flex-wrap gap-3">
                    <ActionLink to={`/entrenamientos/${id}/editar`}><Edit3 className="h-4 w-4" />Editar sesión</ActionLink>
                    <Button variant="secondary" onClick={() => setShowReuse(true)}><Copy className="h-4 w-4" />Duplicar</Button>
                    <Button variant="secondary" onClick={() => setShowDelete(true)} className="ml-auto border-red-200 text-red-700 hover:bg-red-50 hover:text-red-800"><Trash2 className="h-4 w-4" />Eliminar</Button>
                </div>
            </div>

            {selectedExerciseId && <ExerciseDetail id={selectedExerciseId} onClose={() => setSelectedExerciseId(null)} />}

            {showReuse && (
                <Modal
                    title="Duplicar entrenamiento"
                    description="Se creará una copia independiente y el original permanecerá intacto."
                    onClose={() => setShowReuse(false)}
                    footer={<div className="flex justify-end gap-3"><Button variant="secondary" onClick={() => setShowReuse(false)}>Cancelar</Button><Button onClick={handleReuse} disabled={!reuseForm.fecha}><Copy className="h-4 w-4" />Crear copia</Button></div>}
                >
                    <div className="space-y-4">
                        <div><label className="field-label">Nueva fecha *</label><input type="date" value={reuseForm.fecha} onChange={event => setReuseForm(current => ({ ...current, fecha: event.target.value }))} className="field-control" /></div>
                        <div><label className="field-label">Nombre de la copia</label><input value={reuseForm.nombre} onChange={event => setReuseForm(current => ({ ...current, nombre: event.target.value }))} className="field-control" placeholder={training.nombre} /></div>
                    </div>
                </Modal>
            )}

            {showDelete && (
                <Modal
                    title="Eliminar entrenamiento"
                    description={`Se eliminará “${training.nombre}”. Los ejercicios de la biblioteca no se verán afectados.`}
                    onClose={() => setShowDelete(false)}
                    footer={<div className="flex justify-end gap-3"><Button variant="secondary" onClick={() => setShowDelete(false)}>Cancelar</Button><Button variant="danger" onClick={handleDelete}>Eliminar</Button></div>}
                >
                    <p className="text-sm leading-6 text-slate-700">Esta acción no se puede deshacer.</p>
                </Modal>
            )}
        </AppLayout>
    );
};
