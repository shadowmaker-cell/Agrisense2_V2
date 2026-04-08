import { useState, useEffect, useRef } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { ingestaAPI, procesamientoAPI, dispositivosAPI } from '../api/client'

const METRICA_CONFIG = {
  humedad_suelo:    { color: '#22c55e', unit: '%'     },
  ph_suelo:         { color: '#a78bfa', unit: 'pH'    },
  ec_suelo:         { color: '#f59e0b', unit: 'mS'    },
  temperatura_suelo:{ color: '#fb923c', unit: 'C'     },
  temperatura_aire: { color: '#f87171', unit: 'C'     },
  humedad_aire:     { color: '#38bdf8', unit: '%'     },
  luz:              { color: '#fbbf24', unit: 'Lux'   },
  velocidad_viento: { color: '#60a5fa', unit: 'km/h'  },
  lluvia:           { color: '#818cf8', unit: 'mm'    },
  ph_agua:          { color: '#2dd4bf', unit: 'pH'    },
  caudal:           { color: '#06b6d4', unit: 'L/m'   },
  voltaje_valvula:  { color: '#84cc16', unit: 'V'     },
  consumo_bomba:    { color: '#f97316', unit: 'W'     },
  voltaje_bateria:  { color: '#facc15', unit: 'V'     },
  potencia_solar:   { color: '#fde047', unit: 'V'     },
  latencia_red:     { color: '#c084fc', unit: 'ms'    },
  ciclos_bateria:   { color: '#e879f9', unit: 'ciclos'},
}

const TIPO_METRICA = {
  1:'humedad_suelo', 2:'ph_suelo', 3:'ec_suelo',
  4:'temperatura_suelo', 5:'temperatura_aire', 6:'humedad_aire',
  7:'luz', 8:'velocidad_viento', 9:'lluvia',
  10:'ph_agua', 11:'caudal', 12:'voltaje_valvula',
  13:'consumo_bomba', 14:'latencia_red', 15:'latencia_red',
  16:'voltaje_bateria', 17:'potencia_solar',
}

const SEV_COLOR    = { critica: '#f87171', alta: '#fbbf24', media: '#60a5fa', baja: '#22c55e' }
const ESTADO_COLOR = { activo: '#22c55e', inactivo: '#6b7280', mantenimiento: '#fbbf24' }

const VENTANAS = [
  { id: '30m', label: 'Última 30 min' },
  { id: '1h',  label: 'Última hora'   },
  { id: '6h',  label: 'Últimas 6h'    },
  { id: '24h', label: 'Último día'    },
  { id: '7d',  label: 'Última semana' },
]

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#0d1510', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '8px', padding: '10px 14px' }}>
      <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>{label}</div>
      <div style={{ color: payload[0]?.color, fontSize: '14px', fontWeight: 700 }}>{payload[0]?.value}</div>
    </div>
  )
}

const INTERVALO_REFRESCO = 10000 // 10 segundos

export default function Lecturas() {
  const [sensores, setSensores]         = useState([])
  const [sensorSel, setSensorSel]       = useState(null)
  const [lecturas, setLecturas]         = useState([])
  const [alertas, setAlertas]           = useState([])
  const [promedios, setPromedios]       = useState([])
  const [loading, setLoading]           = useState(false)
  const [loadingSensores, setLoadingSensores] = useState(true)
  const [loadingProm, setLoadingProm]   = useState(false)
  const [exportLoading, setExportLoading] = useState(false)
  const [filtroSev, setFiltroSev]       = useState('todos')
  const [filtroEstado, setFiltroEstado] = useState('activo')
  const [activeTab, setActiveTab]       = useState('tiempo-real')
  const [ventana, setVentana]           = useState('1h')
  const [diasExport, setDiasExport]     = useState(7)
  const [ultimaActualizacion, setUltimaActualizacion] = useState(null)
  const intervalRef = useRef(null)

  // ── Cargar sensores ───────────────────────────────
  const loadSensores = async () => {
    setLoadingSensores(true)
    try {
      const res      = await dispositivosAPI.listar(0, 200)
      const filtrados = filtroEstado === 'todos' ? res.data : res.data.filter(d => d.estado === filtroEstado)
      const mapeados  = filtrados.map(d => {
        const metrica = TIPO_METRICA[d.tipo_dispositivo_id] || 'humedad_suelo'
        const config  = METRICA_CONFIG[metrica] || { color: '#22c55e', unit: '' }
        return {
          id:      d.id_logico,
          metric:  metrica,
          color:   config.color,
          unit:    config.unit,
          estado:  d.estado,
          db_id:   d.id,
        }
      })
      setSensores(mapeados)
      setSensorSel(prev => {
        if (!prev) return mapeados[0] || null
        return mapeados.find(s => s.id === prev.id) || mapeados[0] || null
      })
    } catch(e) { console.error(e) }
    finally { setLoadingSensores(false) }
  }

  useEffect(() => { loadSensores() }, [filtroEstado])

  // ── Cargar lecturas ───────────────────────────────
  const loadLecturas = async (sensor) => {
    if (!sensor) return
    setLoading(true)
    try {
      const res  = await ingestaAPI.ultimasLecturas(sensor.id, 50)
      const data = res.data.map(l => ({
        time:  new Date(l.timestamp_lectura).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        valor: l.valor_metrica,
      })).reverse()
      setLecturas(data)
      setUltimaActualizacion(new Date().toLocaleTimeString('es-CO'))
    } catch(e) { setLecturas([]) }
    finally { setLoading(false) }
  }

  // ── Cargar alertas ────────────────────────────────
  const loadAlertas = async (sensor) => {
    if (!sensor) return
    try {
      const res = await procesamientoAPI.alertasSensor(sensor.id)
      setAlertas(res.data || [])
    } catch(e) { setAlertas([]) }
  }

  // ── Cargar promedios ──────────────────────────────
  const loadPromedios = async (sensor, v) => {
    if (!sensor) return
    setLoadingProm(true)
    try {
      const res = await ingestaAPI.promedios(sensor.id, v || ventana)
      setPromedios(res.data || [])
    } catch(e) { setPromedios([]) }
    finally { setLoadingProm(false) }
  }

  // ── Auto-refresco ─────────────────────────────────
  useEffect(() => {
    if (!sensorSel) return
    loadLecturas(sensorSel)
    loadAlertas(sensorSel)

    if (intervalRef.current) clearInterval(intervalRef.current)
    intervalRef.current = setInterval(() => {
      loadLecturas(sensorSel)
      loadAlertas(sensorSel)
    }, INTERVALO_REFRESCO)

    return () => clearInterval(intervalRef.current)
  }, [sensorSel])

  useEffect(() => {
    if (activeTab === 'promedios' && sensorSel) loadPromedios(sensorSel, ventana)
  }, [activeTab, ventana, sensorSel])

  // ── Export Excel ──────────────────────────────────
  const handleExportExcel = async () => {
    if (!sensorSel) return
    setExportLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      const url   = `/api/v1/telemetria/export/${sensorSel.id}/excel?dias=${diasExport}`
      const res   = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      if (!res.ok) { alert('No hay datos para exportar en ese rango'); return }
      const blob  = await res.blob()
      const link  = document.createElement('a')
      link.href   = URL.createObjectURL(blob)
      link.download = `lecturas_${sensorSel.id}_${diasExport}d.xlsx`
      link.click()
      URL.revokeObjectURL(link.href)
    } catch(e) { alert('Error al exportar') }
    finally { setExportLoading(false) }
  }

  const lastVal = lecturas[lecturas.length - 1]?.valor
  const avg     = lecturas.length ? (lecturas.reduce((s, l) => s + l.valor, 0) / lecturas.length).toFixed(1) : '—'
  const maxVal  = lecturas.length ? Math.max(...lecturas.map(l => l.valor)).toFixed(1) : '—'
  const minVal  = lecturas.length ? Math.min(...lecturas.map(l => l.valor)).toFixed(1) : '—'
  const alertasFiltradas = filtroSev === 'todos' ? alertas : alertas.filter(a => a.severidad === filtroSev)
  const metricas_unicas  = [...new Set(promedios.map(p => p.tipo_metrica))]

  return (
    <div style={styles.wrapper} className="animate-fade">

      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Monitor de Lecturas</h1>
          <p style={styles.subtitle}>
            {sensores.length} sensores · Auto-refresco cada {INTERVALO_REFRESCO/1000}s
            {ultimaActualizacion && <span style={{ color: '#22c55e' }}> · Última actualización: {ultimaActualizacion}</span>}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <select value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)} style={styles.select}>
            <option value="activo">Solo activos</option>
            <option value="todos">Todos los estados</option>
            <option value="mantenimiento">Mantenimiento</option>
          </select>
          <button onClick={() => { if (sensorSel) { loadLecturas(sensorSel); loadAlertas(sensorSel) } loadSensores() }}
            className="btn btn-ghost" style={{ fontSize: '12px' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Actualizar
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={styles.tabsBar}>
        {[
          { id: 'tiempo-real', label: '📡 Tiempo Real'        },
          { id: 'promedios',   label: '📊 Promedios'          },
          { id: 'alertas',     label: `⚠️ Alertas (${alertas.length})` },
        ].map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            style={{ ...styles.tabBtn, ...(activeTab === t.id ? styles.tabBtnActive : {}) }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Grid de sensores */}
      {loadingSensores ? (
        <div style={styles.sensorGrid}>{[...Array(6)].map((_, i) =>
          <div key={i} className="skeleton" style={{ height: '56px', borderRadius: '10px' }} />
        )}</div>
      ) : sensores.length === 0 ? (
        <div style={styles.empty}>
          <div>No hay sensores con el filtro seleccionado</div>
          <div style={{ fontSize: '11px', marginTop: '4px', color: '#4b5563' }}>Registra sensores en la sección Dispositivos</div>
        </div>
      ) : (
        <div style={styles.sensorGrid}>
          {sensores.map(s => (
            <button key={s.id} onClick={() => setSensorSel(s)} style={{
              ...styles.sensorBtn,
              borderColor: sensorSel?.id === s.id ? s.color : 'rgba(34,197,94,0.1)',
              background:  sensorSel?.id === s.id ? `${s.color}15` : '#0d1510',
              color:       sensorSel?.id === s.id ? s.color : '#6b7280',
            }}>
              <div style={{ fontWeight: 700, fontSize: '11px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.id}</div>
              <div style={{ fontSize: '10px', opacity: 0.7, marginTop: '2px' }}>{s.metric}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '3px' }}>
                <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: ESTADO_COLOR[s.estado] || '#6b7280' }} />
                <span style={{ fontSize: '9px', color: ESTADO_COLOR[s.estado] || '#6b7280' }}>{s.estado}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* ── TAB: Tiempo Real ── */}
      {activeTab === 'tiempo-real' && sensorSel && (
        <>
          {/* Stats */}
          <div style={styles.statsRow}>
            {[
              { label: 'Sensor',       val: sensorSel.id,                          color: sensorSel.color, mono: true },
              { label: 'Ultimo valor', val: `${lastVal ?? '—'} ${sensorSel.unit}`, color: sensorSel.color },
              { label: 'Promedio',     val: `${avg} ${sensorSel.unit}`,            color: '#60a5fa' },
              { label: 'Maximo',       val: `${maxVal} ${sensorSel.unit}`,         color: '#f87171' },
              { label: 'Minimo',       val: `${minVal} ${sensorSel.unit}`,         color: '#22c55e' },
              { label: 'Lecturas',     val: lecturas.length,                        color: '#a78bfa' },
            ].map(s => (
              <div key={s.label} style={styles.statCard}>
                <div style={styles.statLabel}>{s.label}</div>
                <div style={{ ...styles.statVal, color: s.color, fontFamily: s.mono ? 'monospace' : "'Syne', sans-serif", fontSize: s.mono ? '11px' : '14px' }}>{s.val}</div>
              </div>
            ))}
          </div>

          {/* Grafica */}
          <div className="card" style={{ marginBottom: '20px' }}>
            <div style={styles.chartHeader}>
              <div style={styles.chartTitle}>
                {sensorSel.id} — {sensorSel.metric}
                <span style={{ fontSize: '11px', color: '#4b5563', marginLeft: '8px', fontFamily: 'sans-serif', fontWeight: 400 }}>
                  Ultimas {lecturas.length} lecturas · refresco automático
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e', animation: 'pulse-green 2s infinite' }} />
                <span style={{ fontSize: '11px', color: '#22c55e' }}>EN VIVO</span>
              </div>
            </div>
            {loading ? (
              <div className="skeleton" style={{ height: '220px', borderRadius: '8px' }} />
            ) : lecturas.length === 0 ? (
              <div style={styles.noData}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#374151" strokeWidth="1.5" style={{ marginBottom: '8px' }}>
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
                <div>Sin lecturas para {sensorSel.id}</div>
                <div style={{ fontSize: '11px', marginTop: '4px', color: '#4b5563' }}>
                  Las lecturas aparecerán aquí automáticamente cuando el sensor envíe datos
                </div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={lecturas} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                  <defs>
                    <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={sensorSel.color} stopOpacity={0.3}/>
                      <stop offset="95%" stopColor={sensorSel.color} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(34,197,94,0.06)" />
                  <XAxis dataKey="time" tick={{ fill: '#4b5563', fontSize: 10 }} tickLine={false} />
                  <YAxis tick={{ fill: '#4b5563', fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="valor" stroke={sensorSel.color} strokeWidth={2} fill="url(#grad)" dot={{ fill: sensorSel.color, r: 3 }} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </>
      )}

      {activeTab === 'tiempo-real' && !sensorSel && (
        <div style={styles.empty}><div>Selecciona un sensor para ver sus lecturas en tiempo real</div></div>
      )}

      {/* ── TAB: Promedios ── */}
      {activeTab === 'promedios' && (
        <div className="animate-fade">
          {!sensorSel ? (
            <div style={styles.empty}><div>Selecciona un sensor para ver sus promedios</div></div>
          ) : (
            <>
              <div className="card" style={{ marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <div style={styles.chartTitle}>Promedios — {sensorSel.id}</div>
                    <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>Agregaciones temporales de lecturas reales</div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {VENTANAS.map(v => (
                      <button key={v.id} onClick={() => setVentana(v.id)} style={{
                        ...styles.ventanaBtn, ...(ventana === v.id ? styles.ventanaBtnActive : {})
                      }}>{v.label}</button>
                    ))}
                  </div>
                </div>
              </div>

              {loadingProm ? (
                <div className="skeleton" style={{ height: '280px', borderRadius: '12px', marginBottom: '20px' }} />
              ) : promedios.length === 0 ? (
                <div style={styles.empty}>
                  <div>Sin datos en la ventana seleccionada</div>
                  <div style={{ fontSize: '11px', marginTop: '4px', color: '#4b5563' }}>Los promedios aparecerán cuando el sensor tenga lecturas en ese rango de tiempo</div>
                </div>
              ) : (
                metricas_unicas.map(metrica => {
                  const datos  = promedios.filter(p => p.tipo_metrica === metrica).map(p => ({
                    periodo:  p.periodo ? new Date(p.periodo).toLocaleString('es-CO', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '',
                    promedio: p.promedio,
                  }))
                  const config = METRICA_CONFIG[metrica] || { color: '#22c55e', unit: '' }
                  const prom   = promedios.find(p => p.tipo_metrica === metrica)
                  return (
                    <div key={metrica} className="card" style={{ marginBottom: '20px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                        <div style={styles.chartTitle}>{metrica} <span style={{ color: config.color, fontSize: '12px' }}>({config.unit})</span></div>
                        {prom && (
                          <div style={{ display: 'flex', gap: '16px', fontSize: '12px' }}>
                            <span style={{ color: '#60a5fa' }}>Prom: <b>{prom.promedio}</b></span>
                            <span style={{ color: '#f87171' }}>Max: <b>{prom.maximo}</b></span>
                            <span style={{ color: '#22c55e' }}>Min: <b>{prom.minimo}</b></span>
                            <span style={{ color: '#6b7280' }}>Muestras: <b>{prom.total_lecturas}</b></span>
                          </div>
                        )}
                      </div>
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={datos} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(34,197,94,0.06)" />
                          <XAxis dataKey="periodo" tick={{ fill: '#4b5563', fontSize: 9 }} tickLine={false} />
                          <YAxis tick={{ fill: '#4b5563', fontSize: 10 }} tickLine={false} axisLine={false} />
                          <Tooltip content={<CustomTooltip />} />
                          <Bar dataKey="promedio" fill={config.color} opacity={0.85} radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )
                })
              )}

              {/* Export Excel */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <div style={styles.chartTitle}>📊 Exportar a Excel</div>
                    <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                      Lecturas de <b style={{ color: sensorSel.color }}>{sensorSel.id}</b> organizadas por día y hora con promedios
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <select value={diasExport} onChange={e => setDiasExport(Number(e.target.value))} style={styles.select}>
                      <option value={1}>Último día</option>
                      <option value={7}>Últimos 7 días</option>
                      <option value={15}>Últimos 15 días</option>
                      <option value={30}>Últimos 30 días</option>
                    </select>
                    <button onClick={handleExportExcel} disabled={exportLoading} style={{ ...styles.exportBtn, opacity: exportLoading ? 0.6 : 1 }}>
                      {exportLoading ? 'Generando...' : (
                        <>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="7 10 12 15 17 10"/>
                            <line x1="12" y1="15" x2="12" y2="3"/>
                          </svg>
                          Descargar Excel
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* ── TAB: Alertas ── */}
      {activeTab === 'alertas' && (
        <div className="animate-fade">
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={styles.chartTitle}>
                Alertas {sensorSel ? `— ${sensorSel.id}` : ''}
              </div>
              <select value={filtroSev} onChange={e => setFiltroSev(e.target.value)} style={styles.select}>
                <option value="todos">Todas las severidades</option>
                <option value="critica">Critica</option>
                <option value="alta">Alta</option>
                <option value="media">Media</option>
                <option value="baja">Baja</option>
              </select>
            </div>

            {!sensorSel ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#4b5563', fontSize: '13px' }}>Selecciona un sensor para ver sus alertas</div>
            ) : alertasFiltradas.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#4b5563', fontSize: '13px' }}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#374151" strokeWidth="1.5" style={{ marginBottom: '8px', display: 'block', margin: '0 auto 8px' }}>
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                Sin alertas para este sensor
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {alertasFiltradas.map(a => (
                  <div key={a.id} style={{ ...styles.alertItem, borderLeft: `3px solid ${SEV_COLOR[a.severidad] || '#6b7280'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: '12px', fontWeight: 700, color: SEV_COLOR[a.severidad] }}>{a.severidad?.toUpperCase()}</span>
                      <span style={{ fontSize: '11px', color: '#4b5563' }}>{new Date(a.generada_en).toLocaleString('es-CO')}</span>
                    </div>
                    <div style={{ fontSize: '13px', color: '#d1fae5' }}>{a.condicion}</div>
                    <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>
                      Valor detectado: {a.valor_detectado} · Tipo: {a.tipo_alerta}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <style>{`
        @keyframes pulse-green {
          0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.4); }
          50%       { box-shadow: 0 0 0 6px rgba(34,197,94,0); }
        }
      `}</style>
    </div>
  )
}

const styles = {
  wrapper:        { padding: '32px', maxWidth: '1100px' },
  header:         { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' },
  title:          { fontFamily: "'Syne', sans-serif", fontSize: '26px', fontWeight: 700, color: '#f0fdf4' },
  subtitle:       { fontSize: '13px', color: '#6b7280', marginTop: '4px' },
  select:         { padding: '7px 12px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#9ca3af', fontSize: '12px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  tabsBar:        { display: 'flex', gap: '4px', marginBottom: '20px', background: '#0d1510', borderRadius: '10px', padding: '4px', border: '1px solid rgba(34,197,94,0.1)' },
  tabBtn:         { flex: 1, padding: '9px', borderRadius: '7px', border: 'none', background: 'transparent', color: '#6b7280', fontSize: '13px', fontWeight: 500, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s' },
  tabBtnActive:   { background: 'rgba(34,197,94,0.15)', color: '#22c55e' },
  sensorGrid:     { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '8px', marginBottom: '20px' },
  sensorBtn:      { padding: '10px 8px', borderRadius: '10px', border: '1px solid', background: '#0d1510', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s', textAlign: 'center' },
  statsRow:       { display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '10px', marginBottom: '20px' },
  statCard:       { background: '#0d1510', border: '1px solid rgba(34,197,94,0.1)', borderRadius: '10px', padding: '12px', textAlign: 'center' },
  statLabel:      { fontSize: '10px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '6px' },
  statVal:        { fontFamily: "'Syne', sans-serif", fontSize: '14px', fontWeight: 700 },
  chartHeader:    { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' },
  chartTitle:     { fontFamily: "'Syne', sans-serif", fontSize: '14px', fontWeight: 600, color: '#f0fdf4' },
  noData:         { textAlign: 'center', padding: '50px', color: '#4b5563', fontSize: '13px', display: 'flex', flexDirection: 'column', alignItems: 'center' },
  empty:          { textAlign: 'center', padding: '40px', color: '#4b5563', fontSize: '13px', background: '#0d1510', borderRadius: '12px', border: '1px solid rgba(34,197,94,0.1)', marginBottom: '20px' },
  ventanaBtn:     { padding: '6px 12px', borderRadius: '20px', border: '1px solid rgba(34,197,94,0.15)', background: 'transparent', color: '#6b7280', fontSize: '12px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s' },
  ventanaBtnActive:{ background: 'rgba(34,197,94,0.15)', color: '#22c55e', borderColor: 'rgba(34,197,94,0.3)' },
  exportBtn:      { display: 'flex', alignItems: 'center', gap: '7px', padding: '10px 18px', borderRadius: '10px', border: 'none', background: 'linear-gradient(135deg, #16a34a, #15803d)', color: '#fff', fontSize: '13px', fontWeight: 600, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  alertItem:      { background: 'rgba(6,12,7,0.6)', borderRadius: '8px', padding: '10px 12px' },
}