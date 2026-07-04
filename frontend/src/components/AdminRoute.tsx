import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import type { ReactNode } from 'react'

export default function AdminRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex justify-center items-center min-h-screen text-gray-500 text-lg">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  if (!user.is_staff) return <Navigate to="/" replace />
  return children
}
