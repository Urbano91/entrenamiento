import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import {
    LayoutDashboard, CalendarDays, Dumbbell, BookOpen, UserCircle2, LogOut, Shield
} from 'lucide-react';

const navItems = [
    { to: '/dashboard', label: 'Inicio', mobileLabel: 'Inicio', icon: LayoutDashboard },
    { to: '/calendario', label: 'Calendario', mobileLabel: 'Calendario', icon: CalendarDays },
    { to: '/entrenamientos', label: 'Mis entrenamientos', mobileLabel: 'Entrenos', icon: Dumbbell },
    { to: '/biblioteca', label: 'Biblioteca', mobileLabel: 'Biblioteca', icon: BookOpen },
    { to: '/perfil', label: 'Mi Perfil', mobileLabel: 'Mi Perfil', icon: UserCircle2 },
];

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <div className="flex min-h-screen flex-col bg-slate-100">
            <header className="sticky top-0 z-50 border-b border-primary-800 bg-primary-950 text-white shadow-lg shadow-slate-950/10">
                <div className="mx-auto flex h-16 max-w-[1600px] items-center justify-between px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center gap-3">
                        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary-700 text-white ring-1 ring-white/20">
                            <Shield className="h-5 w-5" aria-hidden="true" />
                        </span>
                        <div className="leading-none">
                            <span className="block text-sm font-bold tracking-wide">PLATAFORMA</span>
                            <span className="mt-1 block text-[10px] font-semibold tracking-[0.2em] text-primary-300">ENTRENADOR</span>
                        </div>
                    </div>
                    <nav className="hidden items-center gap-1 lg:flex" aria-label="Navegación principal">
                        {navItems.map(({ to, label, icon: Icon }) => (
                            <NavLink
                                key={to}
                                to={to}
                                className={({ isActive }) =>
                                    `flex min-h-10 items-center gap-2 rounded-xl px-3.5 py-2 text-sm font-semibold transition-colors ${isActive
                                        ? 'bg-white text-primary-950 shadow-sm'
                                        : 'text-primary-100 hover:bg-primary-800 hover:text-white'
                                    }`
                                }
                            >
                                <Icon className="w-4 h-4" />
                                {label}
                            </NavLink>
                        ))}
                        <button
                            onClick={handleLogout}
                            className="ml-2 flex min-h-10 items-center gap-2 rounded-xl border border-white/15 px-3.5 py-2 text-sm font-semibold text-white transition-colors hover:border-red-400 hover:bg-red-700"
                        >
                            <LogOut className="w-4 h-4" />
                            Salir
                        </button>
                    </nav>
                    <button
                        onClick={handleLogout}
                        className="flex min-h-10 items-center gap-2 rounded-xl border border-white/15 px-3 text-sm font-semibold text-white hover:bg-primary-800 lg:hidden"
                        aria-label="Cerrar sesión"
                    >
                        <LogOut className="w-4 h-4" />
                    </button>
                </div>
                {/* Mobile bottom nav */}
            </header>

            <nav className="fixed bottom-0 left-0 right-0 z-50 flex border-t border-primary-800 bg-primary-950 px-1 pb-[env(safe-area-inset-bottom)] shadow-2xl lg:hidden" aria-label="Navegación móvil">
                {navItems.map(({ to, mobileLabel, icon: Icon }) => (
                    <NavLink
                        key={to}
                        to={to}
                        className={({ isActive }) =>
                            `flex min-h-16 min-w-0 flex-1 flex-col items-center justify-center rounded-lg px-1 py-2 text-[11px] font-semibold transition-colors ${isActive ? 'bg-primary-800 text-white' : 'text-primary-200 hover:bg-primary-900 hover:text-white'
                            }`
                        }
                    >
                        <Icon className="w-5 h-5 mb-0.5" />
                        <span className="whitespace-nowrap text-center leading-tight">{mobileLabel}</span>
                    </NavLink>
                ))}
            </nav>

            <main className="mx-auto w-full max-w-[1600px] flex-grow px-4 py-5 pb-24 sm:px-6 lg:px-8 lg:py-6 lg:pb-9">
                {children}
            </main>
        </div>
    );
};
