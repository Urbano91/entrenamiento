import React, { useEffect, useId, useRef, useState } from 'react';
import { api } from '../services/api';
import { taxonomyApi } from '../services/taxonomy';
import { ExerciseFilters, TipoTarea } from '../types/ejercicios';
import { CategoriaObjetivoV2, ObjetivoNormalizadoV2 } from '../types/taxonomy';
import { Check, ChevronDown, RotateCcw, SlidersHorizontal, X } from 'lucide-react';
import {
    filterObjectiveIdsByCategory,
    toggleObjectiveFilter,
} from '../utils/exerciseFilters';

interface FiltersProps {
    filters: ExerciseFilters;
    setFilters: React.Dispatch<React.SetStateAction<ExerciseFilters>>;
    compact?: boolean;
    showTitle?: boolean;
    touchFriendly?: boolean;
}

export const SidebarFilters: React.FC<FiltersProps> = ({
    filters,
    setFilters,
    compact = false,
    showTitle = true,
    touchFriendly = false,
}) => {
    const [tipos, setTipos] = useState<TipoTarea[]>([]);
    const [categorias, setCategorias] = useState<CategoriaObjetivoV2[]>([]);
    const [objetivos, setObjetivos] = useState<ObjetivoNormalizadoV2[]>([]);
    const [objectiveSearch, setObjectiveSearch] = useState('');
    const [objectivesOpen, setObjectivesOpen] = useState(false);
    const [taxonomyError, setTaxonomyError] = useState(false);
    const [taxonomyLoading, setTaxonomyLoading] = useState(true);
    const objectiveSearchId = useId();
    const objectiveListId = useId();
    const taxonomyErrorId = useId();
    const objectivesDropdownRef = useRef<HTMLDivElement>(null);
    const objectivesTriggerRef = useRef<HTMLButtonElement>(null);

    useEffect(() => {
        let active = true;
        const fetchCatalogs = async () => {
            try {
                const t = await api.get<TipoTarea[]>('/tipos');
                if (!active) return;
                setTipos(t);
            } catch {
                // Los catálogos históricos mantienen su comportamiento previo.
            }
        };
        const fetchTaxonomy = async () => {
            try {
                const taxonomy = await taxonomyApi.getCatalog();
                if (!active) return;
                setCategorias(taxonomy.categorias);
                setObjetivos(taxonomy.objetivos);
                setTaxonomyError(false);
            } catch {
                if (active) setTaxonomyError(true);
            } finally {
                if (active) setTaxonomyLoading(false);
            }
        };
        fetchCatalogs();
        fetchTaxonomy();
        return () => { active = false; };
    }, []);

    useEffect(() => {
        if (!objectivesOpen) return;

        const closeOnOutsideClick = (event: PointerEvent) => {
            if (!objectivesDropdownRef.current?.contains(event.target as Node)) {
                setObjectivesOpen(false);
            }
        };
        const closeOnEscape = (event: KeyboardEvent) => {
            if (event.key !== 'Escape') return;
            setObjectivesOpen(false);
            objectivesTriggerRef.current?.focus();
        };

        document.addEventListener('pointerdown', closeOnOutsideClick);
        document.addEventListener('keydown', closeOnEscape);
        return () => {
            document.removeEventListener('pointerdown', closeOnOutsideClick);
            document.removeEventListener('keydown', closeOnEscape);
        };
    }, [objectivesOpen]);

    const handleChange = (
        key: keyof ExerciseFilters,
        value: string | number | undefined,
    ) => {
        setFilters(prev => ({ ...prev, [key]: value, page: 1 }));
    };

    const handleCategoryChange = (value: string) => {
        const categoryId = value ? Number(value) : undefined;
        setObjectiveSearch('');
        setFilters(previous => {
            const selectedIds = previous.objetivo_v2_ids
                ?? (previous.objetivo_v2_id ? [previous.objetivo_v2_id] : []);
            const objectiveCategories = new Map(
                objetivos.map(objective => [objective.id, objective.categoria_id]),
            );
            return {
                ...previous,
                categoria_v2_id: categoryId,
                objetivo_v2_id: undefined,
                objetivo_v2_ids: filterObjectiveIdsByCategory(
                    selectedIds,
                    categoryId,
                    objectiveCategories,
                ),
                page: 1,
            };
        });
    };

    const selectedObjectiveIds = filters.objetivo_v2_ids
        ?? (filters.objetivo_v2_id ? [filters.objetivo_v2_id] : []);
    const selectedObjectives = objetivos.filter(objective => (
        selectedObjectiveIds.includes(objective.id)
    ));

    const handleObjectiveToggle = (objectiveId: number) => {
        setFilters(previous => {
            const currentIds = previous.objetivo_v2_ids
                ?? (previous.objetivo_v2_id ? [previous.objetivo_v2_id] : []);
            return {
                ...previous,
                objetivo_v2_id: undefined,
                objetivo_v2_ids: toggleObjectiveFilter(currentIds, objectiveId),
                page: 1,
            };
        });
    };

    const clearObjectiveSelection = () => {
        setFilters(previous => ({
            ...previous,
            objetivo_v2_id: undefined,
            objetivo_v2_ids: [],
            page: 1,
        }));
    };

    const clearFilters = () => {
        setFilters({
            page: 1,
            page_size: filters.page_size,
            scope: filters.scope,
        });
    };

    const controlClassName = `field-control ${touchFriendly ? 'min-h-11' : ''}`;
    const normalizeSearchValue = (value: string) => value
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLocaleLowerCase('es');
    const normalizedSearch = normalizeSearchValue(objectiveSearch.trim());
    const visibleObjectives = objetivos.filter(objective => {
        if (
            filters.categoria_v2_id !== undefined
            && objective.categoria_id !== filters.categoria_v2_id
        ) return false;
        return selectedObjectiveIds.includes(objective.id)
            || !normalizedSearch
            || normalizeSearchValue(objective.nombre).includes(normalizedSearch)
            || normalizeSearchValue(objective.categoria_nombre).includes(normalizedSearch)
            || normalizeSearchValue(objective.categoria_codigo).includes(normalizedSearch);
    });

    return (
        <div className={`bg-white ${compact ? 'p-2' : 'sticky top-24 rounded-2xl border border-slate-200 p-5 shadow-panel'} h-fit`}>
            {showTitle && (
                <h2 className={`mb-5 flex items-center gap-2 font-bold text-slate-950 ${compact ? 'text-base' : 'text-lg'}`}><SlidersHorizontal className="h-4 w-4 text-primary-700" />Filtros</h2>
            )}

            <div className="space-y-4">
                <div>
                    <label className="field-label">Buscar</label>
                    <input
                        type="text"
                        placeholder="Códigos, nombres..."
                        value={filters.q || ''}
                        onChange={(e) => handleChange('q', e.target.value)}
                        className={controlClassName}
                    />
                </div>

                <div>
                    <label className="field-label">Tipo de tarea</label>
                    <select
                        value={filters.tipo || ''}
                        onChange={(e) => handleChange('tipo', e.target.value)}
                        className={controlClassName}
                    >
                        <option value="">Todos</option>
                        {tipos.map(t => <option key={t.id} value={t.nombre}>{t.nombre}</option>)}
                    </select>
                </div>

                <div>
                    <label className="field-label">Jugadores</label>
                    <input
                        type="number"
                        min="1"
                        value={filters.jugadores || ''}
                        onChange={(e) => handleChange('jugadores', e.target.value)}
                        className={controlClassName}
                    />
                </div>

                <div>
                    <label className="field-label">Categoría</label>
                    <select
                        value={filters.categoria_v2_id ?? ''}
                        onChange={(e) => handleCategoryChange(e.target.value)}
                        className={controlClassName}
                        disabled={taxonomyLoading || taxonomyError}
                    >
                        <option value="">
                            {taxonomyLoading ? 'Cargando categorías…' : 'Todas las categorías'}
                        </option>
                        {categorias.map(category => (
                            <option key={category.id} value={category.id}>
                                {category.nombre}
                            </option>
                        ))}
                    </select>
                </div>

                <div ref={objectivesDropdownRef} className="relative">
                    <label className="field-label">Objetivos</label>
                    <button
                        ref={objectivesTriggerRef}
                        type="button"
                        onClick={() => setObjectivesOpen(open => !open)}
                        className={`${controlClassName} flex w-full items-center justify-between gap-2 text-left disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500`}
                        disabled={taxonomyLoading || taxonomyError}
                        aria-expanded={objectivesOpen}
                        aria-haspopup="listbox"
                        aria-controls={objectiveListId}
                        aria-describedby={taxonomyError ? taxonomyErrorId : undefined}
                    >
                        <span className="min-w-0 flex-1 truncate">
                            {taxonomyLoading
                                ? 'Cargando objetivos…'
                                : selectedObjectives.length === 0
                                ? 'Seleccionar objetivos'
                                : selectedObjectives.length === 1
                                ? selectedObjectives[0].nombre
                                : `${selectedObjectives.length} objetivos seleccionados`}
                        </span>
                        <ChevronDown
                            className={`h-4 w-4 shrink-0 text-slate-500 transition-transform ${objectivesOpen ? 'rotate-180' : ''}`}
                            aria-hidden="true"
                        />
                    </button>

                    {objectivesOpen && !taxonomyError && !taxonomyLoading && (
                        <div className={`${touchFriendly
                            ? 'relative mt-1.5'
                            : 'absolute left-0 right-0 top-full z-40 mt-1.5'
                        } overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl`}>
                            <div className="border-b border-slate-200 p-2">
                                <input
                                    id={objectiveSearchId}
                                    type="search"
                                    placeholder="Buscar objetivos…"
                                    value={objectiveSearch}
                                    onChange={(event) => setObjectiveSearch(event.target.value)}
                                    className={`${controlClassName} min-h-11`}
                                    autoFocus
                                />
                                <div className="mt-1 flex items-center justify-between gap-2 px-1">
                                    <span className="text-xs font-medium text-slate-500">
                                        {selectedObjectives.length} seleccionados
                                    </span>
                                    <button
                                        type="button"
                                        onClick={clearObjectiveSelection}
                                        disabled={selectedObjectives.length === 0}
                                        className="min-h-9 rounded-lg px-2 text-xs font-bold text-primary-700 hover:bg-primary-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 disabled:cursor-not-allowed disabled:text-slate-400"
                                    >
                                        Limpiar selección
                                    </button>
                                </div>
                            </div>

                            <div
                                id={objectiveListId}
                                className="max-h-64 overflow-x-hidden overflow-y-auto p-1"
                                role="listbox"
                                aria-label="Seleccionar objetivos"
                                aria-multiselectable="true"
                            >
                                {categorias.map(category => {
                                    const categoryObjectives = visibleObjectives.filter(
                                        objective => objective.categoria_id === category.id,
                                    );
                                    if (categoryObjectives.length === 0) return null;
                                    return (
                                        <div key={category.id} className="py-1">
                                            {filters.categoria_v2_id === undefined && (
                                                <p className="px-2 py-1 text-[11px] font-bold uppercase tracking-wide text-slate-500">
                                                    {category.nombre}
                                                </p>
                                            )}
                                            {categoryObjectives.map(objective => {
                                                const selected = selectedObjectiveIds.includes(objective.id);
                                                return (
                                                    <button
                                                        key={objective.id}
                                                        type="button"
                                                        role="option"
                                                        aria-selected={selected}
                                                        onClick={() => handleObjectiveToggle(objective.id)}
                                                        className={`flex min-h-11 w-full cursor-pointer items-center gap-2 rounded-lg px-2 py-2 text-left text-sm transition-colors ${selected
                                                            ? 'bg-primary-100 font-semibold text-primary-950'
                                                            : 'text-slate-700 hover:bg-slate-50'
                                                        }`}
                                                    >
                                                        <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border ${selected
                                                            ? 'border-primary-700 bg-primary-700 text-white'
                                                            : 'border-slate-400 bg-white'
                                                        }`} aria-hidden="true">
                                                            {selected && <Check className="h-3.5 w-3.5" />}
                                                        </span>
                                                        <span className="min-w-0 break-words">{objective.nombre}</span>
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    );
                                })}
                                {normalizedSearch && visibleObjectives.length === 0 && (
                                    <p className="px-3 py-4 text-center text-xs text-slate-500">
                                        No hay objetivos que coincidan.
                                    </p>
                                )}
                            </div>
                        </div>
                    )}

                    {selectedObjectives.length > 0 && (
                        <div className="mt-2 flex flex-wrap items-center gap-1.5" aria-label="Objetivos seleccionados">
                            {selectedObjectives.map(objective => (
                                <span
                                    key={objective.id}
                                    className="inline-flex min-w-0 items-center gap-1 rounded-lg bg-primary-100 py-1 pl-2.5 pr-1 text-xs font-semibold text-primary-900"
                                >
                                    <span className="break-words">{objective.nombre}</span>
                                    <button
                                        type="button"
                                        onClick={() => handleObjectiveToggle(objective.id)}
                                        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-primary-800 transition-colors hover:bg-primary-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-600"
                                        aria-label={`Quitar objetivo ${objective.nombre}`}
                                    >
                                        <X className="h-3.5 w-3.5" aria-hidden="true" />
                                    </button>
                                </span>
                            ))}
                            <button
                                type="button"
                                onClick={clearObjectiveSelection}
                                className="min-h-8 rounded-lg px-2 text-xs font-bold text-slate-600 hover:bg-slate-100 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-600"
                            >
                                Limpiar
                            </button>
                        </div>
                    )}
                    {taxonomyError && (
                        <p id={taxonomyErrorId} className="mt-1.5 text-xs font-medium text-red-700">
                            No se pudieron cargar los objetivos.
                        </p>
                    )}
                </div>

                <div className="pt-2">
                    <button
                        onClick={clearFilters}
                        className={`flex w-full items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-700 hover:bg-slate-100 hover:text-slate-950 ${touchFriendly ? 'min-h-11' : 'min-h-10'}`}
                    >
                        <RotateCcw className="h-4 w-4" />Limpiar filtros
                    </button>
                </div>
            </div>
        </div>
    );
};
