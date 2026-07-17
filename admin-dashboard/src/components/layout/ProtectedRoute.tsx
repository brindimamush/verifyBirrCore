import React from "react"
import { Navigate, Outlet } from "react-router-dom"

export const ProtectedRoute: React.FC = () => {
  // Phase 1 Mock Auth Context (Simulating authenticated Admin state)
  // Phase 2 will implement explicit JWT parsing & backend role evaluation
  const isAuthenticated = true 
  const userRole = "admin" // Options: admin, merchant

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (userRole !== "admin") {
    return <Navigate to="/404" replace />
  }

  return <Outlet />
}