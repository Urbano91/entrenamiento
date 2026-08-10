import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api, API_ORIGIN } from '../services/api';
import { AppLayout } from '../components/AppLayout';
import { EjercicioSelector } from '../components/EjercicioSelector';
import { EjercicioEnEntreno, EntrenamientoDetail } from '../types/fase2';
import { EjercicioList } from '../types/ejercicios';
import { ChevronUp, ChevronDown, Trash2, Plus, Save, Clock3, Dumbbell, Target, PackageOpen, Users, Maximize2 } from 'lucide-react';
import { Badge, Button, PageHeader, Surface } from '../components/ui';

interface Props {
    editId?: number;
}

export const EntrenamientoForm: React.FC<Props> = ({ editId }) => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const initFecha = searchParams.get('fecha') || new Date().toISOString().slice(0, 10);

    const [form, setForm] = useState({
        fecha: initFecha,
        nombre: '',
        duracion_minutos: '',
        objetivo_principal: '',
        observaciones: '',
    });
    const [ejercicios, setEjercicios] = useState<EjercicioEnEntreno[]>([]);
    const [initialExercises, setInitialExercises] = useState<EjercicioEnEntreno[]>([]);
    const [showSelector, setShowSelector] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(!!editId);

    // Load existing entrenamiento if editing
    useEffect(() => {
        if (!editId) return;
        api.get<EntrenamientoDetail>(`/entrenamientos/${editId}`).then(e => {
            setForm({
                fecha: e.fecha,
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

    const moveUp = (idx: number) => {
        if (idx === 0) return;
        setEjercicios(prev => {
            const arr = [...prev];
            [arr[idx - 1], arr[idx]] = [arr[idx], arr[idx - 1]];
            return arr.map((e, i) => ({ ...e, orden: i }));
        });
    };

    const moveDown = (idx: number) => {
        setEjercicios(prev => {
            if (idx >= prev.length - 1) return prev;
            const arr = [...prev];
            [arr[idx], arr[idx + 1]] = [arr[idx + 1], arr[idx]];
            return arr.map((e, i) => ({ ...e, orden: i }));
        });
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
        setSaving(true);
        setError('');
        try {
            const payload = {
                fecha: form.fecha,
                nombre: form.nombre.trim(),
                duracion_minutos: form.duracion_minutos ? Number(form.duracion_minutos) : null,
                objetivo_principal: form.objetivo_principal.trim() || null,
                observaciones: form.observaciones.trim() || null,
            };

            if (editId) {
                await api.put<EntrenamientoDetail>(`/entrenamientos/${editId}`, payload);
                await syncEditedExercises(editId);
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

                <div className="mb-6 grid grid-cols-3 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-panel">
                    {['Información', 'Ejercicios', 'Resumen'].map((label, index) => (
                        <div key={label} className={`flex items-center gap-2 border-r border-slate-200 px-3 py-3 last:border-r-0 sm:px-5 ${index === 0 ? 'bg-primary-50' : ''}`}>
                            <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${index === 0 ? 'bg-primary-700 text-white' : 'bg-slate-100 text-slate-700'}`}>{index + 1}</span>
                            <span className="hidden text-sm font-semibold text-slate-700 sm:block">{label}</span>
                        </div>
                    ))}
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <Surface className="overflow-hidden">
                        <div className="border-b border-slate-200 bg-slate-50 px-5 py-4 sm:px-6">
                            <p className="text-xs font-bold uppercase tracking-[0.16em] text-primary-700">Paso 1</p>
                            <h2 className="mt-1 text-lg font-bold text-slate-950">Información del entrenamiento</h2>
                        </div>
                        <div className="grid gap-5 p-5 sm:grid-cols-2 sm:p-6">
                            <div className="sm:col-span-2">
                                <label className="field-label">Nombre del entrenamiento *</label>
                                <input type="text" value={form.nombre} onChange={event => setForm(current => ({ ...current, nombre: event.target.value }))}
                                    className="field-control" placeholder="Ej: Presión tras pérdida" />
                            </div>
                            <div>
                                <label className="field-label">Fecha *</label>
                                <input type="date" value={form.fecha} onChange={event => setForm(current => ({ ...current, fecha: event.target.value }))} className="field-control" />
                            </div>
                            <div>
                                <label className="field-label">Duración (minutos)</label>
                                <input type="number" min="1" value={form.duracion_minutos} onChange={event => setForm(current => ({ ...current, duracion_minutos: event.target.value }))} className="field-control" placeholder="90" />
                            </div>
                            <div>
                                <label className="field-label">Objetivo principal</label>
                                <input type="text" value={form.objetivo_principal} onChange={event => setForm(current => ({ ...current, objetivo_principal: event.target.value }))}
                                    className="field-control" placeholder="Ej: Mejorar la presión tras pérdida" />
                            </div>
                            <div className="sm:col-span-2">
                                <label className="field-label">Observaciones</label>
                                <textarea rows={4} value={form.observaciones} onChange={event => setForm(current => ({ ...current, observaciones: event.target.value }))}
                                    className="field-control resize-none" placeholder="Indicaciones para el cuerpo técnico, carga prevista…" />
                            </div>
                        </div>
                    </Surface>

                    <Surface className="overflow-hidden">
                        <div className="flex flex-col gap-3 border-b border-slate-200 bg-slate-50 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
                            <div>
                                <p className="text-xs font-bold uppercase tracking-[0.16em] text-primary-700">Paso 2</p>
                                <h2 className="mt-1 text-lg font-bold text-slate-950">Ejercicios de la sesión</h2>
                            </div>
                            <Button type="button" variant="secondary" size="sm" onClick={() => setShowSelector(true)}><Plus className="h-4 w-4" />Añadir ejercicio</Button>
                        </div>
                        <div className="p-5 sm:p-6">
                            {ejercicios.length === 0 ? (
                            <div className="rounded-2xl border-2 border-dashed border-slate-300 px-6 py-10 text-center">
                                <Dumbbell className="mx-auto h-8 w-8 text-slate-400" />
                                <p className="mt-3 font-semibold text-slate-800">Construye la sesión desde la biblioteca</p>
                                <p className="mt-1 text-sm text-slate-600">Selecciona ejercicios y ordénalos según la secuencia de trabajo.</p>
                                <Button type="button" size="sm" className="mt-5" onClick={() => setShowSelector(true)}><Plus className="h-4 w-4" />Seleccionar ejercicios</Button>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {ejercicios.map((ej, idx) => (
                                    <article key={ej.id} className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm sm:grid-cols-[auto_auto_minmax(0,1fr)_auto] sm:p-4">
                                        <div className="flex flex-col gap-1">
                                            <button type="button" onClick={() => moveUp(idx)} disabled={idx === 0}
                                                className="rounded-lg border border-slate-200 bg-white p-1.5 text-slate-700 hover:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-500" aria-label="Subir ejercicio">
                                                <ChevronUp className="h-4 w-4" />
                                            </button>
                                            <button type="button" onClick={() => moveDown(idx)} disabled={idx === ejercicios.length - 1}
                                                className="rounded-lg border border-slate-200 bg-white p-1.5 text-slate-700 hover:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-500" aria-label="Bajar ejercicio">
                                                <ChevronDown className="h-4 w-4" />
                                            </button>
                                        </div>
                                        <div className="hidden h-14 w-14 items-center justify-center overflow-hidden rounded-xl bg-primary-950 text-lg font-bold text-white sm:flex">
                                            {ej.tiene_portada ? (
                                            <img src={`${API_ORIGIN}/api/ejercicios/${ej.ejercicio_id}/portada`} alt={`Portada de ${ej.nombre}`}
                                                className="h-full w-full object-cover" />
                                            ) : ej.imagen_principal ? (
                                            <img src={`${API_ORIGIN}/api/imagenes/${ej.imagen_principal}`} alt=""
                                                className="h-full w-full object-cover" />
                                            ) : String(idx + 1).padStart(2, '0')}
                                        </div>
                                        <div className="min-w-0">
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs font-bold text-primary-700 sm:hidden">{String(idx + 1).padStart(2, '0')}</span>
                                                <p className="truncate font-bold text-slate-950">{ej.nombre || `Ejercicio ${ej.ejercicio_id}`}</p>
                                            </div>
                                            <div className="mt-2 flex flex-wrap gap-1.5">
                                                {ej.tipo && <Badge tone="green">{ej.tipo}</Badge>}
                                                <Badge><Users className="mr-1 h-3 w-3" />{ej.jugadores} jugadores</Badge>
                                                {ej.espacio && <Badge><Maximize2 className="mr-1 h-3 w-3" />{ej.espacio}</Badge>}
                                                {ej.tiempo && <Badge><Clock3 className="mr-1 h-3 w-3" />{ej.tiempo}</Badge>}
                                            </div>
                                        </div>
                                        <button type="button" onClick={() => removeEjercicio(ej.ejercicio_id)}
                                            className="rounded-xl border border-red-200 bg-red-50 p-2.5 text-red-700 hover:bg-red-100 hover:text-red-800" aria-label={`Eliminar ${ej.nombre}`} title="Eliminar ejercicio">
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </article>
                                ))}
                            </div>
                        )}
                        </div>
                    </Surface>

                    <Surface className="overflow-hidden">
                        <div className="border-b border-slate-200 bg-slate-50 px-5 py-4 sm:px-6">
                            <p className="text-xs font-bold uppercase tracking-[0.16em] text-primary-700">Paso 3</p>
                            <h2 className="mt-1 text-lg font-bold text-slate-950">Resumen de la sesión</h2>
                        </div>
                        <div className="grid gap-3 p-5 sm:grid-cols-2 sm:p-6 lg:grid-cols-4">
                            <div className="rounded-xl bg-slate-50 p-4"><Clock3 className="h-5 w-5 text-primary-700" /><p className="mt-3 text-xs font-bold uppercase text-slate-500">Duración</p><p className="mt-1 font-bold text-slate-950">{form.duracion_minutos ? `${form.duracion_minutos} min` : 'Sin definir'}</p></div>
                            <div className="rounded-xl bg-slate-50 p-4"><Dumbbell className="h-5 w-5 text-primary-700" /><p className="mt-3 text-xs font-bold uppercase text-slate-500">Ejercicios</p><p className="mt-1 font-bold text-slate-950">{ejercicios.length}</p></div>
                            <div className="rounded-xl bg-slate-50 p-4"><Target className="h-5 w-5 text-primary-700" /><p className="mt-3 text-xs font-bold uppercase text-slate-500">Objetivo</p><p className="mt-1 truncate font-bold text-slate-950">{form.objetivo_principal || 'Sin definir'}</p></div>
                            <div className="rounded-xl bg-slate-50 p-4"><PackageOpen className="h-5 w-5 text-primary-700" /><p className="mt-3 text-xs font-bold uppercase text-slate-500">Material</p><p className="mt-1 font-bold text-slate-950">Según ejercicios</p></div>
                        </div>
                    </Surface>

                    {error && <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</p>}

                    <div className="sticky bottom-20 z-20 flex justify-end gap-3 rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-panel backdrop-blur lg:bottom-4">
                        <Button type="button" variant="secondary" onClick={() => navigate(-1)}>Cancelar</Button>
                        <Button type="submit" disabled={saving}><Save className="h-4 w-4" />{saving ? 'Guardando…' : 'Guardar entrenamiento'}</Button>
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
