// Fase 2 types

export interface Temporada {
    id: number;
    nombre: string;
    fecha_inicio?: string;
    fecha_fin?: string;
    activa?: boolean;
}

export interface Perfil {
    id: number;
    usuario_id: number;
    nombre: string;
    apellidos: string;
    club_actual?: string;
    temporada_actual_id?: number;
    temporada_actual?: Temporada;
}

export interface EjercicioEnEntreno {
    id: number;       // relacion id
    ejercicio_id: number;
    orden: number;
    codigo: string;
    nombre: string;
    tipo: string;
    jugadores: number;
    espacio: string;
    tiempo: string;
    imagen_principal?: number;
    tiene_portada?: boolean;
}

export interface EntrenamientoList {
    id: number;
    temporada_id: number;
    fecha: string;
    hora?: string | null;
    nombre: string;
    duracion_minutos?: number;
    objetivo_principal?: string;
    num_ejercicios: number;
    created_at?: string;
    entrenador?: string | null;
    categoria?: string | null;
}

export interface EntrenamientoDetail {
    id: number;
    fecha: string;
    hora?: string | null;
    nombre: string;
    duracion_minutos?: number;
    objetivo_principal?: string;
    observaciones?: string;
    temporada_id: number;
    ejercicios: EjercicioEnEntreno[];
    created_at?: string;
    updated_at?: string;
}

export interface EntrenamientoCalendario {
    id: number;
    nombre: string;
    hora?: string | null;
    duracion_minutos?: number | null;
    num_ejercicios: number;
    objetivo_principal?: string | null;
}

export interface Partido {
    id: number;
    usuario_id?: number;
    temporada_id?: number | null;
    fecha: string;
    hora?: string | null;
    rival: string;
    local_visitante: 'local' | 'visitante';
    campo?: string | null;
    observaciones?: string | null;
    created_at?: string;
    updated_at?: string;
}

export interface PlanificacionDia {
    fecha: string;
    nota?: string | null;
    entrenamientos: EntrenamientoCalendario[];
    resumen_entrenamiento: {
        entrenamientos_planificados: number;
        sesiones: number;
        duracion_total: number;
        num_ejercicios_total: number;
    };
    partidos: Partido[];
}

export interface CalendarioResponse {
    year: number;
    month: number;
    num_days: number;
    temporada_id: number;
    dias: Record<string, EntrenamientoCalendario[]>;
    planificacion: Record<string, PlanificacionDia>;
}

export interface AgendaDia {
    fecha: string;
    entrenamiento: {
        cantidad: number;
        sesiones: number;
        duracion_total: number;
    };
    partidos: Array<{
        id: number;
        hora?: string | null;
        rival: string;
        local_visitante: 'local' | 'visitante';
    }>;
    url_calendario: string;
}

export interface DocumentoPlanificacion {
    id: number;
    planificacion_id: number;
    partido_id?: number | null;
    nombre_original: string;
    nombre_archivo: string;
    tipo_mime: string;
    tamano: number;
    fecha_subida: string;
    download_url: string;
}

export interface PlanificacionContexto {
    id?: number | null;
    fecha: string;
    nota?: string | null;
    documentos: DocumentoPlanificacion[];
}
