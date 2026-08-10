import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Espacio, ExerciseFilters, Objetivo, Tiempo, TipoTarea } from '../types/ejercicios';
import { RotateCcw, SlidersHorizontal } from 'lucide-react';

interface FiltersProps {
    filters: ExerciseFilters;
    setFilters: React.Dispatch<React.SetStateAction<ExerciseFilters>>;
    compact?: boolean;
}

export const SidebarFilters: React.FC<FiltersProps> = ({ filters, setFilters, compact = false }) => {
    const [tipos, setTipos] = useState<TipoTarea[]>([]);
    const [objetivos, setObjetivos] = useState<Objetivo[]>([]);
    const [espacios, setEspacios] = useState<Espacio[]>([]);
    const [tiempos, setTiempos] = useState<Tiempo[]>([]);

    useEffect(() => {
        const fetchCatalogs = async () => {
            const [t, o, e, time] = await Promise.all([
                api.get<TipoTarea[]>('/tipos'),
                api.get<Objetivo[]>('/objetivos'),
                api.get<Espacio[]>('/espacios'),
                api.get<Tiempo[]>('/tiempos')
            ]);
            setTipos(t);
            setObjetivos(o);
            setEspacios(e);
            setTiempos(time);
        };
        fetchCatalogs();
    }, []);

    const handleChange = (key: string, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value, page: 1 }));
    };

    const clearFilters = () => {
        setFilters({ page: 1, page_size: filters.page_size });
    };

    return (
        <div className={`bg-white ${compact ? 'p-2' : 'sticky top-24 rounded-2xl border border-slate-200 p-5 shadow-panel'} h-fit`}>
            <h2 className={`mb-5 flex items-center gap-2 font-bold text-slate-950 ${compact ? 'text-base' : 'text-lg'}`}><SlidersHorizontal className="h-4 w-4 text-primary-700" />Filtros</h2>

            <div className="space-y-4">
                <div>
                    <label className="field-label">Buscar</label>
                    <input
                        type="text"
                        placeholder="Códigos, nombres..."
                        value={filters.q || ''}
                        onChange={(e) => handleChange('q', e.target.value)}
                        className="field-control"
                    />
                </div>

                <div>
                    <label className="field-label">Tipo de tarea</label>
                    <select
                        value={filters.tipo || ''}
                        onChange={(e) => handleChange('tipo', e.target.value)}
                        className="field-control"
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
                        className="field-control"
                    />
                </div>

                <div>
                    <label className="field-label">Objetivo</label>
                    <select
                        value={filters.objetivo || ''}
                        onChange={(e) => handleChange('objetivo', e.target.value)}
                        className="field-control"
                    >
                        <option value="">Todos</option>
                        {objetivos.map(o => <option key={o.id} value={o.nombre_normalizado}>{o.nombre_normalizado}</option>)}
                    </select>
                </div>

                <div>
                    <label className="field-label">Espacio</label>
                    <select
                        value={filters.espacio || ''}
                        onChange={(e) => handleChange('espacio', e.target.value)}
                        className="field-control"
                    >
                        <option value="">Todos</option>
                        {espacios.map(e => <option key={e.id} value={e.descripcion_original}>{e.descripcion_original}</option>)}
                    </select>
                </div>

                <div>
                    <label className="field-label">Duración</label>
                    <select
                        value={filters.tiempo || ''}
                        onChange={(e) => handleChange('tiempo', e.target.value)}
                        className="field-control"
                    >
                        <option value="">Todos</option>
                        {tiempos.map(t => <option key={t.id} value={t.descripcion_original}>{t.descripcion_original}</option>)}
                    </select>
                </div>

                <div className="pt-2">
                    <button
                        onClick={clearFilters}
                        className="flex min-h-10 w-full items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-700 hover:bg-slate-100 hover:text-slate-950"
                    >
                        <RotateCcw className="h-4 w-4" />Limpiar filtros
                    </button>
                </div>
            </div>
        </div>
    );
};
