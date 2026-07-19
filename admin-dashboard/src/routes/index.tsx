
import { createBrowserRouter, RouterProvider } from "react-router-dom"
import { ProtectedRoute } from "../components/layout/ProtectedRoute"
import { AppLayout } from "../layouts/AppLayout"
import { LoginPage } from '@/pages/auth/LoginPage';
import { DashboardPage } from '@/pages/DashboardPage'; // Assuming this exists based on your setup
import { MerchantsPage } from '@/pages/MerchantsPage'; // <-- New Import
import { UsersPage } from '@/pages/UsersPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { PlaceholderPage } from '@/pages/PlaceholderPage';

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
        element: <AppLayout />, // <-- Uncommented from Phase 3
        children: [
          {
            index: true,
            element: <DashboardPage />,
          },
          {
            path: 'dashboard',
            element: <DashboardPage />, 
          },
          {
            path: 'merchants', // <-- Added Merchants Route
            element: <MerchantsPage />,
          },
          {
            path: 'users', // <-- Added Phase 6 Users Route
            element: <UsersPage />,
          },
          {
            path: 'subscriptions',
            element: <PlaceholderPage title="Subscriptions" />,
          }
          // Future protected routes...
        ],
      },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />, 
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}