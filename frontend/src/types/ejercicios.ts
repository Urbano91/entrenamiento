export interface TipoTarea {
    id: number;
    nombre: string;
}

export interface Espacio {
    id: number;
    descripcion_original: string;
}

export interface Tiempo {
    id: number;
    descripcion_original: string;
}

export interface Objetivo {
    id: number;
    nombre_normalizado: string;
}

export interface Material {
    id: number;
    nombre_normalizado: string;
}

export interface Imagen {
    id: number;
    archivo: string;
    width?: number;
    height?: number;
}

export interface EjercicioList {
    id: number;
    numero: number;
    codigo: string;
    nombre: string;
    tipo_tarea_id: number;
    tipo: TipoTarea;
    jugadores: number;
    espacio: Espacio;
    tiempo: Tiempo;
    objetivo_1_normalizado?: string;
    tiene_portada: boolean;
    tiene_animacion: boolean;
    is_official: boolean;
    can_edit: boolean;
    created_by_user_id?: number;
    creator_display?: string;
    assignment_context?: string;
}

export interface EjercicioDetail extends EjercicioList {
    desarrollo?: string;
    objetivo_1_original?: string;
    objetivo_2_original?: string;
    objetivo_2_normalizado?: string;
    objetivos_asociados: Array<{
        tipo_objetivo: string;
        objetivo_original?: string;
        objetivo: Objetivo;
    }>;
    materiales_asociados: Array<{
        material_original?: string;
        material: Material;
    }>;
    imagenes_asociadas: Array<{
        orden: number;
        imagen: Imagen;
    }>;
}

export interface PaginatedEjercicios {
    items: EjercicioList[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    official_total: number;
    my_total: number;
}

export interface ExerciseFilters {
    [key: string]: string | number | boolean | number[] | null | undefined;
    page: number;
    page_size: number;
    q?: string;
    tipo?: string;
    jugadores?: string;
    categoria_v2_id?: number;
    objetivo_v2_ids?: number[];
    // Compatibilidad con consumidores que todavía envíen un único ID V2.
    objetivo_v2_id?: number;
    // Compatibilidad con consumidores que todavía utilicen el filtro histórico.
    objetivo?: string;
    espacio?: string;
    tiempo?: string;
    scope?: 'official' | 'private';
}

export interface EjercicioDraft {
    nombre: string;
    descripcion?: string;
    tipo_tarea_id: number;
    jugadores: number;
    espacio_id: number;
    tiempo_id: number;
    categoria_objetivo_id: number;
    objetivo_ids: number[];
    materiales: string[];
}

export interface SimilarExerciseCandidate {
    exercise_id?: number | null;
    name?: string | null;
    similarity: number | null;
    objectives: string[];
    description?: string | null;
    material: string[];
    players: number | null;
    space: string | null;
    duration: string | null;
    details_visible: boolean;
    private_match: boolean;
}

export interface SimilarExercisesResponse {
    candidates: SimilarExerciseCandidate[];
}

export interface EjercicioCreateResponse {
    exercise: EjercicioDetail;
    relation_type?: 'VARIANTE_DE';
    related_exercise_id?: number;
}
