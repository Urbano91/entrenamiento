export const toggleExerciseSelection = (
    selectedIds: number[], exerciseId: number
): number[] => (
    selectedIds.includes(exerciseId)
        ? selectedIds.filter(id => id !== exerciseId)
        : [...selectedIds, exerciseId]
);
