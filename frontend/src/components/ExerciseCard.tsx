import React, { useEffect, useState } from 'react';
import { ArrowUpRight, CirclePlay, Flag, ImageIcon, Scaling, Timer, Users } from 'lucide-react';
import { api } from '../services/api';
import { EjercicioDetail, EjercicioList } from '../types/ejercicios';
import { Badge } from './ui';

interface CardProps {
    ejercicio: EjercicioList;
    onClick: () => void;
}

export const ExerciseCard: React.FC<CardProps> = ({ ejercicio, onClick }) => {
    const [imageId, setImageId] = useState<number | null>(null);

    useEffect(() => {
        if (ejercicio.tiene_portada) {
            setImageId(null);
            return;
        }
        let active = true;
        api.get<EjercicioDetail>(`/ejercicios/${ejercicio.id}`)
            .then(detail => {
                if (active) setImageId(detail.imagenes_asociadas[0]?.imagen.id || null);
            })
            .catch(() => undefined);
        return () => { active = false; };
    }, [ejercicio.id, ejercicio.tiene_portada]);

    return (
        <button
            type="button"
            onClick={onClick}
            className="group flex h-full w-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-panel transition hover:-translate-y-0.5 hover:border-primary-300 hover:shadow-lg"
        >
            <div className="relative h-40 w-full overflow-hidden bg-primary-950">
                {ejercicio.tiene_portada ? (
                    <img
                        src={`http://localhost:8000/api/ejercicios/${ejercicio.id}/portada`}
                        alt={`Representación táctica de ${ejercicio.nombre}`}
                        className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]"
                    />
                ) : imageId ? (
                    <img src={`http://localhost:8000/api/imagenes/${imageId}`} alt="" className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]" />
                ) : (
                    <div className="flex h-full flex-col items-center justify-center bg-gradient-to-br from-primary-900 to-primary-700 text-primary-200">
                        <ImageIcon className="h-8 w-8" />
                        <span className="mt-2 text-xs font-semibold">Ficha de ejercicio</span>
                    </div>
                )}
                <span className="absolute left-3 top-3 rounded-lg bg-slate-950/80 px-2 py-1 font-mono text-xs font-bold text-white backdrop-blur">{ejercicio.codigo}</span>
                <span className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-lg bg-white text-primary-800 shadow-sm"><ArrowUpRight className="h-4 w-4" /></span>
                {ejercicio.tiene_animacion && (
                    <span className="absolute bottom-3 left-3 flex items-center gap-1.5 rounded-lg bg-primary-950/90 px-2.5 py-1.5 text-xs font-bold text-white shadow-sm backdrop-blur">
                        <CirclePlay className="h-4 w-4 text-primary-300" /> Ver movimiento
                    </span>
                )}
            </div>

            <div className="flex flex-1 flex-col p-4">
                <Badge tone="green" className="w-fit">{ejercicio.tipo.nombre}</Badge>
                <h3 className="mt-3 line-clamp-2 text-base font-bold leading-6 text-slate-950 group-hover:text-primary-800">{ejercicio.nombre}</h3>

                <div className="mt-4 grid grid-cols-2 gap-2 border-t border-slate-100 pt-4 text-xs font-medium text-slate-600">
                    <span className="flex items-center gap-1.5"><Users className="h-4 w-4 text-slate-400" />{ejercicio.jugadores} jug.</span>
                    <span className="flex min-w-0 items-center gap-1.5"><Scaling className="h-4 w-4 shrink-0 text-slate-400" /><span className="truncate">{ejercicio.espacio.descripcion_original}</span></span>
                    <span className="flex min-w-0 items-center gap-1.5"><Timer className="h-4 w-4 shrink-0 text-slate-400" /><span className="truncate">{ejercicio.tiempo.descripcion_original}</span></span>
                    {ejercicio.objetivo_1_normalizado && <span className="flex min-w-0 items-center gap-1.5"><Flag className="h-4 w-4 shrink-0 text-slate-400" /><span className="truncate">{ejercicio.objetivo_1_normalizado}</span></span>}
                </div>
            </div>
        </button>
    );
};
