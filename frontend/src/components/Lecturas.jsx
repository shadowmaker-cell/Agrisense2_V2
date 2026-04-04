import { useState, useEffect } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { ingestaAPI, procesamientoAPI, notificacionesAPI, dispositivosAPI, parcelasAPI, recomendacionesAPI } from '../api/client'

const METRICA_CONFIG = {
  humedad_suelo:    { color: '#22c55e', unit: '%',    min: 5,    max: 95   },
  ph_suelo:         { color: '#a78bfa', unit: 'pH',   min: 4,    max: 9    },
  ec_suelo:         { color: '#f59e0b', unit: 'mS',   min: 0,    max: 5    },
  temperatura_suelo:{ color: '#fb923c', unit: 'C',    min: -10,  max: 85   },
  temperatura_aire: { color: '#f87171', unit: 'C',    min: -40,  max: 80   },
  humedad_aire:     { color: '#38bdf8', unit: '%',    min: 0,    max: 100  },
  luz:              { color: '#fbbf24', unit: 'Lux',  min: 0,    max: 65000},
  velocidad_viento: { color: '#60a5fa', unit: 'km/h', min: 0,    max: 150  },
  lluvia:           { color: '#818cf8', unit: 'mm',   min: 0,    max: 500  },
  ph_agua:          { color: '#2dd4bf', unit: 'pH',   min: 0,    max: 14   },
  caudal:           { color: '#06b6d4', unit: 'L/m',  min: 1,    max: 30   },
  voltaje_valvula:  { color: '#84cc16', unit: 'V',    min: 0,    max: 500  },
  consumo_bomba:    { color: '#f97316', unit: 'W',    min: 0,    max: 220  },
  voltaje_bateria:  { color: '#facc15', unit: 'V',    min: 0,    max: 5    },
  potencia_solar:   { color: '#fde047', unit: 'V',    min: 0,    max: 50   },
  latencia_red:     { color: '#c084fc', unit: 'ms',   min: 0,    max: 2000 },
  ciclos_bateria:   { color: '#e879f9', unit: 'ciclos',min: 0,  max: 1000 },
}

const TIPO_METRICA = {
  1: 'humedad_suelo',     2: 'ph_suelo',        3: 'ec_suelo',
  4: 'temperatura_suelo', 5: 'temperatura_aire', 6: 'humedad_aire',
  7: 'luz',               8: 'velocidad_viento', 9: 'lluvia',
  10: 'ph_agua',          11: 'caudal',          12: 'voltaje_valvula',
  13: 'consumo_bomba',    14: 'latencia_red',    15: 'latencia_red',
  16: 'voltaje_bateria',  17: 'potencia_solar',
}

const SEV_COLOR = { critica: '#f87171', alta: '#fbbf24', media: '#60a5fa', baja: '#22c55e' }

const METRICA_CAMPO_REC = {
  humedad_suelo:    'humedad_suelo',
  temperatura_aire: 'temperatura_aire',
  ph_suelo:         'ph_suelo',
  lluvia:           'lluvia',
  velocidad_viento: 'velocidad_viento',
  humedad_aire:     'humedad_aire',
}

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
  const [sensores, setSensores]   = useState([])
  const [sensorSel, setSensorSel] = useState(null)
  const [lecturas, setLecturas]   = useState([])
  const [alertas, setAlertas]     = useState([])
  const [loading, setLoading]     = useState(false)
  const [loadingSensores, setLoadingSensores] = useState(true)
  const [filtroSev, setFiltroSev] = useState('todos')
  const [filtroEstado, setFiltroEstado] = useState('activo')
  const [simVal, setSimVal]       = useState('')
  const [simMsg, setSimMsg]       = useState('')
  const [autoSim, setAutoSim]     = useState(false)
  const [activeTab, setActiveTab] = useState('lectura')
  const [loteRows, setLoteRows]   = useState([])
  const [loteMsg, setLoteMsg]     = useState('')
  const [loteLoading, setLoteLoading] = useState(false)

  // ── Cargar sensores dinamicamente ─────────────────
  const loadSensores = async () => {
    setLoadingSensores(true)
    try {
      const res = await dispositivosAPI.listar(0, 200)
      const todos = res.data
      const filtrados = filtroEstado === 'todos'
        ? todos
        : todos.filter(d => d.estado === filtroEstado)

      const mapeados = filtrados.map(d => {
        const metrica = TIPO_METRICA[d.tipo_dispositivo_id] || 'humedad_suelo'
        const config  = METRICA_CONFIG[metrica] || { color: '#22c55e', unit: '', min: 0, max: 100 }
        return {
          id:      d.id_logico,
          label:   d.id_logico,
          metric:  metrica,
          color:   config.color,
          unit:    config.unit,
          min:     config.min,
          max:     config.max,
          estado:  d.estado,
          tipo_id: d.tipo_dispositivo_id,
          db_id:   d.id,
        }
      })

      setSensores(mapeados)
      if (mapeados.length > 0) {
        setSensorSel(prev => {
          if (!prev) return mapeados[0]
          const sigue = mapeados.find(s => s.id === prev.id)
          return sigue || mapeados[0]
        })
      } else {
        setSensorSel(null)
      }
      setLoteRows(mapeados.map(s => ({
        id_logico:    s.id,
        tipo_metrica: s.metric,
        valor:        '',
        unidad:       s.unit,
      })))
    } catch(e) { console.error(e) }
    finally { setLoadingSensores(false) }
  }

  useEffect(() => { loadSensores() }, [filtroEstado])

  const loadLecturas = async (sensor) => {
    if (!sensor) return
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
    if (!sensor) return
    try {
      const res = await procesamientoAPI.alertasSensor(sensor.id)
      setAlertas(res.data || [])
    } catch(e) { setAlertas([]) }
  }

  useEffect(() => {
    if (sensorSel) {
      loadLecturas(sensorSel)
      loadAlertas(sensorSel)
    }
  }, [sensorSel])

  // ── Buscar parcela asignada al sensor ─────────────
  const buscarParcelaDelSensor = async (id_logico) => {
    try {
      const parcelasRes = await parcelasAPI.listar()
      for (const parcela of parcelasRes.data) {
        const asignado = parcela.sensores?.find(s => s.id_logico === id_logico && s.activo)
        if (asignado) return parcela.id
      }
    } catch(e) {}
    return null
  }

  // ── Generar recomendaciones automaticas ───────────
  const generarRecomendacionesAuto = async (sensorData, resultado) => {
    if (!resultado?.data?.alertas_generadas || resultado.data.alertas_generadas === 0) return
    try {
      const parcela_id = await buscarParcelaDelSensor(sensorData.id_logico)
      const payload = { id_logico: sensorData.id_logico }
      if (parcela_id) payload.parcela_id = parcela_id
      const campo = METRICA_CAMPO_REC[sensorData.tipo_metrica]
      if (campo) payload[campo] = sensorData.valor_metrica
      await recomendacionesAPI.generar(payload)
    } catch(e) {
      console.warn('Recomendaciones auto no generadas:', e)
    }
  }

  useEffect(() => {
    if (!autoSim || !sensorSel) return
    const interval = setInterval(async () => {
      try {
        const disps = await dispositivosAPI.listar(0, 200)
        const dispositivo = disps.data.find(d => d.id_logico === sensorSel.id)
        if (dispositivo && dispositivo.estado !== 'activo') {
          setAutoSim(false)
          setSimMsg(`Detenido — sensor ${sensorSel.id} ya no esta activo`)
          return
        }
      } catch(e) {}

      const val = parseFloat((Math.random() * (sensorSel.max - sensorSel.min) + sensorSel.min).toFixed(2))
      try {
        await ingestaAPI.enviarLectura({
          dispositivo_id: 1,
          id_logico: sensorSel.id,
          tipo_metrica: sensorSel.metric,
          valor_metrica: val,
          unidad: sensorSel.unit,
        })
        const resultado = await procesamientoAPI.procesarManual({
          dispositivo_id: 1,
          id_logico: sensorSel.id,
          tipo_metrica: sensorSel.metric,
          valor_metrica: val,
          unidad: sensorSel.unit,
        })
        if (resultado.data.alertas_generadas > 0) {
          const tipos = resultado.data.tipos_alerta
          await notificacionesAPI.enviar({
            dispositivo_id: 1,
            id_logico: sensorSel.id,
            tipo_alerta: tipos[0],
            tipo_metrica: sensorSel.metric,
            valor: val,
            condicion: `Valor ${val} ${sensorSel.unit} — ${tipos.join(', ')}`,
            severidad: resultado.data.alertas_generadas > 1 ? 'critica' : 'alta',
            canal: 'push',
          })
          await generarRecomendacionesAuto(
            { id_logico: sensorSel.id, tipo_metrica: sensorSel.metric, valor_metrica: val },
            resultado
          )
        }
        await loadLecturas(sensorSel)
        await loadAlertas(sensorSel)
      } catch(e) { console.error(e) }
    }, 5000)
    return () => clearInterval(interval)
  }, [autoSim, sensorSel])

  const handleSimular = async () => {
    const val = parseFloat(simVal)
    if (isNaN(val)) { setSimMsg('Ingresa un valor numerico'); return }
    if (!sensorSel) { setSimMsg('Selecciona un sensor'); return }
    setSimMsg('')

    try {
      const disps = await dispositivosAPI.listar(0, 200)
      const dispositivo = disps.data.find(d => d.id_logico === sensorSel.id)
      if (dispositivo && dispositivo.estado !== 'activo') {
        setSimMsg(`Sensor ${sensorSel.id} en estado "${dispositivo.estado}" — no puede recibir lecturas`)
        return
      }
    } catch(e) {}

    try {
      await ingestaAPI.enviarLectura({
        dispositivo_id: 1,
        id_logico: sensorSel.id,
        tipo_metrica: sensorSel.metric,
        valor_metrica: val,
        unidad: sensorSel.unit,
      })
      const resultado = await procesamientoAPI.procesarManual({
        dispositivo_id: 1,
        id_logico: sensorSel.id,
        tipo_metrica: sensorSel.metric,
        valor_metrica: val,
        unidad: sensorSel.unit,
      })
      if (resultado.data.alertas_generadas > 0) {
        const tipos = resultado.data.tipos_alerta
        await notificacionesAPI.enviar({
          dispositivo_id: 1,
          id_logico: sensorSel.id,
          tipo_alerta: tipos[0],
          tipo_metrica: sensorSel.metric,
          valor: val,
          condicion: `Valor ${val} ${sensorSel.unit} — ${tipos.join(', ')}`,
          severidad: resultado.data.alertas_generadas > 1 ? 'critica' : 'alta',
          canal: 'push',
        })
        await generarRecomendacionesAuto(
          { id_logico: sensorSel.id, tipo_metrica: sensorSel.metric, valor_metrica: val },
          resultado
        )
        setSimMsg(`${resultado.data.alertas_generadas} alerta(s): ${tipos.join(', ')} — Recomendacion generada`)
      } else {
        setSimMsg(`Lectura ${val} ${sensorSel.unit} enviada — sin alertas`)
      }
      setSimVal('')
      setTimeout(() => { loadLecturas(sensorSel); loadAlertas(sensorSel) }, 500)
    } catch(e) {
      setSimMsg('Error enviando lectura')
      console.error(e)
    }
  }

  const handleEnviarLote = async () => {
    const filas = loteRows.filter(r => r.valor !== '' && !isNaN(parseFloat(r.valor)))
    if (filas.length === 0) { setLoteMsg('Ingresa al menos un valor'); return }
    setLoteLoading(true); setLoteMsg('')
    let alertasTotal = 0
    try {
      for (const fila of filas) {
        const val = parseFloat(fila.valor)
        await ingestaAPI.enviarLectura({
          dispositivo_id: 1,
          id_logico: fila.id_logico,
          tipo_metrica: fila.tipo_metrica,
          valor_metrica: val,
          unidad: fila.unidad,
        })
        const resultado = await procesamientoAPI.procesarManual({
          dispositivo_id: 1,
          id_logico: fila.id_logico,
          tipo_metrica: fila.tipo_metrica,
          valor_metrica: val,
          unidad: fila.unidad,
        })
        if (resultado.data.alertas_generadas > 0) {
          alertasTotal += resultado.data.alertas_generadas
          const tipos = resultado.data.tipos_alerta
          await notificacionesAPI.enviar({
            dispositivo_id: 1,
            id_logico: fila.id_logico,
            tipo_alerta: tipos[0],
            tipo_metrica: fila.tipo_metrica,
            valor: val,
            condicion: `Valor ${val} ${fila.unidad} — ${tipos.join(', ')}`,
            severidad: resultado.data.alertas_generadas > 1 ? 'critica' : 'alta',
            canal: 'push',
          })
          await generarRecomendacionesAuto(
            { id_logico: fila.id_logico, tipo_metrica: fila.tipo_metrica, valor_metrica: val },
            resultado
          )
        }
      }
      setLoteMsg(`${filas.length} lecturas enviadas · ${alertasTotal} alertas · recomendaciones generadas`)
      setLoteRows(prev => prev.map(r => ({ ...r, valor: '' })))
      if (sensorSel) {
        setTimeout(() => { loadLecturas(sensorSel); loadAlertas(sensorSel) }, 500)
      }
    } catch(e) {
      setLoteMsg('Error enviando lote')
    } finally {
      setLoteLoading(false)
      setTimeout(() => setLoteMsg(''), 6000)
    }
  }

  const generarLoteAleatorio = () => {
    setLoteRows(prev => prev.map(r => {
      const sensor = sensores.find(s => s.id === r.id_logico)
      if (!sensor) return r
      const val = parseFloat((Math.random() * (sensor.max - sensor.min) + sensor.min).toFixed(2))
      return { ...r, valor: String(val) }
    }))
  }

  const lastVal = lecturas[lecturas.length - 1]?.valor
  const avg     = lecturas.length ? (lecturas.reduce((s, l) => s + l.valor, 0) / lecturas.length).toFixed(1) : '—'
  const maxVal  = lecturas.length ? Math.max(...lecturas.map(l => l.valor)).toFixed(1) : '—'
  const minVal  = lecturas.length ? Math.min(...lecturas.map(l => l.valor)).toFixed(1) : '—'
  const alertasFiltradas = filtroSev === 'todos' ? alertas : alertas.filter(a => a.severidad === filtroSev)
  const ESTADO_COLOR = { activo: '#22c55e', inactivo: '#6b7280', mantenimiento: '#fbbf24', desconectado: '#f87171' }

  return (
    <div style={styles.wrapper} className="animate-fade">
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Lecturas de Sensores</h1>
          <p style={styles.subtitle}>
            {sensores.length} sensores disponibles
            {sensorSel ? ` · Viendo: ${sensorSel.id}` : ''}
          </p>
        </div>
        <div style={styles.headerRight}>
          <select value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)} style={styles.estadoSelect}>
            <option value="activo">Solo activos</option>
            <option value="todos">Todos los estados</option>
            <option value="mantenimiento">Mantenimiento</option>
          </select>
          <button onClick={() => setAutoSim(!autoSim)} style={{
            ...styles.autoBtn,
            background:  autoSim ? 'rgba(34,197,94,0.15)' : 'rgba(107,114,128,0.1)',
            color:       autoSim ? '#22c55e' : '#6b7280',
            borderColor: autoSim ? 'rgba(34,197,94,0.3)' : 'rgba(107,114,128,0.2)',
          }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: autoSim ? '#22c55e' : '#6b7280', animation: autoSim ? 'pulse-green 2s infinite' : 'none' }} />
            {autoSim ? 'Auto-sim ON' : 'Auto-sim OFF'}
          </button>
          <button onClick={() => { if (sensorSel) { loadLecturas(sensorSel); loadAlertas(sensorSel) } loadSensores() }} className="btn btn-ghost" style={{ fontSize: '12px' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Actualizar
          </button>
        </div>
      </div>

      <div style={styles.tabsBar}>
        {[
          { id: 'lectura', label: 'Lectura individual' },
          { id: 'lote',    label: `Lote de lecturas (${sensores.length} sensores)` },
        ].map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            ...styles.tabBtn,
            ...(activeTab === t.id ? styles.tabBtnActive : {})
          }}>{t.label}</button>
        ))}
      </div>

      {activeTab === 'lectura' && (
        <>
          {loadingSensores ? (
            <div style={styles.loadingGrid}>
              {[...Array(6)].map((_, i) => <div key={i} className="skeleton" style={{ height: '56px', borderRadius: '10px' }} />)}
            </div>
          ) : sensores.length === 0 ? (
            <div style={styles.noSensores}>
              <div>No hay sensores disponibles con el filtro seleccionado</div>
              <div style={{ fontSize: '11px', marginTop: '4px', color: '#4b5563' }}>Cambia el filtro o registra sensores en Dispositivos</div>
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
                  <div style={{ fontWeight: 700, fontSize: '11px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.id}</div>
                  <div style={{ fontSize: '10px', opacity: 0.7, marginTop: '2px' }}>{s.metric}</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '3px' }}>
                    <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: ESTADO_COLOR[s.estado] || '#6b7280' }} />
                    <span style={{ fontSize: '9px', color: ESTADO_COLOR[s.estado] || '#6b7280' }}>{s.estado}</span>
                  </div>
                </button>
              ))}
            </div>
          )}

          {sensorSel && (
            <>
              <div style={styles.statsRow}>
                {[
                  { label: 'Sensor',       val: sensorSel.id,                          color: sensorSel.color },
                  { label: 'Ultimo valor', val: `${lastVal ?? '—'} ${sensorSel.unit}`, color: sensorSel.color },
                  { label: 'Promedio',     val: `${avg} ${sensorSel.unit}`,            color: '#60a5fa'       },
                  { label: 'Maximo',       val: `${maxVal} ${sensorSel.unit}`,         color: '#f87171'       },
                  { label: 'Minimo',       val: `${minVal} ${sensorSel.unit}`,         color: '#22c55e'       },
                  { label: 'Lecturas',     val: lecturas.length,                        color: '#a78bfa'       },
                ].map(s => (
                  <div key={s.label} style={styles.statCard}>
                    <div style={styles.statLabel}>{s.label}</div>
                    <div style={{ ...styles.statVal, color: s.color, fontSize: s.label === 'Sensor' ? '11px' : '14px', fontFamily: s.label === 'Sensor' ? 'monospace' : "'Syne', sans-serif" }}>{s.val}</div>
                  </div>
                ))}
              </div>

              <div className="card" style={{ marginBottom: '20px' }}>
                <div style={styles.chartHeader}>
                  <div style={styles.chartTitle}>{sensorSel.id} — {sensorSel.metric} — Ultimas {lecturas.length} lecturas</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: sensorSel.color }} />
                    <span style={{ fontSize: '12px', color: '#6b7280' }}>{sensorSel.unit}</span>
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
                    <div style={{ fontSize: '11px', marginTop: '4px', color: '#4b5563' }}>Usa el simulador para enviar lecturas</div>
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

              <div style={styles.bottomGrid}>
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
                  {simMsg && (
                    <div style={{ marginTop: '10px', fontSize: '13px', color: simMsg.includes('alerta') || simMsg.includes('Recomendacion') ? '#fbbf24' : simMsg.includes('Error') || simMsg.includes('estado') ? '#f87171' : '#22c55e' }}>
                      {simMsg}
                    </div>
                  )}
                </div>

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
                      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#374151" strokeWidth="1.5" style={{ marginBottom: '6px' }}>
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                      </svg>
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
            </>
          )}
        </>
      )}

      {activeTab === 'lote' && (
        <div className="animate-fade">
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '18px' }}>
              <div>
                <div style={styles.chartTitle}>Lote de lecturas — {sensores.length} sensores</div>
                <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                  Deja en blanco los sensores que no quieras enviar. Si hay alertas se generan recomendaciones automaticamente.
                </div>
              </div>
              <button onClick={generarLoteAleatorio} style={styles.genBtn}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                </svg>
                Generar aleatorio
              </button>
            </div>

            {loteRows.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#4b5563', fontSize: '13px' }}>
                No hay sensores disponibles. Registra sensores en Dispositivos.
              </div>
            ) : (
              <>
                <div style={styles.loteGrid}>
                  <div style={styles.loteHeader}>Sensor</div>
                  <div style={styles.loteHeader}>Metrica</div>
                  <div style={styles.loteHeader}>Valor</div>
                  <div style={styles.loteHeader}>Unidad</div>
                  {loteRows.map((row, i) => {
                    const sensor = sensores.find(s => s.id === row.id_logico)
                    return (
                      <>
                        <div key={`id-${i}`} style={styles.loteCell}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                            <span style={{ fontFamily: 'monospace', color: sensor?.color || '#4ade80', fontSize: '12px' }}>{row.id_logico}</span>
                            {sensor && <span style={{ fontSize: '10px', color: '#4b5563' }}>{sensor.estado}</span>}
                          </div>
                        </div>
                        <div key={`metric-${i}`} style={styles.loteCell}>
                          <span style={{ fontSize: '11px', color: '#9ca3af' }}>{row.tipo_metrica}</span>
                        </div>
                        <div key={`val-${i}`} style={styles.loteCellInput}>
                          <input
                            type="number"
                            placeholder="—"
                            value={row.valor}
                            onChange={e => setLoteRows(prev => prev.map((r, idx) => idx === i ? { ...r, valor: e.target.value } : r))}
                            style={styles.loteInput}
                          />
                        </div>
                        <div key={`unit-${i}`} style={styles.loteCell}>
                          <span style={{ fontSize: '12px', color: '#6b7280' }}>{row.unidad}</span>
                        </div>
                      </>
                    )
                  })}
                </div>

                <div style={{ marginTop: '18px', display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <button onClick={handleEnviarLote} disabled={loteLoading} className="btn btn-primary">
                    {loteLoading ? 'Enviando...' : `Enviar ${loteRows.filter(r => r.valor !== '').length} lecturas`}
                  </button>
                  <button onClick={() => setLoteRows(prev => prev.map(r => ({ ...r, valor: '' })))} className="btn btn-ghost" style={{ fontSize: '12px' }}>
                    Limpiar
                  </button>
                  {loteMsg && (
                    <span style={{ fontSize: '13px', color: loteMsg.includes('Error') ? '#f87171' : '#22c55e' }}>
                      {loteMsg}
                    </span>
                  )}
                </div>
              </>
            )}
          </div>
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
  wrapper: { padding: '32px', maxWidth: '1100px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' },
  title: { fontFamily: "'Syne', sans-serif", fontSize: '26px', fontWeight: 700, color: '#f0fdf4' },
  subtitle: { fontSize: '13px', color: '#6b7280', marginTop: '4px' },
  headerRight: { display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' },
  estadoSelect: { padding: '7px 12px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#9ca3af', fontSize: '12px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  autoBtn: { display: 'flex', alignItems: 'center', gap: '7px', padding: '8px 14px', borderRadius: '20px', border: '1px solid', fontSize: '12px', fontWeight: 600, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.2s' },
  tabsBar: { display: 'flex', gap: '4px', marginBottom: '20px', background: '#0d1510', borderRadius: '10px', padding: '4px', border: '1px solid rgba(34,197,94,0.1)' },
  tabBtn: { flex: 1, padding: '9px', borderRadius: '7px', border: 'none', background: 'transparent', color: '#6b7280', fontSize: '13px', fontWeight: 500, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s' },
  tabBtnActive: { background: 'rgba(34,197,94,0.15)', color: '#22c55e' },
  loadingGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '8px', marginBottom: '20px' },
  noSensores: { textAlign: 'center', padding: '40px', color: '#4b5563', fontSize: '13px', display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#0d1510', borderRadius: '12px', border: '1px solid rgba(34,197,94,0.1)', marginBottom: '20px' },
  sensorGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '8px', marginBottom: '20px' },
  sensorBtn: { padding: '10px 8px', borderRadius: '10px', border: '1px solid', background: '#0d1510', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s', textAlign: 'center' },
  statsRow: { display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '10px', marginBottom: '20px' },
  statCard: { background: '#0d1510', border: '1px solid rgba(34,197,94,0.1)', borderRadius: '10px', padding: '12px', textAlign: 'center' },
  statLabel: { fontSize: '10px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '6px' },
  statVal: { fontFamily: "'Syne', sans-serif", fontSize: '14px', fontWeight: 700 },
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
  noAlertas: { textAlign: 'center', padding: '30px', color: '#4b5563', display: 'flex', flexDirection: 'column', alignItems: 'center' },
  alertItem: { background: 'rgba(6,12,7,0.6)', borderRadius: '6px', padding: '8px 10px' },
  genBtn: { display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px', borderRadius: '8px', border: '1px solid rgba(34,197,94,0.2)', background: 'rgba(34,197,94,0.08)', color: '#4ade80', fontSize: '12px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", whiteSpace: 'nowrap' },
  loteGrid: { display: 'grid', gridTemplateColumns: '160px 1fr 150px 80px', gap: '8px', alignItems: 'center' },
  loteHeader: { fontSize: '10px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.7px', padding: '6px 10px', fontWeight: 600 },
  loteCell: { padding: '8px 12px', background: 'rgba(6,12,7,0.5)', borderRadius: '7px', minHeight: '38px', display: 'flex', alignItems: 'center', border: '1px solid rgba(34,197,94,0.06)' },
  loteCellInput: { minHeight: '38px', display: 'flex', alignItems: 'center' },
  loteInput: { width: '100%', padding: '8px 12px', background: 'rgba(6,12,7,0.8)', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '7px', color: '#f0fdf4', fontSize: '13px', fontFamily: "'DM Sans', sans-serif" },
}