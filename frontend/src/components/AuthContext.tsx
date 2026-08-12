import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

export interface User {
    id: number;
    usuario: string;
    activo: boolean;
    account_type: 'ADMIN' | 'ENTRENADOR' | 'CLUB';
    must_change_password: boolean;
    onboarding_complete: boolean;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (user: User) => void;
    refreshUser: () => Promise<User | null>;
    logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    const refreshUser = async () => {
            try {
                const userData = await api.get<User>('/auth/me');
                setUser(userData);
                return userData;
            } catch {
                setUser(null);
                return null;
            } finally {
                setLoading(false);
            }
    };

    useEffect(() => {
        refreshUser();
    }, []);

    const login = (userData: User) => setUser(userData);

    const logout = async () => {
        try {
            await api.post('/auth/logout', {});
        } finally {
            setUser(null);
        }
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, refreshUser, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) throw new Error("useAuth must be inside AuthProvider");
    return context;
};
