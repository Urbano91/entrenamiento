import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Dumbbell, Plus, Shield } from 'lucide-react';
import { api } from '../services/api';
import { AppLayout } from '../components/AppLayout';
import { ActionLink, Badge, EmptyState, PageHeader, Surface } from '../components/ui';
import { AgendaDia, Perfil } from '../types/fase2';
import { useAuth } from '../components/AuthContext';

const isoDate = (date: Date) => {
    const pad = (value: number) => String(value).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
};
const fromIso = (value: string) => new Date(`${value}T00:00:00`);

export const Dashboard: React.FC = () => {
    const { user } = useAuth();
    const today = useMemo(() => new Date(), []);
    const todayIso = isoDate(today);
    const [perfil, setPerfil] = useState<Perfil | null>(null);
    const [agenda, setAgenda] = useState<AgendaDia[]>([]);

    useEffect(() => {
        Promise.all([
            api.get<Perfil>('/perfil'),
            api.get<AgendaDia[]>('/planificaciones/agenda', { desde: todayIso, limite: 7 }),
        ]).then(([profile, upcomingDays]) => {
            setPerfil(profile);
            setAgenda(upcomingDays);
        }).catch(() => {
            setAgenda([]);
        });
    }, [todayIso]);

    const greeting = today.getHours() < 12 ? 'Buenos días' : today.getHours() < 20 ? 'Buenas tardes' : 'Buenas noches';

    return (
        <AppLayout>
            <div className="mb-5 overflow-hidden rounded-2xl bg-primary-950 text-white shadow-panel">
                <div className="relative px-5 py-5 sm:px-6 sm:py-6">
                    <div className="absolute -right-16 -top-24 h-64 w-64 rounded-full border-[40px] border-primary-800/40" />
                    <div className="relative flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                        <div>
                            <p className="text-sm font-semibold text-primary-300">Panel del cuerpo técnico</p>
                            <h1 className="mt-1.5 text-2xl font-bold tracking-tight sm:text-[28px]">
                                {greeting}, {perfil?.nombre || user?.usuario}
                            </h1>
                            <div className="mt-3 flex flex-wrap items-center gap-2">
                                {perfil?.club_actual && <Badge tone="green" className="bg-white/10 text-white ring-white/20">{perfil.club_actual}</Badge>}
                                <Badge tone="green" className="bg-white/10 text-white ring-white/20">
                                    Temporada {perfil?.temporada_actual?.nombre || 'sin asignar'}
                                </Badge>
                            </div>
                        </div>
                        <ActionLink to="/entrenamientos/nuevo" className="bg-primary-500 text-primary-950 hover:bg-primary-400">
                            <Plus className="h-5 w-5" />Nueva sesión
                        </ActionLink>
                    </div>
                </div>
            </div>

            <PageHeader
                title="Agenda"
            />

            <Surface className="overflow-hidden">
                {agenda.length === 0 ? (
                    <EmptyState
                        icon={Dumbbell}
                        title="Sin planificación próxima"
                        description="Crea una sesión o añade un partido para empezar a organizar la agenda."
                        action={<ActionLink to="/entrenamientos/nuevo" size="sm"><Plus className="h-4 w-4" />Crear sesión</ActionLink>}
                    />
                ) : (
                    <div className="divide-y divide-slate-200">
                        {agenda.map(day => (
                            <Link
                                key={day.fecha}
                                to={day.url_calendario}
                                className="group grid gap-3 p-3 transition hover:bg-slate-50 sm:grid-cols-[76px_minmax(0,1fr)_auto] sm:items-center sm:px-4 sm:py-3"
                            >
                                <div className="rounded-xl bg-primary-50 px-3 py-2 text-center ring-1 ring-inset ring-primary-100">
                                    <p className="text-xl font-bold text-primary-900">{fromIso(day.fecha).getDate()}</p>
                                    <p className="text-xs font-bold uppercase tracking-wider text-primary-700">
                                        {fromIso(day.fecha).toLocaleDateString('es-ES', { month: 'short' })}
                                    </p>
                                </div>
                                <div className="min-w-0">
                                    <div className="flex flex-col items-start gap-1 text-sm">
                                        {day.entrenamiento.cantidad > 0 && (
                                            <span className="flex items-center gap-2 rounded-lg bg-primary-100 px-2.5 py-1 font-semibold text-primary-900">
                                                <Dumbbell className="h-4 w-4" />Entrenamiento · {day.entrenamiento.sesiones} {day.entrenamiento.sesiones === 1 ? 'sesión' : 'sesiones'}{day.entrenamiento.duracion_total > 0 ? ` · ${day.entrenamiento.duracion_total} min` : ''}
                                            </span>
                                        )}
                                        {day.partidos.map(match => (
                                            <span key={match.id} className="flex items-center gap-2 rounded-lg bg-orange-100 px-2.5 py-1 font-semibold text-orange-950">
                                                <Shield className="h-4 w-4" />Partido · {match.hora || 'Sin hora'} vs {match.rival}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                                <span className="flex items-center gap-1 text-sm font-bold text-primary-700">Ver planificación<ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" /></span>
                            </Link>
                        ))}
                    </div>
                )}
            </Surface>
        </AppLayout>
    );
};
