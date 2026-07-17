import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { LoginForm } from '@/features/auth/LoginForm';

export function LoginPage() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  // Auto-redirect if already logged in
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="flex min-h-screen flex-1 flex-col justify-center px-6 py-12 lg:px-8 bg-gray-50">
      <div className="sm:mx-auto sm:w-full sm:max-w-sm">
        <h2 className="mt-10 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
          Platform Administration
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Authorized personnel only
        </p>
      </div>

      <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-sm bg-white px-6 py-10 shadow-sm sm:rounded-lg sm:px-12">
        <LoginForm />
      </div>
    </div>
  );
}