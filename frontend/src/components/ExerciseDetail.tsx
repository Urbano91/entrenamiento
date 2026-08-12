import React, { useEffect, useState } from 'react';
import { api, exerciseAnimationUrl, exerciseCoverUrl, imageUrl } from '../services/api';
import { X, Loader2, CirclePlay, Pencil, Trash2 } from 'lucide-react';
import { EjercicioDetail } from '../types/ejercicios';
import { ObjetivoV2Trazabilidad } from '../types/taxonomy';
import { taxonomyApi } from '../services/taxonomy';
import { useModalBehavior } from './useModalBehavior';
import {
    cleanExerciseDescription,
    splitMaterialItems,
} from '../utils/exercisePresentation';

interface Props {
    id: number;
    onClose: () => void;
    onEdit?: (exercise: EjercicioDetail) => void;
    onDeleted?: (exerciseId: number) => void;
}

export const ExerciseDetail: React.FC<Props> = ({ id, onClose, onEdit, onDeleted }) => {
    const [ejercicio, setEjercicio] = useState<EjercicioDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [animationError, setAnimationError] = useState(false);
    const [showAnimation, setShowAnimation] = useState(false);
    const [taxonomyTrace, setTaxonomyTrace] = useState<ObjetivoV2Trazabilidad[]>([]);
    const [taxonomyError, setTaxonomyError] = useState(false);
    const [deleting, setDeleting] = useState(false);

    useModalBehavior(onClose, !error);

    useEffect(() => {
        const fetchDetail = async () => {
            setLoading(true);
            setError('');
            setAnimationError(false);
            setShowAnimation(false);
            setTaxonomyError(false);
            const [detailResult, taxonomyResult] = await Promise.allSettled([
                api.get<EjercicioDetail>(`/ejercicios/${id}`),
                taxonomyApi.getExerciseTrace(id),
            ]);
            if (detailResult.status === 'fulfilled') {
                setEjercicio(detailResult.value);
            } else {
                const reason = detailResult.reason;
                setError(reason instanceof Error ? reason.message : 'Error al cargar detalle');
            }
            if (taxonomyResult.status === 'fulfilled') {
                setTaxonomyTrace(taxonomyResult.value);
            } else {
                setTaxonomyTrace([]);
                setTaxonomyError(true);
            }
            setLoading(false);
        };
        fetchDetail();
    }, [id]);

    if (loading) {
        return (
            <div
                className="fixed inset-0 z-[70] flex items-center justify-center overflow-x-hidden bg-slate-950/60 p-3 backdrop-blur-sm"
                onClick={event => { if (event.target === event.currentTarget) onClose(); }}
            >
                <div role="dialog" aria-modal="true" aria-label="Cargando ficha de ejercicio" className="relative flex h-28 w-full max-w-sm items-center justify-center rounded-2xl bg-primary-950 shadow-2xl">
                    <Loader2 className="h-8 w-8 animate-spin text-white" />
                    <button
                        type="button"
                        onClick={onClose}
                        className="absolute right-3 top-3 flex h-11 w-11 items-center justify-center rounded-xl border border-white/20 bg-white/10 text-white transition-colors hover:bg-white/20"
                        aria-label="Cerrar"
                    >
                        <X className="h-6 w-6" aria-hidden="true" />
                    </button>
                </div>
            </div>
        );
    }

    if (error || !ejercicio) return null;

    const objectivesByCategory = [
        ...taxonomyTrace.reduce((categories, objective) => {
            const category = categories.get(objective.categoria_id) ?? {
                id: objective.categoria_id,
                name: objective.categoria_nombre,
                objectives: new Map<number, string>(),
            };
            category.objectives.set(objective.objetivo_id, objective.objetivo_nombre);
            categories.set(objective.categoria_id, category);
            return categories;
        }, new Map<number, {
            id: number;
            name: string;
            objectives: Map<number, string>;
        }>()).values(),
    ];
    const materialItems = [
        ...new Map(
            ejercicio.materiales_asociados
                .flatMap(material => splitMaterialItems(
                    material.material_original || material.material.nombre_normalizado,
                ))
                .map(item => [item.toLocaleLowerCase('es'), item]),
        ).values(),
    ];

    const deleteExercise = async () => {
        if (!window.confirm('¿Eliminar este ejercicio de tu biblioteca? Los entrenamientos históricos conservarán su referencia.')) return;
        setDeleting(true);
        try {
            await api.delete(`/ejercicios/${ejercicio.id}`);
            onDeleted?.(ejercicio.id);
            onClose();
        } catch (reason) {
            window.alert(reason instanceof Error ? reason.message : 'No se pudo eliminar el ejercicio');
            setDeleting(false);
        }
    };

    return (
        <div
            className="fixed inset-0 z-[70] flex justify-center overflow-x-hidden overflow-y-auto bg-slate-950/70 p-3 backdrop-blur-sm sm:p-6"
            onClick={event => { if (event.target === event.currentTarget) onClose(); }}
        >
            <div
                role="dialog"
                aria-modal="true"
                aria-label={ejercicio.nombre}
                className="my-auto flex max-h-[calc(100dvh-1.5rem)] min-w-0 w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl sm:max-h-[94dvh]"
                onClick={e => e.stopPropagation()}
            >
                {/* Cabecera modal */}
                <div className="flex shrink-0 items-start justify-between gap-3 bg-primary-950 px-4 py-4 text-white sm:px-6">
                    <div className="min-w-0">
                        <span className="text-xs font-bold uppercase tracking-wider text-primary-300">{ejercicio.tipo.nombre}</span>
                        <h2 className="mt-1 break-words text-xl font-bold leading-tight sm:text-[22px]">{ejercicio.nombre}</h2>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                        {ejercicio.can_edit && onEdit && <button type="button" onClick={() => onEdit(ejercicio)} className="flex min-h-11 items-center gap-2 rounded-xl border border-white/20 bg-white/10 px-3 text-sm font-bold text-white hover:bg-white/20"><Pencil className="h-4 w-4" />Editar</button>}
                        {ejercicio.can_edit && onDeleted && <button type="button" disabled={deleting} onClick={deleteExercise} className="flex h-11 w-11 items-center justify-center rounded-xl border border-red-300/40 bg-red-700/70 text-white hover:bg-red-700 disabled:opacity-60" aria-label="Eliminar ejercicio"><Trash2 className="h-5 w-5" /></button>}
                        <button type="button" onClick={onClose} className="flex h-11 w-11 items-center justify-center rounded-xl border border-white/20 bg-white/10 text-white transition-colors hover:bg-white/20" aria-label="Cerrar">
                            <X className="h-6 w-6" aria-hidden="true" />
                        </button>
                    </div>
                </div>

                {/* Contenido scrolleable */}
                <div className="flex min-w-0 w-full flex-col gap-6 overflow-x-hidden overflow-y-auto overscroll-contain break-words p-4 text-slate-800 sm:p-6">

                    {/* INFO BASICA */}
                    <div className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl bg-slate-200 ring-1 ring-slate-200 sm:grid-cols-4">
                        <div className="bg-slate-50 p-3"><strong className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Tipo</strong><span className="mt-1 block text-sm font-medium">{ejercicio.tipo.nombre}</span></div>
                        <div className="bg-slate-50 p-3"><strong className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Jugadores</strong><span className="mt-1 block text-sm font-medium">{ejercicio.jugadores}</span></div>
                        <div className="bg-slate-50 p-3"><strong className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Espacio</strong><span className="mt-1 block text-sm font-medium">{ejercicio.espacio.descripcion_original}</span></div>
                        <div className="bg-slate-50 p-3"><strong className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Tiempo</strong><span className="mt-1 block text-sm font-medium">{ejercicio.tiempo.descripcion_original}</span></div>
                    </div>

                    {(objectivesByCategory.length > 0 || taxonomyError) && (
                        <section>
                            <h3 className="mb-3 border-b border-slate-200 pb-2 text-lg font-semibold text-slate-950">
                                Objetivos
                            </h3>
                            {objectivesByCategory.length > 0 && (
                                <div className="space-y-4">
                                    {objectivesByCategory.map(category => (
                                        <div key={category.id} className="min-w-0">
                                            <h4 className="break-words text-sm font-bold text-primary-800">
                                                {category.name}
                                            </h4>
                                            <p className="mt-1 break-words text-sm font-medium leading-6 text-slate-800 [overflow-wrap:anywhere]">
                                                {[...category.objectives.values()].join(' · ')}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {taxonomyError && (
                                <p className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-medium text-amber-800">
                                    No se pudieron cargar los objetivos del ejercicio.
                                </p>
                            )}
                        </section>
                    )}

                    {ejercicio.desarrollo && (
                        <section>
                            <h3 className="mb-3 border-b border-slate-200 pb-2 text-lg font-semibold text-slate-950">Descripción</h3>
                            <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700 font-medium">
                                {cleanExerciseDescription(ejercicio.desarrollo)}
                            </p>
                        </section>
                    )}

                    {materialItems.length > 0 && (
                        <section>
                            <h3 className="mb-3 border-b border-slate-200 pb-2 text-lg font-semibold text-slate-950">Material</h3>
                            <ul className="list-disc space-y-1.5 pl-5 text-sm font-medium text-slate-700">
                                {materialItems.map(item => (
                                    <li key={item} className="break-words [overflow-wrap:anywhere]">
                                        {item}
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}

                    {/* REPRESENTACION ORIGINAL DEL PILOTO */}
                    {ejercicio.tiene_portada && (
                        <section className="order-first">
                            <h3 className="mb-3 flex items-center gap-2 border-b border-slate-200 pb-2 text-lg font-semibold text-slate-950">
                                <CirclePlay className="h-5 w-5 text-primary-700" /> Representación táctica
                            </h3>
                            {showAnimation && ejercicio.tiene_animacion ? (
                                <video
                                    autoPlay
                                    controls
                                    loop
                                    preload="metadata"
                                    poster={exerciseCoverUrl(ejercicio.id)}
                                    onError={() => {
                                        setAnimationError(true);
                                        setShowAnimation(false);
                                    }}
                                    className="aspect-video w-full rounded-2xl border border-slate-200 bg-primary-950 object-contain shadow-panel"
                                    aria-label={`Animación táctica de ${ejercicio.nombre}`}
                                >
                                    <source src={exerciseAnimationUrl(ejercicio.id)} type="video/webm" />
                                    Tu navegador no puede reproducir este vídeo.
                                </video>
                            ) : ejercicio.tiene_animacion ? (
                                <button
                                    type="button"
                                    onClick={() => {
                                        setAnimationError(false);
                                        setShowAnimation(true);
                                    }}
                                    className="group relative block aspect-video w-full overflow-hidden rounded-2xl border border-slate-200 bg-primary-950 shadow-panel"
                                    aria-label={`Ver movimiento de ${ejercicio.nombre}`}
                                >
                                    <img
                                        src={exerciseCoverUrl(ejercicio.id)}
                                        alt={`Representación táctica de ${ejercicio.nombre}`}
                                        className="h-full w-full object-contain transition duration-300 group-hover:scale-[1.01]"
                                    />
                                    <span className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/15 transition group-hover:bg-slate-950/25">
                                        <span className="flex h-16 w-16 items-center justify-center rounded-full bg-white/95 text-primary-800 shadow-xl">
                                            <CirclePlay className="h-9 w-9" />
                                        </span>
                                        <span className="mt-3 rounded-full bg-slate-950/85 px-4 py-2 text-sm font-bold text-white backdrop-blur">
                                            Ver movimiento
                                        </span>
                                    </span>
                                </button>
                            ) : (
                                <img
                                    src={exerciseCoverUrl(ejercicio.id)}
                                    alt={`Representación táctica de ${ejercicio.nombre}`}
                                    className="aspect-video w-full rounded-2xl border border-slate-200 bg-primary-950 object-contain shadow-panel"
                                />
                            )}
                            {animationError && (
                                <p className="mt-3 text-sm font-medium text-amber-700">No se pudo reproducir el movimiento. La portada permanece disponible.</p>
                            )}
                        </section>
                    )}

                    {/* IMAGENES EXTERNAS: SOLO EJERCICIOS FUERA DEL PILOTO */}
                    {!ejercicio.tiene_portada && ejercicio.imagenes_asociadas && ejercicio.imagenes_asociadas.length > 0 && (
                        <section>
                            <h3 className="mb-3 border-b border-slate-200 pb-2 text-lg font-semibold text-slate-950">Imágenes</h3>
                            <div className="grid gap-4 lg:grid-cols-2">
                                {ejercicio.imagenes_asociadas.map(img => (
                                    <img
                                        key={img.orden}
                                        src={imageUrl(img.imagen.id)}
                                        alt={`Imagen ${img.orden}`}
                                        className="w-full rounded-2xl border border-slate-200 bg-slate-50 object-contain shadow-panel"
                                    />
                                ))}
                            </div>
                        </section>
                    )}
                </div>
            </div>
        </div>
    );
};
