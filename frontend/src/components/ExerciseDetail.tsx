import React, { useEffect, useState } from 'react';
import { api, API_ORIGIN } from '../services/api';
import { X, Loader2, CirclePlay } from 'lucide-react';
import { EjercicioDetail } from '../types/ejercicios';

interface Props {
    id: number;
    onClose: () => void;
}

export const ExerciseDetail: React.FC<Props> = ({ id, onClose }) => {
    const [ejercicio, setEjercicio] = useState<EjercicioDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [animationError, setAnimationError] = useState(false);
    const [showAnimation, setShowAnimation] = useState(false);

    useEffect(() => {
        const fetchDetail = async () => {
            setAnimationError(false);
            setShowAnimation(false);
            try {
                const data = await api.get<EjercicioDetail>(`/ejercicios/${id}`);
                setEjercicio(data);
            } catch (err: unknown) {
                setError(err instanceof Error ? err.message : 'Error al cargar detalle');
            } finally {
                setLoading(false);
            }
        };
        fetchDetail();
    }, [id]);

    if (loading) {
        return (
            <div className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/60 backdrop-blur-sm">
                <Loader2 className="w-8 h-8 text-white animate-spin" />
            </div>
        );
    }

    if (error || !ejercicio) return null;

    // Agrupar objetivos por tipo
    const objetivosPorTipo: Record<string, string[]> = {};
    if (ejercicio.objetivos_asociados) {
        ejercicio.objetivos_asociados.forEach(obj => {
            if (!objetivosPorTipo[obj.tipo_objetivo]) objetivosPorTipo[obj.tipo_objetivo] = [];
            objetivosPorTipo[obj.tipo_objetivo].push(obj.objetivo.nombre_normalizado);
        });
    }

    return (
        <div className="fixed inset-0 z-[70] flex justify-center overflow-y-auto bg-slate-950/70 p-3 backdrop-blur-sm sm:p-6" onClick={onClose}>
            <div
                role="dialog"
                aria-modal="true"
                aria-label={ejercicio.nombre}
                className="my-auto flex max-h-[94vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
                onClick={e => e.stopPropagation()}
            >
                {/* Cabecera modal */}
                <div className="flex shrink-0 items-center justify-between bg-primary-950 px-5 py-5 text-white sm:px-7">
                    <div>
                        <span className="font-mono text-xs font-bold uppercase tracking-wider text-primary-300">{ejercicio.codigo} · {ejercicio.tipo.nombre}</span>
                        <h2 className="mt-1 text-xl font-bold sm:text-2xl">{ejercicio.nombre}</h2>
                    </div>
                    <button onClick={onClose} className="rounded-xl border border-white/20 bg-white/10 p-2 text-white hover:bg-white/20" aria-label="Cerrar ficha">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Contenido scrolleable */}
                <div className="flex w-full flex-col gap-8 overflow-y-auto p-5 text-slate-800 sm:p-7">

                    {/* INFO BASICA */}
                    <div className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl bg-slate-200 ring-1 ring-slate-200 sm:grid-cols-4">
                        <div className="bg-slate-50 p-4"><strong className="block text-xs uppercase tracking-wider text-slate-500">Tipo</strong><span className="mt-1 block font-semibold">{ejercicio.tipo.nombre}</span></div>
                        <div className="bg-slate-50 p-4"><strong className="block text-xs uppercase tracking-wider text-slate-500">Jugadores</strong><span className="mt-1 block font-semibold">{ejercicio.jugadores}</span></div>
                        <div className="bg-slate-50 p-4"><strong className="block text-xs uppercase tracking-wider text-slate-500">Espacio</strong><span className="mt-1 block font-semibold">{ejercicio.espacio.descripcion_original}</span></div>
                        <div className="bg-slate-50 p-4"><strong className="block text-xs uppercase tracking-wider text-slate-500">Tiempo</strong><span className="mt-1 block font-semibold">{ejercicio.tiempo.descripcion_original}</span></div>
                    </div>

                    {/* OBJETIVOS */}
                    {Object.keys(objetivosPorTipo).length > 0 && (
                        <section>
                            <h3 className="mb-4 border-b border-slate-200 pb-2 text-lg font-bold text-slate-950">Objetivos</h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                {Object.entries(objetivosPorTipo).map(([tipo, objs]) => (
                                    <div key={tipo}>
                                        <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-primary-700">{tipo}</h4>
                                        <ul className="list-disc list-inside text-sm text-slate-700">
                                            {objs.map((o, i) => <li key={i}>{o}</li>)}
                                        </ul>
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* DESARROLLO */}
                    {ejercicio.desarrollo && (
                        <section>
                            <h3 className="mb-4 border-b border-slate-200 pb-2 text-lg font-bold text-slate-950">Desarrollo</h3>
                            <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700 font-medium">
                                {ejercicio.desarrollo}
                            </p>
                        </section>
                    )}

                    {/* MATERIAL */}
                    {ejercicio.materiales_asociados && ejercicio.materiales_asociados.length > 0 && (
                        <section>
                            <h3 className="mb-4 border-b border-slate-200 pb-2 text-lg font-bold text-slate-950">Material</h3>
                            <div className="flex flex-wrap gap-2">
                                {ejercicio.materiales_asociados.map((m, idx) => (
                                    <span key={idx} className="bg-amber-50 text-amber-800 text-xs px-2.5 py-1 rounded-full border border-amber-200">
                                        {m.material.nombre_normalizado}
                                    </span>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* REPRESENTACION ORIGINAL DEL PILOTO */}
                    {ejercicio.tiene_portada && (
                        <section className="order-first">
                            <h3 className="mb-4 flex items-center gap-2 border-b border-slate-200 pb-2 text-lg font-bold text-slate-950">
                                <CirclePlay className="h-5 w-5 text-primary-700" /> Representación táctica
                            </h3>
                            {showAnimation && ejercicio.tiene_animacion ? (
                                <video
                                    autoPlay
                                    controls
                                    loop
                                    preload="metadata"
                                    poster={`${API_ORIGIN}/api/ejercicios/${ejercicio.id}/portada`}
                                    onError={() => {
                                        setAnimationError(true);
                                        setShowAnimation(false);
                                    }}
                                    className="aspect-video w-full rounded-2xl border border-slate-200 bg-primary-950 object-contain shadow-panel"
                                    aria-label={`Animación táctica de ${ejercicio.nombre}`}
                                >
                                    <source src={`${API_ORIGIN}/api/ejercicios/${ejercicio.id}/animacion`} type="video/webm" />
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
                                        src={`${API_ORIGIN}/api/ejercicios/${ejercicio.id}/portada`}
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
                                    src={`${API_ORIGIN}/api/ejercicios/${ejercicio.id}/portada`}
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
                            <h3 className="mb-4 border-b border-slate-200 pb-2 text-lg font-bold text-slate-950">Imágenes</h3>
                            <div className="grid gap-5 lg:grid-cols-2">
                                {ejercicio.imagenes_asociadas.map(img => (
                                    <img
                                        key={img.orden}
                                        src={`http://localhost:8000/api/imagenes/${img.imagen.id}`}
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
