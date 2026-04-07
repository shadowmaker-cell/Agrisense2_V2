import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      authAPI.me()
        .then(res => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email, password) => {
    const res = await authAPI.login({ email, password })
    const { access_token, refresh_token, usuario } = res.data
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    setUser(usuario)
    return usuario
  }

  const logout = async () => {
    try {
      const refresh_token = localStorage.getItem('refresh_token')
      if (refresh_token) await authAPI.logout({ refresh_token })
    } catch(e) {}
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }

  const actualizarUsuario = (data) => setUser(prev => ({...prev, ...data}))

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, actualizarUsuario }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}