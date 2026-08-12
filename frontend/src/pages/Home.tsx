import React, { useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import { AppLayout } from '../components/AppLayout';
import { SidebarFilters } from '../components/SidebarFilters';
import { ExerciseCard } from '../components/ExerciseCard';
import { ExerciseDetail } from '../components/ExerciseDetail';
import { Loader2, ChevronLeft, ChevronRight, BookOpen, Plus, SearchX, SlidersHorizontal, UserRound } from 'lucide-react';
import { EjercicioDetail, ExerciseFilters, PaginatedEjercicios } from '../types/ejercicios';
import { Button, EmptyState, Modal, PageHeader, Surface } from '../components/ui';
import { countActiveExerciseFilters } from '../utils/exerciseFilters';
import { ExerciseCreator } from '../components/ExerciseCreator';

export const Home: React.FC = () => {
    const [filters, setFilters] = useState<ExerciseFilters>({ page: 1, page_size: 20, scope: 'official' });
    const [data, setData] = useState<PaginatedEjercicios | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedExercise, setSelectedExercise] = useState<number | null>(null);
    const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
    const [creatorOpen, setCreatorOpen] = useState(false);
    const [editingExercise, setEditingExercise] = useState<EjercicioDetail | null>(null);
    const [refreshKey, setRefreshKey] = useState(0);
    const mobileFiltersButtonRef = useRef<HTMLButtonElement>(null);

    const activeFilterCount = countActiveExerciseFilters(filters);
    const filtersLabel = activeFilterCount > 0 ? `Filtros (${activeFilterCount})` : 'Filtros';

    useEffect(() => {
        const fetchEjercicios = async () => {
            setLoading(true);
            try {
                const res = await api.get<PaginatedEjercicios>('/ejercicios', filters);
                setData(res);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        const timer = setTimeout(fetchEjercicios, 300); // debounce
        return () => clearTimeout(timer);
    }, [filters, refreshKey]);

    const changeScope = (scope: 'official' | 'private') => {
        setFilters(current => ({ ...current, scope, page: 1 }));
    };

    const exerciseSaved = (exercise: EjercicioDetail) => {
        setCreatorOpen(false);
        setEditingExercise(null);
        setFilters(current => ({ ...current, scope: 'private', page: 1 }));
        setSelectedExercise(exercise.id);
        setRefreshKey(value => value + 1);
    };

    const handlePageChange = (newPage: number) => {
        if (newPage < 1 || !data || newPage > data.total_pages) return;
        setFilters(f => ({ ...f, page: newPage }));
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const closeMobileFilters = () => {
        setMobileFiltersOpen(false);
        window.requestAnimationFrame(() => mobileFiltersButtonRef.current?.focus());
    };

    return (
        <AppLayout>
            <PageHeader
                title="Biblioteca de ejercicios"
                actions={<Button type="button" onClick={() => setCreatorOpen(true)}><Plus className="h-4 w-4" />Crear ejercicio</Button>}
            />
            <div className="mb-4 grid grid-cols-2 gap-3">
                <button type="button" onClick={() => changeScope('official')} className={`rounded-2xl border p-4 text-left transition ${filters.scope === 'official' ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-200' : 'border-slate-200 bg-white hover:border-primary-300'}`}><BookOpen className="h-5 w-5 text-primary-700" /><span className="mt-2 block font-bold text-slate-950">Ejercicios oficiales</span><span className="text-sm text-slate-600">{data?.official_total ?? 114}</span></button>
                <button type="button" onClick={() => changeScope('private')} className={`rounded-2xl border p-4 text-left transition ${filters.scope === 'private' ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-200' : 'border-slate-200 bg-white hover:border-primary-300'}`}><UserRound className="h-5 w-5 text-primary-700" /><span className="mt-2 block font-bold text-slate-950">Mis ejercicios</span><span className="text-sm text-slate-600">{data?.my_total ?? 0}</span></button>
            </div>
            <button
                ref={mobileFiltersButtonRef}
                type="button"
                onClick={() => setMobileFiltersOpen(true)}
                className="mb-4 flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 shadow-sm transition-colors hover:border-primary-400 hover:bg-primary-50 lg:hidden"
                aria-expanded={mobileFiltersOpen}
                aria-controls="mobile-exercise-filters"
            >
                <SlidersHorizontal className="h-4 w-4 text-primary-700" aria-hidden="true" />
                {filtersLabel}
            </button>
            <div className="flex flex-col gap-5 lg:flex-row">
                {/* Sidebar Izquierdo */}
                <aside className="hidden w-72 shrink-0 lg:block">
                    <SidebarFilters filters={filters} setFilters={setFilters} />
                </aside>

                {/* Contenido Principal */}
                <section className="min-w-0 flex-grow">
                    {loading && !data ? (
                        <div className="flex h-64 items-center justify-center">
                            <Loader2 className="h-10 w-10 animate-spin text-primary-600" />
                        </div>
                    ) : (
                        <>
                            <div className="mb-3 flex items-center justify-between border-b border-slate-200 pb-2">
                                <h2 className="text-lg font-bold text-slate-950">
                                    Resultados <span className="ml-2 text-sm font-medium text-slate-500">{data?.total || 0} encontrados</span>
                                </h2>
                            </div>

                            {data?.items.length === 0 ? (
                                <Surface><EmptyState icon={SearchX} title="Sin resultados" description="Prueba a limpiar algún filtro o utiliza otros términos de búsqueda." /></Surface>
                            ) : (
                                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
                                    {data?.items.map(ej => (
                                        <ExerciseCard
                                            key={ej.id}
                                            ejercicio={ej}
                                            onClick={() => setSelectedExercise(ej.id)}
                                        />
                                    ))}
                                </div>
                            )}

                            {/* Paginación */}
                            {data && data.total_pages > 1 && (
                                <div className="mt-6 flex items-center justify-center gap-3">
                                    <button
                                        onClick={() => handlePageChange(data.page - 1)}
                                        disabled={data.page === 1}
                                        className="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-500"
                                        aria-label="Página anterior"
                                    >
                                        <ChevronLeft className="w-5 h-5" />
                                    </button>
                                    <span className="text-sm font-semibold text-slate-700">
                                        Página {data.page} de {data.total_pages}
                                    </span>
                                    <button
                                        onClick={() => handlePageChange(data.page + 1)}
                                        disabled={data.page === data.total_pages}
                                        className="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-500"
                                        aria-label="Página siguiente"
                                    >
                                        <ChevronRight className="w-5 h-5" />
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </section>
            </div>

            {mobileFiltersOpen && (
                <Modal
                    title={filtersLabel}
                    description="Ajusta los criterios para encontrar ejercicios."
                    onClose={closeMobileFilters}
                    size="sm"
                    footer={(
                        <div className="pb-[env(safe-area-inset-bottom)]">
                            <Button type="button" className="w-full" onClick={closeMobileFilters}>
                                Ver resultados
                            </Button>
                        </div>
                    )}
                >
                    <div id="mobile-exercise-filters">
                        <SidebarFilters
                            filters={filters}
                            setFilters={setFilters}
                            compact
                            showTitle={false}
                            touchFriendly
                        />
                    </div>
                </Modal>
            )}

            {/* Modal de Detalle */}
            {selectedExercise && (
                <ExerciseDetail
                    id={selectedExercise}
                    onClose={() => setSelectedExercise(null)}
                    onEdit={exercise => { setSelectedExercise(null); setEditingExercise(exercise); }}
                    onDeleted={() => setRefreshKey(value => value + 1)}
                />
            )}
            {(creatorOpen || editingExercise) && (
                <ExerciseCreator
                    exerciseId={editingExercise?.id}
                    onClose={() => { setCreatorOpen(false); setEditingExercise(null); }}
                    onExerciseReady={exerciseSaved}
                />
            )}
        </AppLayout>
    );
};
