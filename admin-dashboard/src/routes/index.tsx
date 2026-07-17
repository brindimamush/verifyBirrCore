
import { createBrowserRouter, RouterProvider } from "react-router-dom"
import { ProtectedRoute } from "../components/layout/ProtectedRoute"
import { LoginPage } from '@/pages/auth/LoginPage';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: <ProtectedRoute />,
    children: [
      {
        // element: <AppLayout />, // From Phase 3
        children: [
          {
            index: true,
            element: <div>Dashboard Overview (Phase 4)</div>,
          },
          // Future protected routes...
        ],
      },
    ],
  },
  {
    path: '*',
    element: <div>404 - Not Found</div>, // Map to your 404 page from Phase 1
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}