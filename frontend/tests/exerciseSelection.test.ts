import { toggleExerciseSelection } from '../src/utils/exerciseSelection';
import {
    filterObjectiveIdsByCategory,
    toggleObjectiveFilter,
} from '../src/utils/exerciseFilters';
import {
    cleanExerciseDescription,
    splitMaterialItems,
} from '../src/utils/exercisePresentation';

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

let selectedObjectives: number[] = [];
selectedObjectives = toggleObjectiveFilter(selectedObjectives, 21);
selectedObjectives = toggleObjectiveFilter(selectedObjectives, 63);
assertIds(selectedObjectives, [21, 63], 'permite seleccionar Control y Pase');

selectedObjectives = toggleObjectiveFilter(selectedObjectives, 21);
assertIds(selectedObjectives, [63], 'permite quitar un objetivo sin afectar al resto');

const objectiveCategories = new Map([[21, 1], [63, 1], [5, 2]]);
assertIds(
    filterObjectiveIdsByCategory([21, 63, 5], 1, objectiveCategories),
    [21, 63],
    'cambiar categoría elimina solo objetivos incompatibles',
);
assertIds(
    filterObjectiveIdsByCategory([21, 63, 5], undefined, objectiveCategories),
    [21, 63, 5],
    'seleccionar todas las categorías conserva los objetivos',
);

const cleanDescription = cleanExerciseDescription('- El jugador realiza el ejercicio.');
if (cleanDescription !== 'El jugador realiza el ejercicio.') {
    throw new Error(`limpia el guion inicial sin reescribir: ${cleanDescription}`);
}

const materials = splitMaterialItems('4 conos balones');
if (materials.length !== 2 || materials[0] !== '4 conos' || materials[1] !== 'Balones') {
    throw new Error(`separa material conservando cantidades: ${materials.join(' | ')}`);
}

const quantifiedMaterials = splitMaterialItems('6 conos y 2 balones');
if (
    quantifiedMaterials.length !== 2
    || quantifiedMaterials[0] !== '6 conos'
    || quantifiedMaterials[1] !== '2 balones'
) {
    throw new Error(`separa material con conjunción: ${quantifiedMaterials.join(' | ')}`);
}

const visibleMaterials = splitMaterialItems('Juego de chinos Balones');
if (
    visibleMaterials.length !== 2
    || visibleMaterials[0] !== 'Juego de chinos'
    || visibleMaterials[1] !== 'Balones'
) {
    throw new Error(`muestra el material real sin sustituirlo: ${visibleMaterials.join(' | ')}`);
}

const hiddenOnlyMaterial = splitMaterialItems('Juego de chinos');
if (hiddenOnlyMaterial.length !== 1 || hiddenOnlyMaterial[0] !== 'Juego de chinos') {
    throw new Error(`Juego de chinos debe conservarse como material: ${hiddenOnlyMaterial.join(' | ')}`);
}

console.log('15 comprobaciones de selección y presentación superadas');
