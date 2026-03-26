import { useState, useEffect } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { ingestaAPI, procesamientoAPI } from '../api/client'

const SENSOR_OPTIONS = [
  { id: 'SOIL_HUM_01', label: 'Humedad Suelo',    metric: 'humedad_suelo',    color: '#22c55e', unit: '%',    min: 5,   max: 95  },
  { id: 'AIR_TEMP_01', label: 'Temperatura Aire', metric: 'temperatura_aire', color: '#f87171', unit: 'C',    min: -5,  max: 42  },
  { id: 'SOIL_PH_01',  label: 'pH Suelo',         metric: 'ph_suelo',         color: '#a78bfa', unit: 'pH',   min: 4,   max: 9   },
  { id: 'LUX_01',      label: 'Luz Solar',        metric: 'luz',              color: '#fbbf24', unit: 'Lux',  min: 200, max: 8000},
  { id: 'WIND_01',     label: 'Viento',           metric: 'velocidad_viento', color: '#60a5fa', unit: 'km/h', min: 0,   max: 60  },
  { id: 'RAIN_01',     label: 'Lluvia',           metric: 'lluvia',           color: '#818cf8', unit: 'mm',   min: 0,   max: 80  },
]

const SEV_COLOR = { critica: '#f87171', alta: '#fbbf24', media: '#60a5fa', baja: '#22c55e' }

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#0d1510', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '8px', padding: '10px 14px' }}>
      <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>{label}</div>
      <div style={{ color: payload[0]?.color, fontSize: '14px', fontWeight: 700 }}>{payload[0]?.value}</div>
    </div>
  )
}

export default function Lecturas() {
  const [sensorSel, setSensorSel] = useState(SENSOR_OPTIONS[0])
  const [lecturas, setLecturas]   = useState([])
  const [alertas, setAlertas]     = useState([])
  const [loading, setLoading]     = useState(false)
  const [filtroSev, setFiltroSev] = useState('todos')
  const [simVal, setSimVal]       = useState('')
  const [simMsg, setSimMsg]       = useState('')
  const [autoSim, setAutoSim]     = useState(false)

  const loadLecturas = async (sensor) => {
    setLoading(true)
    try {
      const res = await ingestaAPI.ultimasLecturas(sensor.id, 30)
      const data = res.data.map(l => ({
        time:  new Date(l.timestamp_lectura).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        valor: l.valor_metrica,
      })).reverse()
      setLecturas(data)
    } catch(e) { setLecturas([]) }
    finally { setLoading(false) }
  }

  const loadAlertas = async (sensor) => {
    try {
      const res = await procesamientoAPI.alertasSensor(sensor.id)
      setAlertas(res.data || [])
    } catch(e) { setAlertas([]) }
  }

  useEffect(() => {
    loadLecturas(sensorSel)
    loadAlertas(sensorSel)
  }, [sensorSel])

  useEffect(() => {
    if (!autoSim) return
    const interval = setInterval(async () => {
      const val = parseFloat((Math.random() * (sensorSel.max - sensorSel.min) + sensorSel.min).toFixed(2))
      try {
        await ingestaAPI.enviarLectura({
          dispositivo_id: 1,
          id_logico: sensorSel.id,
          tipo_metrica: sensorSel.metric,
          valor_metrica: val,
          unidad: sensorSel.unit,
        })
        await loadLecturas(sensorSel)
      } catch(e) {}
    }, 5000)
    return () => clearInterval(interval)
  }, [autoSim, sensorSel])

  const handleSimular = async () => {
    const val = parseFloat(simVal)
    if (isNaN(val)) { setSimMsg('Ingresa un valor numerico'); return }
    setSimMsg('')
    try {
      await ingestaAPI.enviarLectura({
        dispositivo_id: 1,
        id_logico: sensorSel.id,
        tipo_metrica: sensorSel.metric,
        valor_metrica: val,
        unidad: sensorSel.unit,
      })
      setSimMsg(`✅ Lectura ${val} ${sensorSel.unit} enviada`)
      setSimVal('')
      setTimeout(() => { loadLecturas(sensorSel); loadAlertas(sensorSel) }, 500)
    } catch(e) { setSimMsg('❌ Error enviando lectura') }
  }

  const lastVal = lecturas[lecturas.length - 1]?.valor
  const avg     = lecturas.length ? (lecturas.reduce((s, l) => s + l.valor, 0) / lecturas.length).toFixed(1) : '—'
  const max     = lecturas.length ? Math.max(...lecturas.map(l => l.valor)).toFixed(1) : '—'
  const min     = lecturas.length ? Math.min(...lecturas.map(l => l.valor)).toFixed(1) : '—'

  const alertasFiltradas = filtroSev === 'todos' ? alertas : alertas.filter(a => a.severidad === filtroSev)

  return (
    <div style={styles.wrapper} className="animate-fade">
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Lecturas de Sensores</h1>
          <p style={styles.subtitle}>Telemetria en tiempo real por dispositivo</p>
        </div>
        <div style={styles.headerRight}>
          <button onClick={() => setAutoSim(!autoSim)} style={{
            ...styles.autoBtn,
            background: autoSim ? 'rgba(34,197,94,0.15)' : 'rgba(107,114,128,0.1)',
            color: autoSim ? '#22c55e' : '#6b7280',
            borderColor: autoSim ? 'rgba(34,197,94,0.3)' : 'rgba(107,114,128,0.2)',
          }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: autoSim ? '#22c55e' : '#6b7280', animation: autoSim ? 'pulse-green 2s infinite' : 'none' }} />
            {autoSim ? 'Auto-sim ON' : 'Auto-sim OFF'}
          </button>
          <button onClick={() => { loadLecturas(sensorSel); loadAlertas(sensorSel) }} className="btn btn-ghost" style={{ fontSize: '12px' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Actualizar
          </button>
        </div>
      </div>

      {/* Sensor selector */}
      <div style={styles.sensorGrid}>
        {SENSOR_OPTIONS.map(s => (
          <button key={s.id} onClick={() => setSensorSel(s)} style={{
            ...styles.sensorBtn,
            borderColor:  sensorSel.id === s.id ? s.color : 'rgba(34,197,94,0.1)',
            background:   sensorSel.id === s.id ? `${s.color}15` : '#0d1510',
            color:        sensorSel.id === s.id ? s.color : '#6b7280',
          }}>
            <div style={{ fontWeight: 700, fontSize: '12px' }}>{s.label}</div>
            <div style={{ fontSize: '10px', fontFamily: 'monospace', opacity: 0.7 }}>{s.id}</div>
          </button>
        ))}
      </div>

      {/* Stats */}
      <div style={styles.statsRow}>
        {[
          { label: 'Ultimo valor', val: `${lastVal ?? '—'} ${sensorSel.unit}`, color: sensorSel.color },
          { label: 'Promedio',     val: `${avg} ${sensorSel.unit}`,            color: '#60a5fa'       },
          { label: 'Maximo',       val: `${max} ${sensorSel.unit}`,            color: '#f87171'       },
          { label: 'Minimo',       val: `${min} ${sensorSel.unit}`,            color: '#22c55e'       },
          { label: 'Lecturas',     val: lecturas.length,                        color: '#a78bfa'       },
        ].map(s => (
          <div key={s.label} style={styles.statCard}>
            <div style={styles.statLabel}>{s.label}</div>
            <div style={{ ...styles.statVal, color: s.color }}>{s.val}</div>
          </div>
        ))}
      </div>

      {/* Chart — full width */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={styles.chartHeader}>
          <div style={styles.chartTitle}>{sensorSel.label} — Ultimas {lecturas.length} lecturas</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: sensorSel.color }} />
            <span style={{ fontSize: '12px', color: '#6b7280' }}>{sensorSel.metric}</span>
          </div>
        </div>
        {loading ? (
          <div className="skeleton" style={{ height: '220px', borderRadius: '8px' }} />
        ) : lecturas.length === 0 ? (
          <div style={styles.noData}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#374151" strokeWidth="1.5" style={{ marginBottom: '8px' }}>
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            <div>Sin datos para {sensorSel.id}</div>
            <div style={{ fontSize: '11px', marginTop: '4px' }}>Usa el simulador o el boton de datos del Dashboard</div>
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

      {/* Bottom: simulator + alertas side by side */}
      <div style={styles.bottomGrid}>
        {/* Simulator */}
        <div className="card" style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={styles.chartTitle}>Simular lectura</div>
            <span style={styles.simBadge}>Modo prueba</span>
          </div>
          <div style={styles.simInfo}>
            <div style={styles.simInfoItem}>Sensor <span style={{ color: sensorSel.color }}>{sensorSel.id}</span></div>
            <div style={styles.simInfoItem}>Metrica <span style={{ color: '#9ca3af' }}>{sensorSel.metric}</span></div>
            <div style={styles.simInfoItem}>Rango <span style={{ color: '#9ca3af' }}>{sensorSel.min}–{sensorSel.max} {sensorSel.unit}</span></div>
          </div>
          <div style={styles.simForm}>
            <input
              type="number"
              placeholder={`Valor (${sensorSel.min}–${sensorSel.max} ${sensorSel.unit})`}
              value={simVal}
              onChange={e => setSimVal(e.target.value)}
              style={styles.simInput}
              onKeyDown={e => e.key === 'Enter' && handleSimular()}
            />
            <button onClick={handleSimular} className="btn btn-primary">Enviar</button>
          </div>
          {simMsg && <div style={{ marginTop: '10px', fontSize: '13px', color: simMsg.includes('✅') ? '#22c55e' : '#f87171' }}>{simMsg}</div>}
        </div>

        {/* Alertas del sensor con filtro */}
        <div className="card" style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={styles.chartTitle}>Alertas de {sensorSel.id}</div>
            <select value={filtroSev} onChange={e => setFiltroSev(e.target.value)} style={styles.sevSelect}>
              <option value="todos">Todas</option>
              <option value="critica">Critica</option>
              <option value="alta">Alta</option>
              <option value="media">Media</option>
              <option value="baja">Baja</option>
            </select>
          </div>
          {alertasFiltradas.length === 0 ? (
            <div style={styles.noAlertas}>
              <div style={{ fontSize: '28px', marginBottom: '6px' }}>—</div>
              <div style={{ fontSize: '13px', color: '#4b5563' }}>Sin alertas para este sensor</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '200px', overflowY: 'auto' }}>
              {alertasFiltradas.slice(0, 8).map(a => (
                <div key={a.id} style={{ ...styles.alertItem, borderLeft: `3px solid ${SEV_COLOR[a.severidad] || '#6b7280'}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 700, color: SEV_COLOR[a.severidad] }}>{a.severidad?.toUpperCase()}</span>
                    <span style={{ fontSize: '10px', color: '#4b5563' }}>{new Date(a.generada_en).toLocaleTimeString('es-CO')}</span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#d1fae5' }}>{a.condicion}</div>
                  <div style={{ fontSize: '11px', color: '#6b7280' }}>Valor: {a.valor_detectado} · {a.tipo_alerta}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

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
  wrapper: { padding: '32px', maxWidth: '1100px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' },
  title: { fontFamily: "'Syne', sans-serif", fontSize: '26px', fontWeight: 700, color: '#f0fdf4' },
  subtitle: { fontSize: '13px', color: '#6b7280', marginTop: '4px' },
  headerRight: { display: 'flex', gap: '10px', alignItems: 'center' },
  autoBtn: { display: 'flex', alignItems: 'center', gap: '7px', padding: '8px 14px', borderRadius: '20px', border: '1px solid', fontSize: '12px', fontWeight: 600, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.2s' },
  sensorGrid: { display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '8px', marginBottom: '20px' },
  sensorBtn: { padding: '10px 8px', borderRadius: '10px', border: '1px solid', background: '#0d1510', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s', textAlign: 'center' },
  statsRow: { display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px', marginBottom: '20px' },
  statCard: { background: '#0d1510', border: '1px solid rgba(34,197,94,0.1)', borderRadius: '10px', padding: '14px', textAlign: 'center' },
  statLabel: { fontSize: '10px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '6px' },
  statVal: { fontFamily: "'Syne', sans-serif", fontSize: '15px', fontWeight: 700 },
  chartHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' },
  chartTitle: { fontFamily: "'Syne', sans-serif", fontSize: '14px', fontWeight: 600, color: '#f0fdf4' },
  noData: { textAlign: 'center', padding: '50px', color: '#4b5563', fontSize: '13px', display: 'flex', flexDirection: 'column', alignItems: 'center' },
  bottomGrid: { display: 'flex', gap: '16px' },
  simBadge: { background: 'rgba(96,165,250,0.1)', color: '#60a5fa', padding: '3px 10px', borderRadius: '20px', fontSize: '11px', border: '1px solid rgba(96,165,250,0.2)' },
  simInfo: { display: 'flex', gap: '12px', marginBottom: '12px', flexWrap: 'wrap' },
  simInfoItem: { fontSize: '12px', color: '#6b7280', display: 'flex', gap: '5px' },
  simForm: { display: 'flex', gap: '10px' },
  simInput: { flex: 1, padding: '9px 14px', background: 'rgba(6,12,7,0.8)', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#f0fdf4', fontSize: '13px', fontFamily: "'DM Sans', sans-serif" },
  sevSelect: { padding: '5px 10px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#9ca3af', fontSize: '12px', cursor: 'pointer' },
  noAlertas: { textAlign: 'center', padding: '30px', color: '#4b5563' },
  alertItem: { background: 'rgba(6,12,7,0.6)', borderRadius: '6px', padding: '8px 10px' },
}