import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

const LEAVES = Array.from({ length: 18 }, (_, i) => ({
  id: i,
  left: Math.random() * 100,
  delay: Math.random() * 8,
  duration: 6 + Math.random() * 6,
  size: 10 + Math.random() * 16,
}))

export default function Login() {
  const { login } = useAuth()
  const [form, setForm] = useState({ usuario: '', contrasena: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => { setMounted(true) }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!form.usuario || !form.contrasena) {
      setError('Completa todos los campos')
      return
    }
    setLoading(true)
    await new Promise(r => setTimeout(r, 800))
    if (form.contrasena.length >= 4) {
      login(form)
    } else {
      setError('Contrasena minimo 4 caracteres')
      setLoading(false)
    }
  }

  return (
    <div style={styles.wrapper}>
      {LEAVES.map(l => (
        <div key={l.id} style={{
          position: 'fixed',
          left: `${l.left}%`,
          top: '-20px',
          width: l.size,
          height: l.size,
          background: 'radial-gradient(circle, #22c55e 0%, #16a34a 60%, transparent 100%)',
          borderRadius: '50% 10% 50% 10%',
          opacity: 0,
          pointerEvents: 'none',
          animation: `leaf-fall ${l.duration}s ${l.delay}s linear infinite`,
        }} />
      ))}

      <div style={styles.grid} />
      <div style={styles.orb1} />
      <div style={styles.orb2} />

      <div style={{
        ...styles.card,
        opacity: mounted ? 1 : 0,
        transform: mounted ? 'none' : 'translateY(30px)',
        transition: 'all 0.7s cubic-bezier(0.16, 1, 0.3, 1)',
      }}>
        <div style={styles.logoWrap}>
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

        <div style={styles.divider} />
        <h1 style={styles.title}>Bienvenido</h1>
        <p style={styles.subtitle}>Ingresa tus credenciales para continuar</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.fieldGroup}>
            <label style={styles.label}>Usuario</label>
            <div style={styles.inputWrap}>
              <svg style={styles.inputIcon} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              <input
                type="text"
                placeholder="admin"
                value={form.usuario}
                onChange={e => setForm(p => ({...p, usuario: e.target.value}))}
                style={styles.input}
              />
            </div>
          </div>

          <div style={styles.fieldGroup}>
            <label style={styles.label}>Contrasena</label>
            <div style={styles.inputWrap}>
              <svg style={styles.inputIcon} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <input
                type="password"
                placeholder="••••••••"
                value={form.contrasena}
                onChange={e => setForm(p => ({...p, contrasena: e.target.value}))}
                style={styles.input}
              />
            </div>
          </div>

          {error && (
            <div style={styles.error}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              {error}
            </div>
          )}

          <button type="submit" style={styles.btn} disabled={loading}>
            {loading ? <span style={styles.spinner} /> : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                  <polyline points="10 17 15 12 10 7"/>
                  <line x1="15" y1="12" x2="3" y2="12"/>
                </svg>
                Ingresar al sistema
              </>
            )}
          </button>
        </form>

        <p style={styles.hint}>Demo: usuario <strong>admin</strong> · contrasena de 4+ caracteres</p>
      </div>

      <style>{`
        @keyframes leaf-fall {
          0%   { transform: translateY(-40px) rotate(0deg); opacity: 0; }
          10%  { opacity: 0.5; }
          90%  { opacity: 0.2; }
          100% { transform: translateY(110vh) rotate(540deg); opacity: 0; }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50%       { transform: translateY(-10px); }
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        input:focus { outline: none; border-color: rgba(34,197,94,0.5) !important; box-shadow: 0 0 0 3px rgba(34,197,94,0.1) !important; }
        button:not(:disabled):hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(22,163,74,0.35) !important; }
        button:disabled { opacity: 0.7; cursor: not-allowed; }
      `}</style>
    </div>
  )
}

const styles = {
  wrapper: {
    minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
    background: 'radial-gradient(ellipse at 20% 50%, #052e16 0%, #060c07 50%, #0a0a0a 100%)',
    position: 'relative', overflow: 'hidden', padding: '20px',
  },
  grid: {
    position: 'fixed', inset: 0, pointerEvents: 'none',
    backgroundImage: `linear-gradient(rgba(34,197,94,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(34,197,94,0.03) 1px, transparent 1px)`,
    backgroundSize: '60px 60px',
  },
  orb1: { position: 'fixed', top: '-20%', left: '-10%', width: '60vw', height: '60vw', borderRadius: '50%', background: 'radial-gradient(circle, rgba(22,163,74,0.08) 0%, transparent 70%)', pointerEvents: 'none' },
  orb2: { position: 'fixed', bottom: '-20%', right: '-10%', width: '50vw', height: '50vw', borderRadius: '50%', background: 'radial-gradient(circle, rgba(34,197,94,0.05) 0%, transparent 70%)', pointerEvents: 'none' },
  card: {
    position: 'relative', zIndex: 10,
    background: 'rgba(13,21,16,0.85)', backdropFilter: 'blur(20px)',
    border: '1px solid rgba(34,197,94,0.2)', borderRadius: '20px',
    padding: '40px', width: '100%', maxWidth: '420px',
    boxShadow: '0 25px 80px rgba(0,0,0,0.5), inset 0 1px 0 rgba(34,197,94,0.1)',
  },
  logoWrap: { display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' },
  logoIcon: {
    width: '48px', height: '48px', borderRadius: '12px',
    background: 'rgba(22,163,74,0.15)', border: '1px solid rgba(34,197,94,0.3)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    animation: 'float 3s ease-in-out infinite',
  },
  logoText: { fontFamily: "'Syne', sans-serif", fontSize: '20px', fontWeight: 700, color: '#f0fdf4' },
  logoSub: { fontSize: '11px', color: '#4ade80', marginTop: '1px' },
  divider: { height: '1px', background: 'rgba(34,197,94,0.1)', marginBottom: '24px' },
  title: { fontFamily: "'Syne', sans-serif", fontSize: '22px', fontWeight: 700, color: '#f0fdf4', marginBottom: '6px' },
  subtitle: { fontSize: '13px', color: '#6b7280', marginBottom: '28px' },
  form: { display: 'flex', flexDirection: 'column', gap: '16px' },
  fieldGroup: { display: 'flex', flexDirection: 'column', gap: '6px' },
  label: { fontSize: '12px', fontWeight: 500, color: '#86efac', letterSpacing: '0.5px' },
  inputWrap: { position: 'relative' },
  inputIcon: { position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#4ade80' },
  input: {
    width: '100%', padding: '11px 14px 11px 38px',
    background: 'rgba(6,12,7,0.8)', border: '1px solid rgba(34,197,94,0.15)',
    borderRadius: '10px', color: '#f0fdf4', fontSize: '14px',
    fontFamily: "'DM Sans', sans-serif", transition: 'all 0.2s',
  },
  error: {
    display: 'flex', alignItems: 'center', gap: '6px', padding: '10px 14px',
    borderRadius: '8px', background: 'rgba(248,113,113,0.1)',
    border: '1px solid rgba(248,113,113,0.2)', color: '#f87171', fontSize: '13px',
  },
  btn: {
    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
    padding: '13px', borderRadius: '10px', border: 'none',
    background: 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)',
    color: '#fff', fontSize: '14px', fontWeight: 600,
    fontFamily: "'DM Sans', sans-serif", cursor: 'pointer',
    transition: 'all 0.2s', boxShadow: '0 4px 15px rgba(22,163,74,0.25)', marginTop: '4px',
  },
  spinner: {
    width: '18px', height: '18px', border: '2px solid rgba(255,255,255,0.3)',
    borderTop: '2px solid #fff', borderRadius: '50%',
    animation: 'spin 0.7s linear infinite', display: 'inline-block',
  },
  hint: { marginTop: '20px', fontSize: '12px', color: '#374151', textAlign: 'center' },
}