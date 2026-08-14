import React, { useEffect, useRef, useState } from 'react';
import { api, exerciseCoverUrl, imageUrl } from '../services/api';
import { SidebarFilters } from './SidebarFilters';
import { ExerciseDetail } from './ExerciseDetail';
import {
    Check, ChevronLeft, ChevronRight, Eye, ImageIcon, Loader2, Plus, SlidersHorizontal, X,
} from 'lucide-react';
import {
    EjercicioDetail, EjercicioList, ExerciseFilters, PaginatedEjercicios,
} from '../types/ejercicios';
import { Badge, Button } from './ui';
import { useModalBehavior } from './useModalBehavior';
import { toggleExerciseSelection } from '../utils/exerciseSelection';
import { countActiveExerciseFilters } from '../utils/exerciseFilters';
import { ExerciseCreator } from './ExerciseCreator';

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
                src={exerciseCoverUrl(exercise.id)}
                alt={`Portada táctica de ${exercise.nombre}`}
                className="h-full w-full object-contain"
                onError={() => setCoverAvailable(false)}
            />
        );
    }
    if (fallbackImageId) {
        return (
            <img
                src={imageUrl(fallbackImageId)}
                alt={`Imagen de ${exercise.nombre}`}
                className="h-full w-full object-contain"
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
    const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
    const [showCreator, setShowCreator] = useState(false);
    const mobileFiltersButtonRef = useRef<HTMLButtonElement>(null);
    const mobileFiltersCloseButtonRef = useRef<HTMLButtonElement>(null);

    const activeFilterCount = countActiveExerciseFilters(filters);
    const filtersLabel = activeFilterCount > 0 ? `Filtros (${activeFilterCount})` : 'Filtros';

    const closeMobileFilters = () => {
        setMobileFiltersOpen(false);
        window.requestAnimationFrame(() => mobileFiltersButtonRef.current?.focus());
    };

    useModalBehavior(onClose);
    useModalBehavior(closeMobileFilters, mobileFiltersOpen);

    useEffect(() => {
        if (!mobileFiltersOpen) return;
        const frame = window.requestAnimationFrame(() => mobileFiltersCloseButtonRef.current?.focus());
        return () => window.cancelAnimationFrame(frame);
    }, [mobileFiltersOpen]);

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

    const addCreatedExercise = (exercise: EjercicioDetail) => {
        setDraftIds(current => current.includes(exercise.id) ? current : [...current, exercise.id]);
        setDraftData(current => ({ ...current, [exercise.id]: exercise }));
    };

    return (
        <div
            className="fixed inset-0 z-[60] flex items-center justify-center overflow-x-hidden bg-slate-950/60 p-0 backdrop-blur-sm sm:p-6"
            onClick={event => { if (event.target === event.currentTarget) onClose(); }}
        >
            <div role="dialog" aria-modal="true" aria-label="Seleccionar ejercicios" className="flex h-[100dvh] max-h-[100dvh] min-w-0 w-full max-w-6xl flex-col overflow-hidden bg-white shadow-2xl sm:h-auto sm:max-h-[94dvh] sm:rounded-2xl" onClick={event => event.stopPropagation()}>
                <div className="flex shrink-0 items-center justify-between gap-4 border-b border-slate-200 px-4 py-3 sm:px-6 sm:py-4">
                    <div className="min-w-0">
                        <p className="hidden text-xs font-bold uppercase tracking-[0.16em] text-primary-700 sm:block">Biblioteca del club</p>
                        <h2 className="break-words text-lg font-bold leading-6 text-slate-950 sm:mt-1 sm:text-xl">Seleccionar ejercicios</h2>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                        <Button type="button" size="sm" onClick={() => setShowCreator(true)}><Plus className="h-4 w-4" />Crear</Button>
                        <button type="button" onClick={onClose} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 transition-colors hover:bg-slate-100 hover:text-slate-950" aria-label="Cerrar">
                            <X className="h-5 w-5" aria-hidden="true" />
                        </button>
                    </div>
                </div>

                <div className="grid h-0 min-h-0 min-w-0 flex-1 overflow-hidden md:grid-cols-[250px_minmax(0,1fr)]">
                    <aside
                        id="exercise-selector-filters"
                        role={mobileFiltersOpen ? 'dialog' : undefined}
                        aria-modal={mobileFiltersOpen ? 'true' : undefined}
                        aria-label={mobileFiltersOpen ? filtersLabel : undefined}
                        className={`${mobileFiltersOpen ? 'fixed inset-0 z-[70] flex items-center justify-center overflow-x-hidden p-3' : 'hidden'} min-w-0 md:static md:z-auto md:block md:min-h-0 md:overflow-x-hidden md:overflow-y-auto md:border-r md:border-slate-200 md:bg-slate-50 md:p-3`}
                    >
                        {mobileFiltersOpen && (
                            <button
                                type="button"
                                tabIndex={-1}
                                onClick={closeMobileFilters}
                                className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm md:hidden"
                                aria-label="Cerrar filtros"
                            />
                        )}
                        <div className={`${mobileFiltersOpen ? 'relative flex max-h-[calc(100dvh-1.5rem)] min-w-0 w-full max-w-sm flex-col overflow-hidden rounded-2xl bg-white shadow-2xl' : ''} md:block md:max-h-none md:w-auto md:max-w-none md:overflow-visible md:rounded-none md:bg-transparent md:shadow-none`}>
                            {mobileFiltersOpen && (
                                <div className="flex shrink-0 items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 md:hidden">
                                    <h3 className="break-words text-lg font-bold text-slate-950">{filtersLabel}</h3>
                                    <button
                                        ref={mobileFiltersCloseButtonRef}
                                        type="button"
                                        onClick={closeMobileFilters}
                                        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 transition-colors hover:bg-slate-100 hover:text-slate-950"
                                        aria-label="Cerrar filtros"
                                    >
                                        <X className="h-5 w-5" aria-hidden="true" />
                                    </button>
                                </div>
                            )}
                            <div className={`${mobileFiltersOpen ? 'min-h-0 overflow-x-hidden overflow-y-auto overscroll-contain p-3' : 'hidden'} md:block md:overflow-visible md:p-0 [&_h2]:hidden md:[&_h2]:flex`}>
                                <p className="hidden px-2 pb-2 text-xs font-bold uppercase tracking-wider text-slate-500 md:block">Filtros</p>
                                <SidebarFilters filters={filters} setFilters={setFilters} compact touchFriendly />
                            </div>
                            {mobileFiltersOpen && (
                                <div className="shrink-0 border-t border-slate-200 bg-slate-50 px-4 pb-[calc(0.75rem+env(safe-area-inset-bottom))] pt-3 md:hidden">
                                    <Button type="button" className="w-full" onClick={closeMobileFilters}>Ver resultados</Button>
                                </div>
                            )}
                        </div>
                    </aside>

                    <div className="min-w-0 overflow-x-hidden overflow-y-auto overscroll-contain p-3 pb-5 sm:p-4 sm:pb-5">
                        <div className="mb-3 flex items-center justify-between gap-3 sm:mb-4">
                            <div>
                                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Resultados</p>
                                <p className="mt-1 text-sm font-semibold text-slate-800">{data?.total || 0} ejercicios disponibles</p>
                            </div>
                            <button
                                ref={mobileFiltersButtonRef}
                                type="button"
                                onClick={() => setMobileFiltersOpen(true)}
                                className="flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-800 transition-colors hover:border-primary-400 hover:bg-primary-50 md:hidden"
                                aria-expanded={mobileFiltersOpen}
                                aria-controls="exercise-selector-filters"
                            >
                                <SlidersHorizontal className="h-4 w-4 text-primary-700" aria-hidden="true" />
                                {filtersLabel}
                            </button>
                            <Badge tone="green" className="hidden md:inline-flex"><Check className="mr-1 h-3.5 w-3.5" />Ejercicios seleccionados: {draftIds.length}</Badge>
                        </div>
                        {loading && !data ? (
                            <div className="flex h-48 items-center justify-center">
                                <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
                            </div>
                        ) : (
                            <>
                                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
                                    {data?.items.map(exercise => {
                                        const isSelected = draftIds.includes(exercise.id);
                                        return (
                                            <article key={exercise.id} className={`relative overflow-hidden rounded-xl border transition ${isSelected ? 'border-primary-600 bg-primary-50 shadow-sm ring-1 ring-primary-600' : 'border-slate-200 bg-white hover:border-primary-300'}`}>
                                                <button
                                                    type="button"
                                                    onClick={() => toggleExercise(exercise)}
                                                    aria-pressed={isSelected}
                                                    aria-label={`${isSelected ? 'Deseleccionar' : 'Seleccionar'} ${exercise.nombre}`}
                                                    className="group flex w-full text-left sm:block"
                                                >
                                                    <div className="relative h-32 w-28 shrink-0 overflow-hidden bg-primary-950 sm:h-36 sm:w-full">
                                                        <SelectorCover exercise={exercise} />
                                                        {isSelected && (
                                                            <span className="absolute bottom-2 right-2 flex h-8 w-8 items-center justify-center rounded-full bg-primary-700 text-white shadow sm:bottom-auto sm:right-3 sm:top-3 sm:h-auto sm:w-auto sm:gap-1 sm:px-2.5 sm:py-1 sm:text-[11px] sm:font-bold">
                                                                <Check className="h-4 w-4 sm:h-3.5 sm:w-3.5" /><span className="sr-only sm:not-sr-only">Seleccionado</span>
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className="min-w-0 flex-1 p-3">
                                                        <Badge tone="green" className="max-w-full truncate">{exercise.tipo.nombre}</Badge>
                                                        <p className="mt-2 line-clamp-2 min-h-10 text-sm font-bold leading-5 text-slate-950">{exercise.nombre}</p>
                                                        <p className="mt-1 truncate text-xs text-slate-500">{exercise.jugadores} jugadores · {exercise.espacio.descripcion_original} · {exercise.tiempo.descripcion_original}</p>
                                                        <span className={`mt-2.5 flex min-h-11 w-full items-center justify-center gap-1.5 rounded-xl border px-3 text-xs font-semibold ${isSelected ? 'border-primary-700 bg-primary-700 text-white' : 'border-slate-300 bg-white text-slate-700'}`}>
                                                            {isSelected && <Check className="h-3.5 w-3.5" />}
                                                            {isSelected ? 'Seleccionado' : 'Seleccionar'}
                                                        </span>
                                                    </div>
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => setPreviewId(exercise.id)}
                                                    className="flex min-h-11 w-full items-center justify-center gap-1.5 border-t border-slate-200 bg-white px-3 text-xs font-bold text-primary-700 hover:bg-primary-50 hover:text-primary-900"
                                                >
                                                    <Eye className="h-3.5 w-3.5" />Ver ficha completa
                                                </button>
                                            </article>
                                        );
                                    })}
                                </div>
                                {data && data.total_pages > 1 && (
                                    <div className="mt-4 flex items-center justify-center gap-3">
                                        <button type="button" onClick={() => setFilters(current => ({ ...current, page: current.page - 1 }))} disabled={data.page === 1} className="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-500" aria-label="Página anterior">
                                            <ChevronLeft className="h-4 w-4" />
                                        </button>
                                        <span className="text-sm font-semibold text-slate-700">Página {data.page} de {data.total_pages}</span>
                                        <button type="button" onClick={() => setFilters(current => ({ ...current, page: current.page + 1 }))} disabled={data.page === data.total_pages} className="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-500" aria-label="Página siguiente">
                                            <ChevronRight className="h-4 w-4" />
                                        </button>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>

                <div className="flex min-w-0 shrink-0 flex-col gap-2 border-t border-slate-200 bg-slate-50 px-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))] pt-2.5 sm:flex-row sm:items-center sm:justify-between sm:gap-3 sm:px-5 sm:py-3">
                    <span className="text-sm font-semibold text-slate-700">Ejercicios seleccionados: {draftIds.length}</span>
                    <div className="flex min-w-0 justify-end gap-2 sm:gap-3">
                        <Button type="button" variant="secondary" className="min-w-0 flex-1 sm:flex-none" onClick={onClose}>Cancelar</Button>
                        <Button type="button" className="min-w-0 flex-1 sm:flex-none" onClick={applySelection}><Check className="h-4 w-4" />Aplicar</Button>
                    </div>
                </div>
            </div>

            {previewId && <ExerciseDetail id={previewId} onClose={() => setPreviewId(null)} />}
            {showCreator && (
                <ExerciseCreator
                    onClose={() => setShowCreator(false)}
                    onExerciseReady={addCreatedExercise}
                />
            )}
        </div>
    );
};
