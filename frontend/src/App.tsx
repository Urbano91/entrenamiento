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
import { ClubDashboard } from './pages/ClubDashboard';
import { AdminDashboard } from './pages/AdminDashboard';
import { FirstAccess } from './pages/FirstAccess';

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

const TrainerOnly = ({ children }: { children: React.ReactNode }) => {
  const { user } = useAuth();
  if (user?.account_type !== 'ENTRENADOR') return <Navigate to={user?.account_type === 'ADMIN' ? '/admin' : '/club'} replace />;
  return <>{children}</>;
};

const ClubOnly = ({ children }: { children: React.ReactNode }) => {
  const { user } = useAuth();
  if (user?.account_type !== 'CLUB') return <Navigate to={user?.account_type === 'ADMIN' ? '/admin' : '/dashboard'} replace />;
  if (user.must_change_password) return <Navigate to="/first-access" replace />;
  return <>{children}</>;
};

const AdminOnly = ({ children }: { children: React.ReactNode }) => {
  const { user } = useAuth();
  if (user?.account_type !== 'ADMIN') return <Navigate to={user?.account_type === 'CLUB' ? '/club' : '/dashboard'} replace />;
  if (user.must_change_password) return <Navigate to="/first-access" replace />;
  return <>{children}</>;
};

const ProfileRequiredRoute: React.FC = () => {
  const { user } = useAuth();
  const [status, setStatus] = useState<'loading' | 'ready' | 'missing' | 'error'>('loading');

  useEffect(() => {
    if (user?.account_type !== 'ENTRENADOR' || user.must_change_password || !user.onboarding_complete) return;
    api.get<Perfil>('/perfil')
      .then(() => setStatus('ready'))
      .catch((error: unknown) => {
        setStatus(error instanceof ApiError && error.status === 404 ? 'missing' : 'error');
      });
  }, [user]);

  if (user?.account_type === 'CLUB') return <Navigate to="/club" replace />;
  if (user?.account_type === 'ADMIN') return <Navigate to="/admin" replace />;
  if (user?.must_change_password || !user?.onboarding_complete) return <Navigate to="/onboarding" replace />;

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
              <TrainerOnly><PerfilPage /></TrainerOnly>
            </ProtectedRoute>
          } />
          <Route path="/onboarding" element={<ProtectedRoute><TrainerOnly><PerfilForm isSetup /></TrainerOnly></ProtectedRoute>} />
          <Route path="/first-access" element={<ProtectedRoute><FirstAccess /></ProtectedRoute>} />
          <Route path="/club" element={<ProtectedRoute><ClubOnly><ClubDashboard /></ClubOnly></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute><AdminOnly><AdminDashboard /></AdminOnly></ProtectedRoute>} />
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
