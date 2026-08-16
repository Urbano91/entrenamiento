import React, { useEffect, useState } from 'react';
import { ArrowUpRight, CirclePlay, ImageIcon, Scaling, Timer, Users, Heart } from 'lucide-react';
import { api, exerciseCoverUrl, imageUrl } from '../services/api';
import { EjercicioDetail, EjercicioList } from '../types/ejercicios';
import { Badge } from './ui';
import { useToast } from '../utils/useToast';

interface CardProps {
    ejercicio: EjercicioList;
    onClick: () => void;
}

export const ExerciseCard: React.FC<CardProps> = ({ ejercicio, onClick }) => {
    const [imageId, setImageId] = useState<number | null>(null);
    const [isFavorite, setIsFavorite] = useState(ejercicio.is_favorite);
    const { success, error } = useToast();

    useEffect(() => { setIsFavorite(ejercicio.is_favorite); }, [ejercicio.is_favorite]);

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

    const toggleFavorite = async (e: React.MouseEvent) => {
        e.stopPropagation();
        const prev = isFavorite;
        setIsFavorite(!prev);
        try {
            if (prev) {
                await api.delete(`/ejercicios/${ejercicio.id}/favorito`);
                success('Eliminado de favoritos');
            } else {
                await api.post(`/ejercicios/${ejercicio.id}/favorito`, {});
                success('Añadido a favoritos');
            }
        } catch (err) {
            setIsFavorite(prev);
            error('No se pudo actualizar favoritos');
        }
    };

    return (
        <button
            type="button"
            onClick={onClick}
            className="group flex h-full w-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition hover:-translate-y-0.5 hover:border-primary-300 hover:shadow-panel"
        >
            <div className="relative h-36 w-full overflow-hidden bg-primary-950 sm:h-40">
                {ejercicio.tiene_portada ? (
                    <img
                        src={exerciseCoverUrl(ejercicio.id)}
                        alt={`Representación táctica de ${ejercicio.nombre}`}
                        className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]"
                    />
                ) : imageId ? (
                    <img src={imageUrl(imageId)} alt="" className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]" />
                ) : (
                    <div className="flex h-full flex-col items-center justify-center bg-gradient-to-br from-primary-900 to-primary-700 text-primary-200">
                        <ImageIcon className="h-8 w-8" />
                        <span className="mt-2 text-xs font-semibold">Ficha de ejercicio</span>
                    </div>
                )}
                <button type="button" onClick={toggleFavorite} className="absolute right-12 top-3 flex h-8 w-8 items-center justify-center rounded-lg bg-white shadow-sm transition hover:scale-105 active:scale-95" aria-label={isFavorite ? "Quitar de favoritos" : "Añadir a favoritos"}><Heart className={`h-4 w-4 transition-colors ${isFavorite ? 'fill-red-500 text-red-500' : 'text-slate-400 hover:text-slate-600'}`} /></button>
                <span className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-lg bg-white text-primary-800 shadow-sm"><ArrowUpRight className="h-4 w-4" /></span>
                {ejercicio.tiene_animacion && (
                    <span className="absolute bottom-3 left-3 flex items-center gap-1.5 rounded-lg bg-primary-950/90 px-2.5 py-1.5 text-xs font-bold text-white shadow-sm backdrop-blur">
                        <CirclePlay className="h-4 w-4 text-primary-300" /> Ver movimiento
                    </span>
                )}
            </div>

            <div className="flex flex-1 flex-col p-3 sm:p-4">
                <Badge tone="green" className="max-w-full w-fit break-words">{ejercicio.tipo.nombre}</Badge>
                <h3 className="mt-2 break-words text-base font-bold leading-5 text-slate-950 [overflow-wrap:anywhere] group-hover:text-primary-800">{ejercicio.nombre}</h3>

                <div className="mt-3 grid grid-cols-2 gap-x-2 gap-y-1.5 border-t border-slate-100 pt-3 text-xs font-normal leading-5 text-slate-600">
                    <span className="order-1 flex min-w-0 items-start gap-1.5"><Users className="h-4 w-4 shrink-0 text-slate-400" /><span className="break-words [overflow-wrap:anywhere]">{ejercicio.jugadores} jug.</span></span>
                    <span className="order-3 col-span-2 flex min-w-0 items-start gap-1.5"><Scaling className="h-4 w-4 shrink-0 text-slate-400" /><span className="break-words [overflow-wrap:anywhere]">{ejercicio.espacio.descripcion_original}</span></span>
                    <span className="order-2 flex min-w-0 items-start gap-1.5"><Timer className="h-4 w-4 shrink-0 text-slate-400" /><span className="break-words [overflow-wrap:anywhere]">{ejercicio.tiempo.descripcion_original}</span></span>
                </div>
            </div>
        </button>
    );
};
