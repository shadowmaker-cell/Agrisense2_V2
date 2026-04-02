import { useAuth } from '../context/AuthContext'

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
      <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
    </svg>
  )},
  { id: 'dispositivos', label: 'Dispositivos', icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
    </svg>
  )},
  { id: 'lecturas', label: 'Lecturas', icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>
  )},
  { id: 'alertas', label: 'Alertas', icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
  )},
  { id: 'notificaciones', label: 'Notificaciones', icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
      <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>
  )},
  { id: 'parcelas', label: 'Parcelas', icon: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
      <polyline points="9 22 9 12 15 12 15 22"/>
    </svg>
  )},
]

export default function Sidebar({ active, setActive }) {
  const { user, logout } = useAuth()

  return (
    <aside style={styles.aside}>
      <div style={styles.logo}>
        <div style={styles.logoIcon}>
          <svg width="22" height="22" viewBox="0 0 28 28" fill="none">
            <path d="M14 3C14 3 6 9 6 16a8 8 0 0 0 16 0C22 9 14 3 14 3Z" fill="#22c55e" opacity="0.9"/>
            <path d="M14 8C14 8 10 12 10 16a4 4 0 0 0 8 0C18 12 14 8 14 8Z" fill="#4ade80"/>
            <line x1="14" y1="16" x2="14" y2="26" stroke="#16a34a" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        <div>
          <div style={styles.logoText}>AgriSense</div>
          <div style={styles.logoSub}>v1.0.0</div>
        </div>
      </div>

      <div style={styles.divider} />

      <nav style={styles.nav}>
        {navItems.map((item, i) => (
          <button key={item.id} onClick={() => setActive(item.id)} style={{
            ...styles.navItem,
            ...(active === item.id ? styles.navItemActive : {}),
            animationDelay: `${i * 0.05}s`,
          }}>
            <span style={{ color: active === item.id ? '#22c55e' : '#4b5563' }}>
              {item.icon}
            </span>
            <span>{item.label}</span>
            {active === item.id && <div style={styles.activeDot} />}
          </button>
        ))}
      </nav>

      <div style={styles.statusCard}>
        <div style={styles.statusTitle}>Estado del sistema</div>
        {['Dispositivos', 'Ingesta', 'Procesamiento', 'Notificaciones', 'Parcelas'].map(s => (
          <div key={s} style={styles.statusRow}>
            <div style={{ ...styles.statusDot, animation: 'pulse-green 2s infinite' }} />
            <span style={styles.statusLabel}>{s}</span>
            <span style={styles.statusOk}>Online</span>
          </div>
        ))}
      </div>

      <div style={styles.userCard}>
        <div style={styles.avatar}>{user?.nombre?.[0]?.toUpperCase() || 'A'}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={styles.userName}>{user?.nombre || 'Usuario'}</div>
          <div style={styles.userRole}>Agricultor</div>
        </div>
        <button onClick={logout} style={styles.logoutBtn} title="Cerrar sesion">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
        </button>
      </div>

      <style>{`
        @keyframes pulse-green {
          0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.4); }
          50%       { box-shadow: 0 0 0 5px rgba(34,197,94,0); }
        }
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(-20px); }
          to   { opacity: 1; transform: none; }
        }
      `}</style>
    </aside>
  )
}

const styles = {
  aside: {
    width: '240px', minWidth: '240px', background: '#0d1510',
    borderRight: '1px solid rgba(34,197,94,0.1)',
    display: 'flex', flexDirection: 'column',
    padding: '20px 0', height: '100vh',
    position: 'sticky', top: 0, overflow: 'hidden',
  },
  logo: { display: 'flex', alignItems: 'center', gap: '10px', padding: '0 20px 16px' },
  logoIcon: {
    width: '40px', height: '40px', borderRadius: '10px',
    background: 'rgba(22,163,74,0.15)', border: '1px solid rgba(34,197,94,0.25)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  logoText: { fontFamily: "'Syne', sans-serif", fontSize: '16px', fontWeight: 700, color: '#f0fdf4' },
  logoSub: { fontSize: '10px', color: '#4ade80' },
  divider: { height: '1px', background: 'rgba(34,197,94,0.08)', margin: '0 0 12px' },
  nav: { display: 'flex', flexDirection: 'column', gap: '2px', padding: '0 10px', flex: 1, overflowY: 'auto' },
  navItem: {
    display: 'flex', alignItems: 'center', gap: '10px',
    padding: '10px 12px', borderRadius: '8px', border: 'none',
    background: 'transparent', color: '#9ca3af',
    fontFamily: "'DM Sans', sans-serif", fontSize: '13px', fontWeight: 500,
    cursor: 'pointer', transition: 'all 0.15s',
    position: 'relative', textAlign: 'left',
    animation: 'slideIn 0.3s ease both',
  },
  navItemActive: { background: 'rgba(34,197,94,0.1)', color: '#f0fdf4' },
  activeDot: { position: 'absolute', right: '10px', width: '6px', height: '6px', borderRadius: '50%', background: '#22c55e' },
  statusCard: {
    margin: '12px 10px', background: 'rgba(6,12,7,0.6)',
    border: '1px solid rgba(34,197,94,0.1)', borderRadius: '10px', padding: '12px',
  },
  statusTitle: { fontSize: '10px', fontWeight: 600, letterSpacing: '0.8px', color: '#4b5563', textTransform: 'uppercase', marginBottom: '8px' },
  statusRow: { display: 'flex', alignItems: 'center', gap: '7px', padding: '3px 0' },
  statusDot: { width: '7px', height: '7px', borderRadius: '50%', background: '#22c55e' },
  statusLabel: { fontSize: '12px', color: '#9ca3af', flex: 1 },
  statusOk: { fontSize: '11px', fontWeight: 600, color: '#22c55e' },
  userCard: {
    display: 'flex', alignItems: 'center', gap: '10px',
    margin: '0 10px', padding: '12px',
    background: 'rgba(6,12,7,0.6)', border: '1px solid rgba(34,197,94,0.1)', borderRadius: '10px',
  },
  avatar: {
    width: '32px', height: '32px', borderRadius: '8px',
    background: 'linear-gradient(135deg, #16a34a, #15803d)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: '14px', color: '#fff',
  },
  userName: { fontSize: '13px', fontWeight: 600, color: '#f0fdf4', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  userRole: { fontSize: '11px', color: '#4ade80' },
  logoutBtn: { background: 'none', border: 'none', cursor: 'pointer', color: '#4b5563', padding: '4px', borderRadius: '6px', transition: 'all 0.15s' },
}