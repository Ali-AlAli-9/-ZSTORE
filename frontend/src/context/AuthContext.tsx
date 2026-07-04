import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import api, { setAccessToken, clearAccessToken } from '../api/axios'
import type { User, LoginResponse, RegisterResponse } from '../types'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<User>
  logout: () => Promise<void>
  resendVerification: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    try {
      const { data } = await api.get<User>('/users/me/')
      setUser(data)
    } catch {
      setUser(null)
    }
  }, [])

  useEffect(() => {
    refreshUser().finally(() => setLoading(false))
  }, [refreshUser])

  const login = async (username: string, password: string) => {
    const { data } = await api.post<LoginResponse>('/users/login/', { username, password })
    setAccessToken(data.access)
    const me = await api.get<User>('/users/me/')
    setUser(me.data)
  }

  const register = async (username: string, email: string, password: string) => {
    const { data } = await api.post<RegisterResponse>('/users/register/', { username, email, password })
    setAccessToken(data.access)
    const userObj: User = { ...data.user, is_email_verified: false }
    setUser(userObj)
    return userObj
  }

  const resendVerification = async () => {
    await api.post('/users/resend-verification/')
  }

  const logout = async () => {
    try { await api.post('/users/logout/') } catch (err) { console.error('Logout error:', err) }
    clearAccessToken()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, resendVerification, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextType => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
