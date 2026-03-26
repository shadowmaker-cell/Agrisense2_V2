import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('agrisense_user')
    return saved ? JSON.parse(saved) : null
  })

  const login = (credentials) => {
    const userData = {
      id: 1,
      nombre: credentials.usuario === 'admin' ? 'Administrador' : credentials.usuario,
      rol: 'agricultor',
      token: 'demo-token-' + Date.now()
    }
    setUser(userData)
    localStorage.setItem('agrisense_user', JSON.stringify(userData))
    return true
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('agrisense_user')
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)