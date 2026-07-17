import React from "react"
import { createBrowserRouter, Navigate } from "react-router-dom"
import { AppLayout } from "../layouts/AppLayout"
import { ProtectedRoute } from "../components/layout/ProtectedRoute"
import { NotFoundPage } from "../pages/NotFoundPage"
import { PlaceholderPage } from "../pages/PlaceholderPage"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/dashboard" replace />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: "dashboard", element: <PlaceholderPage title="Dashboard Overview" /> },
          { path: "merchants", element: <PlaceholderPage title="Merchant Management" /> },
          { path: "users", element: <PlaceholderPage title="User Accounts" /> },
          { path: "subscriptions", element: <PlaceholderPage title="Subscription Controls" /> },
          { path: "invoices", element: <PlaceholderPage title="Invoice Monitoring" /> },
          { path: "verifications", element: <PlaceholderPage title="Verification Logs" /> },
          { path: "callbacks", element: <PlaceholderPage title="Callback Webhook Engine Queue" /> },
          { path: "api-keys", element: <PlaceholderPage title="API Identity Keys" /> },
        ],
      },
    ],
  },
  {
    path: "404",
    element: <NotFoundPage />,
  },
  {
    path: "*",
    element: <Navigate to="/404" replace />,
  },
])