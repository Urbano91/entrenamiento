import { api } from './api';
import {
    CategoriaObjetivoV2,
    ObjetivoNormalizadoV2,
    ObjetivoV2Trazabilidad,
    TaxonomyCatalog,
} from '../types/taxonomy';

let catalogRequest: Promise<TaxonomyCatalog> | null = null;
const exerciseTraceRequests = new Map<number, Promise<ObjetivoV2Trazabilidad[]>>();

const cachedRequest = <T>(
    current: Promise<T> | null,
    request: () => Promise<T>,
    onRejected: () => void,
): Promise<T> => {
    if (current) return current;
    const pending = request().catch(error => {
        onRejected();
        throw error;
    });
    return pending;
};

export const taxonomyApi = {
    getCategories(): Promise<CategoriaObjetivoV2[]> {
        return api.get<CategoriaObjetivoV2[]>('/taxonomia/categorias');
    },

    getObjectives(categoriaId?: number): Promise<ObjetivoNormalizadoV2[]> {
        return api.get<ObjetivoNormalizadoV2[]>('/taxonomia/objetivos', {
            categoria_id: categoriaId,
        });
    },

    getCategoryObjectives(categoriaId: number): Promise<ObjetivoNormalizadoV2[]> {
        return api.get<ObjetivoNormalizadoV2[]>(
            `/taxonomia/categorias/${categoriaId}/objetivos`,
        );
    },

    getObjective(objetivoId: number): Promise<ObjetivoNormalizadoV2> {
        return api.get<ObjetivoNormalizadoV2>(`/taxonomia/objetivos/${objetivoId}`);
    },

    getCatalog(): Promise<TaxonomyCatalog> {
        catalogRequest = cachedRequest(
            catalogRequest,
            async () => {
                const [categorias, objetivos] = await Promise.all([
                    taxonomyApi.getCategories(),
                    taxonomyApi.getObjectives(),
                ]);
                return { categorias, objetivos };
            },
            () => { catalogRequest = null; },
        );
        return catalogRequest;
    },

    getExerciseTrace(ejercicioId: number): Promise<ObjetivoV2Trazabilidad[]> {
        const current = exerciseTraceRequests.get(ejercicioId) ?? null;
        const request = cachedRequest(
            current,
            () => api.get<ObjetivoV2Trazabilidad[]>(
                `/taxonomia/ejercicios/${ejercicioId}/objetivos`,
            ),
            () => { exerciseTraceRequests.delete(ejercicioId); },
        );
        exerciseTraceRequests.set(ejercicioId, request);
        return request;
    },
};

