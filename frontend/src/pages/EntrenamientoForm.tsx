import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api, exerciseCoverUrl, imageUrl } from '../services/api';
import { AppLayout } from '../components/AppLayout';
import { EjercicioSelector } from '../components/EjercicioSelector';
import { EjercicioEnEntreno, EntrenamientoDetail } from '../types/fase2';
import { EjercicioList } from '../types/ejercicios';
import { GripVertical, Trash2, Plus, Save, Clock3, Dumbbell, Target, PackageOpen, Users, Maximize2 } from 'lucide-react';
import { Badge, Button, PageHeader, Surface } from '../components/ui';
import { useToast } from '../utils/useToast';

interface Props {
    editId?: number;
}

const todayIso = () => {
    const today = new Date();
    const pad = (value: number) => String(value).padStart(2, '0');
    return `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
};

export const EntrenamientoForm: React.FC<Props> = ({ editId }) => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const minimumDate = todayIso();
    const requestedDate = searchParams.get('fecha');
    const initFecha = !editId && requestedDate && requestedDate < minimumDate
        ? minimumDate
        : requestedDate || minimumDate;

    const { success } = useToast();

    const [form, setForm] = useState({
        fecha: initFecha,
        hora: '',
        nombre: '',
        duracion_minutos: '',
        objetivo_principal: '',
        observaciones: '',
    });
    const [ejercicios, setEjercicios] = useState<EjercicioEnEntreno[]>([]);
    const ejerciciosRef = useRef<EjercicioEnEntreno[]>([]);
    const [initialExercises, setInitialExercises] = useState<EjercicioEnEntreno[]>([]);
    const [showSelector, setShowSelector] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(!!editId);
    const [draggedExerciseId, setDraggedExerciseId] = useState<number | null>(null);
    const draggedExerciseIdRef = useRef<number | null>(null);
    const [reordering, setReordering] = useState(false);

    useEffect(() => {
        ejerciciosRef.current = ejercicios;
    }, [ejercicios]);

    // Load existing entrenamiento if editing
    useEffect(() => {
        if (!editId) return;
        api.get<EntrenamientoDetail>(`/entrenamientos/${editId}`).then(e => {
            setForm({
                fecha: e.fecha,
                hora: e.hora?.slice(0, 5) ?? '',
                nombre: e.nombre,
                duracion_minutos: e.duracion_minutos != null ? String(e.duracion_minutos) : '',
                objetivo_principal: e.objetivo_principal ?? '',
                observaciones: e.observaciones ?? '',
            });
            setEjercicios(e.ejercicios || []);
            setInitialExercises(e.ejercicios || []);
            setLoading(false);
        }).catch(() => navigate('/entrenamientos'));
    }, [editId, navigate]);

    const removeEjercicio = (exerciseId: number) => {
        setEjercicios(current => current.filter(
            exercise => exercise.ejercicio_id !== exerciseId
        ));
    };

    const reorderTo = (targetId: number) => {
        const sourceId = draggedExerciseIdRef.current;
        if (sourceId === null || sourceId === targetId) return;
        setEjercicios(current => {
            const from = current.findIndex(item => item.id === sourceId);
            const to = current.findIndex(item => item.id === targetId);
            if (from < 0 || to < 0 || from === to) return current;
            const next = [...current];
            const [moved] = next.splice(from, 1);
            next.splice(to, 0, moved);
            const ordered = next.map((item, index) => ({ ...item, orden: index }));
            ejerciciosRef.current = ordered;
            return ordered;
        });
    };

    const persistReorder = async () => {
        if (!editId || ejerciciosRef.current.some(item => item.id <= 0)) return;
        setReordering(true);
        try {
            await api.put<{ ok: boolean }>(
                `/entrenamientos/${editId}/ejercicios/reordenar`,
                ejerciciosRef.current.map((item, index) => ({ id: item.id, orden: index })),
            );
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'No se pudo guardar el nuevo orden.');
        } finally {
            setReordering(false);
        }
    };

    const finishDrag = (pointerId: number, target: HTMLButtonElement) => {
        if (target.hasPointerCapture(pointerId)) target.releasePointerCapture(pointerId);
        if (draggedExerciseIdRef.current === null) return;
        draggedExerciseIdRef.current = null;
        setDraggedExerciseId(null);
        void persistReorder();
    };

    const syncEditedExercises = async (trainingId: number) => {
        const finalIds = new Set(ejercicios.map(item => item.ejercicio_id));
        const initialByExerciseId = new Map(
            initialExercises.map(item => [item.ejercicio_id, item])
        );

        for (const original of initialExercises) {
            if (!finalIds.has(original.ejercicio_id)) {
                await api.delete(
                    `/entrenamientos/${trainingId}/ejercicios/${original.id}`
                );
            }
        }

        const persisted: EjercicioEnEntreno[] = [];
        for (const [index, exercise] of ejercicios.entries()) {
            const original = initialByExerciseId.get(exercise.ejercicio_id);
            if (original) {
                persisted.push({ ...exercise, id: original.id, orden: index });
            } else {
                const relation = await api.post<EjercicioEnEntreno>(
                    `/entrenamientos/${trainingId}/ejercicios`,
                    { ejercicio_id: exercise.ejercicio_id, orden: index },
                );
                persisted.push(relation);
            }
        }

        if (persisted.length > 0) {
            await api.put<{ ok: boolean }>(
                `/entrenamientos/${trainingId}/ejercicios/reordenar`,
                persisted.map((item, index) => ({ id: item.id, orden: index })),
            );
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!form.nombre.trim()) { setError('El nombre es obligatorio.'); return; }
        if (!form.fecha) { setError('La fecha es obligatoria.'); return; }
        if (!editId && form.fecha < minimumDate) {
            setError('No puedes crear un entrenamiento en una fecha pasada.');
            return;
        }
        setSaving(true);
        setError('');
        try {
            const payload = {
                fecha: form.fecha,
                hora: form.hora || null,
                nombre: form.nombre.trim(),
                duracion_minutos: form.duracion_minutos ? Number(form.duracion_minutos) : null,
                objetivo_principal: form.objetivo_principal.trim() || null,
                observaciones: form.observaciones.trim() || null,
            };

            if (editId) {
                await api.put<EntrenamientoDetail>(`/entrenamientos/${editId}`, payload);
                await syncEditedExercises(editId);
                success('Entrenamiento actualizado con éxito');
                navigate(`/entrenamientos/${editId}`);
            } else {
                const nuevo = await api.post<EntrenamientoDetail>('/entrenamientos', payload);
                // Add exercises one by one
                for (let i = 0; i < ejercicios.length; i++) {
                    await api.post<EjercicioEnEntreno>(`/entrenamientos/${nuevo.id}/ejercicios`, {
                        ejercicio_id: ejercicios[i].ejercicio_id,
                        orden: i,
                    });
                }
                success('Entrenamiento creado con éxito');
                navigate(`/entrenamientos/${nuevo.id}`);
            }
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Error al guardar.');
        } finally {
            setSaving(false);
        }
    };

    const applyExerciseSelection = (
        selectedIds: number[], exerciseData: Record<number, EjercicioList>
    ) => {
        setEjercicios(current => selectedIds.map((exerciseId, index) => {
            const existing = current.find(item => item.ejercicio_id === exerciseId);
            if (existing) return { ...existing, orden: index };

            const selected = exerciseData[exerciseId];
            return {
                id: -(Date.now() + exerciseId),
                ejercicio_id: exerciseId,
                orden: index,
                codigo: selected.codigo,
                nombre: selected.nombre,
                tipo: selected.tipo.nombre,
                jugadores: selected.jugadores,
                espacio: selected.espacio.descripcion_original,
                tiempo: selected.tiempo.descripcion_original,
                tiene_portada: selected.tiene_portada,
            };
        }));
    };

    if (loading) return <AppLayout><div className="flex justify-center py-20 font-semibold text-primary-700">Cargando entrenamiento…</div></AppLayout>;

    return (
        <AppLayout>
            <div className="mx-auto max-w-5xl">
                <PageHeader
                    eyebrow={editId ? 'Editar sesión' : 'Planificar sesión'}
                    title={editId ? 'Editar entrenamiento' : 'Nuevo entrenamiento'}
                    description="Define la sesión, selecciona los ejercicios y revisa el resumen antes de guardar."
                />

                <form onSubmit={handleSubmit} className="space-y-4">
                    <Surface className="overflow-hidden">
                        <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">
                            <h2 className="text-lg font-bold text-slate-950">Información del entrenamiento</h2>
                        </div>
                        <div className="grid gap-4 p-4 sm:grid-cols-2 sm:p-5">
                            <div className="sm:col-span-2">
                                <label className="field-label">Nombre *</label>
                                <input type="text" value={form.nombre} onChange={event => setForm(current => ({ ...current, nombre: event.target.value }))}
                                    className="field-control" placeholder="Ej: Presión tras pérdida" />
                            </div>
                            <div>
                                <label className="field-label">Fecha *</label>
                                <input type="date" min={editId ? undefined : minimumDate} value={form.fecha} onChange={event => setForm(current => ({ ...current, fecha: event.target.value }))} className="field-control" />
                            </div>
                            <div>
                                <label className="field-label">Hora</label>
                                <input type="time" value={form.hora} onChange={event => setForm(current => ({ ...current, hora: event.target.value }))} className="field-control" />
                            </div>
                            <div>
                                <label className="field-label">Duración (minutos)</label>
                                <input type="number" min="1" value={form.duracion_minutos} onChange={event => setForm(current => ({ ...current, duracion_minutos: event.target.value }))} className="field-control" placeholder="90" />
                            </div>
                        </div>
                    </Surface>

                    <Surface className="overflow-hidden">
                        <div className="flex flex-col gap-2 border-b border-slate-200 bg-slate-50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5">
                            <div>
                                <h2 className="text-lg font-bold text-slate-950">Ejercicios de la sesión</h2>
                            </div>
                            <Button type="button" variant="secondary" size="sm" onClick={() => setShowSelector(true)}><Plus className="h-4 w-4" />Seleccionar ejercicio</Button>
                        </div>
                        <div className="p-4 sm:p-5">
                            {ejercicios.length === 0 ? (
                                <div className="rounded-2xl border border-dashed border-slate-300 px-5 py-7 text-center">
                                    <Dumbbell className="mx-auto h-8 w-8 text-slate-400" />
                                    <p className="mt-3 font-semibold text-slate-800">Construye la sesión desde la biblioteca</p>
                                    <p className="mt-1 text-sm text-slate-600">Selecciona ejercicios y ordénalos según la secuencia de trabajo.</p>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {ejercicios.map((ej, idx) => (
                                        <article key={ej.id} data-exercise-id={ej.id} className={`grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-2 rounded-xl border bg-white p-2.5 transition sm:grid-cols-[auto_auto_minmax(0,1fr)_auto] sm:p-3 ${draggedExerciseId === ej.id ? 'border-primary-400 bg-primary-50 opacity-75 shadow-sm' : 'border-slate-200'}`}>
                                            <button
                                                type="button"
                                                onPointerDown={event => {
                                                    if (!event.isPrimary || reordering) return;
                                                    event.currentTarget.setPointerCapture(event.pointerId);
                                                    draggedExerciseIdRef.current = ej.id;
                                                    setDraggedExerciseId(ej.id);
                                                }}
                                                onPointerMove={event => {
                                                    if (draggedExerciseIdRef.current === null) return;
                                                    const row = document.elementFromPoint(event.clientX, event.clientY)
                                                        ?.closest<HTMLElement>('[data-exercise-id]');
                                                    const targetId = Number(row?.dataset.exerciseId);
                                                    if (Number.isFinite(targetId)) reorderTo(targetId);
                                                }}
                                                onPointerUp={event => finishDrag(event.pointerId, event.currentTarget)}
                                                onPointerCancel={event => finishDrag(event.pointerId, event.currentTarget)}
                                                className="flex h-11 w-9 touch-none cursor-grab items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 active:cursor-grabbing disabled:cursor-default disabled:opacity-50"
                                                aria-label={`Arrastrar ${ej.nombre || `ejercicio ${idx + 1}`} para cambiar el orden`}
                                                title="Mantén pulsado y arrastra para reordenar"
                                                disabled={reordering}
                                            >
                                                <GripVertical className="h-5 w-5" aria-hidden="true" />
                                            </button>
                                            <div className="hidden h-14 w-14 items-center justify-center overflow-hidden rounded-xl bg-primary-950 text-lg font-bold text-white sm:flex">
                                                {ej.tiene_portada ? (
                                                    <img src={exerciseCoverUrl(ej.ejercicio_id)} alt={`Portada de ${ej.nombre}`}
                                                        className="h-full w-full object-cover" />
                                                ) : ej.imagen_principal ? (
                                                    <img src={imageUrl(ej.imagen_principal)} alt=""
                                                        className="h-full w-full object-cover" />
                                                ) : String(idx + 1).padStart(2, '0')}
                                            </div>
                                            <div className="min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs font-bold text-primary-700 sm:hidden">{String(idx + 1).padStart(2, '0')}</span>
                                                    <p className="break-words font-bold text-slate-950 [overflow-wrap:anywhere]">{ej.nombre || `Ejercicio ${ej.ejercicio_id}`}</p>
                                                </div>
                                                <div className="mt-2 flex flex-wrap gap-1.5">
                                                    {ej.tipo && <Badge tone="green">{ej.tipo}</Badge>}
                                                    <Badge><Users className="mr-1 h-3 w-3" />{ej.jugadores} jugadores</Badge>
                                                    {ej.espacio && <Badge><Maximize2 className="mr-1 h-3 w-3" />{ej.espacio}</Badge>}
                                                    {ej.tiempo && <Badge><Clock3 className="mr-1 h-3 w-3" />{ej.tiempo}</Badge>}
                                                </div>
                                            </div>
                                            <button type="button" onClick={() => removeEjercicio(ej.ejercicio_id)}
                                                className="flex h-11 w-11 items-center justify-center rounded-xl border border-red-200 bg-red-50 text-red-700 hover:bg-red-100 hover:text-red-800" aria-label={`Eliminar ${ej.nombre}`} title="Eliminar">
                                                <Trash2 className="h-4 w-4" />
                                            </button>
                                        </article>
                                    ))}
                                </div>
                            )}
                        </div>
                    </Surface>

                    <Surface className="overflow-hidden">
                        <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">
                            <h2 className="text-lg font-bold text-slate-950">Objetivo principal</h2>
                        </div>
                        <div className="p-4 sm:p-5">
                            <label className="sr-only" htmlFor="objetivo-principal">Objetivo principal</label>
                            <input id="objetivo-principal" type="text" value={form.objetivo_principal} onChange={event => setForm(current => ({ ...current, objetivo_principal: event.target.value }))}
                                className="field-control" placeholder="Ej: Mejorar la presión tras pérdida" />
                        </div>
                    </Surface>

                    <Surface className="overflow-hidden">
                        <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">
                            <h2 className="text-lg font-bold text-slate-950">Observaciones</h2>
                        </div>
                        <div className="p-4 sm:p-5">
                            <label className="sr-only" htmlFor="observaciones-entrenamiento">Observaciones</label>
                            <textarea id="observaciones-entrenamiento" rows={3} value={form.observaciones} onChange={event => setForm(current => ({ ...current, observaciones: event.target.value }))}
                                className="field-control resize-none" placeholder="Indicaciones para el cuerpo técnico, carga prevista…" />
                        </div>
                    </Surface>

                    <Surface className="overflow-hidden">
                        <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 sm:px-5">
                            <h2 className="text-lg font-bold text-slate-950">Resumen de la sesión</h2>
                        </div>
                        <div className="grid gap-2 p-4 sm:grid-cols-2 sm:p-5 lg:grid-cols-4">
                            <div className="rounded-xl bg-slate-50 p-3"><Clock3 className="h-4 w-4 text-primary-700" /><p className="mt-2 text-xs font-semibold uppercase text-slate-500">Duración</p><p className="mt-1 text-sm font-semibold text-slate-950">{form.duracion_minutos ? `${form.duracion_minutos} min` : 'Sin definir'}</p></div>
                            <div className="rounded-xl bg-slate-50 p-3"><Dumbbell className="h-4 w-4 text-primary-700" /><p className="mt-2 text-xs font-semibold uppercase text-slate-500">Ejercicios</p><p className="mt-1 text-sm font-semibold text-slate-950">{ejercicios.length}</p></div>
                            <div className="rounded-xl bg-slate-50 p-3"><Target className="h-4 w-4 text-primary-700" /><p className="mt-2 text-xs font-semibold uppercase text-slate-500">Objetivo</p><p className="mt-1 break-words text-sm font-semibold text-slate-950 [overflow-wrap:anywhere]">{form.objetivo_principal || 'Sin definir'}</p></div>
                            <div className="rounded-xl bg-slate-50 p-3"><PackageOpen className="h-4 w-4 text-primary-700" /><p className="mt-2 text-xs font-semibold uppercase text-slate-500">Material</p><p className="mt-1 text-sm font-semibold text-slate-950">Según ejercicios</p></div>
                        </div>
                    </Surface>

                    {error && <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</p>}

                    <div className="sticky bottom-20 z-20 flex justify-end gap-2 rounded-2xl border border-slate-200 bg-white/95 p-3 shadow-panel backdrop-blur lg:bottom-4">
                        <Button type="button" variant="secondary" onClick={() => navigate(-1)}>Cancelar</Button>
                        <Button type="submit" loading={saving} loadingText="Guardando..."><Save className="h-4 w-4" />Guardar</Button>
                    </div>
                </form>
            </div>

            {showSelector && (
                <EjercicioSelector
                    initialSelectedIds={ejercicios.map(e => e.ejercicio_id)}
                    onApply={applyExerciseSelection}
                    onClose={() => setShowSelector(false)}
                />
            )}
        </AppLayout>
    );
};
