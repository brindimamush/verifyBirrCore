import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

import { authService } from '@/services/auth/auth.service';
import { useAuthStore } from '@/store/authStore';

// Matches backend validation: email format and password constraints
const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginForm() {
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormValues) => {
    try {
      setIsLoading(true);
      // 1. Get tokens
      const tokens = await authService.login(data);
      
      // 2. Temporarily set token in store so the next request succeeds
      useAuthStore.getState().updateAccessToken(tokens.access_token, tokens.refresh_token);

      // 3. Get user profile and evaluate role
      const user = await authService.getMe();

      if (user.role !== 'admin') {
        toast.error('Access Denied', {
          description: 'This portal is restricted to administrators only.',
        });
        useAuthStore.getState().clearAuth();
        return;
      }

      // 4. Finalize auth state and redirect
      setAuth(user, tokens);
      toast.success('Welcome back');
      navigate('/', { replace: true });

    } catch (error: any) {
      toast.error('Login failed', {
        description: error.response?.data?.detail || 'Invalid credentials or server error.',
      });
      useAuthStore.getState().clearAuth();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email address
        </label>
        <div className="mt-2">
          <input
            id="email"
            type="email"
            autoComplete="email"
            className={`block w-full rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ${
              errors.email ? 'ring-red-500 focus:ring-red-500' : 'ring-gray-300 focus:ring-blue-600'
            } sm:text-sm`}
            {...register('email')}
          />
          {errors.email && (
            <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Password
        </label>
        <div className="mt-2">
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            className={`block w-full rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ${
              errors.password ? 'ring-red-500 focus:ring-red-500' : 'ring-gray-300 focus:ring-blue-600'
            } sm:text-sm`}
            {...register('password')}
          />
          {errors.password && (
            <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
          )}
        </div>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            Authenticating...
          </>
        ) : (
          'Sign in to Dashboard'
        )}
      </button>
    </form>
  );
}