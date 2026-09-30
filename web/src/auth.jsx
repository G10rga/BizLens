import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api, clearToken, getToken, setToken } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [business, setBusiness] = useState(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setUser(null)
      setBusiness(null)
      setLoading(false)
      return null
    }
    try {
      const me = await api('/auth/me')
      setUser(me)
      setBusiness(me.business || null)
      return me
    } catch {
      clearToken()
      setUser(null)
      setBusiness(null)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const login = async (email, password) => {
    const data = await api('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    setToken(data.access_token)
    setLoading(true)
    return refresh()
  }

  const register = async (payload) => {
    const data = await api('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    setToken(data.access_token)
    setLoading(true)
    return refresh()
  }

  const logout = () => {
    clearToken()
    setUser(null)
    setBusiness(null)
  }

  return (
    <AuthContext.Provider
      value={{ user, business, loading, login, register, logout, refresh, setBusiness }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
