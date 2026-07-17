import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

export function ProtectedRoute() {
  const { isAuthenticated, user } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Strict role validation: Admin ONLY
  if (user.role !== 'admin') {
    // If a merchant somehow logs in, clear auth and send them away
    useAuthStore.getState().clearAuth();
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}