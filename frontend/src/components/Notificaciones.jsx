import { useState, useEffect } from 'react'
import { notificacionesAPI } from '../api/client'

const SEV_COLOR  = { critica: '#f87171', alta: '#fbbf24', media: '#60a5fa', baja: '#22c55e' }
const CANAL_ICON = { push: '📱', email: '📧', sms: '💬', sistema: '🖥️' }

export default function Notificaciones() {
  const [notifs, setNotifs]                   = useState([])
  const [resumen, setResumen]                 = useState(null)
  const [loading, setLoading]                 = useState(true)
  const [filtroEstado, setFiltroEstado]       = useState('todos')
  const [filtroSev, setFiltroSev]             = useState('todos')
  const [leidas, setLeidas]                   = useState(new Set())

  const load = async () => {
    try {
      const [nRes, rRes] = await Promise.all([
        notificacionesAPI.listar(
          filtroEstado !== 'todos' ? filtroEstado : null,
          filtroSev    !== 'todos' ? filtroSev    : null,
        ),
        notificacionesAPI.resumen(),
      ])
      setNotifs(nRes.data)
      setResumen(rRes.data)
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [filtroEstado, filtroSev])

  const marcarLeida = async (id) => {
    try {
      await notificacionesAPI.marcarLeida(id)
      setLeidas(prev => new Set([...prev, id]))
      setResumen(prev => prev ? { ...prev, no_leidas: Math.max(0, prev.no_leidas - 1) } : prev)
    } catch(e) {}
  }

  return (
    <div style={styles.wrapper} className="animate-fade">
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Notificaciones</h1>
          <p style={styles.subtitle}>Historial de alertas enviadas al agricultor</p>
        </div>
        <button onClick={load} className="btn btn-ghost" style={{ fontSize: '12px' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          Actualizar
        </button>
      </div>

      {/* Resumen */}
      {resumen && (
        <div style={styles.resumenGrid}>
          {[
            { label: 'Total',      val: resumen.total,      color: '#f0fdf4', bg: 'rgba(255,255,255,0.04)' },
            { label: 'Enviadas',   val: resumen.enviadas,   color: '#22c55e', bg: 'rgba(34,197,94,0.08)'   },
            { label: 'Pendientes', val: resumen.pendientes, color: '#fbbf24', bg: 'rgba(251,191,36,0.08)'  },
            { label: 'Sin leer',   val: resumen.no_leidas,  color: '#60a5fa', bg: 'rgba(96,165,250,0.08)'  },
            { label: 'Criticas',   val: resumen.criticas,   color: '#f87171', bg: 'rgba(248,113,113,0.08)' },
          ].map(item => (
            <div key={item.label} style={{ ...styles.resumenCard, background: item.bg }}>
              <div style={{ ...styles.resumenVal, color: item.color }}>{item.val}</div>
              <div style={styles.resumenLabel}>{item.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filters — dropdowns */}
      <div style={styles.filters}>
        <div style={styles.filterItem}>
          <label style={styles.filterLabel}>Estado</label>
          <select value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)} style={styles.select}>
            <option value="todos">Todos los estados</option>
            <option value="enviada">Enviada</option>
            <option value="pendiente">Pendiente</option>
            <option value="fallida">Fallida</option>
          </select>
        </div>
        <div style={styles.filterItem}>
          <label style={styles.filterLabel}>Severidad</label>
          <select value={filtroSev} onChange={e => setFiltroSev(e.target.value)} style={styles.select}>
            <option value="todos">Todas las severidades</option>
            <option value="critica">Critica</option>
            <option value="alta">Alta</option>
            <option value="media">Media</option>
            <option value="baja">Baja</option>
          </select>
        </div>
        <div style={styles.countTag}>{notifs.length} resultados</div>
      </div>

      {/* List */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: '100px', borderRadius: '12px' }} />)}
        </div>
      ) : notifs.length === 0 ? (
        <div style={styles.empty}>
          <div style={styles.emptyIcon}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#374151" strokeWidth="1.5">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
          </div>
          <div style={styles.emptyText}>Sin notificaciones</div>
          <div style={styles.emptySub}>No hay notificaciones que coincidan con los filtros seleccionados</div>
        </div>
      ) : (
        <div style={styles.notifList}>
          {notifs.map((n, i) => {
            const isLeida  = n.leida || leidas.has(n.id)
            const sevColor = SEV_COLOR[n.severidad] || '#6b7280'
            return (
              <div key={n.id} style={{
                ...styles.notifCard,
                opacity:     isLeida ? 0.55 : 1,
                borderLeft:  `4px solid ${isLeida ? '#374151' : sevColor}`,
                animationDelay: `${i * 0.03}s`,
              }} className="animate-fade">
                <div style={styles.notifLeft}>
                  {/* Top row */}
                  <div style={styles.notifTop}>
                    <span style={{ ...styles.sevBadge, color: sevColor, background: `${sevColor}12`, border: `1px solid ${sevColor}35` }}>
                      {n.severidad?.toUpperCase()}
                    </span>
                    <span style={styles.canalTag}>
                      {CANAL_ICON[n.canal] || ''} {n.canal}
                    </span>
                    <span style={{ ...styles.estadoTag, color: n.estado === 'enviada' ? '#22c55e' : n.estado === 'fallida' ? '#f87171' : '#fbbf24' }}>
                      {n.estado === 'enviada' ? 'Enviada' : n.estado === 'fallida' ? 'Fallida' : 'Pendiente'}
                    </span>
                    {!isLeida && <span style={styles.nuevaTag}>Nueva</span>}
                  </div>

                  {/* Title */}
                  <div style={styles.notifTitulo}>{n.titulo}</div>

                  {/* Meta */}
                  <div style={styles.notifMeta}>
                    <span style={{ fontFamily: 'monospace', color: '#4ade80', fontSize: '11px' }}>{n.id_logico}</span>
                    <span style={styles.metaDot}>·</span>
                    <span style={styles.metaItem}>{n.tipo}</span>
                    <span style={styles.metaDot}>·</span>
                    <span style={styles.metaItem}>{new Date(n.creada_en).toLocaleString('es-CO')}</span>
                  </div>
                </div>

                {!isLeida && (
                  <button onClick={() => marcarLeida(n.id)} style={styles.leerBtn}>
                    Marcar leida
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

const styles = {
  wrapper: { padding: '32px', maxWidth: '1000px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' },
  title: { fontFamily: "'Syne', sans-serif", fontSize: '26px', fontWeight: 700, color: '#f0fdf4' },
  subtitle: { fontSize: '13px', color: '#6b7280', marginTop: '4px' },
  resumenGrid: { display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px', marginBottom: '20px' },
  resumenCard: { borderRadius: '12px', padding: '16px', border: '1px solid rgba(34,197,94,0.08)', textAlign: 'center' },
  resumenVal: { fontFamily: "'Syne', sans-serif", fontSize: '28px', fontWeight: 800, lineHeight: 1 },
  resumenLabel: { fontSize: '11px', color: '#6b7280', marginTop: '5px' },
  filters: { display: 'flex', gap: '12px', marginBottom: '20px', alignItems: 'flex-end', flexWrap: 'wrap' },
  filterItem: { display: 'flex', flexDirection: 'column', gap: '5px' },
  filterLabel: { fontSize: '11px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px' },
  select: { padding: '9px 14px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#9ca3af', fontSize: '13px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", minWidth: '180px' },
  countTag: { background: 'rgba(34,197,94,0.08)', color: '#4ade80', padding: '6px 12px', borderRadius: '20px', fontSize: '12px', border: '1px solid rgba(34,197,94,0.15)', alignSelf: 'flex-end' },
  notifList: { display: 'flex', flexDirection: 'column', gap: '10px' },
  notifCard: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', borderRadius: '12px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.08)', transition: 'opacity 0.3s' },
  notifLeft: { flex: 1 },
  notifTop: { display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '7px', flexWrap: 'wrap' },
  sevBadge: { padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 700, letterSpacing: '0.5px' },
  canalTag: { fontSize: '11px', color: '#6b7280', background: 'rgba(107,114,128,0.1)', padding: '2px 8px', borderRadius: '4px' },
  estadoTag: { fontSize: '11px', fontWeight: 600 },
  nuevaTag: { background: 'rgba(96,165,250,0.15)', color: '#60a5fa', padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 600, border: '1px solid rgba(96,165,250,0.25)' },
  notifTitulo: { fontSize: '13px', color: '#f0fdf4', fontWeight: 500, marginBottom: '5px', lineHeight: 1.4 },
  notifMeta: { display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap' },
  metaDot: { color: '#374151', fontSize: '11px' },
  metaItem: { fontSize: '11px', color: '#4b5563' },
  leerBtn: { marginLeft: '16px', padding: '7px 14px', background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '8px', color: '#22c55e', fontSize: '12px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", whiteSpace: 'nowrap', transition: 'all 0.15s' },
  empty: { textAlign: 'center', padding: '80px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' },
  emptyIcon: { marginBottom: '4px' },
  emptyText: { fontSize: '18px', fontWeight: 600, color: '#f0fdf4', fontFamily: "'Syne', sans-serif" },
  emptySub: { fontSize: '13px', color: '#6b7280' },
}