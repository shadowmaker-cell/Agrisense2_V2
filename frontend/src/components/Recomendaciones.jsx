import { useState, useEffect } from 'react'
import { recomendacionesAPI } from '../api/client'

const PRIORIDAD_CONFIG = {
  critica: { color: '#f87171', bg: 'rgba(248,113,113,0.1)', border: 'rgba(248,113,113,0.2)', label: 'CRITICA' },
  alta:    { color: '#fbbf24', bg: 'rgba(251,191,36,0.1)',  border: 'rgba(251,191,36,0.2)',  label: 'ALTA'    },
  media:   { color: '#60a5fa', bg: 'rgba(96,165,250,0.1)',  border: 'rgba(96,165,250,0.2)',  label: 'MEDIA'   },
  baja:    { color: '#22c55e', bg: 'rgba(34,197,94,0.1)',   border: 'rgba(34,197,94,0.2)',   label: 'BAJA'    },
}

const ESTADO_COLOR = {
  activa:     '#22c55e',
  aplicada:   '#60a5fa',
  descartada: '#6b7280',
  vencida:    '#f87171',
}

const CAT_ICON = {
  'Riego':           '💧',
  'Nutricion':       '🌱',
  'Proteccion':      '🛡️',
  'Clima':           '🌤️',
  'Suelo':           '🪱',
  'Cosecha':         '🌾',
  'Infraestructura': '🔧',
}

export default function Recomendaciones() {
  const [recomendaciones, setRecomendaciones] = useState([])
  const [resumen, setResumen]                 = useState(null)
  const [loading, setLoading]                 = useState(true)
  const [activeTab, setActiveTab]             = useState('lista')
  const [filtroPrioridad, setFiltroPrioridad] = useState('todos')
  const [filtroEstado, setFiltroEstado]       = useState('activa')
  const [genLoading, setGenLoading]           = useState(false)
  const [genMsg, setGenMsg]                   = useState('')

  const [genForm, setGenForm] = useState({
    parcela_id: '', id_logico: '',
    humedad_suelo: '', temperatura_aire: '', ph_suelo: '',
    lluvia: '', velocidad_viento: '', humedad_aire: '',
    tipo_cultivo: 'maiz', area_hectareas: '',
  })

  const CULTIVOS = ['maiz','arroz','cafe','platano','yuca','papa','tomate','cana','cacao','aguacate','frijol','soya','sorgo','palma','flores']

  const load = async () => {
    try {
      const [rRes, sumRes] = await Promise.all([
        recomendacionesAPI.listar({
          prioridad: filtroPrioridad !== 'todos' ? filtroPrioridad : undefined,
          estado:    filtroEstado   !== 'todos' ? filtroEstado    : undefined,
          limite:    100,
        }),
        recomendacionesAPI.resumen(),
      ])
      setRecomendaciones(rRes.data)
      setResumen(sumRes.data)
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [filtroPrioridad, filtroEstado])

  const handleGenerar = async (e) => {
    e.preventDefault()
    setGenLoading(true); setGenMsg('')
    const payload = {}
    Object.entries(genForm).forEach(([k, v]) => {
      if (v !== '' && v !== null) {
        payload[k] = ['parcela_id'].includes(k) ? parseInt(v) :
                     ['humedad_suelo','temperatura_aire','ph_suelo','lluvia','velocidad_viento','humedad_aire','area_hectareas'].includes(k)
                     ? parseFloat(v) : v
      }
    })
    try {
      const res = await recomendacionesAPI.generar(payload)
      const data = res.data
      setGenMsg(`${data.total_generadas} recomendaciones generadas — ${data.criticas} criticas, ${data.altas} altas`)
      await load()
      setActiveTab('lista')
    } catch(e) {
      setGenMsg('Error generando recomendaciones')
    } finally { setGenLoading(false) }
  }

  const handleActualizar = async (id, estado) => {
    try {
      await recomendacionesAPI.actualizarEstado(id, estado)
      await load()
    } catch(e) { console.error(e) }
  }

  const filtered = recomendaciones.filter(r => {
    const okP = filtroPrioridad === 'todos' || r.prioridad === filtroPrioridad
    const okE = filtroEstado    === 'todos' || r.estado    === filtroEstado
    return okP && okE
  })

  const TABS = [
    { id: 'lista',   label: 'Recomendaciones' },
    { id: 'generar', label: 'Generar nuevas'   },
  ]

  return (
    <div style={styles.wrapper} className="animate-fade">
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Recomendaciones Agronomicas</h1>
          <p style={styles.subtitle}>Motor de inteligencia combinando reglas y predicciones ML</p>
        </div>
        <button onClick={load} className="btn btn-ghost" style={{ fontSize: '12px' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          Actualizar
        </button>
      </div>

      {resumen && (
        <div style={styles.kpiGrid}>
          {[
            { label: 'Total',     val: resumen.total,    color: '#f0fdf4', bg: 'rgba(255,255,255,0.04)' },
            { label: 'Activas',   val: resumen.activas,  color: '#22c55e', bg: 'rgba(34,197,94,0.08)'   },
            { label: 'Aplicadas', val: resumen.aplicadas,color: '#60a5fa', bg: 'rgba(96,165,250,0.08)'  },
            { label: 'Criticas',  val: resumen.criticas, color: '#f87171', bg: 'rgba(248,113,113,0.08)' },
            { label: 'Altas',     val: resumen.altas,    color: '#fbbf24', bg: 'rgba(251,191,36,0.08)'  },
          ].map(k => (
            <div key={k.label} style={{ ...styles.kpiCard, background: k.bg }}>
              <div style={{ fontFamily: "'Syne', sans-serif", fontSize: '28px', fontWeight: 800, color: k.color }}>{k.val}</div>
              <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>{k.label}</div>
            </div>
          ))}
        </div>
      )}

      <div style={styles.tabsBar}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            ...styles.tabBtn,
            ...(activeTab === t.id ? styles.tabBtnActive : {})
          }}>{t.label}</button>
        ))}
      </div>

      {activeTab === 'lista' && (
        <>
          <div style={styles.filters}>
            <div style={styles.filterGroup}>
              <label style={styles.filterLabel}>Prioridad</label>
              <select value={filtroPrioridad} onChange={e => setFiltroPrioridad(e.target.value)} style={styles.select}>
                <option value="todos">Todas</option>
                <option value="critica">Critica</option>
                <option value="alta">Alta</option>
                <option value="media">Media</option>
                <option value="baja">Baja</option>
              </select>
            </div>
            <div style={styles.filterGroup}>
              <label style={styles.filterLabel}>Estado</label>
              <select value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)} style={styles.select}>
                <option value="todos">Todos</option>
                <option value="activa">Activa</option>
                <option value="aplicada">Aplicada</option>
                <option value="descartada">Descartada</option>
                <option value="vencida">Vencida</option>
              </select>
            </div>
            <div style={styles.countTag}>{filtered.length} resultados</div>
          </div>

          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: '120px', borderRadius: '12px' }} />)}
            </div>
          ) : filtered.length === 0 ? (
            <div style={styles.empty}>
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#374151" strokeWidth="1.5" style={{ marginBottom: '10px' }}>
                <path d="M9 11l3 3L22 4"/>
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
              </svg>
              <div style={styles.emptyText}>Sin recomendaciones</div>
              <div style={styles.emptySub}>Usa el tab "Generar nuevas" para crear recomendaciones</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {filtered.map((r, i) => {
                const prio = PRIORIDAD_CONFIG[r.prioridad] || PRIORIDAD_CONFIG.baja
                const icon = CAT_ICON[r.categoria_nombre] || '📋'
                return (
                  <div key={r.id} style={{
                    ...styles.recCard,
                    borderLeft: `4px solid ${prio.color}`,
                    animationDelay: `${i * 0.03}s`,
                  }} className="animate-fade">
                    <div style={styles.recHeader}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1 }}>
                        <span style={{ fontSize: '20px' }}>{icon}</span>
                        <div>
                          <div style={styles.recTitulo}>{r.titulo}</div>
                          <div style={{ display: 'flex', gap: '8px', marginTop: '4px', flexWrap: 'wrap' }}>
                            <span style={{ ...styles.prioBadge, color: prio.color, background: prio.bg, border: `1px solid ${prio.border}` }}>
                              {prio.label}
                            </span>
                            {r.categoria_nombre && (
                              <span style={styles.catBadge}>{r.categoria_nombre}</span>
                            )}
                            {r.fuente && (
                              <span style={styles.fuenteBadge}>{r.fuente === 'ml' ? '🤖 ML' : r.fuente === 'manual' ? '✍️ Manual' : '📋 Regla'}</span>
                            )}
                            <span style={{ fontSize: '11px', fontWeight: 600, color: ESTADO_COLOR[r.estado] || '#6b7280' }}>
                              {r.estado}
                            </span>
                          </div>
                        </div>
                      </div>
                      {r.estado === 'activa' && (
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <button onClick={() => handleActualizar(r.id, 'aplicada')} style={styles.aplicarBtn}>
                            Aplicada
                          </button>
                          <button onClick={() => handleActualizar(r.id, 'descartada')} style={styles.descartarBtn}>
                            Descartar
                          </button>
                        </div>
                      )}
                    </div>
                    <div style={styles.recDesc}>{r.descripcion}</div>
                    <div style={styles.recAccion}>
                      <span style={{ fontSize: '11px', color: '#4ade80', fontWeight: 600 }}>ACCION: </span>
                      {r.accion}
                    </div>
                    <div style={styles.recMeta}>
                      {r.parcela_id && <span>Parcela #{r.parcela_id}</span>}
                      {r.id_logico  && <span style={{ fontFamily: 'monospace', color: '#4ade80' }}>{r.id_logico}</span>}
                      <span>{new Date(r.generada_en).toLocaleString('es-CO')}</span>
                      {r.valida_hasta && <span>Valida hasta: {new Date(r.valida_hasta).toLocaleDateString('es-CO')}</span>}
                    </div>
                    {r.evidencias && r.evidencias.length > 0 && (
                      <div style={styles.evidencias}>
                        {r.evidencias.map(ev => (
                          <div key={ev.id} style={styles.evidencia}>
                            <span style={{ fontSize: '10px', color: '#4b5563' }}>{ev.tipo_fuente}</span>
                            <span style={{ fontSize: '11px', color: '#9ca3af' }}>{ev.descripcion}</span>
                            {ev.valor_observado !== null && (
                              <span style={{ fontSize: '11px', color: prio.color, fontWeight: 600 }}>
                                {ev.valor_observado} {ev.unidad}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}

      {activeTab === 'generar' && (
        <div style={styles.genCard}>
          <div style={styles.genTitle}>Generar recomendaciones agronomicas</div>
          <p style={{ fontSize: '13px', color: '#6b7280', marginBottom: '20px', lineHeight: 1.6 }}>
            Ingresa las condiciones actuales del cultivo. El motor analizara los datos y generara
            recomendaciones combinando reglas agronomicas y predicciones del modelo ML.
          </p>
          <form onSubmit={handleGenerar} style={styles.genGrid}>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Parcela ID</label>
              <input type="number" placeholder="ej: 1" value={genForm.parcela_id}
                onChange={e => setGenForm(p => ({...p, parcela_id: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>ID Logico sensor</label>
              <input placeholder="ej: SOIL_HUM_01" value={genForm.id_logico}
                onChange={e => setGenForm(p => ({...p, id_logico: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Tipo de cultivo</label>
              <select value={genForm.tipo_cultivo}
                onChange={e => setGenForm(p => ({...p, tipo_cultivo: e.target.value}))} style={styles.input}>
                {CULTIVOS.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
              </select>
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Area (hectareas)</label>
              <input type="number" step="0.1" placeholder="ej: 10.5" value={genForm.area_hectareas}
                onChange={e => setGenForm(p => ({...p, area_hectareas: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Humedad suelo (%)</label>
              <input type="number" step="0.1" placeholder="ej: 35.0" value={genForm.humedad_suelo}
                onChange={e => setGenForm(p => ({...p, humedad_suelo: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Temperatura aire (C)</label>
              <input type="number" step="0.1" placeholder="ej: 28.0" value={genForm.temperatura_aire}
                onChange={e => setGenForm(p => ({...p, temperatura_aire: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>pH suelo</label>
              <input type="number" step="0.1" placeholder="ej: 6.5" value={genForm.ph_suelo}
                onChange={e => setGenForm(p => ({...p, ph_suelo: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Lluvia (mm)</label>
              <input type="number" step="0.1" placeholder="ej: 5.0" value={genForm.lluvia}
                onChange={e => setGenForm(p => ({...p, lluvia: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Velocidad viento (km/h)</label>
              <input type="number" step="0.1" placeholder="ej: 12.0" value={genForm.velocidad_viento}
                onChange={e => setGenForm(p => ({...p, velocidad_viento: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Humedad aire (%)</label>
              <input type="number" step="0.1" placeholder="ej: 70.0" value={genForm.humedad_aire}
                onChange={e => setGenForm(p => ({...p, humedad_aire: e.target.value}))} style={styles.input} />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <button type="submit" disabled={genLoading} style={styles.submitBtn}>
                {genLoading ? 'Generando recomendaciones...' : 'Generar recomendaciones'}
              </button>
            </div>
          </form>
          {genMsg && (
            <div style={{ marginTop: '14px', fontSize: '13px', color: genMsg.includes('Error') ? '#f87171' : '#22c55e', padding: '10px 14px', background: genMsg.includes('Error') ? 'rgba(248,113,113,0.08)' : 'rgba(34,197,94,0.08)', borderRadius: '8px' }}>
              {genMsg}
            </div>
          )}
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
  kpiGrid: { display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px', marginBottom: '20px' },
  kpiCard: { borderRadius: '12px', padding: '16px', border: '1px solid rgba(34,197,94,0.08)', textAlign: 'center' },
  tabsBar: { display: 'flex', gap: '4px', marginBottom: '20px', background: '#0d1510', borderRadius: '10px', padding: '4px', border: '1px solid rgba(34,197,94,0.1)' },
  tabBtn: { flex: 1, padding: '9px', borderRadius: '7px', border: 'none', background: 'transparent', color: '#6b7280', fontSize: '13px', fontWeight: 500, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s' },
  tabBtnActive: { background: 'rgba(34,197,94,0.15)', color: '#22c55e' },
  filters: { display: 'flex', gap: '12px', marginBottom: '20px', alignItems: 'flex-end', flexWrap: 'wrap' },
  filterGroup: { display: 'flex', flexDirection: 'column', gap: '5px' },
  filterLabel: { fontSize: '11px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px' },
  select: { padding: '9px 14px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#9ca3af', fontSize: '13px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", minWidth: '160px' },
  countTag: { background: 'rgba(34,197,94,0.08)', color: '#4ade80', padding: '6px 12px', borderRadius: '20px', fontSize: '12px', border: '1px solid rgba(34,197,94,0.15)', alignSelf: 'flex-end' },
  recCard: { background: '#0d1510', border: '1px solid rgba(34,197,94,0.08)', borderRadius: '12px', padding: '16px 18px' },
  recHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' },
  recTitulo: { fontFamily: "'Syne', sans-serif", fontSize: '14px', fontWeight: 600, color: '#f0fdf4' },
  prioBadge: { padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 700, letterSpacing: '0.5px' },
  catBadge: { fontSize: '11px', color: '#6b7280', background: 'rgba(107,114,128,0.1)', padding: '2px 8px', borderRadius: '4px' },
  fuenteBadge: { fontSize: '11px', color: '#a78bfa', background: 'rgba(167,139,250,0.1)', padding: '2px 8px', borderRadius: '4px' },
  recDesc: { fontSize: '13px', color: '#9ca3af', marginBottom: '8px', lineHeight: 1.5 },
  recAccion: { fontSize: '12px', color: '#d1fae5', background: 'rgba(34,197,94,0.05)', padding: '8px 12px', borderRadius: '6px', marginBottom: '8px', lineHeight: 1.5 },
  recMeta: { display: 'flex', gap: '10px', fontSize: '11px', color: '#4b5563', flexWrap: 'wrap' },
  evidencias: { display: 'flex', gap: '8px', marginTop: '10px', flexWrap: 'wrap' },
  evidencia: { display: 'flex', gap: '6px', alignItems: 'center', background: 'rgba(6,12,7,0.6)', padding: '4px 10px', borderRadius: '6px', border: '1px solid rgba(34,197,94,0.06)' },
  aplicarBtn: { padding: '5px 12px', borderRadius: '6px', border: '1px solid rgba(34,197,94,0.2)', background: 'rgba(34,197,94,0.08)', color: '#22c55e', fontSize: '11px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  descartarBtn: { padding: '5px 12px', borderRadius: '6px', border: '1px solid rgba(107,114,128,0.2)', background: 'rgba(107,114,128,0.08)', color: '#6b7280', fontSize: '11px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  empty: { textAlign: 'center', padding: '80px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center' },
  emptyText: { fontSize: '18px', fontWeight: 600, color: '#f0fdf4', fontFamily: "'Syne', sans-serif", marginBottom: '6px' },
  emptySub: { fontSize: '13px', color: '#6b7280' },
  genCard: { background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '16px', padding: '24px' },
  genTitle: { fontFamily: "'Syne', sans-serif", fontSize: '15px', fontWeight: 600, color: '#f0fdf4', marginBottom: '8px' },
  genGrid: { display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px' },
  fieldGroup: { display: 'flex', flexDirection: 'column', gap: '5px' },
  label: { fontSize: '11px', fontWeight: 500, color: '#86efac', letterSpacing: '0.4px' },
  input: { padding: '9px 12px', background: 'rgba(6,12,7,0.8)', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#f0fdf4', fontSize: '13px', fontFamily: "'DM Sans', sans-serif" },
  submitBtn: { width: '100%', padding: '12px', background: 'linear-gradient(135deg, #16a34a, #15803d)', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
}