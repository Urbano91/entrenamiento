export interface CategoriaObjetivoV2 {
    id: number;
    codigo: string;
    nombre: string;
    orden: number;
}

export interface ObjetivoNormalizadoV2 {
    id: number;
    nombre: string;
    categoria_id: number;
    categoria_codigo: string;
    categoria_nombre: string;
    orden: number;
}

export interface ObjetivoV2Trazabilidad {
    objetivo_id: number;
    objetivo_nombre: string;
    categoria_id: number;
    categoria_codigo: string;
    categoria_nombre: string;
    objetivo_origen_id: number;
    objetivo_original?: string;
    rol_historico: string;
    alcance: 'global' | 'excepcion';
}

export interface TaxonomyCatalog {
    categorias: CategoriaObjetivoV2[];
    objetivos: ObjetivoNormalizadoV2[];
}

