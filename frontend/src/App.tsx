import React from 'react';
import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet, useParams } from 'react-router-dom';
import { AuthProvider, useAuth } from './components/AuthContext';
import { Login } from './components/Login';
import { Home } from './pages/Home';
import { Loader2 } from 'lucide-react';
import { ApiError, api } from './services/api';
import { Perfil } from './types/fase2';
import { PerfilForm } from './components/PerfilForm';
import { AppLayout } from './components/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { Calendario } from './pages/Calendario';
import { MisEntrenamientos } from './pages/MisEntrenamientos';
import { EntrenamientoForm } from './pages/EntrenamientoForm';
import { DetalleEntrenamiento } from './pages/DetalleEntrenamiento';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const ProfileRequiredRoute: React.FC = () => {
  const [status, setStatus] = useState<'loading' | 'ready' | 'missing' | 'error'>('loading');

  useEffect(() => {
    api.get<Perfil>('/perfil')
      .then(() => setStatus('ready'))
      .catch((error: unknown) => {
        setStatus(error instanceof ApiError && error.status === 404 ? 'missing' : 'error');
      });
  }, []);

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    );
  }

  if (status === 'missing') return <Navigate to="/perfil?setup=1" replace />;

  if (status === 'error') {
    return <div className="min-h-screen flex items-center justify-center text-red-600">No se pudo comprobar el perfil.</div>;
  }

  return <Outlet />;
};

const PerfilPage: React.FC = () => {
  const [status, setStatus] = useState<'loading' | 'existing' | 'missing' | 'error'>('loading');

  useEffect(() => {
    api.get<Perfil>('/perfil')
      .then(() => setStatus('existing'))
      .catch((error: unknown) => {
        setStatus(error instanceof ApiError && error.status === 404 ? 'missing' : 'error');
      });
  }, []);

  if (status === 'loading') {
    return <div className="min-h-screen flex items-center justify-center text-primary-500">Cargando...</div>;
  }

  if (status === 'error') {
    return <div className="min-h-screen flex items-center justify-center text-red-600">No se pudo cargar el perfil.</div>;
  }

  if (status === 'missing') return <PerfilForm isSetup />;

  return <AppLayout><PerfilForm /></AppLayout>;
};

const EditarEntrenamiento: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  return <EntrenamientoForm editId={Number(id)} />;
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/perfil" element={
            <ProtectedRoute>
              <PerfilPage />
            </ProtectedRoute>
          } />
          <Route element={<ProtectedRoute><ProfileRequiredRoute /></ProtectedRoute>}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/calendario" element={<Calendario />} />
            <Route path="/entrenamientos" element={<MisEntrenamientos />} />
            <Route path="/entrenamientos/nuevo" element={<EntrenamientoForm />} />
            <Route path="/entrenamientos/:id/editar" element={<EditarEntrenamiento />} />
            <Route path="/entrenamientos/:id" element={<DetalleEntrenamiento />} />
            <Route path="/biblioteca" element={<Home />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
