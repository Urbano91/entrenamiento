import React, { useEffect, useMemo, useState } from 'react';
import { taxonomyApi } from '../services/taxonomy';
import { ObjetivoV2Trazabilidad } from '../types/taxonomy';

interface Props {
    exerciseId: number;
    fallback?: string;
    className?: string;
}

export const ExerciseTaxonomySummary: React.FC<Props> = ({
    exerciseId,
    fallback,
    className = '',
}) => {
    const [trace, setTrace] = useState<ObjetivoV2Trazabilidad[] | null>(null);

    useEffect(() => {
        let active = true;
        setTrace(null);
        taxonomyApi.getExerciseTrace(exerciseId)
            .then(data => { if (active) setTrace(data); })
            .catch(() => { if (active) setTrace([]); });
        return () => { active = false; };
    }, [exerciseId]);

    const objectives = useMemo(() => {
        const unique = new Map<number, ObjetivoV2Trazabilidad>();
        trace?.forEach(item => {
            if (!unique.has(item.objetivo_id)) unique.set(item.objetivo_id, item);
        });
        return [...unique.values()];
    }, [trace]);

    const visible = objectives.slice(0, 2);
    const accessibleLabel = objectives
        .map(item => `${item.categoria_nombre}: ${item.objetivo_nombre}`)
        .join(', ');

    if (trace === null) {
        return (
            <span className={`flex min-w-0 items-start text-slate-500 ${className}`}>
                <span>Cargando objetivos…</span>
            </span>
        );
    }

    if (visible.length === 0) {
        if (!fallback) return null;
        return (
            <span className={`flex min-w-0 items-start ${className}`}>
                <span className="break-words [overflow-wrap:anywhere]">{fallback}</span>
            </span>
        );
    }

    return (
        <span
            className={`flex min-w-0 items-start ${className}`}
            aria-label={`Objetivos: ${accessibleLabel}`}
        >
            <span className="min-w-0 break-words [overflow-wrap:anywhere]">
                {visible.map(item => (
                    <span key={item.objetivo_id} className="block">
                        <span className="font-bold text-primary-700">{item.categoria_nombre}</span>
                        {' · '}{item.objetivo_nombre}
                    </span>
                ))}
                {objectives.length > visible.length && (
                    <span className="block font-semibold text-slate-500">
                        +{objectives.length - visible.length} objetivos
                    </span>
                )}
            </span>
        </span>
    );
};
