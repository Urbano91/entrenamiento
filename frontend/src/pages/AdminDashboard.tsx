import React, { useEffect, useState } from 'react';
import { Building2, Loader2, LogOut, Plus, ShieldCheck, Trash2, UserRound } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../components/AuthContext';
import { Button, Modal, PageHeader, Surface } from '../components/ui';
import { api } from '../services/api';

interface Assignment {
    club?: string | null;
    categoria: string;
    temporada: string;
}

interface Account {
    user_id: number;
    usuario: string;
    account_type: 'ADMIN' | 'CLUB' | 'ENTRENADOR';
    activo: boolean;
    must_change_password: boolean;
    display_name: string;
    club_id?: number | null;
    assignments: Assignment[];
}

interface Catalogs {
    clubs: { id: number; nombre: string }[];
    seasons: { id: number; nombre: string }[];
    categories: string[];
}

type AccountKind = 'ENTRENADOR' | 'CLUB';

const emptyTrainer = {
    nombre: '',
    apellidos: '',
    usuario: '',
    password_provisional: '',
    tipo: 'INDEPENDIENTE' as 'INDEPENDIENTE' | 'CLUB',
    club_id: '',
    categoria: '',
    temporada_id: '',
};
const emptyClub = { nombre_club: '', usuario: '', password_provisional: '' };

export const AdminDashboard: React.FC = () => {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const [accounts, setAccounts] = useState<Account[]>([]);
    const [catalogs, setCatalogs] = useState<Catalogs>({ clubs: [], seasons: [], categories: [] });
    const [modalOpen, setModalOpen] = useState(false);
    const [accountKind, setAccountKind] = useState<AccountKind | null>(null);
    const [trainerForm, setTrainerForm] = useState(emptyTrainer);
    const [clubForm, setClubForm] = useState(emptyClub);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [deleteTarget, setDeleteTarget] = useState<Account | null>(null);
    const [deleting, setDeleting] = useState(false);
    const [success, setSuccess] = useState('');

    const loadAdministration = async () => {
        const [accountData, catalogData] = await Promise.all([
            api.get<Account[]>('/admin/accounts'),
            api.get<Catalogs>('/admin/catalogs'),
        ]);
        setAccounts(accountData);
        setCatalogs(catalogData);
    };

    useEffect(() => {
        loadAdministration().catch(reason => {
            setError(reason instanceof Error ? reason.message : 'No se pudo cargar la administración');
        });
    }, []);

    const openCreateUser = () => {
        setError('');
        setAccountKind(null);
        setTrainerForm(emptyTrainer);
        setClubForm(emptyClub);
        setModalOpen(true);
    };

    const createUser = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!accountKind) {
            setError('Selecciona el tipo de usuario.');
            return;
        }
        setSaving(true);
        setError('');
        try {
            if (accountKind === 'ENTRENADOR') {
                await api.post('/admin/trainers', {
                    nombre: trainerForm.nombre,
                    apellidos: trainerForm.apellidos,
                    usuario: trainerForm.usuario,
                    password_provisional: trainerForm.password_provisional,
                    tipo: trainerForm.tipo,
                    club_id: trainerForm.tipo === 'CLUB' ? Number(trainerForm.club_id) : null,
                    categoria: trainerForm.tipo === 'CLUB' ? trainerForm.categoria : null,
                    temporada_id: trainerForm.tipo === 'CLUB' ? Number(trainerForm.temporada_id) : null,
                });
            } else {
                await api.post('/admin/clubs', clubForm);
            }
            setModalOpen(false);
            await loadAdministration();
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : 'No se pudo crear el usuario');
        } finally {
            setSaving(false);
        }
    };

    const deleteUser = async () => {
        if (!deleteTarget) return;
        const removed = deleteTarget;
        setDeleting(true);
        setError('');
        try {
            if (removed.account_type === 'CLUB' && removed.club_id) {
                await api.delete(`/admin/clubs/${removed.club_id}`);
            } else {
                await api.delete(`/admin/users/${removed.user_id}`);
            }
            setDeleteTarget(null);
            setSuccess(
                removed.account_type === 'CLUB'
                    ? `Se ha eliminado el club ${removed.display_name}.`
                    : `Se ha eliminado a ${removed.display_name}.`,
            );
            await loadAdministration();
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : 'No se pudo eliminar el usuario');
        } finally {
            setDeleting(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-100 p-4 sm:p-6">
            <div className="mx-auto max-w-6xl">
                <PageHeader
                    eyebrow="ScoutIA"
                    title="Administración"
                    actions={(
                        <>
                            <Button onClick={openCreateUser}>
                                <Plus className="h-4 w-4" />Crear usuario
                            </Button>
                            <Button variant="ghost" onClick={async () => { await logout(); navigate('/login'); }}>
                                <LogOut className="h-4 w-4" />Salir
                            </Button>
                        </>
                    )}
                />

                {error && !modalOpen && (
                    <p className="mb-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-800">{error}</p>
                )}
                {success && (
                    <p className="mb-4 rounded-xl border border-green-200 bg-green-50 p-3 text-sm font-semibold text-green-800">{success}</p>
                )}

                <Surface className="overflow-hidden">
                    <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
                        <h2 className="font-bold text-slate-950">Usuarios</h2>
                    </div>
                    <div className="divide-y divide-slate-200">
                        {accounts.map(account => {
                            const context = account.assignments[0];
                            const role = account.account_type === 'ADMIN'
                                ? 'ADMIN'
                                : account.account_type === 'CLUB' ? 'CLUB' : 'ENTRENADOR';
                            return (
                                <article key={account.user_id} className="flex items-start gap-3 p-4">
                                    <span className="mt-0.5 rounded-xl bg-primary-100 p-2 text-primary-800">
                                        {account.account_type === 'CLUB'
                                            ? <Building2 className="h-5 w-5" />
                                            : account.account_type === 'ADMIN'
                                            ? <ShieldCheck className="h-5 w-5" />
                                            : <UserRound className="h-5 w-5" />}
                                    </span>
                                    <div className="min-w-0 flex-1">
                                        <h3 className="break-words font-bold text-slate-950">{account.display_name}</h3>
                                        <p className="mt-1 text-sm font-bold text-primary-800">{role}</p>
                                        <p className="mt-1 text-sm text-slate-600">
                                            {account.activo ? 'Activo' : 'Inactivo'}
                                            {context ? ` · ${context.club || 'Independiente'} · ${context.categoria} · ${context.temporada}` : ''}
                                        </p>
                                        <p className="mt-1 text-xs text-slate-500">
                                            Usuario {account.usuario} · ID {account.user_id}
                                            {account.must_change_password ? ' · Contraseña provisional' : ''}
                                        </p>
                                    </div>
                                    {(account.account_type === 'ENTRENADOR' || account.account_type === 'CLUB') && (
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="shrink-0 text-red-700 hover:bg-red-50 hover:text-red-800"
                                            onClick={() => { setSuccess(''); setDeleteTarget(account); }}
                                        >
                                            <Trash2 className="h-4 w-4" />{account.account_type === 'CLUB' ? 'Eliminar club' : 'Eliminar usuario'}
                                        </Button>
                                    )}
                                </article>
                            );
                        })}
                    </div>
                </Surface>
            </div>

            {modalOpen && (
                <Modal
                    title="Crear usuario"
                    description="La contraseña inicial deberá cambiarse en el primer acceso."
                    onClose={() => setModalOpen(false)}
                    size="lg"
                >
                    <form onSubmit={createUser} className="space-y-4">
                        <fieldset>
                            <legend className="field-label">Tipo de usuario *</legend>
                            <div className="grid grid-cols-2 gap-2">
                                <AccountKindButton
                                    active={accountKind === 'ENTRENADOR'}
                                    onClick={() => setAccountKind('ENTRENADOR')}
                                    icon={UserRound}
                                >
                                    Entrenador
                                </AccountKindButton>
                                <AccountKindButton
                                    active={accountKind === 'CLUB'}
                                    onClick={() => setAccountKind('CLUB')}
                                    icon={Building2}
                                >
                                    Club
                                </AccountKindButton>
                            </div>
                        </fieldset>

                        {accountKind === 'ENTRENADOR' && (
                            <div className="grid gap-4 sm:grid-cols-2">
                                <Field label="Nombre" value={trainerForm.nombre} onChange={value => setTrainerForm(current => ({ ...current, nombre: value }))} />
                                <Field label="Apellidos" value={trainerForm.apellidos} onChange={value => setTrainerForm(current => ({ ...current, apellidos: value }))} />
                                <Field label="Usuario" value={trainerForm.usuario} onChange={value => setTrainerForm(current => ({ ...current, usuario: value }))} />
                                <Field label="Contraseña inicial" type="password" value={trainerForm.password_provisional} onChange={value => setTrainerForm(current => ({ ...current, password_provisional: value }))} />
                                <div className="sm:col-span-2">
                                    <label className="field-label">Vinculación *</label>
                                    <select
                                        className="field-control"
                                        value={trainerForm.tipo}
                                        onChange={event => setTrainerForm(current => ({
                                            ...current,
                                            tipo: event.target.value as 'INDEPENDIENTE' | 'CLUB',
                                            club_id: '', categoria: '', temporada_id: '',
                                        }))}
                                    >
                                        <option value="INDEPENDIENTE">Entrenador independiente</option>
                                        <option value="CLUB">Entrenador asociado a un club</option>
                                    </select>
                                </div>
                                {trainerForm.tipo === 'CLUB' && (
                                    <>
                                        <SelectField
                                            label="Club"
                                            value={trainerForm.club_id}
                                            onChange={value => setTrainerForm(current => ({ ...current, club_id: value }))}
                                            options={catalogs.clubs.map(item => ({ value: String(item.id), label: item.nombre }))}
                                        />
                                        <SelectField
                                            label="Categoría"
                                            value={trainerForm.categoria}
                                            onChange={value => setTrainerForm(current => ({ ...current, categoria: value }))}
                                            options={catalogs.categories.map(item => ({ value: item, label: item }))}
                                        />
                                        <div className="sm:col-span-2">
                                            <SelectField
                                                label="Temporada"
                                                value={trainerForm.temporada_id}
                                                onChange={value => setTrainerForm(current => ({ ...current, temporada_id: value }))}
                                                options={catalogs.seasons.map(item => ({ value: String(item.id), label: item.nombre }))}
                                            />
                                        </div>
                                    </>
                                )}
                            </div>
                        )}

                        {accountKind === 'CLUB' && (
                            <div className="space-y-4">
                                <Field label="Nombre del club" value={clubForm.nombre_club} onChange={value => setClubForm(current => ({ ...current, nombre_club: value }))} />
                                <Field label="Usuario" value={clubForm.usuario} onChange={value => setClubForm(current => ({ ...current, usuario: value }))} />
                                <Field label="Contraseña inicial" type="password" value={clubForm.password_provisional} onChange={value => setClubForm(current => ({ ...current, password_provisional: value }))} />
                            </div>
                        )}

                        {error && (
                            <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-800">{error}</p>
                        )}

                        <Button type="submit" className="w-full" disabled={saving || !accountKind}>
                            {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                            {accountKind === null
                                ? 'Crear usuario'
                                : accountKind === 'CLUB' ? 'Crear club' : 'Crear entrenador'}
                        </Button>
                    </form>
                </Modal>
            )}
            {deleteTarget && (
                <Modal
                    title={deleteTarget.account_type === 'CLUB'
                        ? `¿Seguro que quieres eliminar el club ${deleteTarget.display_name}?`
                        : `¿Quieres eliminar a ${deleteTarget.display_name}?`}
                    description={deleteTarget.account_type === 'CLUB'
                        ? 'Esta acción eliminará el club, su cuenta y sus relaciones. Los entrenadores conservarán sus cuentas y datos.'
                        : 'Esta acción eliminará su cuenta y sus entrenamientos, partidos y ejercicios privados. Esta acción no se puede deshacer.'}
                    onClose={() => { if (!deleting) setDeleteTarget(null); }}
                    footer={(
                        <div className="flex justify-end gap-3">
                            <Button variant="secondary" onClick={() => setDeleteTarget(null)} disabled={deleting}>Cancelar</Button>
                            <Button variant="danger" onClick={() => { void deleteUser(); }} disabled={deleting}>
                                {deleting && <Loader2 className="h-4 w-4 animate-spin" />}{deleteTarget.account_type === 'CLUB' ? 'Eliminar club' : 'Eliminar usuario'}
                            </Button>
                        </div>
                    )}
                >
                    <p className="text-sm leading-6 text-slate-700">
                        {deleteTarget.account_type === 'CLUB'
                            ? 'Los entrenadores dejarán de estar asociados a este club, pero no serán eliminados.'
                            : 'Confirma únicamente si quieres borrar definitivamente todos sus datos privados.'}
                    </p>
                </Modal>
            )}
        </div>
    );
};

const AccountKindButton: React.FC<{
    active: boolean;
    onClick: () => void;
    icon: React.ComponentType<{ className?: string }>;
    children: React.ReactNode;
}> = ({ active, onClick, icon: Icon, children }) => (
    <button
        type="button"
        role="radio"
        aria-checked={active}
        onClick={onClick}
        className={`flex min-h-12 items-center justify-center gap-2 rounded-xl border px-3 text-sm font-bold ${active
            ? 'border-primary-700 bg-primary-100 text-primary-900'
            : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'}`}
    >
        <Icon className="h-4 w-4" />{children}
    </button>
);

const Field: React.FC<{
    label: string;
    value: string;
    onChange: (value: string) => void;
    type?: string;
}> = ({ label, value, onChange, type = 'text' }) => (
    <div>
        <label className="field-label">{label}</label>
        <input
            type={type}
            minLength={type === 'password' ? 8 : undefined}
            className="field-control"
            required
            value={value}
            onChange={event => onChange(event.target.value)}
        />
    </div>
);

const SelectField: React.FC<{
    label: string;
    value: string;
    onChange: (value: string) => void;
    options: { value: string; label: string }[];
}> = ({ label, value, onChange, options }) => (
    <div>
        <label className="field-label">{label} *</label>
        <select
            className="field-control"
            required
            value={value}
            onChange={event => onChange(event.target.value)}
        >
            <option value="">Seleccionar</option>
            {options.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
            ))}
        </select>
    </div>
);
