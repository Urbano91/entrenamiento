import { ExerciseFilters } from '../types/ejercicios';

const ACTIVE_FILTER_KEYS: Array<keyof ExerciseFilters> = [
    'q',
    'tipo',
    'jugadores',
    'categoria_v2_id',
    'objetivo_v2_ids',
    'objetivo_v2_id',
    'objetivo',
];

export const countActiveExerciseFilters = (filters: ExerciseFilters) => (
    ACTIVE_FILTER_KEYS.reduce<number>((count, key) => {
        const value = filters[key];
        const active = Array.isArray(value)
            ? value.length > 0
            : typeof value === 'string'
            ? value.trim().length > 0
            : value !== null && value !== undefined;
        return count + (active ? 1 : 0);
    }, 0)
);

export const toggleObjectiveFilter = (selectedIds: number[], objectiveId: number) => (
    selectedIds.includes(objectiveId)
        ? selectedIds.filter(id => id !== objectiveId)
        : [...selectedIds, objectiveId]
);

export const filterObjectiveIdsByCategory = (
    selectedIds: number[],
    categoryId: number | undefined,
    objectiveCategories: ReadonlyMap<number, number>,
) => categoryId === undefined
    ? selectedIds
    : selectedIds.filter(id => objectiveCategories.get(id) === categoryId);
