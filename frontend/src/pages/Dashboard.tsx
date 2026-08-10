import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
    ArrowRight, CalendarCheck, CalendarDays, Clock3, Dumbbell,
    LibraryBig, Plus, Shield,
} from 'lucide-react';
import { api } from '../services/api';
import { AppLayout } from '../components/AppLayout';
import { ActionLink, Badge, EmptyState, PageHeader, Surface } from '../components/ui';
import { AgendaDia, EntrenamientoList, Perfil } from '../types/fase2';
import { PaginatedEjercicios } from '../types/ejercicios';
import { useAuth } from '../components/AuthContext';

const isoDate = (date: Date) => {
    const pad = (value: number) => String(value).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
};
const fromIso = (value: string) => new Date(`${value}T00:00:00`);

interface StatProps {
    label: string;
    value: string | number;
    detail: string;
    icon: React.ComponentType<{ className?: string }>;
    tone: string;
}

const StatCard: React.FC<StatProps> = ({ label, value, detail, icon: Icon, tone }) => (
    <Surface className="p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3">
            <div>
                <p className="text-sm font-semibold text-slate-600">{label}</p>
                <p className="mt-2 text-2xl font-bold tracking-tight text-slate-950">{value}</p>
                <p className="mt-1 text-xs font-medium text-slate-500">{detail}</p>
            </div>
            <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${tone}`}>
                <Icon className="h-5 w-5" />
            </span>
        </div>
    </Surface>
);

export const Dashboard: React.FC = () => {
    const { user } = useAuth();
    const today = useMemo(() => new Date(), []);
    const todayIso = isoDate(today);
    const [perfil, setPerfil] = useState<Perfil | null>(null);
    const [trainings, setTrainings] = useState<EntrenamientoList[]>([]);
    const [agenda, setAgenda] = useState<AgendaDia[]>([]);
    const [exerciseCount, setExerciseCount] = useState(0);

    useEffect(() => {
        Promise.all([
            api.get<Perfil>('/perfil'),
            api.get<EntrenamientoList[]>('/entrenamientos'),
            api.get<PaginatedEjercicios>('/ejercicios', { page: 1, page_size: 1 }),
            api.get<AgendaDia[]>('/planificaciones/agenda', { desde: todayIso, limite: 4 }),
        ]).then(([profile, sessions, exercises, upcomingDays]) => {
            setPerfil(profile);
            setTrainings(sessions);
            setExerciseCount(exercises.total);
            setAgenda(upcomingDays);
        }).catch(() => {
            setTrainings([]);
            setAgenda([]);
        });
    }, [todayIso]);

    const weekStart = useMemo(() => {
        const result = new Date(today);
        result.setDate(result.getDate() - (result.getDay() === 0 ? 6 : result.getDay() - 1));
        result.setHours(0, 0, 0, 0);
        return result;
    }, [today]);
    const weekEnd = useMemo(() => {
        const result = new Date(weekStart);
        result.setDate(result.getDate() + 6);
        return result;
    }, [weekStart]);

    const weekTrainings = trainings.filter(training => {
        const date = fromIso(training.fecha);
        return date >= weekStart && date <= weekEnd;
    });
    const monthTrainings = trainings.filter(training => {
        const date = fromIso(training.fecha);
        return date.getFullYear() === today.getFullYear() && date.getMonth() === today.getMonth();
    });
    const weekPlannedTrainings = new Set(
        weekTrainings.map(training => training.fecha)
    ).size;
    const nextPlannedTraining = agenda.find(day => day.entrenamiento.cantidad > 0);
    const greeting = today.getHours() < 12 ? 'Buenos días' : today.getHours() < 20 ? 'Buenas tardes' : 'Buenas noches';

    return (
        <AppLayout>
            <div className="mb-7 overflow-hidden rounded-3xl bg-primary-950 text-white shadow-panel">
                <div className="relative px-6 py-7 sm:px-8 sm:py-9">
                    <div className="absolute -right-16 -top-24 h-64 w-64 rounded-full border-[40px] border-primary-800/40" />
                    <div className="relative flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
                        <div>
                            <p className="text-sm font-semibold text-primary-300">Panel del cuerpo técnico</p>
                            <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
                                {greeting}, {perfil?.nombre || user?.usuario}
                            </h1>
                            <div className="mt-4 flex flex-wrap items-center gap-2">
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

            <div className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard label="Esta semana" value={weekPlannedTrainings} detail={weekPlannedTrainings === 1 ? 'entrenamiento planificado' : 'entrenamientos planificados'} icon={CalendarCheck} tone="bg-primary-100 text-primary-800" />
                <StatCard
                    label="Próximo entrenamiento"
                    value={nextPlannedTraining ? fromIso(nextPlannedTraining.fecha).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' }) : '—'}
                    detail={nextPlannedTraining ? `${nextPlannedTraining.entrenamiento.sesiones} ${nextPlannedTraining.entrenamiento.sesiones === 1 ? 'sesión' : 'sesiones'}` : 'Sin sesiones próximas'}
                    icon={Clock3}
                    tone="bg-blue-100 text-blue-700"
                />
                <StatCard label="Ejercicios disponibles" value={exerciseCount} detail="en la biblioteca del club" icon={LibraryBig} tone="bg-violet-100 text-violet-700" />
                <StatCard label="Este mes" value={monthTrainings.length} detail="sesiones en calendario" icon={CalendarDays} tone="bg-amber-100 text-amber-800" />
            </div>

            <PageHeader
                eyebrow="Agenda"
                title="Próximos días"
                description="La planificación deportiva agrupada por fecha, sin repetir sesiones del mismo día."
                actions={<ActionLink to="/calendario" variant="secondary" size="sm"><CalendarDays className="h-4 w-4" />Abrir calendario</ActionLink>}
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
                                className="group grid gap-4 p-4 transition hover:bg-slate-50 sm:grid-cols-[90px_minmax(0,1fr)_auto] sm:items-center sm:px-6 sm:py-5"
                            >
                                <div className="rounded-xl bg-primary-50 px-3 py-2 text-center ring-1 ring-inset ring-primary-100">
                                    <p className="text-2xl font-bold text-primary-900">{fromIso(day.fecha).getDate()}</p>
                                    <p className="text-xs font-bold uppercase tracking-wider text-primary-700">
                                        {fromIso(day.fecha).toLocaleDateString('es-ES', { month: 'short' })}
                                    </p>
                                </div>
                                <div className="min-w-0">
                                    <h3 className="text-base font-bold capitalize text-slate-950 group-hover:text-primary-800">
                                        {fromIso(day.fecha).toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}
                                    </h3>
                                    <div className="mt-2 flex flex-col items-start gap-1.5 text-sm">
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
