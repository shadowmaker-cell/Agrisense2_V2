import { useState, useEffect } from 'react'
import { procesamientoAPI } from '../api/client'

const SEV_CONFIG = {
  critica: { color: '#f87171', bg: 'rgba(248,113,113,0.08)', border: 'rgba(248,113,113,0.2)', label: 'CRITICA' },
  alta:    { color: '#fbbf24', bg: 'rgba(251,191,36,0.08)',  border: 'rgba(251,191,36,0.2)',  label: 'ALTA'    },
  media:   { color: '#60a5fa', bg: 'rgba(96,165,250,0.08)',  border: 'rgba(96,165,250,0.2)',  label: 'MEDIA'   },
  baja:    { color: '#22c55e', bg: 'rgba(34,197,94,0.08)',   border: 'rgba(34,197,94,0.2)',   label: 'BAJA'    },
}

export default function Alertas() {
  const [alertas, setAlertas]         = useState([])
  const [loading, setLoading]         = useState(true)
  const [filtroSev, setFiltroSev]     = useState('todos')
  const [filtroTipo, setFiltroTipo]   = useState('')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const load = async () => {
    try {
      const res = await procesamientoAPI.alertas(
        filtroSev !== 'todos' ? filtroSev : null,
        filtroTipo || null
      )
      setAlertas(res.data)
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [filtroSev, filtroTipo])

  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(load, 15000)
    return () => clearInterval(interval)
  }, [autoRefresh, filtroSev, filtroTipo])

  const criticas = alertas.filter(a => a.severidad === 'critica').length
  const altas    = alertas.filter(a => a.severidad === 'alta').length
  const medias   = alertas.filter(a => a.severidad === 'media').length
  const tipos    = [...new Set(alertas.map(a => a.tipo_alerta))]

  return (
    <div style={styles.wrapper} className="animate-fade">
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Panel de Alertas</h1>
          <p style={styles.subtitle}>{alertas.length} alertas detectadas por el Stream Processor</p>
        </div>
        <div style={styles.headerActions}>
          <button onClick={load} className="btn btn-ghost" style={{ fontSize: '12px', padding: '7px 14px' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Actualizar
          </button>
          <div onClick={() => setAutoRefresh(!autoRefresh)} style={{
            ...styles.refreshToggle,
            background:   autoRefresh ? 'rgba(34,197,94,0.1)' : 'rgba(107,114,128,0.1)',
            borderColor:  autoRefresh ? 'rgba(34,197,94,0.3)' : 'rgba(107,114,128,0.2)',
            color:        autoRefresh ? '#22c55e' : '#6b7280',
          }}>
            <div style={{ ...styles.refreshDot, background: autoRefresh ? '#22c55e' : '#6b7280', animation: autoRefresh ? 'pulse-green 2s infinite' : 'none' }} />
            {autoRefresh ? 'Auto: ON' : 'Auto: OFF'}
          </div>
        </div>
      </div>

      {/* Summary cards */}
      <div style={styles.summaryGrid}>
        {[
          { label: 'Total alertas', val: alertas.length, color: '#f0fdf4', bg: 'rgba(255,255,255,0.04)' },
          { label: 'Criticas',      val: criticas,        color: '#f87171', bg: 'rgba(248,113,113,0.08)' },
          { label: 'Altas',         val: altas,           color: '#fbbf24', bg: 'rgba(251,191,36,0.08)'  },
          { label: 'Medias',        val: medias,          color: '#60a5fa', bg: 'rgba(96,165,250,0.08)'  },
        ].map(item => (
          <div key={item.label} style={{ ...styles.summaryCard, background: item.bg }}>
            <div style={{ ...styles.summaryVal, color: item.color }}>{item.val}</div>
            <div style={styles.summaryLabel}>{item.label}</div>
          </div>
        ))}
      </div>

      {/* Filters — dropdowns */}
      <div style={styles.filters}>
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
        <div style={styles.filterItem}>
          <label style={styles.filterLabel}>Tipo de alerta</label>
          <select value={filtroTipo} onChange={e => setFiltroTipo(e.target.value)} style={styles.select}>
            <option value="">Todos los tipos</option>
            {tipos.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div style={styles.countTag}>{alertas.length} resultados</div>
      </div>

      {/* Alert list */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {[...Array(5)].map((_, i) => <div key={i} className="skeleton" style={{ height: '90px', borderRadius: '12px' }} />)}
        </div>
      ) : alertas.length === 0 ? (
        <div style={styles.empty}>
          <div style={styles.emptyIcon}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#374151" strokeWidth="1.5">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </div>
          <div style={styles.emptyText}>Sin alertas activas</div>
          <div style={styles.emptySub}>El sistema esta operando dentro de los parametros normales</div>
        </div>
      ) : (
        <div style={styles.alertList}>
          {alertas.map((a, i) => {
            const sev = SEV_CONFIG[a.severidad] || SEV_CONFIG.baja
            return (
              <div key={a.id} style={{
                ...styles.alertCard,
                borderColor: sev.border,
                borderLeft:  `4px solid ${sev.color}`,
                animationDelay: `${i * 0.03}s`,
              }} className="animate-fade">

                {/* Left: info */}
                <div style={styles.alertLeft}>
                  <div style={styles.alertTopRow}>
                    <span style={{ ...styles.sevTag, color: sev.color, background: sev.bg, border: `1px solid ${sev.border}` }}>
                      {sev.label}
                    </span>
                    <span style={styles.tipoTag}>{a.tipo_alerta}</span>
                    <span style={styles.sensorTag}>{a.id_logico}</span>
                  </div>
                  <div style={styles.alertCondicion}>{a.condicion}</div>
                  <div style={styles.alertMeta}>
                    <span>{a.tipo_metrica}</span>
                    <span style={styles.dot}>·</span>
                    <span>{new Date(a.generada_en).toLocaleString('es-CO')}</span>
                  </div>
                </div>

                {/* Right: value */}
                <div style={styles.alertRight}>
                  <div style={{ ...styles.alertValor, color: sev.color }}>{a.valor_detectado}</div>
                  <div style={styles.alertUnidad}>{a.tipo_metrica?.includes('temperatura') ? 'C' : a.tipo_metrica?.includes('humedad') ? '%' : ''}</div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <style>{`
        @keyframes pulse-green {
          0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.4); }
          50%       { box-shadow: 0 0 0 5px rgba(34,197,94,0); }
        }
      `}</style>
    </div>
  )
}

const styles = {
  wrapper: { padding: '32px', maxWidth: '1000px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' },
  title: { fontFamily: "'Syne', sans-serif", fontSize: '26px', fontWeight: 700, color: '#f0fdf4' },
  subtitle: { fontSize: '13px', color: '#6b7280', marginTop: '4px' },
  headerActions: { display: 'flex', gap: '10px', alignItems: 'center' },
  refreshToggle: { display: 'flex', alignItems: 'center', gap: '6px', padding: '7px 12px', borderRadius: '20px', border: '1px solid', fontSize: '12px', cursor: 'pointer', fontWeight: 500 },
  refreshDot: { width: '7px', height: '7px', borderRadius: '50%' },
  summaryGrid: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' },
  summaryCard: { borderRadius: '12px', padding: '16px 20px', border: '1px solid rgba(34,197,94,0.08)', textAlign: 'center' },
  summaryVal: { fontFamily: "'Syne', sans-serif", fontSize: '32px', fontWeight: 800, lineHeight: 1 },
  summaryLabel: { fontSize: '12px', color: '#6b7280', marginTop: '4px' },
  filters: { display: 'flex', gap: '12px', marginBottom: '20px', alignItems: 'flex-end', flexWrap: 'wrap' },
  filterItem: { display: 'flex', flexDirection: 'column', gap: '5px' },
  filterLabel: { fontSize: '11px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px' },
  select: { padding: '9px 14px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#9ca3af', fontSize: '13px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", minWidth: '180px' },
  countTag: { background: 'rgba(34,197,94,0.08)', color: '#4ade80', padding: '6px 12px', borderRadius: '20px', fontSize: '12px', border: '1px solid rgba(34,197,94,0.15)', alignSelf: 'flex-end' },
  alertList: { display: 'flex', flexDirection: 'column', gap: '10px' },
  alertCard: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', borderRadius: '12px', background: '#0d1510', border: '1px solid' },
  alertLeft: { flex: 1 },
  alertTopRow: { display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '6px', flexWrap: 'wrap' },
  sevTag: { padding: '2px 10px', borderRadius: '4px', fontSize: '10px', fontWeight: 700, letterSpacing: '0.6px' },
  tipoTag: { fontSize: '11px', color: '#6b7280', background: 'rgba(107,114,128,0.1)', padding: '2px 8px', borderRadius: '4px' },
  sensorTag: { fontFamily: 'monospace', fontSize: '11px', color: '#4ade80' },
  alertCondicion: { fontSize: '13px', color: '#f0fdf4', fontWeight: 500, marginBottom: '4px' },
  alertMeta: { display: 'flex', gap: '6px', fontSize: '11px', color: '#4b5563' },
  dot: { color: '#374151' },
  alertRight: { textAlign: 'right', marginLeft: '16px' },
  alertValor: { fontFamily: "'Syne', sans-serif", fontSize: '26px', fontWeight: 800 },
  alertUnidad: { fontSize: '11px', color: '#6b7280' },
  empty: { textAlign: 'center', padding: '80px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center' },
  emptyIcon: { marginBottom: '12px' },
  emptyText: { fontSize: '18px', fontWeight: 600, color: '#f0fdf4', fontFamily: "'Syne', sans-serif", marginBottom: '6px' },
  emptySub: { fontSize: '13px', color: '#6b7280' },
}