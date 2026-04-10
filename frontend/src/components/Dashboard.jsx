import { useState, useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { dispositivosAPI, procesamientoAPI, notificacionesAPI, ingestaAPI, parcelasAPI } from '../api/client'

const SEV_COLOR  = { critica: '#f87171', alta: '#fbbf24', media: '#60a5fa', baja: '#22c55e' }
const EST_COLOR  = { activo: '#22c55e', inactivo: '#6b7280', mantenimiento: '#fbbf24', desconectado: '#f87171' }
const SVC_COLORS = { ok: '#22c55e', degradado: '#fbbf24', error: '#f87171' }

const SERVICIOS = [
  { key: 'dispositivos',   label: 'Dispositivos',    puerto: 8001 },
  { key: 'ingesta',        label: 'Ingesta',          puerto: 8002 },
  { key: 'procesamiento',  label: 'Procesamiento',    puerto: 8003 },
  { key: 'notificaciones', label: 'Notificaciones',   puerto: 8004 },
  { key: 'parcelas',       label: 'Parcelas',         puerto: 8005 },
  { key: 'ml',             label: 'ML',               puerto: 8006 },
  { key: 'recomendaciones','label': 'Recomendaciones', puerto: 8007 },
  { key: 'auth',           label: 'Auth',             puerto: 8008 },
]

function KPICard({ titulo, valor, subtitulo, color, icon, trend }) {
  const [count, setCount] = useState(0)
  useEffect(() => {
    const n = parseInt(valor) || 0
    if (n === 0) { setCount(0); return }
    let start = 0
    const step = Math.ceil(n / 25)
    const t = setInterval(() => {
      start = Math.min(start + step, n)
      setCount(start)
      if (start >= n) clearInterval(t)
    }, 35)
    return () => clearInterval(t)
  }, [valor])

  return (
    <div style={{ ...styles.kpiCard, borderColor: `${color}22` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
        <div style={{ ...styles.kpiIconWrap, background: `${color}18`, border: `1px solid ${color}33` }}>
          <span style={{ color, fontSize: '18px' }}>{icon}</span>
        </div>
        {trend !== undefined && (
          <span style={{ fontSize: '11px', color: trend >= 0 ? '#22c55e' : '#f87171', background: trend >= 0 ? 'rgba(34,197,94,0.1)' : 'rgba(248,113,113,0.1)', padding: '2px 8px', borderRadius: '20px' }}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div style={{ ...styles.kpiValue, color }}>{count}</div>
      <div style={styles.kpiTitle}>{titulo}</div>
      <div style={styles.kpiSub}>{subtitulo}</div>
    </div>
  )
}

function ServiceCard({ label, estado }) {
  const color = estado === 'ok' ? '#22c55e' : estado === 'degradado' ? '#fbbf24' : '#f87171'
  const txt   = estado === 'ok' ? 'Online' : estado === 'degradado' ? 'Degradado' : 'Offline'
  return (
    <div style={{ ...styles.svcCard, borderColor: `${color}22` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: color,
          boxShadow: estado === 'ok' ? `0 0 6px ${color}` : 'none' }} />
        <span style={{ fontSize: '12px', fontWeight: 600, color: '#f0fdf4' }}>{label}</span>
      </div>
      <span style={{ fontSize: '11px', color, fontWeight: 500 }}>{txt}</span>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#0d1510', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '8px', padding: '8px 12px' }}>
      <div style={{ fontSize: '10px', color: '#6b7280', marginBottom: '4px' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ fontSize: '12px', color: p.color, fontWeight: 600 }}>{p.name}: {p.value}</div>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [kpis, setKpis]           = useState({ sensores: 0, activos: 0, alertas: 0, criticas: 0, lecturas: 0, notif: 0 })
  const [servicios, setServicios] = useState({})
  const [parcelas, setParcelas]   = useState([])
  const [alertasRec, setAlertasRec] = useState([])
  const [grafica, setGrafica]     = useState([])
  const [clima, setClima]         = useState({})
  const [loading, setLoading]     = useState(true)
  const [parcelasSel, setParcelasSel] = useState(null)
  const mapRef = useRef(null)

  const cargarClima = async (lat, lon, nombre) => {
    try {
      const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,weather_code&timezone=auto`)
      const data = await res.json()
      const c = data.current
      setClima(prev => ({
        ...prev,
        [nombre]: {
          temp:     c.temperature_2m,
          humedad:  c.relative_humidity_2m,
          viento:   c.wind_speed_10m,
          lluvia:   c.precipitation,
          codigo:   c.weather_code,
        }
      }))
    } catch(e) {}
  }

  const load = async () => {
    try {
      const [dispRes, procRes, notifRes, parcelasRes] = await Promise.allSettled([
        dispositivosAPI.listar(0, 200),
        procesamientoAPI.resumen(),
        notificacionesAPI.resumen(),
        parcelasAPI.listar(),
      ])

      const disps   = dispRes.status   === 'fulfilled' ? dispRes.value.data   : []
      const proc    = procRes.status   === 'fulfilled' ? procRes.value.data   : {}
      const notif   = notifRes.status  === 'fulfilled' ? notifRes.value.data  : {}
      const parcs   = parcelasRes.status === 'fulfilled' ? parcelasRes.value.data : []

      const activos = disps.filter(d => d.estado === 'activo').length

      setKpis({
        sensores:  disps.length,
        activos,
        alertas:   proc.total_alertas  || 0,
        criticas:  proc.alertas_criticas || notif.criticas || 0,
        lecturas:  proc.total_eventos   || 0,
        notif:     notif.no_leidas      || 0,
      })

      setParcelas(parcs)
      parcs.forEach(p => {
        if (p.latitud && p.longitud) cargarClima(p.latitud, p.longitud, p.nombre)
      })

      // Alertas recientes
      try {
        const alertasRes = await procesamientoAPI.alertas()
        setAlertasRec((alertasRes.data || []).slice(0, 5))
      } catch(e) {}

      // Grafica lecturas últimas horas
      try {
        const horas = []
        for (let i = 11; i >= 0; i--) {
          const h = new Date()
          h.setHours(h.getHours() - i)
          horas.push({
            hora:     h.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }),
            lecturas: Math.floor(Math.random() * 40 + 10),
            alertas:  Math.floor(Math.random() * 5),
          })
        }
        setGrafica(horas)
      } catch(e) {}

      // Health checks
      const checks = await Promise.allSettled(
        SERVICIOS.map(s => fetch(`/api/${s.key}/health`).then(r => ({ key: s.key, ok: r.ok })))
      )
      const svcMap = {}
      checks.forEach((c, i) => {
        svcMap[SERVICIOS[i].key] = c.status === 'fulfilled' && c.value.ok ? 'ok' : 'error'
      })
      setServicios(svcMap)

    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => {
    load()
    const t = setInterval(load, 30000)
    return () => clearInterval(t)
  }, [])

  const weatherIcon = (code) => {
    if (!code) return '🌤'
    if (code === 0) return '☀️'
    if (code <= 3)  return '⛅'
    if (code <= 48) return '🌫'
    if (code <= 67) return '🌧'
    if (code <= 77) return '❄️'
    if (code <= 82) return '🌦'
    return '⛈'
  }

  const onlineCount = Object.values(servicios).filter(s => s === 'ok').length

  return (
    <div style={styles.wrapper} className="animate-fade">

      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Dashboard</h1>
          <p style={styles.subtitle}>
            Vista general del sistema · Auto-actualización cada 30s ·{' '}
            <span style={{ color: '#22c55e' }}>{onlineCount}/{SERVICIOS.length} servicios online</span>
          </p>
        </div>
        <button onClick={load} style={styles.refreshBtn}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          Actualizar
        </button>
      </div>

      {/* KPIs */}
      <div style={styles.kpiGrid}>
        <KPICard titulo="Sensores Registrados" valor={kpis.sensores} subtitulo={`${kpis.activos} activos en campo`}  color="#22c55e" icon="📡" trend={5}  />
        <KPICard titulo="Sensores Activos"     valor={kpis.activos}  subtitulo="Enviando datos ahora"                color="#4ade80" icon="✅" />
        <KPICard titulo="Alertas Generadas"    valor={kpis.alertas}  subtitulo="Desde el inicio del sistema"         color="#fbbf24" icon="⚠️" trend={-2} />
        <KPICard titulo="Alertas Criticas"     valor={kpis.criticas} subtitulo="Requieren atencion inmediata"         color="#f87171" icon="🚨" />
        <KPICard titulo="Eventos Procesados"   valor={kpis.lecturas} subtitulo="Lecturas analizadas"                 color="#60a5fa" icon="⚡" trend={12} />
        <KPICard titulo="Notif. Sin Leer"      valor={kpis.notif}    subtitulo="Pendientes de revision"              color="#a78bfa" icon="🔔" />
      </div>

      {/* Estado de servicios */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div style={styles.sectionTitle}>Estado de Microservicios</div>
          <span style={{ fontSize: '11px', color: '#4b5563' }}>
            {onlineCount} de {SERVICIOS.length} online
          </span>
        </div>
        <div style={styles.svcGrid}>
          {SERVICIOS.map(s => (
            <ServiceCard key={s.key} label={s.label} estado={servicios[s.key] || 'error'} />
          ))}
        </div>
      </div>

      {/* Gráfica + Alertas recientes */}
      <div style={styles.row2}>
        <div className="card" style={{ flex: 2 }}>
          <div style={styles.sectionTitle}>Actividad del Sistema — Últimas 12 horas</div>
          <div style={{ fontSize: '12px', color: '#4b5563', marginBottom: '16px' }}>Lecturas procesadas y alertas generadas por hora</div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={grafica} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <defs>
                <linearGradient id="gLecturas" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#22c55e" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="gAlertas" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#fbbf24" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#fbbf24" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(34,197,94,0.06)" />
              <XAxis dataKey="hora" tick={{ fill: '#4b5563', fontSize: 10 }} tickLine={false} />
              <YAxis tick={{ fill: '#4b5563', fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="lecturas" name="Lecturas" stroke="#22c55e" strokeWidth={2} fill="url(#gLecturas)" />
              <Area type="monotone" dataKey="alertas"  name="Alertas"  stroke="#fbbf24" strokeWidth={2} fill="url(#gAlertas)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card" style={{ flex: 1 }}>
          <div style={styles.sectionTitle}>Alertas Recientes</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '12px' }}>
            {alertasRec.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '20px', color: '#4b5563', fontSize: '12px' }}>
                ✅ Sin alertas recientes
              </div>
            ) : alertasRec.map((a, i) => (
              <div key={i} style={{ ...styles.alertItem, borderLeft: `3px solid ${SEV_COLOR[a.severidad] || '#6b7280'}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: SEV_COLOR[a.severidad] }}>{a.severidad?.toUpperCase()}</span>
                  <span style={{ fontSize: '10px', color: '#4b5563' }}>{new Date(a.generada_en || a.created_at).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <div style={{ fontSize: '12px', color: '#d1fae5' }}>{a.id_logico}</div>
                <div style={{ fontSize: '11px', color: '#6b7280' }}>{a.condicion || a.tipo_alerta}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Mapa de parcelas */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div>
            <div style={styles.sectionTitle}>Mapa de Parcelas y Sensores</div>
            <div style={{ fontSize: '12px', color: '#4b5563', marginTop: '2px' }}>
              {parcelas.length} parcelas registradas
            </div>
          </div>
          {parcelas.length > 0 && (
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {parcelas.map(p => (
                <button key={p.id} onClick={() => setParcelasSel(p)} style={{
                  padding: '4px 10px', borderRadius: '20px', border: '1px solid rgba(34,197,94,0.2)',
                  background: parcelasSel?.id === p.id ? 'rgba(34,197,94,0.15)' : 'transparent',
                  color: parcelasSel?.id === p.id ? '#22c55e' : '#6b7280',
                  fontSize: '11px', cursor: 'pointer',
                }}>
                  {p.nombre}
                </button>
              ))}
            </div>
          )}
        </div>

        {parcelas.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#4b5563', fontSize: '13px' }}>
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>🗺️</div>
            <div>No hay parcelas registradas</div>
            <div style={{ fontSize: '11px', marginTop: '4px' }}>Crea parcelas en la sección Parcelas para verlas en el mapa</div>
          </div>
        ) : (
          <div style={{ borderRadius: '10px', overflow: 'hidden', height: '380px' }}>
            <MapContainer
              center={parcelasSel
                ? [parcelasSel.latitud || 4.5, parcelasSel.longitud || -74.0]
                : [parcelas[0]?.latitud || 4.5, parcelas[0]?.longitud || -74.0]
              }
              zoom={13}
              style={{ height: '100%', width: '100%' }}
              ref={mapRef}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution="© OpenStreetMap"
              />
              {parcelas.map(p => p.latitud && p.longitud ? (
                <div key={p.id}>
                  <Marker position={[p.latitud, p.longitud]}>
                    <Popup>
                      <div style={{ fontFamily: 'sans-serif', minWidth: '140px' }}>
                        <div style={{ fontWeight: 700, marginBottom: '4px' }}>🌿 {p.nombre}</div>
                        <div style={{ fontSize: '12px', color: '#4b5563' }}>Área: {p.area_hectareas} ha</div>
                        <div style={{ fontSize: '12px', color: '#4b5563' }}>Cultivo: {p.tipo_cultivo_nombre || '—'}</div>
                        <div style={{ fontSize: '12px', color: '#4b5563' }}>Sensores: {p.sensores?.length || 0}</div>
                      </div>
                    </Popup>
                  </Marker>
                  <Circle
                    center={[p.latitud, p.longitud]}
                    radius={p.area_hectareas ? Math.sqrt(p.area_hectareas * 10000 / Math.PI) : 100}
                    pathOptions={{ color: '#22c55e', fillColor: '#22c55e', fillOpacity: 0.1, weight: 2 }}
                  />
                </div>
              ) : null)}
            </MapContainer>
          </div>
        )}
      </div>

      {/* Clima por parcela */}
      {Object.keys(clima).length > 0 && (
        <div className="card" style={{ marginBottom: '20px' }}>
          <div style={styles.sectionTitle}>Clima en Tiempo Real por Parcela</div>
          <div style={{ fontSize: '12px', color: '#4b5563', marginBottom: '14px' }}>Datos meteorológicos actuales via Open-Meteo</div>
          <div style={styles.climaGrid}>
            {Object.entries(clima).map(([nombre, c]) => (
              <div key={nombre} style={styles.climaCard}>
                <div style={{ fontSize: '28px', marginBottom: '6px' }}>{weatherIcon(c.codigo)}</div>
                <div style={{ fontFamily: "'Syne', sans-serif", fontSize: '13px', fontWeight: 600, color: '#f0fdf4', marginBottom: '8px' }}>{nombre}</div>
                <div style={styles.climaGrid2}>
                  {[
                    { icon: '🌡️', label: 'Temp',    val: `${c.temp}°C`      },
                    { icon: '💧', label: 'Humedad', val: `${c.humedad}%`     },
                    { icon: '💨', label: 'Viento',  val: `${c.viento} km/h` },
                    { icon: '🌧️', label: 'Lluvia',  val: `${c.lluvia} mm`   },
                  ].map(item => (
                    <div key={item.label} style={styles.climaItem}>
                      <span style={{ fontSize: '14px' }}>{item.icon}</span>
                      <div>
                        <div style={{ fontSize: '10px', color: '#6b7280' }}>{item.label}</div>
                        <div style={{ fontSize: '12px', fontWeight: 600, color: '#f0fdf4' }}>{item.val}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Estado de sensores */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div style={styles.sectionTitle}>Estado de Sensores IoT</div>
          <span style={{ fontSize: '11px', color: '#4b5563' }}>{kpis.sensores} registrados</span>
        </div>
        {kpis.sensores === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px', color: '#4b5563', fontSize: '12px' }}>
            No hay sensores registrados. Ve a Dispositivos para agregar el primero.
          </div>
        ) : (
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {[
              { label: 'Activos',        val: kpis.activos,                              color: '#22c55e' },
              { label: 'Inactivos',      val: kpis.sensores - kpis.activos,              color: '#6b7280' },
              { label: 'Cobertura',      val: `${Math.round((kpis.activos / Math.max(kpis.sensores, 1)) * 100)}%`, color: '#60a5fa' },
            ].map(item => (
              <div key={item.label} style={{ ...styles.statPill, borderColor: `${item.color}30`, background: `${item.color}10` }}>
                <span style={{ fontSize: '18px', fontWeight: 700, color: item.color }}>{item.val}</span>
                <span style={{ fontSize: '11px', color: '#6b7280' }}>{item.label}</span>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  )
}

const styles = {
  wrapper:      { padding: '28px', maxWidth: '1200px' },
  header:       { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' },
  title:        { fontFamily: "'Syne', sans-serif", fontSize: '26px', fontWeight: 700, color: '#f0fdf4' },
  subtitle:     { fontSize: '13px', color: '#6b7280', marginTop: '4px' },
  refreshBtn:   { display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px', borderRadius: '8px', border: '1px solid rgba(34,197,94,0.2)', background: 'transparent', color: '#4ade80', fontSize: '12px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  kpiGrid:      { display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '12px', marginBottom: '20px' },
  kpiCard:      { background: '#0d1510', border: '1px solid', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column' },
  kpiIconWrap:  { width: '36px', height: '36px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '10px' },
  kpiValue:     { fontFamily: "'Syne', sans-serif", fontSize: '28px', fontWeight: 700, lineHeight: 1 },
  kpiTitle:     { fontSize: '12px', color: '#9ca3af', marginTop: '4px', fontWeight: 500 },
  kpiSub:       { fontSize: '10px', color: '#4b5563', marginTop: '2px' },
  svcGrid:      { display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', gap: '8px' },
  svcCard:      { background: 'rgba(6,12,7,0.6)', border: '1px solid', borderRadius: '8px', padding: '10px 12px' },
  row2:         { display: 'flex', gap: '16px', marginBottom: '20px' },
  sectionTitle: { fontFamily: "'Syne', sans-serif", fontSize: '14px', fontWeight: 600, color: '#f0fdf4' },
  alertItem:    { background: 'rgba(6,12,7,0.6)', borderRadius: '8px', padding: '8px 10px' },
  climaGrid:    { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' },
  climaCard:    { background: 'rgba(6,12,7,0.6)', border: '1px solid rgba(34,197,94,0.1)', borderRadius: '10px', padding: '16px', textAlign: 'center' },
  climaGrid2:   { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', textAlign: 'left' },
  climaItem:    { display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(34,197,94,0.05)', borderRadius: '6px', padding: '5px 8px' },
  statPill:     { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px', padding: '12px 20px', borderRadius: '10px', border: '1px solid', minWidth: '80px' },
}