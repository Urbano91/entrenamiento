const MATERIAL_TOKEN = /(?:\d+\s*)?(?:cinta de balizar(?:\s*\([^)]*\))?|tapas de riego(?:\s*\([^)]*\))?|bal[oó]n medicinal|bal[oó]n de pilates|cama el[aá]stica|porteria auxiliar|porter[ií]a m[oó]vil|juego de chinos|setas planas|miniporter[ií]as?|minipoterias|mimiporterias|arn[eé]s de fuerza|bander[ií]n(?:es)?|esterillas?|escaleras?|balones?|conos?|petos?|picas?|vallas?|aros?|bosu|gomas?|altavoz)/giu;

const isOnlySeparator = (value: string) => (
    /^[-\s,;.:+]*(?:y[-\s,;.:+]*)?$/iu.test(value)
);

const formatMaterialItem = (value: string) => {
    const item = value.trim().replace(/^[-,;.:+]+|[-,;.:+]+$/g, '').trim();
    if (!item) return '';
    if (/^\d/u.test(item)) {
        return item.replace(
            /^(\d+\s*)(\p{L})/u,
            (_match, quantity: string, letter: string) => `${quantity}${letter.toLocaleLowerCase('es')}`,
        );
    }
    return `${item.charAt(0).toLocaleUpperCase('es')}${item.slice(1)}`;
};

export const cleanExerciseDescription = (description: string) => (
    description.replace(/^\s*[-–—]\s+/, '')
);

export const splitMaterialItems = (material: string) => {
    const items: string[] = [];
    let cursor = 0;

    for (const match of material.matchAll(MATERIAL_TOKEN)) {
        const index = match.index ?? cursor;
        const gap = material.slice(cursor, index);
        if (!isOnlySeparator(gap)) items.push(gap);
        items.push(match[0]);
        cursor = index + match[0].length;
    }

    const tail = material.slice(cursor);
    if (!isOnlySeparator(tail)) items.push(tail);
    if (items.length === 0) items.push(material);

    return [...new Map(
        items
            .map(formatMaterialItem)
            .filter(Boolean)
            .map(item => [item.toLocaleLowerCase('es'), item]),
    ).values()];
};
