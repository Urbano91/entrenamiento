import React, { useEffect, useState } from 'react';
import { api, API_ORIGIN } from '../services/api';
import { SidebarFilters } from './SidebarFilters';
import { ExerciseDetail } from './ExerciseDetail';
import {
    Check, ChevronLeft, ChevronRight, Eye, ImageIcon, Loader2, X,
} from 'lucide-react';
import {
    EjercicioDetail, EjercicioList, ExerciseFilters, PaginatedEjercicios,
} from '../types/ejercicios';
import { Badge, Button } from './ui';
import { toggleExerciseSelection } from '../utils/exerciseSelection';

type ExerciseDataById = Record<number, EjercicioList>;

interface Props {
    initialSelectedIds: number[];
    onApply: (selectedIds: number[], exerciseData: ExerciseDataById) => void;
    onClose: () => void;
}

const SelectorCover: React.FC<{ exercise: EjercicioList }> = ({ exercise }) => {
    const [coverAvailable, setCoverAvailable] = useState(exercise.tiene_portada);
    const [fallbackImageId, setFallbackImageId] = useState<number | null>(null);

    useEffect(() => {
        if (coverAvailable) return;
        let active = true;
        api.get<EjercicioDetail>(`/ejercicios/${exercise.id}`)
            .then(detail => {
                if (active) {
                    setFallbackImageId(detail.imagenes_asociadas[0]?.imagen.id ?? null);
                }
            })
            .catch(() => undefined);
        return () => { active = false; };
    }, [coverAvailable, exercise.id]);

    if (coverAvailable) {
        return (
            <img
                src={`${API_ORIGIN}/api/ejercicios/${exercise.id}/portada`}
                alt={`Portada táctica de ${exercise.nombre}`}
                className="h-full w-full object-cover"
                onError={() => setCoverAvailable(false)}
            />
        );
    }
    if (fallbackImageId) {
        return (
            <img
                src={`${API_ORIGIN}/api/imagenes/${fallbackImageId}`}
                alt={`Imagen de ${exercise.nombre}`}
                className="h-full w-full object-cover"
            />
        );
    }
    return (
        <div className="flex h-full flex-col items-center justify-center bg-gradient-to-br from-primary-950 to-primary-700 text-primary-100">
            <ImageIcon className="h-8 w-8" />
            <span className="mt-2 text-xs font-semibold">Sin portada disponible</span>
        </div>
    );
};

export const EjercicioSelector: React.FC<Props> = ({
    initialSelectedIds, onApply, onClose,
}) => {
    const [filters, setFilters] = useState<ExerciseFilters>({ page: 1, page_size: 12 });
    const [data, setData] = useState<PaginatedEjercicios | null>(null);
    const [loading, setLoading] = useState(true);
    const [previewId, setPreviewId] = useState<number | null>(null);
    const [draftIds, setDraftIds] = useState<number[]>(
        () => [...new Set(initialSelectedIds)]
    );
    const [draftData, setDraftData] = useState<ExerciseDataById>({});

    useEffect(() => {
        setLoading(true);
        const timeout = setTimeout(() => {
            api.get<PaginatedEjercicios>('/ejercicios', filters)
                .then(setData)
                .catch(() => undefined)
                .finally(() => setLoading(false));
        }, 200);
        return () => clearTimeout(timeout);
    }, [filters]);

    const toggleExercise = (exercise: EjercicioList) => {
        setDraftIds(current => toggleExerciseSelection(current, exercise.id));
        setDraftData(current => ({ ...current, [exercise.id]: exercise }));
    };

    const applySelection = () => {
        onApply(draftIds, draftData);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/60 p-3 backdrop-blur-sm sm:p-6">
            <div role="dialog" aria-modal="true" aria-label="Seleccionar ejercicios" className="flex max-h-[94vh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
                <div className="flex shrink-0 items-center justify-between border-b border-slate-200 px-5 py-4 sm:px-6">
                    <div>
                        <p className="text-xs font-bold uppercase tracking-[0.16em] text-primary-700">Biblioteca del club</p>
                        <h2 className="mt-1 text-xl font-bold text-slate-950">Seleccionar ejercicios</h2>
                    </div>
                    <button type="button" onClick={onClose} className="rounded-xl border border-slate-200 bg-white p-2 text-slate-700 hover:bg-slate-100 hover:text-slate-950" aria-label="Cancelar y cerrar selector">
                        <X className="h-5 w-5" />
                    </button>
                </div>

                <div className="grid flex-1 overflow-hidden md:grid-cols-[250px_minmax(0,1fr)]">
                    <aside className="max-h-56 overflow-y-auto border-b border-slate-200 bg-slate-50 p-3 md:max-h-none md:border-b-0 md:border-r">
                        <p className="px-2 pb-2 text-xs font-bold uppercase tracking-wider text-slate-500">Filtros</p>
                        <SidebarFilters filters={filters} setFilters={setFilters} compact />
                    </aside>

                    <div className="overflow-y-auto p-4 sm:p-5">
                        <div className="mb-4 flex items-center justify-between gap-3">
                            <div>
                                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Resultados</p>
                                <p className="mt-1 text-sm font-semibold text-slate-800">{data?.total || 0} ejercicios disponibles</p>
                            </div>
                            <Badge tone="green"><Check className="mr-1 h-3.5 w-3.5" />Ejercicios seleccionados: {draftIds.length}</Badge>
                        </div>
                        {loading && !data ? (
                            <div className="flex h-48 items-center justify-center">
                                <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
                            </div>
                        ) : (
                            <>
                                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
                                    {data?.items.map(exercise => {
                                        const isSelected = draftIds.includes(exercise.id);
                                        return (
                                            <article key={exercise.id} className={`relative overflow-hidden rounded-2xl border-2 transition ${isSelected ? 'border-primary-600 bg-primary-50 shadow-md' : 'border-slate-200 bg-white hover:border-primary-300'}`}>
                                                <button
                                                    type="button"
                                                    onClick={() => toggleExercise(exercise)}
                                                    aria-pressed={isSelected}
                                                    aria-label={`${isSelected ? 'Deseleccionar' : 'Seleccionar'} ${exercise.nombre}`}
                                                    className="group w-full text-left"
                                                >
                                                    <div className="relative h-40 overflow-hidden bg-primary-950">
                                                        <SelectorCover exercise={exercise} />
                                                        <span className="absolute left-3 top-3 rounded-lg bg-slate-950/80 px-2 py-1 font-mono text-xs font-bold text-white backdrop-blur">{exercise.codigo}</span>
                                                        {isSelected && (
                                                            <span className="absolute right-3 top-3 flex items-center gap-1 rounded-full bg-primary-700 px-2.5 py-1 text-[11px] font-bold text-white shadow">
                                                                <Check className="h-3.5 w-3.5" />Seleccionado
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className="p-4">
                                                        <Badge tone="green">{exercise.tipo.nombre}</Badge>
                                                        <p className="mt-3 line-clamp-2 min-h-10 text-sm font-bold leading-5 text-slate-950">{exercise.nombre}</p>
                                                        <p className="mt-2 truncate text-xs font-semibold text-slate-600">
                                                            Objetivo: {exercise.objetivo_1_normalizado || 'Sin definir'}
                                                        </p>
                                                        <p className="mt-1 truncate text-xs text-slate-500">{exercise.jugadores} jugadores · {exercise.espacio.descripcion_original} · {exercise.tiempo.descripcion_original}</p>
                                                        <span className={`mt-4 flex min-h-9 w-full items-center justify-center gap-1.5 rounded-xl border px-3 text-xs font-bold ${isSelected ? 'border-primary-700 bg-primary-700 text-white' : 'border-slate-300 bg-white text-slate-700'}`}>
                                                            {isSelected && <Check className="h-3.5 w-3.5" />}
                                                            {isSelected ? 'Seleccionado' : 'Seleccionar'}
                                                        </span>
                                                    </div>
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => setPreviewId(exercise.id)}
                                                    className="flex min-h-10 w-full items-center justify-center gap-1.5 border-t border-slate-200 bg-white px-3 text-xs font-bold text-primary-700 hover:bg-primary-50 hover:text-primary-900"
                                                >
                                                    <Eye className="h-3.5 w-3.5" />Ver ficha completa
                                                </button>
                                            </article>
                                        );
                                    })}
                                </div>
                                {data && data.total_pages > 1 && (
                                    <div className="mt-5 flex items-center justify-center gap-3">
                                        <button type="button" onClick={() => setFilters(current => ({ ...current, page: current.page - 1 }))} disabled={data.page === 1} className="rounded-xl border border-slate-300 bg-white p-2 text-slate-700 hover:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-500" aria-label="Página anterior">
                                            <ChevronLeft className="h-4 w-4" />
                                        </button>
                                        <span className="text-sm font-semibold text-slate-700">Página {data.page} de {data.total_pages}</span>
                                        <button type="button" onClick={() => setFilters(current => ({ ...current, page: current.page + 1 }))} disabled={data.page === data.total_pages} className="rounded-xl border border-slate-300 bg-white p-2 text-slate-700 hover:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-500" aria-label="Página siguiente">
                                            <ChevronRight className="h-4 w-4" />
                                        </button>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>

                <div className="flex shrink-0 flex-col gap-3 border-t border-slate-200 bg-slate-50 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
                    <span className="text-sm font-semibold text-slate-700">Ejercicios seleccionados: {draftIds.length}</span>
                    <div className="flex justify-end gap-3">
                        <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
                        <Button type="button" onClick={applySelection}><Check className="h-4 w-4" />Aplicar selección</Button>
                    </div>
                </div>
            </div>

            {previewId && <ExerciseDetail id={previewId} onClose={() => setPreviewId(null)} />}
        </div>
    );
};
