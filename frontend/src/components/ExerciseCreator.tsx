import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Check, Eye, ImagePlus, Loader2, Plus, Save, X } from 'lucide-react';
import { api } from '../services/api';
import { taxonomyApi } from '../services/taxonomy';
import {
    EjercicioCreateResponse,
    EjercicioDetail,
    EjercicioDraft,
    Espacio,
    SimilarExerciseCandidate,
    SimilarExercisesResponse,
    Tiempo,
    TipoTarea,
} from '../types/ejercicios';
import { TaxonomyCatalog } from '../types/taxonomy';
import { Button } from './ui';
import { ExerciseDetail } from './ExerciseDetail';
import { useModalBehavior } from './useModalBehavior';

interface Props {
    exerciseId?: number;
    onClose: () => void;
    onExerciseReady: (exercise: EjercicioDetail) => void;
}

type Catalogs = {
    tipos: TipoTarea[];
    espacios: Espacio[];
    tiempos: Tiempo[];
    taxonomy: TaxonomyCatalog;
};

const emptyDraft: EjercicioDraft = {
    nombre: '',
    descripcion: '',
    tipo_tarea_id: 0,
    jugadores: 1,
    espacio_id: 0,
    tiempo_id: 0,
    categoria_objetivo_id: 0,
    objetivo_ids: [],
    materiales: [],
};

const splitMaterials = (value: string) => value
    .split(/[,;\n]+/)
    .map(item => item.trim())
    .filter(Boolean);

export const ExerciseCreator: React.FC<Props> = ({ exerciseId, onClose, onExerciseReady }) => {
    const [catalogs, setCatalogs] = useState<Catalogs | null>(null);
    const [draft, setDraft] = useState<EjercicioDraft>(emptyDraft);
    const [materialsText, setMaterialsText] = useState('');
    const [loading, setLoading] = useState(true);
    const [checking, setChecking] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [candidates, setCandidates] = useState<SimilarExerciseCandidate[] | null>(null);
    const [selectedCandidateId, setSelectedCandidateId] = useState<number | null>(null);
    const [previewId, setPreviewId] = useState<number | null>(null);
    const [confirmSame, setConfirmSame] = useState(false);
    const [imageFile, setImageFile] = useState<File | null>(null);
    const [hasExistingImage, setHasExistingImage] = useState(false);
    const [removeExistingImage, setRemoveExistingImage] = useState(false);

    useModalBehavior(onClose);

    useEffect(() => {
        Promise.all([
            api.get<TipoTarea[]>('/tipos'),
            api.get<Espacio[]>('/espacios'),
            api.get<Tiempo[]>('/tiempos'),
            taxonomyApi.getCatalog(),
            exerciseId ? api.get<EjercicioDetail>(`/ejercicios/${exerciseId}`) : Promise.resolve(null),
            exerciseId ? taxonomyApi.getExerciseTrace(exerciseId) : Promise.resolve([]),
        ])
            .then(([tipos, espacios, tiempos, taxonomy, exercise, trace]) => {
                setCatalogs({ tipos, espacios, tiempos, taxonomy });
                if (exercise) {
                    const categoryId = trace[0]?.categoria_id ?? taxonomy.categorias[0]?.id ?? 0;
                    setDraft({
                        nombre: exercise.nombre,
                        descripcion: exercise.desarrollo || '',
                        tipo_tarea_id: exercise.tipo_tarea_id,
                        jugadores: exercise.jugadores,
                        espacio_id: exercise.espacio.id,
                        tiempo_id: exercise.tiempo.id,
                        categoria_objetivo_id: categoryId,
                        objetivo_ids: [...new Set(trace.filter(item => item.categoria_id === categoryId).map(item => item.objetivo_id))],
                        materiales: [],
                    });
                    setMaterialsText(exercise.materiales_asociados.map(item => item.material_original || item.material.nombre_normalizado).join('\n'));
                    setHasExistingImage(exercise.imagenes_asociadas.length > 0);
                } else {
                    setDraft(current => ({
                        ...current,
                        tipo_tarea_id: tipos[0]?.id ?? 0,
                        espacio_id: espacios[0]?.id ?? 0,
                        tiempo_id: tiempos[0]?.id ?? 0,
                        categoria_objetivo_id: taxonomy.categorias[0]?.id ?? 0,
                    }));
                }
            })
            .catch(reason => setError(reason instanceof Error ? reason.message : 'No se pudo cargar el formulario'))
            .finally(() => setLoading(false));
    }, [exerciseId]);

    const categoryObjectives = useMemo(() => catalogs?.taxonomy.objetivos.filter(
        objective => objective.categoria_id === draft.categoria_objetivo_id,
    ) ?? [], [catalogs, draft.categoria_objetivo_id]);

    const payload = (): EjercicioDraft => ({
        ...draft,
        materiales: splitMaterials(materialsText),
    });

    const validate = () => {
        if (!draft.nombre.trim()) return 'Escribe un nombre para el ejercicio.';
        if (!draft.descripcion?.trim()) return 'Describe cómo se desarrolla el ejercicio.';
        if (!draft.tipo_tarea_id || !draft.espacio_id || !draft.tiempo_id) return 'Completa los datos del ejercicio.';
        if (!draft.categoria_objetivo_id || draft.objetivo_ids.length === 0) return 'Selecciona una categoría y al menos un objetivo.';
        return '';
    };

    const checkSimilar = async () => {
        const validationError = validate();
        if (validationError) {
            setError(validationError);
            return;
        }
        setError('');
        setChecking(true);
        try {
            const endpoint = exerciseId
                ? `/ejercicios/similares?exclude_exercise_id=${exerciseId}`
                : '/ejercicios/similares';
            const result = await api.post<SimilarExercisesResponse>(endpoint, payload());
            setCandidates(result.candidates);
            setSelectedCandidateId(result.candidates[0]?.exercise_id ?? null);
        } catch (reason) {
            const message = reason instanceof Error ? reason.message : 'No se pudo buscar ejercicios parecidos';
            setError(`${message}. Aun así, puedes guardarlo como nuevo ejercicio.`);
            setCandidates([]);
            setSelectedCandidateId(null);
        } finally {
            setChecking(false);
        }
    };

    const saveExercise = async (variantOfId?: number) => {
        setSaving(true);
        setError('');
        try {
            let exercise: EjercicioDetail;
            if (exerciseId) {
                exercise = await api.put<EjercicioDetail>(`/ejercicios/${exerciseId}`, payload());
            } else {
                const result = await api.post<EjercicioCreateResponse>('/ejercicios', {
                    ...payload(),
                    variant_of_id: variantOfId,
                });
                exercise = result.exercise;
            }
            try {
                if (imageFile) {
                    const formData = new FormData();
                    formData.append('image', imageFile);
                    exercise = await api.upload<EjercicioDetail>(`/ejercicios/${exercise.id}/imagen`, formData);
                } else if (exerciseId && hasExistingImage && removeExistingImage) {
                    await api.delete(`/ejercicios/${exercise.id}/imagen`);
                    exercise = await api.get<EjercicioDetail>(`/ejercicios/${exercise.id}`);
                }
            } catch (imageError) {
                onExerciseReady(exercise);
                onClose();
                window.alert(
                    `El ejercicio se guardó, pero no se pudo actualizar su imagen: ${
                        imageError instanceof Error ? imageError.message : 'error desconocido'
                    }`,
                );
                return;
            }
            onExerciseReady(exercise);
            onClose();
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : 'No se pudo guardar el ejercicio');
        } finally {
            setSaving(false);
        }
    };

    const useExisting = async () => {
        if (!selectedCandidateId) return;
        setSaving(true);
        setError('');
        try {
            const exercise = await api.get<EjercicioDetail>(`/ejercicios/${selectedCandidateId}`);
            onExerciseReady(exercise);
            onClose();
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : 'No se pudo usar el ejercicio existente');
            setConfirmSame(false);
        } finally {
            setSaving(false);
        }
    };

    const toggleObjective = (objectiveId: number) => setDraft(current => ({
        ...current,
        objetivo_ids: current.objetivo_ids.includes(objectiveId)
            ? current.objetivo_ids.filter(id => id !== objectiveId)
            : [...current.objetivo_ids, objectiveId],
    }));

    return (
        <div className="fixed inset-0 z-[80] flex items-center justify-center overflow-x-hidden bg-slate-950/70 p-0 backdrop-blur-sm sm:p-4" onClick={event => { if (event.target === event.currentTarget) onClose(); }}>
            <div role="dialog" aria-modal="true" aria-label="Crear ejercicio" className="flex h-[100dvh] max-h-[100dvh] min-w-0 w-full max-w-4xl flex-col overflow-hidden bg-white shadow-2xl sm:h-auto sm:max-h-[94dvh] sm:rounded-2xl" onClick={event => event.stopPropagation()}>
                <div className="flex shrink-0 items-start justify-between gap-3 border-b border-slate-200 px-4 py-3 sm:px-6 sm:py-4">
                    <div>
                        <p className="text-xs font-bold uppercase tracking-[0.14em] text-primary-700">Mi biblioteca</p>
                        <h2 className="mt-1 text-xl font-bold text-slate-950">{exerciseId ? 'Editar ejercicio' : 'Crear ejercicio'}</h2>
                        <p className="mt-1 text-sm text-slate-600">{exerciseId ? 'Solo tú puedes modificar este ejercicio.' : 'Antes de guardarlo comprobaremos si ya existe uno parecido.'}</p>
                    </div>
                    <button type="button" onClick={onClose} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100" aria-label="Cerrar"><X className="h-5 w-5" /></button>
                </div>

                <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
                    {loading ? (
                        <div className="flex h-56 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary-700" /></div>
                    ) : candidates === null ? (
                        <div className="grid gap-4 sm:grid-cols-2">
                            <div className="sm:col-span-2"><label className="field-label">Nombre *</label><input className="field-control" value={draft.nombre} onChange={event => setDraft(current => ({ ...current, nombre: event.target.value }))} placeholder="Ej: Rueda de pase con tercer hombre" /></div>
                            <div className="sm:col-span-2"><label className="field-label">Descripción *</label><textarea rows={5} className="field-control resize-y" value={draft.descripcion} onChange={event => setDraft(current => ({ ...current, descripcion: event.target.value }))} placeholder="Organización, desarrollo, reglas y consignas…" /></div>
                            <div><label className="field-label">Tipo de tarea *</label><select className="field-control" value={draft.tipo_tarea_id} onChange={event => setDraft(current => ({ ...current, tipo_tarea_id: Number(event.target.value) }))}>{catalogs?.tipos.map(item => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></div>
                            <div><label className="field-label">Número de jugadores *</label><input type="number" min="1" className="field-control" value={draft.jugadores} onChange={event => setDraft(current => ({ ...current, jugadores: Number(event.target.value) }))} /></div>
                            <div><label className="field-label">Espacio *</label><select className="field-control" value={draft.espacio_id} onChange={event => setDraft(current => ({ ...current, espacio_id: Number(event.target.value) }))}>{catalogs?.espacios.map(item => <option key={item.id} value={item.id}>{item.descripcion_original}</option>)}</select></div>
                            <div><label className="field-label">Duración *</label><select className="field-control" value={draft.tiempo_id} onChange={event => setDraft(current => ({ ...current, tiempo_id: Number(event.target.value) }))}>{catalogs?.tiempos.map(item => <option key={item.id} value={item.id}>{item.descripcion_original}</option>)}</select></div>
                            <div className="sm:col-span-2"><label className="field-label">Categoría de objetivos *</label><select className="field-control" value={draft.categoria_objetivo_id} onChange={event => setDraft(current => ({ ...current, categoria_objetivo_id: Number(event.target.value), objetivo_ids: [] }))}>{catalogs?.taxonomy.categorias.map(item => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></div>
                            <fieldset className="sm:col-span-2"><legend className="field-label">Objetivos * <span className="font-normal text-slate-500">(puedes elegir varios)</span></legend><div className="grid gap-2 sm:grid-cols-2">{categoryObjectives.map(objective => <label key={objective.id} className={`flex min-h-11 cursor-pointer items-center gap-3 rounded-xl border px-3 py-2 text-sm font-semibold ${draft.objetivo_ids.includes(objective.id) ? 'border-primary-500 bg-primary-50 text-primary-900' : 'border-slate-200 text-slate-700 hover:bg-slate-50'}`}><input type="checkbox" checked={draft.objetivo_ids.includes(objective.id)} onChange={() => toggleObjective(objective.id)} className="h-4 w-4 accent-primary-700" />{objective.nombre}</label>)}</div></fieldset>
                            <div className="sm:col-span-2"><label className="field-label">Material</label><textarea rows={3} className="field-control resize-y" value={materialsText} onChange={event => setMaterialsText(event.target.value)} placeholder="Balones, 4 conos, petos… (separa con comas o líneas)" /><p className="mt-1 text-xs text-slate-500">El material describe el ejercicio; no se utiliza como filtro.</p></div>
                            <div className="sm:col-span-2"><label className="field-label">Imagen</label><label className="flex min-h-24 cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-center hover:border-primary-400 hover:bg-primary-50"><ImagePlus className="h-6 w-6 text-primary-700" /><span className="mt-2 text-sm font-semibold text-slate-800">{imageFile?.name || (hasExistingImage ? 'Cambiar imagen' : 'Subir imagen')}</span><span className="mt-1 text-xs text-slate-500">PNG, JPEG o WebP · máximo 8 MB</span><input type="file" accept="image/png,image/jpeg,image/webp" className="sr-only" onChange={event => { setImageFile(event.target.files?.[0] ?? null); setRemoveExistingImage(false); }} /></label>{hasExistingImage && !imageFile && <label className="mt-2 flex items-center gap-2 text-sm font-semibold text-red-700"><input type="checkbox" checked={removeExistingImage} onChange={event => setRemoveExistingImage(event.target.checked)} />Eliminar la imagen actual al guardar</label>}<p className="mt-1 text-xs text-slate-500">La imagen no participa en la búsqueda de ejercicios parecidos.</p></div>
                        </div>
                    ) : (
                        <div>
                            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4"><div className="flex gap-3"><AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" /><div><h3 className="font-bold text-amber-950">Ejercicios parecidos encontrados</h3><p className="mt-1 text-sm text-amber-900">Revísalos y decide si el tuyo es nuevo, una variante o ya existe. La puntuación solo es orientativa.</p></div></div></div>
                            <div className="mt-4 space-y-3">{candidates.map((candidate, index) => candidate.details_visible ? <article key={candidate.exercise_id} className={`rounded-2xl border p-4 ${selectedCandidateId === candidate.exercise_id ? 'border-primary-500 bg-primary-50/50 ring-1 ring-primary-200' : 'border-slate-200'}`}><label className="flex cursor-pointer items-start gap-3"><input type="radio" name="similar-candidate" className="mt-1 h-4 w-4 accent-primary-700" checked={selectedCandidateId === candidate.exercise_id} onChange={() => setSelectedCandidateId(candidate.exercise_id ?? null)} /><span className="min-w-0 flex-1"><span className="flex flex-wrap items-baseline justify-between gap-2"><strong className="break-words text-slate-950">{candidate.name}</strong><span className="text-lg font-bold text-primary-800">{Math.round((candidate.similarity ?? 0) * 100)}% similar</span></span><span className="mt-0.5 block text-xs font-semibold uppercase tracking-wide text-slate-500">Similitud semántica</span>{candidate.objectives.length > 0 && <span className="mt-2 block text-sm font-medium text-slate-700">{candidate.objectives.join(' · ')}</span>}<span className="mt-2 block text-xs text-slate-500">{candidate.players} jugadores · {candidate.space} · {candidate.duration}</span></span></label>{candidate.exercise_id && <button type="button" onClick={() => setPreviewId(candidate.exercise_id ?? null)} className="mt-3 inline-flex min-h-11 items-center gap-2 rounded-xl px-3 text-sm font-bold text-primary-700 hover:bg-primary-100"><Eye className="h-4 w-4" />Ver ejercicio</button>}</article> : <article key={`private-${index}`} className="rounded-2xl border border-amber-200 bg-amber-50 p-4"><strong className="text-amber-950">Este ejercicio parece muy similar a otro ejercicio existente.</strong><p className="mt-1 text-sm text-amber-900">Es privado y no podemos mostrar su nombre, autor, contenido, imagen ni puntuación de similitud.</p></article>)}</div>
                            {candidates.length === 0 && <p className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">No hemos encontrado candidatos. Puedes guardarlo como nuevo.</p>}
                        </div>
                    )}
                    {error && <p className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</p>}
                </div>

                <div className="shrink-0 border-t border-slate-200 bg-slate-50 px-4 py-3 sm:px-6">
                    {candidates === null ? (
                        <div className="flex justify-end gap-2"><Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button><Button type="button" disabled={checking || loading} onClick={checkSimilar}>{checking ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}{checking ? 'Buscando ejercicios similares…' : 'Guardar ejercicio'}</Button></div>
                    ) : (
                        <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:justify-end"><Button type="button" variant="secondary" onClick={() => { setCandidates(null); setSelectedCandidateId(null); }}>Editar datos</Button><Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>{!exerciseId && <><Button type="button" variant="secondary" disabled={!selectedCandidateId || saving} onClick={() => setConfirmSame(true)}>Usar ejercicio existente</Button><Button type="button" variant="secondary" disabled={!selectedCandidateId || saving} onClick={() => selectedCandidateId && saveExercise(selectedCandidateId)}>Guardar como variante</Button></>}<Button type="button" disabled={saving} onClick={() => saveExercise()}>{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}{exerciseId ? 'Guardar cambios' : 'Guardar como ejercicio nuevo'}</Button></div>
                    )}
                </div>
            </div>

            {previewId && <ExerciseDetail id={previewId} onClose={() => setPreviewId(null)} />}
            {confirmSame && (
                <div className="fixed inset-0 z-[90] flex items-center justify-center bg-slate-950/70 p-4" onClick={event => { if (event.target === event.currentTarget) setConfirmSame(false); }}>
                    <div role="alertdialog" aria-modal="true" className="w-full max-w-md rounded-2xl bg-white p-5 shadow-2xl"><h3 className="text-lg font-bold text-slate-950">Has indicado que este ejercicio ya existe</h3><p className="mt-2 text-sm leading-6 text-slate-600">No se creará un duplicado. Se utilizará el ejercicio existente que has seleccionado.</p><div className="mt-5 flex justify-end gap-2"><Button type="button" variant="secondary" onClick={() => setConfirmSame(false)}>Cancelar</Button><Button type="button" disabled={saving} onClick={useExisting}>{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}Usar ejercicio existente</Button></div></div>
                </div>
            )}
        </div>
    );
};
