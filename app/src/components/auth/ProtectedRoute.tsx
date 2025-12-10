import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireAdmin?: boolean
  redirectTo?: string
}

export default function ProtectedRoute({
  children,
  requireAdmin = false,
  redirectTo,
}: ProtectedRouteProps) {
  const { isAuthenticated, isAdmin, isLoading } = useAuth()

  if (isLoading) {
    // Show loading state while checking authentication
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    // Redirect to appropriate login page
    const loginPath = redirectTo || (requireAdmin ? '/admin/login' : '/login')
    return <Navigate to={loginPath} replace />
  }

  if (requireAdmin && !isAdmin) {
    // User is authenticated but not admin, redirect to player view
    return <Navigate to="/player" replace />
  }

  return <>{children}</>
}

