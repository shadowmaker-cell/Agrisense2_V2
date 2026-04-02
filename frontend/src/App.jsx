import { useState } from 'react'
import { useAuth } from './context/AuthContext'
import Login from './components/Login'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import Dispositivos from './components/Dispositivos'
import Alertas from './components/Alertas'
import Notificaciones from './components/Notificaciones'
import Lecturas from './components/Lecturas'
import Parcelas from './components/Parcelas'

export default function App() {
  const { user } = useAuth()
  const [activePage, setActivePage] = useState('dashboard')

  if (!user) return <Login />

  const pages = {
    dashboard:      <Dashboard />,
    dispositivos:   <Dispositivos />,
    lecturas:       <Lecturas />,
    alertas:        <Alertas />,
    notificaciones: <Notificaciones />,
    parcelas:       <Parcelas />,
  }

  return (
    <div style={styles.layout}>
      <Sidebar active={activePage} setActive={setActivePage} />
      <main style={styles.main}>
        {pages[activePage] || <Dashboard />}
      </main>
    </div>
  )
}

const styles = {
  layout: { display: 'flex', minHeight: '100vh' },
  main: {
    flex: 1,
    overflow: 'auto',
    background: 'radial-gradient(ellipse at 70% 0%, rgba(22,163,74,0.04) 0%, transparent 60%), var(--bg-base)',
  },
}