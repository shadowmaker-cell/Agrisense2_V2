import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { authAPI } from '../api/client'

const DEPARTAMENTOS_CO = [
  'Amazonas','Antioquia','Arauca','Atlantico','Bolivar','Boyaca','Caldas',
  'Caqueta','Casanare','Cauca','Cesar','Choco','Cordoba','Cundinamarca',
  'Guainia','Guaviare','Huila','La Guajira','Magdalena','Meta','Narino',
  'Norte de Santander','Putumayo','Quindio','Risaralda','San Andres',
  'Santander','Sucre','Tolima','Valle del Cauca','Vaupes','Vichada',
]

export default function Login() {
  const { login } = useAuth()
  const [tab, setTab]         = useState('login')
  const [loading, setLoading] = useState(false)
  const [msg, setMsg]         = useState('')
  const [msgType, setMsgType] = useState('error')

  const [loginForm, setLoginForm] = useState({ email: '', password: '' })

  const [regForm, setRegForm] = useState({
    nombres: '', apellidos: '',
    tipo_documento: 'CC', numero_documento: '',
    email: '', telefono: '',
    ciudad: '', departamento: '',
    password: '', confirmar_password: '',
    acepta_tratamiento: false, acepta_terminos: false,
  })

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true); setMsg('')
    try {
      await login(loginForm.email, loginForm.password)
    } catch(err) {
      const detail = err?.response?.data?.detail
      setMsg(detail || 'Correo o contrasena incorrectos')
      setMsgType('error')
    } finally { setLoading(false) }
  }

  const handleRegistro = async (e) => {
    e.preventDefault()
    setLoading(true); setMsg('')
    try {
      await authAPI.registro(regForm)
      setMsg('Registro exitoso. Inicia sesion con tus credenciales.')
      setMsgType('success')
      setTimeout(() => { setTab('login'); setMsg('') }, 2000)
    } catch(err) {
      const detail = err?.response?.data?.detail
      if (Array.isArray(detail)) {
        setMsg(detail.map(d => d.msg).join(' · '))
      } else {
        setMsg(detail || 'Error al registrar usuario')
      }
      setMsgType('error')
    } finally { setLoading(false) }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.logo}>
          <div style={styles.logoIcon}>
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <path d="M14 3C14 3 6 9 6 16a8 8 0 0 0 16 0C22 9 14 3 14 3Z" fill="#22c55e" opacity="0.9"/>
              <path d="M14 8C14 8 10 12 10 16a4 4 0 0 0 8 0C18 12 14 8 14 8Z" fill="#4ade80"/>
              <line x1="14" y1="16" x2="14" y2="26" stroke="#16a34a" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <div>
            <div style={styles.logoText}>AgriSense</div>
            <div style={styles.logoSub}>Plataforma de Agricultura de Precision</div>
          </div>
        </div>

        <div style={styles.tabs}>
          <button onClick={() => { setTab('login'); setMsg('') }} style={{
            ...styles.tab, ...(tab === 'login' ? styles.tabActive : {})
          }}>Iniciar sesion</button>
          <button onClick={() => { setTab('registro'); setMsg('') }} style={{
            ...styles.tab, ...(tab === 'registro' ? styles.tabActive : {})
          }}>Registrarse</button>
        </div>

        {tab === 'login' && (
          <form onSubmit={handleLogin} style={styles.form}>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Correo electronico</label>
              <input type="email" placeholder="agricultor@agrisense.co"
                value={loginForm.email}
                onChange={e => setLoginForm(p => ({...p, email: e.target.value}))}
                style={styles.input} required />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Contrasena</label>
              <input type="password" placeholder="Tu contrasena"
                value={loginForm.password}
                onChange={e => setLoginForm(p => ({...p, password: e.target.value}))}
                style={styles.input} required />
            </div>
            {msg && (
              <div style={{...styles.msg,
                color: msgType === 'success' ? '#22c55e' : '#f87171',
                background: msgType === 'success' ? 'rgba(34,197,94,0.08)' : 'rgba(248,113,113,0.08)'
              }}>{msg}</div>
            )}
            <button type="submit" disabled={loading} style={styles.submitBtn}>
              {loading ? 'Iniciando sesion...' : 'Iniciar sesion'}
            </button>
          </form>
        )}

        {tab === 'registro' && (
          <form onSubmit={handleRegistro} style={styles.form}>
            <div style={styles.row}>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Nombres *</label>
                <input placeholder="Juan Carlos" value={regForm.nombres}
                  onChange={e => setRegForm(p => ({...p, nombres: e.target.value}))}
                  style={styles.input} required />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Apellidos *</label>
                <input placeholder="Rodriguez Perez" value={regForm.apellidos}
                  onChange={e => setRegForm(p => ({...p, apellidos: e.target.value}))}
                  style={styles.input} required />
              </div>
            </div>

            <div style={styles.row}>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Tipo documento</label>
                <select value={regForm.tipo_documento}
                  onChange={e => setRegForm(p => ({...p, tipo_documento: e.target.value}))}
                  style={styles.input}>
                  <option value="CC">Cedula de ciudadania (CC)</option>
                  <option value="CE">Cedula de extranjeria (CE)</option>
                  <option value="NIT">NIT</option>
                  <option value="PA">Pasaporte (PA)</option>
                  <option value="TI">Tarjeta de identidad (TI)</option>
                </select>
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Numero de documento *</label>
                <input placeholder="1234567890" value={regForm.numero_documento}
                  onChange={e => setRegForm(p => ({...p, numero_documento: e.target.value}))}
                  style={styles.input} required />
              </div>
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Correo electronico *</label>
              <input type="email" placeholder="juan@agrisense.co" value={regForm.email}
                onChange={e => setRegForm(p => ({...p, email: e.target.value}))}
                style={styles.input} required />
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>
                Celular colombiano * <span style={styles.hint}>10 digitos, ej: 3001234567</span>
              </label>
              <input placeholder="3001234567" value={regForm.telefono}
                onChange={e => setRegForm(p => ({...p, telefono: e.target.value}))}
                style={styles.input} required />
            </div>

            <div style={styles.row}>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Ciudad</label>
                <input placeholder="Medellin" value={regForm.ciudad}
                  onChange={e => setRegForm(p => ({...p, ciudad: e.target.value}))}
                  style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Departamento</label>
                <select value={regForm.departamento}
                  onChange={e => setRegForm(p => ({...p, departamento: e.target.value}))}
                  style={styles.input}>
                  <option value="">Seleccionar...</option>
                  {DEPARTAMENTOS_CO.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>
                Contrasena * <span style={styles.hint}>Min 8 chars, mayuscula, numero y especial</span>
              </label>
              <input type="password" placeholder="Agri$2026" value={regForm.password}
                onChange={e => setRegForm(p => ({...p, password: e.target.value}))}
                style={styles.input} required />
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Confirmar contrasena *</label>
              <input type="password" placeholder="Repite tu contrasena"
                value={regForm.confirmar_password}
                onChange={e => setRegForm(p => ({...p, confirmar_password: e.target.value}))}
                style={styles.input} required />
            </div>

            <div style={styles.checkCard}>
              <div style={styles.checkRow}>
                <input type="checkbox" id="tratamiento"
                  checked={regForm.acepta_tratamiento}
                  onChange={e => setRegForm(p => ({...p, acepta_tratamiento: e.target.checked}))}
                  style={styles.checkbox} />
                <label htmlFor="tratamiento" style={styles.checkLabel}>
                  Acepto el tratamiento de mis datos personales conforme a la{' '}
                  <span style={{color:'#4ade80'}}>Ley 1581 de 2012</span> (Habeas Data Colombia) *
                </label>
              </div>
              <div style={styles.checkRow}>
                <input type="checkbox" id="terminos"
                  checked={regForm.acepta_terminos}
                  onChange={e => setRegForm(p => ({...p, acepta_terminos: e.target.checked}))}
                  style={styles.checkbox} />
                <label htmlFor="terminos" style={styles.checkLabel}>
                  Acepto los <span style={{color:'#4ade80'}}>terminos y condiciones</span> del servicio AgriSense *
                </label>
              </div>
            </div>

            {msg && (
              <div style={{...styles.msg,
                color: msgType === 'success' ? '#22c55e' : '#f87171',
                background: msgType === 'success' ? 'rgba(34,197,94,0.08)' : 'rgba(248,113,113,0.08)'
              }}>{msg}</div>
            )}

            <button type="submit" disabled={loading} style={styles.submitBtn}>
              {loading ? 'Registrando...' : 'Crear cuenta'}
            </button>

            <div style={styles.legalNote}>
              🔒 Tus datos estan protegidos bajo la Ley 1581 de 2012 — Proteccion de Datos Personales de Colombia.
              AgriSense garantiza la confidencialidad y seguridad de tu informacion.
            </div>
          </form>
        )}
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to   { opacity: 1; transform: none; }
        }
      `}</style>
    </div>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    background: 'radial-gradient(ellipse at 60% 0%, rgba(22,163,74,0.08) 0%, transparent 60%), #060c07',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: '20px',
  },
  card: {
    background: '#0d1510',
    border: '1px solid rgba(34,197,94,0.15)',
    borderRadius: '20px',
    padding: '36px 40px',
    width: '100%', maxWidth: '520px',
    animation: 'fadeIn 0.4s ease both',
    boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
  },
  logo: { display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '28px' },
  logoIcon: {
    width: '48px', height: '48px', borderRadius: '12px',
    background: 'rgba(22,163,74,0.15)', border: '1px solid rgba(34,197,94,0.25)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  logoText: { fontFamily: "'Syne', sans-serif", fontSize: '20px', fontWeight: 700, color: '#f0fdf4' },
  logoSub: { fontSize: '11px', color: '#4ade80', marginTop: '2px' },
  tabs: {
    display: 'flex', gap: '4px', marginBottom: '24px',
    background: 'rgba(6,12,7,0.6)', borderRadius: '10px', padding: '4px',
    border: '1px solid rgba(34,197,94,0.1)',
  },
  tab: {
    flex: 1, padding: '9px', borderRadius: '7px', border: 'none',
    background: 'transparent', color: '#6b7280', fontSize: '13px',
    fontWeight: 500, cursor: 'pointer',
    fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s',
  },
  tabActive: { background: 'rgba(34,197,94,0.15)', color: '#22c55e' },
  form: { display: 'flex', flexDirection: 'column', gap: '14px' },
  row: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' },
  fieldGroup: { display: 'flex', flexDirection: 'column', gap: '5px' },
  label: { fontSize: '11px', fontWeight: 500, color: '#86efac', letterSpacing: '0.4px' },
  hint: { color: '#4b5563', fontWeight: 400 },
  input: {
    padding: '10px 12px',
    background: 'rgba(6,12,7,0.8)',
    border: '1px solid rgba(34,197,94,0.15)',
    borderRadius: '8px', color: '#f0fdf4', fontSize: '13px',
    fontFamily: "'DM Sans', sans-serif", outline: 'none',
  },
  checkCard: {
    background: 'rgba(6,12,7,0.6)', borderRadius: '10px',
    padding: '14px', border: '1px solid rgba(34,197,94,0.1)',
    display: 'flex', flexDirection: 'column', gap: '10px',
  },
  checkRow: { display: 'flex', gap: '10px', alignItems: 'flex-start' },
  checkbox: { marginTop: '2px', accentColor: '#22c55e', width: '15px', height: '15px', cursor: 'pointer' },
  checkLabel: { fontSize: '12px', color: '#9ca3af', lineHeight: 1.5, cursor: 'pointer' },
  msg: { padding: '10px 14px', borderRadius: '8px', fontSize: '13px', lineHeight: 1.5 },
  submitBtn: {
    padding: '12px',
    background: 'linear-gradient(135deg, #16a34a, #15803d)',
    color: '#fff', border: 'none', borderRadius: '10px',
    fontSize: '14px', fontWeight: 600, cursor: 'pointer',
    fontFamily: "'DM Sans', sans-serif", transition: 'opacity 0.2s', marginTop: '4px',
  },
  legalNote: {
    fontSize: '11px', color: '#4b5563', lineHeight: 1.6,
    background: 'rgba(6,12,7,0.4)', borderRadius: '8px',
    padding: '10px 12px', textAlign: 'center',
  },
}