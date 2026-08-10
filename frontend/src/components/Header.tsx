import React from 'react';
import { useAuth } from './AuthContext';
import { LogOut, User as UserIcon } from 'lucide-react';

export const Header: React.FC = () => {
    const { user, logout } = useAuth();

    return (
        <header className="bg-primary-900 text-white shadow-md sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                    <h1 className="font-bold text-lg hidden sm:block">BASE DE ENTRENAMIENTO DE FÚTBOL</h1>
                    <h1 className="font-bold text-lg sm:hidden">BEF</h1>
                </div>

                {user && (
                    <div className="flex items-center space-x-6">
                        <div className="flex items-center space-x-2 text-primary-100">
                            <UserIcon className="w-4 h-4" />
                            <span className="text-sm font-medium">{user.usuario}</span>
                        </div>
                        <button
                            onClick={logout}
                            className="flex items-center space-x-2 bg-primary-800 hover:bg-primary-700 px-3 py-1.5 rounded-lg transition-colors text-sm font-medium"
                        >
                            <LogOut className="w-4 h-4" />
                            <span>Cerrar sesión</span>
                        </button>
                    </div>
                )}
            </div>
        </header>
    );
};
