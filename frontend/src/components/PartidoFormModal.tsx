import React, { useState } from 'react';
import { Save, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { Partido } from '../types/fase2';
import { Button, Modal } from './ui';

interface PartidoFormModalProps {
    fecha: string;
    partido?: Partido;
    onClose: () => void;
    onSaved: (partido: Partido) => void;
    onDeleted: (partidoId: number) => void;
}

export const PartidoFormModal: React.FC<PartidoFormModalProps> = ({
    fecha, partido, onClose, onSaved, onDeleted,
}) => {
    const [form, setForm] = useState({
        fecha: partido?.fecha || fecha,
        hora: partido?.hora?.slice(0, 5) || '',
        rival: partido?.rival || '',
        local_visitante: partido?.local_visitante || 'local',
        campo: partido?.campo || '',
        observaciones: partido?.observaciones || '',
    });
    const [saving, setSaving] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!form.fecha) {
            setError('La fecha es obligatoria.');
            return;
        }
        if (!form.rival.trim()) {
            setError('El rival es obligatorio.');
            return;
        }
        setSaving(true);
        setError('');
        const payload = {
            fecha: form.fecha,
            hora: form.hora || null,
            rival: form.rival.trim(),
            local_visitante: form.local_visitante,
            campo: form.campo.trim() || null,
            observaciones: form.observaciones.trim() || null,
        };
        try {
            const saved = partido
                ? await api.put<Partido>(`/partidos/${partido.id}`, payload)
                : await api.post<Partido>('/partidos', payload);
            onSaved(saved);
        } catch (caught: unknown) {
            setError(caught instanceof Error ? caught.message : 'No se pudo guardar el partido.');
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async () => {
        if (!partido || !window.confirm(`¿Eliminar el partido contra ${partido.rival}?`)) return;
        setDeleting(true);
        setError('');
        try {
            await api.delete(`/partidos/${partido.id}`);
            onDeleted(partido.id);
        } catch (caught: unknown) {
            setError(caught instanceof Error ? caught.message : 'No se pudo eliminar el partido.');
            setDeleting(false);
        }
    };

    return (
        <Modal
            title={partido ? 'Editar partido' : 'Nuevo partido'}
            description="Añade el compromiso al calendario del entrenador."
            onClose={onClose}
            footer={
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                        {partido && (
                            <Button type="button" variant="danger" size="sm" onClick={handleDelete} disabled={deleting || saving}>
                                <Trash2 className="h-4 w-4" />{deleting ? 'Eliminando…' : 'Eliminar'}
                            </Button>
                        )}
                    </div>
                    <div className="flex gap-3">
                        <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
                        <Button type="submit" form="partido-form" disabled={saving || deleting}>
                            <Save className="h-4 w-4" />{saving ? 'Guardando…' : 'Guardar partido'}
                        </Button>
                    </div>
                </div>
            }
        >
            <form id="partido-form" onSubmit={handleSubmit} className="grid gap-5 sm:grid-cols-2">
                <div>
                    <label className="field-label">Fecha *</label>
                    <input type="date" className="field-control" value={form.fecha} onChange={event => setForm(current => ({ ...current, fecha: event.target.value }))} />
                </div>
                <div>
                    <label className="field-label">Hora</label>
                    <input type="time" className="field-control" value={form.hora} onChange={event => setForm(current => ({ ...current, hora: event.target.value }))} />
                </div>
                <div className="sm:col-span-2">
                    <label className="field-label">Rival *</label>
                    <input className="field-control" maxLength={160} value={form.rival} onChange={event => setForm(current => ({ ...current, rival: event.target.value }))} placeholder="Ej: CD Gines" />
                </div>
                <div>
                    <label className="field-label">Local / Visitante</label>
                    <select className="field-control" value={form.local_visitante} onChange={event => setForm(current => ({ ...current, local_visitante: event.target.value as 'local' | 'visitante' }))}>
                        <option value="local">Local</option>
                        <option value="visitante">Visitante</option>
                    </select>
                </div>
                <div>
                    <label className="field-label">Campo</label>
                    <input className="field-control" maxLength={240} value={form.campo} onChange={event => setForm(current => ({ ...current, campo: event.target.value }))} placeholder="Campo Municipal" />
                </div>
                <div className="sm:col-span-2">
                    <label className="field-label">Observaciones</label>
                    <textarea rows={4} className="field-control resize-none" value={form.observaciones} onChange={event => setForm(current => ({ ...current, observaciones: event.target.value }))} placeholder="Indicaciones para el cuerpo técnico…" />
                </div>
                {error && <p className="sm:col-span-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">{error}</p>}
            </form>
        </Modal>
    );
};
