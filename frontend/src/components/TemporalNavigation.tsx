import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from './ui';
import { TemporalView, titleForView } from './temporal';

interface Props {
    focusDate: Date;
    view: TemporalView;
    onChangeView: (view: TemporalView) => void;
    onChangePeriod: (direction: -1 | 1) => void;
    onToday: () => void;
    ariaLabel: string;
}

export const TemporalNavigation: React.FC<Props> = ({
    focusDate, view, onChangeView, onChangePeriod, onToday, ariaLabel,
}) => (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" className="h-11 w-11 px-0" onClick={() => onChangePeriod(-1)} aria-label="Periodo anterior"><ChevronLeft className="h-4 w-4" /></Button>
            <h2 className="min-w-0 flex-1 text-center text-base font-bold capitalize text-slate-950 sm:min-w-[260px] sm:text-lg">{titleForView(focusDate, view)}</h2>
            <Button variant="secondary" size="sm" className="h-11 w-11 px-0" onClick={() => onChangePeriod(1)} aria-label="Periodo siguiente"><ChevronRight className="h-4 w-4" /></Button>
            <Button variant="ghost" size="sm" className="h-11" onClick={onToday}>Hoy</Button>
        </div>
        <div className="grid grid-cols-3 rounded-xl bg-slate-100 p-1" aria-label={ariaLabel}>
            {(['day', 'week', 'month'] as TemporalView[]).map(value => (
                <button
                    key={value}
                    type="button"
                    onClick={() => onChangeView(value)}
                    aria-pressed={view === value}
                    className={`min-h-11 rounded-lg px-3 text-sm font-semibold ${view === value ? 'bg-white text-primary-800 shadow-sm' : 'text-slate-600 hover:bg-slate-200'}`}
                >
                    {value === 'day' ? 'Día' : value === 'week' ? 'Semana' : 'Mes'}
                </button>
            ))}
        </div>
    </div>
);
