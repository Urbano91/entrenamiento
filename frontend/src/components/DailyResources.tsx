import React, { useEffect, useRef, useState } from 'react';
import {
    Download, FileSpreadsheet, FileText, Image as ImageIcon, Save,
    StickyNote, Trash2, Upload,
} from 'lucide-react';
import { api, fastApiResourceUrl } from '../services/api';
import {
    DocumentoPlanificacion, Partido, PlanificacionContexto,
} from '../types/fase2';
import { Badge, Button } from './ui';

const ACCEPTED_FILES = '.pdf,.doc,.docx,.xls,.xlsx,.csv,.ppt,.pptx,.txt,.jpg,.jpeg,.png,.webp';

const fileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const DocumentIcon: React.FC<{ mime: string }> = ({ mime }) => {
    if (mime.startsWith('image/')) return <ImageIcon className="h-5 w-5" />;
    if (mime.includes('sheet') || mime.includes('excel') || mime === 'text/csv') return <FileSpreadsheet className="h-5 w-5" />;
    return <FileText className="h-5 w-5" />;
};

interface DailyResourcesProps {
    fecha: string;
    partidos: Partido[];
    temporadaId: number;
    onChanged?: () => void;
}

export const DailyResources: React.FC<DailyResourcesProps> = ({
    fecha, partidos, temporadaId, onChanged,
}) => {
    const inputRef = useRef<HTMLInputElement>(null);
    const [context, setContext] = useState<PlanificacionContexto | null>(null);
    const [note, setNote] = useState('');
    const [scope, setScope] = useState('day');
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [savingNote, setSavingNote] = useState(false);
    const [error, setError] = useState('');
    const endpoint = (suffix = '') => (
        `/planificaciones/${fecha}${suffix}?temporada_id=${temporadaId}`
    );

    useEffect(() => {
        let active = true;
        setLoading(true);
        api.get<PlanificacionContexto>(`/planificaciones/${fecha}`, {
            temporada_id: temporadaId,
        })
            .then(data => {
                if (!active) return;
                setContext(data);
                setNote(data.nota || '');
            })
            .catch(caught => {
                if (active) setError(caught instanceof Error ? caught.message : 'No se pudieron cargar los documentos.');
            })
            .finally(() => { if (active) setLoading(false); });
        return () => { active = false; };
    }, [fecha, temporadaId]);

    const uploadFile = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        event.target.value = '';
        if (!file) return;
        setUploading(true);
        setError('');
        const data = new FormData();
        data.append('archivo', file);
        if (scope.startsWith('match:')) data.append('partido_id', scope.slice(6));
        try {
            const document = await api.upload<DocumentoPlanificacion>(
                endpoint('/documentos'), data
            );
            setContext(current => current
                ? { ...current, id: current.id || document.planificacion_id, documentos: [...current.documentos, document] }
                : { id: document.planificacion_id, fecha, nota: null, documentos: [document] });
        } catch (caught: unknown) {
            setError(caught instanceof Error ? caught.message : 'No se pudo subir el archivo.');
        } finally {
            setUploading(false);
        }
    };

    const deleteDocument = async (document: DocumentoPlanificacion) => {
        if (!window.confirm(`¿Eliminar “${document.nombre_original}”?`)) return;
        setError('');
        try {
            await api.delete(`/documentos/${document.id}`);
            setContext(current => current
                ? { ...current, documentos: current.documentos.filter(item => item.id !== document.id) }
                : current);
        } catch (caught: unknown) {
            setError(caught instanceof Error ? caught.message : 'No se pudo eliminar el documento.');
        }
    };

    const saveNote = async () => {
        setSavingNote(true);
        setError('');
        try {
            const updated = await api.put<PlanificacionContexto>(
                endpoint('/nota'), { contenido: note }
            );
            setContext(updated);
            setNote(updated.nota || '');
            onChanged?.();
        } catch (caught: unknown) {
            setError(caught instanceof Error ? caught.message : 'No se pudo guardar la nota.');
        } finally {
            setSavingNote(false);
        }
    };

    const deleteNote = async () => {
        setSavingNote(true);
        setError('');
        try {
            await api.delete(endpoint('/nota'));
            setNote('');
            setContext(current => current ? { ...current, nota: null } : current);
            onChanged?.();
        } catch (caught: unknown) {
            setError(caught instanceof Error ? caught.message : 'No se pudo eliminar la nota.');
        } finally {
            setSavingNote(false);
        }
    };

    return (
        <div className="flex flex-col gap-5 border-t border-slate-200 pt-5">
            <section className="order-2">
                <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-700">Documentos</p>
                        <p className="mt-1 text-sm text-slate-600">PDF, Office, texto o imágenes · máximo 20 MB</p>
                    </div>
                    <div className="flex flex-wrap items-end gap-2">
                        {partidos.length > 0 && (
                            <div>
                                <label className="mb-1 block text-xs font-bold text-slate-600">Vincular a</label>
                                <select className="field-control min-h-11 py-1.5 text-sm" value={scope} onChange={event => setScope(event.target.value)}>
                                    <option value="day">Planificación del día</option>
                                    {partidos.map(match => <option key={match.id} value={`match:${match.id}`}>Partido vs {match.rival}</option>)}
                                </select>
                            </div>
                        )}
                        <input ref={inputRef} type="file" accept={ACCEPTED_FILES} className="hidden" onChange={uploadFile} />
                        <Button type="button" size="sm" onClick={() => inputRef.current?.click()} disabled={uploading}>
                            <Upload className="h-4 w-4" />{uploading ? 'Subiendo…' : 'Añadir archivo'}
                        </Button>
                    </div>
                </div>
                <div className="overflow-hidden rounded-2xl border border-slate-200">
                    {loading ? (
                        <p className="p-4 text-sm font-medium text-slate-600">Cargando documentos…</p>
                    ) : !context || context.documentos.length === 0 ? (
                        <p className="p-4 text-sm text-slate-600">No hay documentos asociados a este día.</p>
                    ) : (
                        <div className="divide-y divide-slate-200">
                            {context.documentos.map(document => {
                                const match = partidos.find(item => item.id === document.partido_id);
                                return (
                                    <div key={document.id} className="flex items-center gap-3 p-3 sm:px-4">
                                        <span className="rounded-xl bg-slate-100 p-2.5 text-slate-700"><DocumentIcon mime={document.tipo_mime} /></span>
                                        <div className="min-w-0 flex-1">
                                            <p className="break-words text-sm font-semibold text-slate-950 [overflow-wrap:anywhere]">{document.nombre_original}</p>
                                            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-600">
                                                <span>{fileSize(document.tamano)}</span>
                                                {match && <Badge tone="amber">Partido vs {match.rival}</Badge>}
                                            </div>
                                        </div>
                                        <a href={fastApiResourceUrl(document.download_url)} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-slate-300 bg-white text-slate-800 transition hover:bg-slate-100" aria-label={`Abrir o descargar ${document.nombre_original}`} title="Abrir o descargar"><Download className="h-4 w-4" /></a>
                                        <button type="button" onClick={() => { void deleteDocument(document); }} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-red-200 bg-red-50 text-red-700 transition hover:bg-red-100" aria-label={`Eliminar ${document.nombre_original}`} title="Eliminar documento"><Trash2 className="h-4 w-4" /></button>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </section>

            <section className="order-1">
                <div className="mb-3 flex items-center gap-2">
                    <StickyNote className="h-5 w-5 text-primary-800" />
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-700">Notas</p>
                        <p className="mt-1 text-sm text-slate-600">Observaciones generales de la planificación diaria.</p>
                    </div>
                </div>
                <textarea value={note} onChange={event => setNote(event.target.value)} rows={4} maxLength={100000} className="field-control resize-y" placeholder="Escribe las conclusiones del día, aspectos a mejorar o incidencias…" />
                <div className="mt-3 flex flex-wrap justify-end gap-2">
                    {(context?.nota || note) && <Button type="button" variant="secondary" size="sm" onClick={() => { void deleteNote(); }} disabled={savingNote}><Trash2 className="h-4 w-4" />Eliminar nota</Button>}
                    <Button type="button" size="sm" onClick={() => { void saveNote(); }} disabled={savingNote}><Save className="h-4 w-4" />{savingNote ? 'Guardando…' : 'Guardar nota'}</Button>
                </div>
            </section>

            {error && <p className="order-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</p>}
        </div>
    );
};
