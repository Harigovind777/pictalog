import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useContext, useEffect, useMemo, type ReactNode } from 'react'
import * as apiClient from './api'
import { markAppReady } from './intro'
import type { User } from './types'

type AuthContextValue = {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, company: string) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const hasToken = apiClient.getToken() !== null
  const { data, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: apiClient.me,
    enabled: hasToken,
    retry: false,
    staleTime: Infinity,
  })

  const setUser = useCallback((user: User) => queryClient.setQueryData(['me'], user), [queryClient])
  const loading = hasToken && isLoading

  // Once we know who's signed in, the first real screen can render: let the launch intro go.
  useEffect(() => {
    if (!loading) markAppReady()
  }, [loading])

  useEffect(() => {
    const signedOut = () => queryClient.clear()
    window.addEventListener(apiClient.SIGNED_OUT_EVENT, signedOut)
    return () => window.removeEventListener(apiClient.SIGNED_OUT_EVENT, signedOut)
  }, [queryClient])

  const value = useMemo<AuthContextValue>(
    () => ({
      user: apiClient.getToken() ? (data ?? null) : null,
      loading,
      setUser,
      async login(email, password) {
        const { token, user } = await apiClient.login(email, password)
        apiClient.setToken(token)
        setUser(user)
      },
      async signup(email, password, company) {
        const { token, user } = await apiClient.signup(email, password, company)
        apiClient.setToken(token)
        setUser(user)
      },
      logout() {
        apiClient.setToken(null)
        queryClient.clear()
      },
    }),
    [data, loading, queryClient, setUser],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside AuthProvider')
  return value
}
