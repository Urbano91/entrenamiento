import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { AppLayout } from '../components/AppLayout';
import { SidebarFilters } from '../components/SidebarFilters';
import { ExerciseCard } from '../components/ExerciseCard';
import { ExerciseDetail } from '../components/ExerciseDetail';
import { Loader2, ChevronLeft, ChevronRight, BookOpen, SearchX } from 'lucide-react';
import { ExerciseFilters, PaginatedEjercicios } from '../types/ejercicios';
import { EmptyState, PageHeader, Surface } from '../components/ui';

export const Home: React.FC = () => {
    const [filters, setFilters] = useState<ExerciseFilters>({ page: 1, page_size: 20 });
    const [data, setData] = useState<PaginatedEjercicios | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedExercise, setSelectedExercise] = useState<number | null>(null);

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
    }, [filters]);

    const handlePageChange = (newPage: number) => {
        if (newPage < 1 || !data || newPage > data.total_pages) return;
        setFilters(f => ({ ...f, page: newPage }));
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    return (
        <AppLayout>
            <PageHeader
                eyebrow="Metodología"
                title="Biblioteca de ejercicios"
                description="Explora el catálogo técnico, filtra por objetivo y abre cada ficha para consultar su desarrollo completo."
                actions={<div className="flex items-center gap-2 rounded-xl bg-primary-100 px-3 py-2 text-sm font-bold text-primary-800"><BookOpen className="h-4 w-4" />{data?.total || 0} ejercicios</div>}
            />
            <div className="flex flex-col gap-6 lg:flex-row">
                {/* Sidebar Izquierdo */}
                <aside className="w-full shrink-0 lg:w-72">
                    <SidebarFilters filters={filters} setFilters={setFilters} />
                </aside>

                {/* Contenido Principal */}
                <section className="flex-grow">
                    {loading && !data ? (
                        <div className="flex h-64 items-center justify-center">
                            <Loader2 className="h-10 w-10 animate-spin text-primary-600" />
                        </div>
                    ) : (
                        <>
                            <div className="mb-4 flex items-center justify-between border-b border-slate-200 pb-3">
                                <h2 className="text-lg font-bold text-slate-950">
                                    Resultados <span className="ml-2 text-sm font-medium text-slate-500">{data?.total || 0} encontrados</span>
                                </h2>
                            </div>

                            {data?.items.length === 0 ? (
                                <Surface><EmptyState icon={SearchX} title="Sin resultados" description="Prueba a limpiar algún filtro o utiliza otros términos de búsqueda." /></Surface>
                            ) : (
                                <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
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
                                <div className="mt-8 flex items-center justify-center gap-3">
                                    <button
                                        onClick={() => handlePageChange(data.page - 1)}
                                        disabled={data.page === 1}
                                        className="rounded-xl border border-slate-300 bg-white p-2.5 text-slate-700 hover:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-500"
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
                                        className="rounded-xl border border-slate-300 bg-white p-2.5 text-slate-700 hover:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-500"
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

            {/* Modal de Detalle */}
            {selectedExercise && (
                <ExerciseDetail
                    id={selectedExercise}
                    onClose={() => setSelectedExercise(null)}
                />
            )}
        </AppLayout>
    );
};
