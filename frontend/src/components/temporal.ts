export type TemporalView = 'day' | 'week' | 'month';

const pad = (value: number) => String(value).padStart(2, '0');

export const isoDate = (date: Date) => (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
);

export const fromIso = (value: string) => new Date(`${value}T00:00:00`);

export const addDays = (date: Date, amount: number) => {
    const result = new Date(date);
    result.setDate(result.getDate() + amount);
    return result;
};

export const startOfWeek = (date: Date) => {
    const result = new Date(date);
    result.setDate(result.getDate() + (result.getDay() === 0 ? -6 : 1 - result.getDay()));
    result.setHours(0, 0, 0, 0);
    return result;
};

export const datesForView = (focusDate: Date, view: TemporalView) => {
    if (view === 'day') return [focusDate];
    if (view === 'week') {
        const weekStart = startOfWeek(focusDate);
        return Array.from({ length: 7 }, (_, index) => addDays(weekStart, index));
    }
    const days = new Date(focusDate.getFullYear(), focusDate.getMonth() + 1, 0).getDate();
    return Array.from(
        { length: days },
        (_, index) => new Date(focusDate.getFullYear(), focusDate.getMonth(), index + 1),
    );
};

export const changeFocusDate = (focusDate: Date, view: TemporalView, direction: -1 | 1) => {
    const next = new Date(focusDate);
    if (view === 'day') next.setDate(next.getDate() + direction);
    else if (view === 'week') next.setDate(next.getDate() + direction * 7);
    else next.setMonth(next.getMonth() + direction, 1);
    return next;
};

export const titleForView = (focusDate: Date, view: TemporalView) => {
    if (view === 'day') {
        return focusDate.toLocaleDateString('es-ES', {
            day: 'numeric', month: 'long', year: 'numeric',
        });
    }
    if (view === 'week') {
        const dates = datesForView(focusDate, view);
        return `${dates[0].toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })} — ${dates[6].toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })}`;
    }
    return focusDate.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
};
