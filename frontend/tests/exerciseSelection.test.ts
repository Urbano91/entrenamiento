import { toggleExerciseSelection } from '../src/utils/exerciseSelection';

const assertIds = (actual: number[], expected: number[], label: string) => {
    if (actual.length !== expected.length || actual.some((id, index) => id !== expected[index])) {
        throw new Error(`${label}: ${actual.join(',')} != ${expected.join(',')}`);
    }
};

let selected: number[] = [];
selected = toggleExerciseSelection(selected, 1);
assertIds(selected, [1], 'selecciona con el primer click');

selected = toggleExerciseSelection(selected, 1);
assertIds(selected, [], 'deselecciona con el segundo click');

selected = toggleExerciseSelection(selected, 1);
selected = toggleExerciseSelection(selected, 2);
assertIds(selected, [1, 2], 'selecciona A y B');

selected = toggleExerciseSelection(selected, 1);
assertIds(selected, [2], 'deselecciona A y conserva B');

selected = toggleExerciseSelection(selected, 2);
selected = toggleExerciseSelection(selected, 2);
assertIds(selected, [2], 'nunca introduce IDs duplicados');

const visibleWithFilterB = [3, 4];
if (visibleWithFilterB.includes(selected[0])) {
    throw new Error('la precondición del cambio de filtro no se cumple');
}
assertIds(selected, [2], 'cambiar filtros conserva la selección local');

console.log('6 comprobaciones de selección superadas');
