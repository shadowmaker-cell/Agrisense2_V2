import { useState, useEffect } from 'react'
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

  // ── Animaciones añadidas ──────────────────────────────────────────
  const [mounted,    setMounted]    = useState(false)
  const [switchAnim, setSwitchAnim] = useState(false)
  const [focused,    setFocused]    = useState('')
  const [showPass,   setShowPass]   = useState(false)

  useEffect(() => { setTimeout(() => setMounted(true), 50) }, [])

  const switchTab = (newTab) => {
    if (newTab === tab) return
    setSwitchAnim(true)
    setTimeout(() => { setTab(newTab); setMsg(''); setSwitchAnim(false) }, 180)
  }
  // ─────────────────────────────────────────────────────────────────

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

  // Estilo de input con glow al hacer foco (añadido, no reemplaza styles.input)
  const inputStyle = (key) => ({
    ...styles.input,
    borderColor:  focused === key ? 'rgba(34,197,94,0.5)' : undefined,
    boxShadow:    focused === key ? '0 0 0 3px rgba(34,197,94,0.08)' : undefined,
    transition:   'border-color 0.2s, box-shadow 0.2s',
  })

  return (
    <div style={styles.page}>

      {/* ── Fondo animado (añadido) ─────────────────────────────── */}
      <div style={anim.bgGlow1} />
      <div style={anim.bgGlow2} />
      <div style={anim.bgGrid}  />

      {/* Partículas flotantes */}
      {[
        { w:6, h:6, l:'8%',  t:'14%', d:'0s',   dur:'6s'  },
        { w:4, h:4, l:'85%', t:'20%', d:'1s',   dur:'8s'  },
        { w:7, h:7, l:'18%', t:'72%', d:'2s',   dur:'7s'  },
        { w:5, h:5, l:'70%', t:'60%', d:'0.5s', dur:'9s'  },
        { w:3, h:3, l:'50%', t:'9%',  d:'3s',   dur:'5s'  },
        { w:6, h:6, l:'92%', t:'48%', d:'1.5s', dur:'10s' },
        { w:4, h:4, l:'4%',  t:'55%', d:'2.5s', dur:'7s'  },
        { w:5, h:5, l:'40%', t:'87%', d:'4s',   dur:'6s'  },
      ].map((p, i) => (
        <div key={i} style={{
          position: 'absolute', width: p.w, height: p.h,
          left: p.l, top: p.t, borderRadius: '50%',
          background: '#22c55e', opacity: 0.3,
          animation: `floatUp ${p.dur} ${p.d} ease-in-out infinite`,
          pointerEvents: 'none',
        }} />
      ))}

      {/* Siluetas de plantas decorativas */}
      <div style={anim.plantLeft}>
        <svg width="110" height="190" viewBox="0 0 120 200" fill="none" opacity="0.06">
          <path d="M60 200 Q60 150 60 100" stroke="#22c55e" strokeWidth="3"/>
          <path d="M60 140 Q40 120 20 130" stroke="#22c55e" strokeWidth="2" fill="none"/>
          <path d="M60 160 Q80 140 100 155" stroke="#22c55e" strokeWidth="2" fill="none"/>
          <path d="M60 120 Q35 90 40 60" stroke="#22c55e" strokeWidth="2" fill="none"/>
          <ellipse cx="40" cy="55" rx="18" ry="28" fill="#16a34a" transform="rotate(-15 40 55)"/>
          <path d="M60 130 Q85 100 82 70" stroke="#22c55e" strokeWidth="2" fill="none"/>
          <ellipse cx="82" cy="65" rx="16" ry="25" fill="#16a34a" transform="rotate(10 82 65)"/>
          <ellipse cx="20" cy="125" rx="20" ry="14" fill="#15803d" transform="rotate(-20 20 125)"/>
          <ellipse cx="100" cy="150" rx="18" ry="12" fill="#15803d" transform="rotate(15 100 150)"/>
        </svg>
      </div>
      <div style={anim.plantRight}>
        <svg width="90" height="170" viewBox="0 0 100 180" fill="none" opacity="0.06">
          <path d="M50 180 Q50 130 50 80" stroke="#22c55e" strokeWidth="3"/>
          <path d="M50 120 Q25 100 15 115" stroke="#22c55e" strokeWidth="2"/>
          <ellipse cx="12" cy="110" rx="16" ry="24" fill="#16a34a" transform="rotate(-10 12 110)"/>
          <path d="M50 100 Q75 80 72 50" stroke="#22c55e" strokeWidth="2"/>
          <ellipse cx="72" cy="45" rx="14" ry="22" fill="#16a34a" transform="rotate(12 72 45)"/>
        </svg>
      </div>
      {/* ────────────────────────────────────────────────────────── */}

      {/* Card con animación de entrada montada (mounted reemplaza el opacity fijo) */}
      <div style={{
        ...styles.card,
        opacity:   mounted ? 1 : 0,
        transform: mounted ? 'translateY(0)' : 'translateY(28px)',
        transition: 'opacity 0.5s ease, transform 0.5s ease',
      }}>
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
          {/* Tabs ahora usan switchTab para la animación de fade */}
          <button
            onClick={() => switchTab('login')}
            style={{ ...styles.tab, ...(tab === 'login' ? styles.tabActive : {}) }}
          >Iniciar sesion</button>
          <button
            onClick={() => switchTab('registro')}
            style={{ ...styles.tab, ...(tab === 'registro' ? styles.tabActive : {}) }}
          >Registrarse</button>
        </div>

        {/* Contenedor con fade al cambiar tab (añadido) */}
        <div style={{
          opacity:   switchAnim ? 0 : 1,
          transform: switchAnim ? 'translateY(6px)' : 'none',
          transition: 'opacity 0.18s ease, transform 0.18s ease',
        }}>

          {tab === 'login' && (
            <form onSubmit={handleLogin} style={styles.form}>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Correo electronico</label>
                <input type="email" placeholder="agricultor@agrisense.co"
                  value={loginForm.email}
                  onChange={e => setLoginForm(p => ({...p, email: e.target.value}))}
                  style={inputStyle('lemail')}
                  onFocus={() => setFocused('lemail')}
                  onBlur={() => setFocused('')}
                  required />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Contrasena</label>
                {/* Wrapper para el toggle de contraseña (añadido) */}
                <div style={{ position: 'relative' }}>
                  <input
                    type={showPass ? 'text' : 'password'}
                    placeholder="Tu contrasena"
                    value={loginForm.password}
                    onChange={e => setLoginForm(p => ({...p, password: e.target.value}))}
                    style={{ ...inputStyle('lpass'), paddingRight: '42px' }}
                    onFocus={() => setFocused('lpass')}
                    onBlur={() => setFocused('')}
                    required
                  />
                  <button type="button" onClick={() => setShowPass(!showPass)} style={anim.eyeBtn}>
                    {showPass ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>
              {msg && (
                <div style={{...styles.msg,
                  color:      msgType === 'success' ? '#22c55e' : '#f87171',
                  background: msgType === 'success' ? 'rgba(34,197,94,0.08)' : 'rgba(248,113,113,0.08)'
                }}>{msg}</div>
              )}
              {/* Botón con spinner y pulse-glow (añadido) */}
              <button type="submit" disabled={loading} style={{
                ...styles.submitBtn,
                animation: !loading ? 'pulseGlow 3s ease-in-out infinite' : 'none',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              }}>
                {loading && <span style={anim.spinner} />}
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
                    style={inputStyle('rnombres')}
                    onFocus={() => setFocused('rnombres')}
                    onBlur={() => setFocused('')}
                    required />
                </div>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Apellidos *</label>
                  <input placeholder="Rodriguez Perez" value={regForm.apellidos}
                    onChange={e => setRegForm(p => ({...p, apellidos: e.target.value}))}
                    style={inputStyle('rapellidos')}
                    onFocus={() => setFocused('rapellidos')}
                    onBlur={() => setFocused('')}
                    required />
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
                    style={inputStyle('rdoc')}
                    onFocus={() => setFocused('rdoc')}
                    onBlur={() => setFocused('')}
                    required />
                </div>
              </div>

              <div style={styles.fieldGroup}>
                <label style={styles.label}>Correo electronico *</label>
                <input type="email" placeholder="juan@agrisense.co" value={regForm.email}
                  onChange={e => setRegForm(p => ({...p, email: e.target.value}))}
                  style={inputStyle('remail')}
                  onFocus={() => setFocused('remail')}
                  onBlur={() => setFocused('')}
                  required />
              </div>

              <div style={styles.fieldGroup}>
                <label style={styles.label}>
                  Celular colombiano * <span style={styles.hint}>10 digitos, ej: 3001234567</span>
                </label>
                <input placeholder="3001234567" value={regForm.telefono}
                  onChange={e => setRegForm(p => ({...p, telefono: e.target.value}))}
                  style={inputStyle('rtel')}
                  onFocus={() => setFocused('rtel')}
                  onBlur={() => setFocused('')}
                  required />
              </div>

              <div style={styles.row}>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Ciudad</label>
                  <input placeholder="Medellin" value={regForm.ciudad}
                    onChange={e => setRegForm(p => ({...p, ciudad: e.target.value}))}
                    style={inputStyle('rciudad')}
                    onFocus={() => setFocused('rciudad')}
                    onBlur={() => setFocused('')}
                  />
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
                  style={inputStyle('rpass')}
                  onFocus={() => setFocused('rpass')}
                  onBlur={() => setFocused('')}
                  required />
              </div>

              <div style={styles.fieldGroup}>
                <label style={styles.label}>Confirmar contrasena *</label>
                <input type="password" placeholder="Repite tu contrasena"
                  value={regForm.confirmar_password}
                  onChange={e => setRegForm(p => ({...p, confirmar_password: e.target.value}))}
                  style={inputStyle('rconfpass')}
                  onFocus={() => setFocused('rconfpass')}
                  onBlur={() => setFocused('')}
                  required />
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
                  color:      msgType === 'success' ? '#22c55e' : '#f87171',
                  background: msgType === 'success' ? 'rgba(34,197,94,0.08)' : 'rgba(248,113,113,0.08)'
                }}>{msg}</div>
              )}

              {/* Botón con spinner y pulse-glow (añadido) */}
              <button type="submit" disabled={loading} style={{
                ...styles.submitBtn,
                animation: !loading ? 'pulseGlow 3s ease-in-out infinite' : 'none',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              }}>
                {loading && <span style={anim.spinner} />}
                {loading ? 'Registrando...' : 'Crear cuenta'}
              </button>

              <div style={styles.legalNote}>
                🔒 Tus datos estan protegidos bajo la Ley 1581 de 2012 — Proteccion de Datos Personales de Colombia.
                AgriSense garantiza la confidencialidad y seguridad de tu informacion.
              </div>
            </form>
          )}

        </div>{/* /switchAnim wrapper */}
      </div>

      {/* CSS original + keyframes de animaciones añadidas */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to   { opacity: 1; transform: none; }
        }
        @keyframes floatUp {
          0%, 100% { transform: translateY(0px) scale(1); }
          50%       { transform: translateY(-18px) scale(1.25); }
        }
        @keyframes pulseGlow {
          0%, 100% { box-shadow: 0 0 16px rgba(34,197,94,0.2); }
          50%       { box-shadow: 0 0 36px rgba(34,197,94,0.45); }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        input::placeholder { color: #3d5940; }
        select option { background: #0d1510; color: #f0fdf4; }
      `}</style>
    </div>
  )
}

// ── Estilos originales — sin tocar ────────────────────────────────
const styles = {
  page: {
    minHeight: '100vh',
    background: 'radial-gradient(ellipse at 60% 0%, rgba(22,163,74,0.08) 0%, transparent 60%), #060c07',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: '20px',
    position: 'relative', overflow: 'hidden',
  },
  card: {
    background: '#0d1510',
    border: '1px solid rgba(34,197,94,0.15)',
    borderRadius: '20px',
    padding: '36px 40px',
    width: '100%', maxWidth: '520px',
    boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
    position: 'relative', zIndex: 10,
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
    width: '100%',
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
    width: '100%',
  },
  legalNote: {
    fontSize: '11px', color: '#4b5563', lineHeight: 1.6,
    background: 'rgba(6,12,7,0.4)', borderRadius: '8px',
    padding: '10px 12px', textAlign: 'center',
  },
}

// ── Estilos exclusivos de las animaciones añadidas ────────────────
const anim = {
  bgGlow1: {
    position: 'absolute', width: '550px', height: '550px', borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(22,163,74,0.1) 0%, transparent 70%)',
    top: '-180px', left: '-100px', pointerEvents: 'none',
  },
  bgGlow2: {
    position: 'absolute', width: '450px', height: '450px', borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(21,128,61,0.07) 0%, transparent 70%)',
    bottom: '-140px', right: '-80px', pointerEvents: 'none',
  },
  bgGrid: {
    position: 'absolute', inset: 0,
    backgroundImage: 'linear-gradient(rgba(34,197,94,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(34,197,94,0.03) 1px, transparent 1px)',
    backgroundSize: '38px 38px', pointerEvents: 'none',
  },
  plantLeft: {
    position: 'absolute', bottom: 0, left: 0,
    pointerEvents: 'none',
    animation: 'floatUp 9s ease-in-out infinite',
  },
  plantRight: {
    position: 'absolute', bottom: 0, right: 0,
    pointerEvents: 'none',
    animation: 'floatUp 11s 2s ease-in-out infinite',
  },
  eyeBtn: {
    position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)',
    background: 'none', border: 'none', cursor: 'pointer',
    fontSize: '15px', padding: '4px', lineHeight: 1,
  },
  spinner: {
    display: 'inline-block',
    width: '14px', height: '14px',
    border: '2px solid rgba(255,255,255,0.25)',
    borderTopColor: '#fff',
    borderRadius: '50%',
    animation: 'spin 0.7s linear infinite',
    flexShrink: 0,
  },
}
