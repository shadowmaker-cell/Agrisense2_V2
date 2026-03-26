import { useState, useEffect } from 'react'
import { dispositivosAPI, procesamientoAPI, notificacionesAPI, ingestaAPI } from '../api/client'

function KPICard({ titulo, valor, subtitulo, color, icon, delay = 0 }) {
  const [count, setCount] = useState(0)
  useEffect(() => {
    const n = parseInt(valor) || 0
    if (n === 0) { setCount(0); return }
    let start = 0
    const step = Math.ceil(n / 30)
    const t = setInterval(() => {
      start = Math.min(start + step, n)
      setCount(start)
      if (start >= n) clearInterval(t)
    }, 30)
    return () => clearInterval(t)
  }, [valor])

  return (
    <div style={{ ...styles.kpiCard, animationDelay: `${delay}s`, borderColor: `${color}22` }}>
      <div style={{ ...styles.kpiIconWrap, background: `${color}18`, border: `1px solid ${color}33` }}>
        <span style={{ color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{icon}</span>
      </div>
      <div style={{ ...styles.kpiValue, color }}>{count}</div>
      <div style={styles.kpiTitle}>{titulo}</div>
      <div style={styles.kpiSub}>{subtitulo}</div>
    </div>
  )
}

const SENSORES_SIM = [
  { id: 'SOIL_HUM_01', metric: 'humedad_suelo',    unit: '%',    min: 5,   max: 95   },
  { id: 'AIR_TEMP_01', metric: 'temperatura_aire', unit: 'C',    min: -5,  max: 42   },
  { id: 'SOIL_PH_01',  metric: 'ph_suelo',         unit: 'pH',   min: 4,   max: 9    },
  { id: 'LUX_01',      metric: 'luz',              unit: 'Lux',  min: 200, max: 8000 },
  { id: 'WIND_01',     metric: 'velocidad_viento', unit: 'km/h', min: 0,   max: 60   },
  { id: 'RAIN_01',     metric: 'lluvia',           unit: 'mm',   min: 0,   max: 80   },
  { id: 'BATT_01',     metric: 'voltaje_bateria',  unit: 'V',    min: 3.0, max: 4.2  },
  { id: 'WAT_PH_01',   metric: 'ph_agua',          unit: 'pH',   min: 5,   max: 8.5  },
]

export default function Dashboard() {
  const [resumenProc, setResumenProc]   = useState(null)
  const [resumenNotif, setResumenNotif] = useState(null)
  const [dispositivos, setDispositivos] = useState([])
  const [services, setServices]         = useState({})
  const [loading, setLoading]           = useState(true)
  const [simLoading, setSimLoading]     = useState(false)
  const [simMsg, setSimMsg]             = useState('')

  const load = async () => {
    try {
      const [proc, notif, disp] = await Promise.allSettled([
        procesamientoAPI.resumen(),
        notificacionesAPI.resumen(),
        dispositivosAPI.listar(0, 100),
      ])
      if (proc.status  === 'fulfilled') setResumenProc(proc.value.data)
      if (notif.status === 'fulfilled') setResumenNotif(notif.value.data)
      if (disp.status  === 'fulfilled') setDispositivos(disp.value.data)
      const checks = await Promise.allSettled([
        dispositivosAPI.health(),
        notificacionesAPI.health(),
        procesamientoAPI.health(),
      ])
      setServices({
        dispositivos:   checks[0].status === 'fulfilled' ? checks[0].value.data.estado : 'error',
        notificaciones: checks[1].status === 'fulfilled' ? checks[1].value.data.estado : 'error',
        procesamiento:  checks[2].status === 'fulfilled' ? checks[2].value.data.estado : 'error',
      })
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, 30000)
    return () => clearInterval(interval)
  }, [])

  const generarDatos = async () => {
    setSimLoading(true)
    setSimMsg('')
    let enviados = 0
    let alertasTotal = 0
    try {
      for (const s of SENSORES_SIM) {
        const valor = parseFloat((Math.random() * (s.max - s.min) + s.min).toFixed(2))
        await ingestaAPI.enviarLectura({
          dispositivo_id: 1,
          id_logico: s.id,
          tipo_metrica: s.metric,
          valor_metrica: valor,
          unidad: s.unit,
        })
        const resultado = await procesamientoAPI.procesarManual({
          dispositivo_id: 1,
          id_logico: s.id,
          tipo_metrica: s.metric,
          valor_metrica: valor,
          unidad: s.unit,
        })
        if (resultado.data.alertas_generadas > 0) {
          alertasTotal += resultado.data.alertas_generadas
          const tipos = resultado.data.tipos_alerta
          await notificacionesAPI.enviar({
            dispositivo_id: 1,
            id_logico: s.id,
            tipo_alerta: tipos[0],
            tipo_metrica: s.metric,
            valor: valor,
            condicion: `Valor ${valor} ${s.unit} — ${tipos.join(', ')}`,
            severidad: resultado.data.alertas_generadas > 1 ? 'critica' : 'alta',
            canal: 'push',
          })
        }
        enviados++
      }
      setSimMsg(`✅ ${enviados} lecturas enviadas · ${alertasTotal} alertas generadas`)
      setTimeout(load, 1000)
    } catch(e) {
      setSimMsg('❌ Error enviando datos simulados')
    } finally {
      setSimLoading(false)
      setTimeout(() => setSimMsg(''), 5000)
    }
  }

  const activos = dispositivos.filter(d => d.estado === 'activo').length
  const distData = [
    { label: 'Suelo',     count: dispositivos.filter(d => d.tipo_dispositivo_id <= 4).length,                                 color: '#22c55e', bg: 'rgba(34,197,94,0.12)'   },
    { label: 'Ambiental', count: dispositivos.filter(d => d.tipo_dispositivo_id >= 5 && d.tipo_dispositivo_id <= 9).length,   color: '#60a5fa', bg: 'rgba(96,165,250,0.12)'  },
    { label: 'Agua',      count: dispositivos.filter(d => d.tipo_dispositivo_id >= 10 && d.tipo_dispositivo_id <= 13).length, color: '#2dd4bf', bg: 'rgba(45,212,191,0.12)'  },
    { label: 'Infra',     count: dispositivos.filter(d => d.tipo_dispositivo_id >= 14).length,                                color: '#a78bfa', bg: 'rgba(167,139,250,0.12)' },
  ]

  return (
    <div style={styles.wrapper} className="animate-fade">
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Dashboard</h1>
          <p style={styles.subtitle}>Resumen general del sistema AgriSense</p>
        </div>
        <div style={styles.headerRight}>
          <button onClick={generarDatos} disabled={simLoading} style={styles.simBtn}>
            {simLoading ? <span style={styles.spinner} /> : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
              </svg>
            )}
            {simLoading ? 'Enviando...' : 'Generar datos simulados'}
          </button>
          {simMsg && <span style={{ fontSize: '12px', color: simMsg.startsWith('✅') ? '#22c55e' : '#f87171' }}>{simMsg}</span>}
        </div>
      </div>

      <div style={styles.servicesRow}>
        {[
          { nombre: 'Dispositivos',   status: services.dispositivos   },
          { nombre: 'Ingesta IoT',    status: 'ok'                    },
          { nombre: 'Procesamiento',  status: services.procesamiento  },
          { nombre: 'Notificaciones', status: services.notificaciones },
        ].map(s => (
          <div key={s.nombre} style={styles.serviceBadge}>
            <div style={{ ...styles.serviceDot, background: s.status === 'ok' ? '#22c55e' : '#f87171', animation: s.status === 'ok' ? 'pulse-green 2s infinite' : 'none' }} />
            <span style={styles.serviceNombre}>{s.nombre}</span>
            <span style={{ fontSize: '11px', fontWeight: 600, color: s.status === 'ok' ? '#22c55e' : '#f87171' }}>
              {s.status === 'ok' ? 'Online' : 'Offline'}
            </span>
          </div>
        ))}
      </div>

      {loading ? (
        <div style={styles.kpiGrid}>
          {[...Array(6)].map((_, i) => <div key={i} className="skeleton" style={{ height: '150px', borderRadius: '16px' }} />)}
        </div>
      ) : (
        <div style={styles.kpiGrid}>
          <KPICard titulo="Sensores Totales"   valor={dispositivos.length}              subtitulo="Registrados en el sistema"  color="#22c55e" delay={0}
            icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>} />
          <KPICard titulo="Sensores Activos"   valor={activos}                           subtitulo="Transmitiendo en campo"     color="#4ade80" delay={0.06}
            icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>} />
          <KPICard titulo="Eventos Procesados" valor={resumenProc?.total_eventos || 0}   subtitulo="Por el Stream Processor"    color="#60a5fa" delay={0.12}
            icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>} />
          <KPICard titulo="Alertas Criticas"   valor={resumenProc?.alertas_criticas||0}  subtitulo="Atencion inmediata"         color="#f87171" delay={0.18}
            icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>} />
          <KPICard titulo="Alertas Altas"      valor={resumenProc?.alertas_altas||0}     subtitulo="Monitoreo prioritario"      color="#fbbf24" delay={0.24}
            icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>} />
          <KPICard titulo="Notificaciones"     valor={resumenNotif?.total||0}            subtitulo={`${resumenNotif?.no_leidas||0} sin leer`} color="#a78bfa" delay={0.30}
            icon={<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>} />
        </div>
      )}

      <div style={styles.bottomGrid}>
        <div className="card" style={{ flex: 1 }}>
          <div style={styles.cardTitle}>Distribucion de Sensores</div>
          <div style={styles.barChart}>
            {distData.map(item => (
              <div key={item.label} style={styles.barItem}>
                <div style={{ ...styles.barCat, background: item.bg, color: item.color }}>{item.label}</div>
                <div style={styles.barTrack}>
                  <div style={{ ...styles.barFill, width: `${dispositivos.length ? (item.count / dispositivos.length * 100) : 0}%`, background: item.color }} />
                </div>
                <div style={{ ...styles.barCount, color: item.color }}>{item.count}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="card" style={{ flex: 1 }}>
          <div style={styles.cardTitle}>Estado de Alertas</div>
          <div style={styles.alertSummary}>
            {[
              { label: 'Criticas', val: resumenProc?.alertas_criticas || 0, color: '#f87171', bg: 'rgba(248,113,113,0.08)' },
              { label: 'Altas',    val: resumenProc?.alertas_altas    || 0, color: '#fbbf24', bg: 'rgba(251,191,36,0.08)'  },
              { label: 'Medias',   val: resumenProc?.alertas_medias   || 0, color: '#60a5fa', bg: 'rgba(96,165,250,0.08)'  },
              { label: 'Total',    val: resumenProc?.total_alertas    || 0, color: '#22c55e', bg: 'rgba(34,197,94,0.08)'   },
            ].map(item => (
              <div key={item.label} style={{ ...styles.alertRow, background: item.bg }}>
                <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: item.color, flexShrink: 0 }} />
                <span style={{ flex: 1, fontSize: '13px', color: '#9ca3af' }}>{item.label}</span>
                <span style={{ fontFamily: "'Syne', sans-serif", fontSize: '22px', fontWeight: 700, color: item.color }}>{item.val}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes pulse-green {
          0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.4); }
          50%       { box-shadow: 0 0 0 5px rgba(34,197,94,0); }
        }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}

const styles = {
  wrapper: { padding: '32px', maxWidth: '1200px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' },
  title: { fontFamily: "'Syne', sans-serif", fontSize: '26px', fontWeight: 700, color: '#f0fdf4' },
  subtitle: { fontSize: '13px', color: '#6b7280', marginTop: '4px' },
  headerRight: { display: 'flex', alignItems: 'center', gap: '12px' },
  simBtn: { display: 'flex', alignItems: 'center', gap: '7px', padding: '9px 16px', borderRadius: '10px', background: 'rgba(34,197,94,0.12)', color: '#22c55e', fontSize: '12px', fontWeight: 600, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.2s', border: '1px solid rgba(34,197,94,0.25)' },
  spinner: { width: '14px', height: '14px', border: '2px solid rgba(34,197,94,0.3)', borderTop: '2px solid #22c55e', borderRadius: '50%', animation: 'spin 0.7s linear infinite', display: 'inline-block' },
  servicesRow: { display: 'flex', gap: '10px', marginBottom: '24px', flexWrap: 'wrap' },
  serviceBadge: { display: 'flex', alignItems: 'center', gap: '7px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.1)', borderRadius: '8px', padding: '7px 14px' },
  serviceDot: { width: '8px', height: '8px', borderRadius: '50%' },
  serviceNombre: { fontSize: '12px', color: '#9ca3af' },
  kpiGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' },
  kpiCard: { background: '#0d1510', border: '1px solid rgba(34,197,94,0.1)', borderRadius: '16px', padding: '24px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', animation: 'fadeIn 0.4s ease both' },
  kpiIconWrap: { width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '14px' },
  kpiValue: { fontFamily: "'Syne', sans-serif", fontSize: '40px', fontWeight: 800, lineHeight: 1, marginBottom: '6px' },
  kpiTitle: { fontSize: '13px', fontWeight: 600, color: '#f0fdf4', marginBottom: '3px' },
  kpiSub: { fontSize: '11px', color: '#6b7280' },
  bottomGrid: { display: 'flex', gap: '16px' },
  cardTitle: { fontFamily: "'Syne', sans-serif", fontSize: '14px', fontWeight: 600, color: '#f0fdf4', marginBottom: '18px' },
  barChart: { display: 'flex', flexDirection: 'column', gap: '14px' },
  barItem: { display: 'flex', alignItems: 'center', gap: '10px' },
  barCat: { fontSize: '11px', fontWeight: 600, padding: '3px 10px', borderRadius: '20px', width: '72px', textAlign: 'center' },
  barTrack: { flex: 1, height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' },
  barFill: { height: '100%', borderRadius: '4px', transition: 'width 0.8s ease' },
  barCount: { fontSize: '14px', fontWeight: 700, width: '20px', textAlign: 'right' },
  alertSummary: { display: 'flex', flexDirection: 'column', gap: '10px' },
  alertRow: { display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 14px', borderRadius: '10px' },
}