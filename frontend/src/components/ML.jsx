import { useState, useEffect } from 'react'
import { mlAPI } from '../api/client'

const CULTIVOS = ['maiz','arroz','cafe','platano','yuca','papa','tomate','cana','cacao','aguacate','frijol','soya','sorgo','palma','flores']

const NIVEL_COLOR = { bajo: '#22c55e', medio: '#fbbf24', alto: '#f97316', critico: '#f87171' }
const URGENCIA_COLOR = { baja: '#22c55e', media: '#fbbf24', alta: '#f97316', critica: '#f87171' }
const CALIF_COLOR = { excelente: '#22c55e', bueno: '#60a5fa', regular: '#fbbf24', bajo: '#f87171' }

export default function ML() {
  const [activeTab, setActiveTab]   = useState('agua')
  const [resumen, setResumen]       = useState(null)
  const [modelos, setModelos]       = useState([])
  const [loading, setLoading]       = useState(false)
  const [resultado, setResultado]   = useState(null)

  const [aguaForm, setAguaForm] = useState({
    humedad_suelo: '', temperatura_aire: '', lluvia: '0',
    area_hectareas: '', tipo_cultivo: 'maiz',
    parcela_id: '', id_logico: '',
  })

  const [rendForm, setRendForm] = useState({
    area_hectareas: '', tipo_cultivo: 'maiz',
    humedad_suelo: '', temperatura_aire: '',
    ph_suelo: '6.5', lluvia_acumulada: '0',
    etapa_fenologica: 'vegetativo',
    parcela_id: '', id_logico: '',
  })

  const [riesgoForm, setRiesgoForm] = useState({
    temperatura_aire: '', humedad_aire: '60',
    humedad_suelo: '50', velocidad_viento: '0',
    lluvia: '0', tipo_riesgo: 'helada',
    parcela_id: '', id_logico: '',
  })

  const ETAPAS = ['germinacion','vegetativo','floracion','fructificacion','maduracion','cosecha']

  useEffect(() => {
    const loadResumen = async () => {
      try {
        const [rRes, mRes] = await Promise.all([mlAPI.resumen(), mlAPI.modelos()])
        setResumen(rRes.data)
        setModelos(mRes.data)
      } catch(e) { console.error(e) }
    }
    loadResumen()
  }, [])

  const cleanPayload = (form, numFields) => {
    const payload = {}
    Object.entries(form).forEach(([k, v]) => {
      if (v !== '' && v !== null) {
        payload[k] = numFields.includes(k) ? parseFloat(v) :
                     k === 'parcela_id' ? parseInt(v) : v
      }
    })
    return payload
  }

  const handlePredecirAgua = async (e) => {
    e.preventDefault()
    if (!aguaForm.humedad_suelo || !aguaForm.temperatura_aire || !aguaForm.area_hectareas) {
      setResultado({ error: 'Humedad, temperatura y area son obligatorios' }); return
    }
    setLoading(true); setResultado(null)
    try {
      const payload = cleanPayload(aguaForm, ['humedad_suelo','temperatura_aire','lluvia','area_hectareas'])
      const res = await mlAPI.predecirAgua(payload)
      setResultado({ tipo: 'agua', data: res.data })
    } catch(e) {
      setResultado({ error: 'Error en prediccion' })
    } finally { setLoading(false) }
  }

  const handlePredecirRendimiento = async (e) => {
    e.preventDefault()
    if (!rendForm.area_hectareas || !rendForm.humedad_suelo || !rendForm.temperatura_aire) {
      setResultado({ error: 'Area, humedad y temperatura son obligatorios' }); return
    }
    setLoading(true); setResultado(null)
    try {
      const payload = cleanPayload(rendForm, ['area_hectareas','humedad_suelo','temperatura_aire','ph_suelo','lluvia_acumulada'])
      const res = await mlAPI.predecirRendimiento(payload)
      setResultado({ tipo: 'rendimiento', data: res.data })
    } catch(e) {
      setResultado({ error: 'Error en prediccion' })
    } finally { setLoading(false) }
  }

  const handlePredecirRiesgo = async (e) => {
    e.preventDefault()
    if (!riesgoForm.temperatura_aire) {
      setResultado({ error: 'La temperatura es obligatoria' }); return
    }
    setLoading(true); setResultado(null)
    try {
      const payload = cleanPayload(riesgoForm, ['temperatura_aire','humedad_aire','humedad_suelo','velocidad_viento','lluvia'])
      const res = await mlAPI.predecirRiesgo(payload)
      setResultado({ tipo: 'riesgo', data: res.data })
    } catch(e) {
      setResultado({ error: 'Error en prediccion' })
    } finally { setLoading(false) }
  }

  const TABS = [
    { id: 'agua',        label: '💧 Necesidades de Agua'  },
    { id: 'rendimiento', label: '🌾 Rendimiento Esperado'  },
    { id: 'riesgo',      label: '⚠️ Riesgo Agronomico'    },
    { id: 'modelos',     label: '🤖 Modelos Activos'       },
  ]

  return (
    <div style={styles.wrapper} className="animate-fade">
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Predicciones Machine Learning</h1>
          <p style={styles.subtitle}>Modelos entrenados con datos agronomicos de cultivos colombianos</p>
        </div>
      </div>

      {resumen && (
        <div style={styles.kpiGrid}>
          {[
            { label: 'Total predicciones', val: resumen.total_predicciones,        color: '#f0fdf4' },
            { label: 'Agua',               val: resumen.predicciones_agua,          color: '#38bdf8' },
            { label: 'Rendimiento',        val: resumen.predicciones_rendimiento,   color: '#22c55e' },
            { label: 'Riesgo',             val: resumen.predicciones_riesgo,        color: '#f87171' },
            { label: 'Modelos activos',    val: resumen.modelos_activos,            color: '#a78bfa' },
          ].map(k => (
            <div key={k.label} style={styles.kpiCard}>
              <div style={{ fontFamily: "'Syne', sans-serif", fontSize: '28px', fontWeight: 800, color: k.color }}>{k.val}</div>
              <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>{k.label}</div>
            </div>
          ))}
        </div>
      )}

      <div style={styles.tabsBar}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => { setActiveTab(t.id); setResultado(null) }} style={{
            ...styles.tabBtn,
            ...(activeTab === t.id ? styles.tabBtnActive : {})
          }}>{t.label}</button>
        ))}
      </div>

      {/* ── Agua ── */}
      {activeTab === 'agua' && (
        <div style={styles.layout}>
          <div style={styles.formCard}>
            <div style={styles.formTitle}>Prediccion de necesidades hidricas</div>
            <p style={styles.formDesc}>Calcula los litros de agua necesarios y la frecuencia de riego optima usando RandomForest.</p>
            <form onSubmit={handlePredecirAgua} style={styles.formGrid}>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Humedad suelo (%) *</label>
                <input type="number" step="0.1" placeholder="ej: 35.0" value={aguaForm.humedad_suelo}
                  onChange={e => setAguaForm(p => ({...p, humedad_suelo: e.target.value}))} style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Temperatura aire (C) *</label>
                <input type="number" step="0.1" placeholder="ej: 28.0" value={aguaForm.temperatura_aire}
                  onChange={e => setAguaForm(p => ({...p, temperatura_aire: e.target.value}))} style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Area hectareas *</label>
                <input type="number" step="0.1" placeholder="ej: 10.5" value={aguaForm.area_hectareas}
                  onChange={e => setAguaForm(p => ({...p, area_hectareas: e.target.value}))} style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Lluvia reciente (mm)</label>
                <input type="number" step="0.1" placeholder="0" value={aguaForm.lluvia}
                  onChange={e => setAguaForm(p => ({...p, lluvia: e.target.value}))} style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Tipo de cultivo</label>
                <select value={aguaForm.tipo_cultivo}
                  onChange={e => setAguaForm(p => ({...p, tipo_cultivo: e.target.value}))} style={styles.input}>
                  {CULTIVOS.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
                </select>
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>ID Logico (opcional)</label>
                <input placeholder="ej: SOIL_HUM_01" value={aguaForm.id_logico}
                  onChange={e => setAguaForm(p => ({...p, id_logico: e.target.value}))} style={styles.input} />
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <button type="submit" disabled={loading} style={styles.submitBtn}>
                  {loading ? 'Calculando...' : 'Predecir necesidades de agua'}
                </button>
              </div>
            </form>
          </div>

          {resultado && !resultado.error && resultado.tipo === 'agua' && (
            <div style={styles.resultCard} className="animate-fade">
              <div style={styles.resultTitle}>Resultado</div>
              <div style={styles.resultMain}>
                <div style={{ fontFamily: "'Syne', sans-serif", fontSize: '48px', fontWeight: 800, color: '#38bdf8' }}>
                  {resultado.data.litros_recomendados.toLocaleString()}
                </div>
                <div style={{ fontSize: '16px', color: '#6b7280' }}>litros recomendados</div>
              </div>
              <div style={styles.resultGrid}>
                <div style={styles.resultItem}>
                  <div style={styles.resultLabel}>Frecuencia</div>
                  <div style={{ fontSize: '18px', fontWeight: 700, color: '#f0fdf4' }}>
                    Cada {resultado.data.frecuencia_horas}h
                  </div>
                </div>
                <div style={styles.resultItem}>
                  <div style={styles.resultLabel}>Urgencia</div>
                  <div style={{ fontSize: '18px', fontWeight: 700, color: URGENCIA_COLOR[resultado.data.urgencia] || '#f0fdf4' }}>
                    {resultado.data.urgencia.toUpperCase()}
                  </div>
                </div>
                <div style={styles.resultItem}>
                  <div style={styles.resultLabel}>Confianza</div>
                  <div style={{ fontSize: '18px', fontWeight: 700, color: '#22c55e' }}>
                    {(resultado.data.confianza * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
              <div style={styles.resultExplicacion}>{resultado.data.explicacion}</div>
            </div>
          )}
          {resultado?.error && <div style={styles.errorCard}>{resultado.error}</div>}
        </div>
      )}

      {/* ── Rendimiento ── */}
      {activeTab === 'rendimiento' && (
        <div style={styles.layout}>
          <div style={styles.formCard}>
            <div style={styles.formTitle}>Prediccion de rendimiento del cultivo</div>
            <p style={styles.formDesc}>Estima el rendimiento esperado en kg/ha considerando condiciones del suelo, clima y etapa fenologica.</p>
            <form onSubmit={handlePredecirRendimiento} style={styles.formGrid}>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Tipo de cultivo *</label>
                <select value={rendForm.tipo_cultivo}
                  onChange={e => setRendForm(p => ({...p, tipo_cultivo: e.target.value}))} style={styles.input}>
                  {CULTIVOS.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
                </select>
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Area hectareas *</label>
                <input type="number" step="0.1" placeholder="ej: 15.0" value={rendForm.area_hectareas}
                  onChange={e => setRendForm(p => ({...p, area_hectareas: e.target.value}))} style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Humedad suelo (%) *</label>
                <input type="number" step="0.1" placeholder="ej: 65.0" value={rendForm.humedad_suelo}
                  onChange={e => setRendForm(p => ({...p, humedad_suelo: e.target.value}))} style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Temperatura aire (C) *</label>
                <input type="number" step="0.1" placeholder="ej: 25.0" value={rendForm.temperatura_aire}
                  onChange={e => setRendForm(p => ({...p, temperatura_aire: e.target.value}))} style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>pH suelo</label>
                <input type="number" step="0.1" placeholder="6.5" value={rendForm.ph_suelo}
                  onChange={e => setRendForm(p => ({...p, ph_suelo: e.target.value}))} style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Lluvia acumulada (mm)</label>
                <input type="number" step="0.1" placeholder="0" value={rendForm.lluvia_acumulada}
                  onChange={e => setRendForm(p => ({...p, lluvia_acumulada: e.target.value}))} style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Etapa fenologica</label>
                <select value={rendForm.etapa_fenologica}
                  onChange={e => setRendForm(p => ({...p, etapa_fenologica: e.target.value}))} style={styles.input}>
                  {ETAPAS.map(et => <option key={et} value={et}>{et.charAt(0).toUpperCase() + et.slice(1)}</option>)}
                </select>
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>ID Logico (opcional)</label>
                <input placeholder="ej: SOIL_HUM_01" value={rendForm.id_logico}
                  onChange={e => setRendForm(p => ({...p, id_logico: e.target.value}))} style={styles.input} />
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <button type="submit" disabled={loading} style={styles.submitBtn}>
                  {loading ? 'Calculando...' : 'Predecir rendimiento'}
                </button>
              </div>
            </form>
          </div>

          {resultado && !resultado.error && resultado.tipo === 'rendimiento' && (
            <div style={styles.resultCard} className="animate-fade">
              <div style={styles.resultTitle}>Resultado</div>
              <div style={styles.resultMain}>
                <div style={{ fontFamily: "'Syne', sans-serif", fontSize: '40px', fontWeight: 800, color: CALIF_COLOR[resultado.data.calificacion] || '#22c55e' }}>
                  {resultado.data.rendimiento_kg_ha.toLocaleString()} kg/ha
                </div>
                <div style={{ fontSize: '14px', color: '#6b7280', marginTop: '4px' }}>
                  Total: {resultado.data.rendimiento_total_kg.toLocaleString()} kg
                </div>
              </div>
              <div style={styles.resultGrid}>
                <div style={styles.resultItem}>
                  <div style={styles.resultLabel}>Calificacion</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: CALIF_COLOR[resultado.data.calificacion] }}>
                    {resultado.data.calificacion.toUpperCase()}
                  </div>
                </div>
                <div style={styles.resultItem}>
                  <div style={styles.resultLabel}>Confianza</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#22c55e' }}>
                    {(resultado.data.confianza * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
              {resultado.data.factores_riesgo?.length > 0 && (
                <div style={{ marginTop: '14px' }}>
                  <div style={{ fontSize: '11px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '8px' }}>Factores de riesgo</div>
                  {resultado.data.factores_riesgo.map((f, i) => (
                    <div key={i} style={{ fontSize: '12px', color: '#fbbf24', marginBottom: '4px', display: 'flex', gap: '6px' }}>
                      <span>⚠</span><span>{f}</span>
                    </div>
                  ))}
                </div>
              )}
              {resultado.data.recomendaciones?.length > 0 && (
                <div style={{ marginTop: '12px' }}>
                  <div style={{ fontSize: '11px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '8px' }}>Recomendaciones</div>
                  {resultado.data.recomendaciones.map((r, i) => (
                    <div key={i} style={{ fontSize: '12px', color: '#d1fae5', marginBottom: '4px', display: 'flex', gap: '6px' }}>
                      <span>✓</span><span>{r}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          {resultado?.error && <div style={styles.errorCard}>{resultado.error}</div>}
        </div>
      )}

      {/* ── Riesgo ── */}
      {activeTab === 'riesgo' && (
        <div style={styles.layout}>
          <div style={styles.formCard}>
            <div style={styles.formTitle}>Prediccion de riesgo agronomico</div>
            <p style={styles.formDesc}>Clasifica el nivel de riesgo para helada, sequia, hongo o inundacion usando GradientBoosting.</p>
            <form onSubmit={handlePredecirRiesgo} style={styles.formGrid}>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Tipo de riesgo *</label>
                <select value={riesgoForm.tipo_riesgo}
                  onChange={e => setRiesgoForm(p => ({...p, tipo_riesgo: e.target.value}))} style={styles.input}>
                  <option value="helada">Helada</option>
                  <option value="sequia">Sequia</option>
                  <option value="hongo">Hongo / Enfermedad fungica</option>
                  <option value="inundacion">Inundacion</option>
                </select>
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Temperatura aire (C) *</label>
                <input type="number" step="0.1" placeholder="ej: -2.0" value={riesgoForm.temperatura_aire}
                  onChange={e => setRiesgoForm(p => ({...p, temperatura_aire: e.target.value}))} style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Humedad aire (%)</label>
                <input type="number" step="0.1" placeholder="60" value={riesgoForm.humedad_aire}
                  onChange={e => setRiesgoForm(p => ({...p, humedad_aire: e.target.value}))} style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Humedad suelo (%)</label>
                <input type="number" step="0.1" placeholder="50" value={riesgoForm.humedad_suelo}
                  onChange={e => setRiesgoForm(p => ({...p, humedad_suelo: e.target.value}))} style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Velocidad viento (km/h)</label>
                <input type="number" step="0.1" placeholder="0" value={riesgoForm.velocidad_viento}
                  onChange={e => setRiesgoForm(p => ({...p, velocidad_viento: e.target.value}))} style={styles.input} />
              </div>
              <div style={styles.fieldGroup}>
                <label style={styles.label}>Lluvia (mm)</label>
                <input type="number" step="0.1" placeholder="0" value={riesgoForm.lluvia}
                  onChange={e => setRiesgoForm(p => ({...p, lluvia: e.target.value}))} style={styles.input} />
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <button type="submit" disabled={loading} style={styles.submitBtn}>
                  {loading ? 'Analizando riesgo...' : 'Predecir riesgo agronomico'}
                </button>
              </div>
            </form>
          </div>

          {resultado && !resultado.error && resultado.tipo === 'riesgo' && (
            <div style={styles.resultCard} className="animate-fade">
              <div style={styles.resultTitle}>Resultado</div>
              <div style={styles.resultMain}>
                <div style={{ fontFamily: "'Syne', sans-serif", fontSize: '40px', fontWeight: 800, color: NIVEL_COLOR[resultado.data.nivel] || '#f0fdf4' }}>
                  {resultado.data.nivel.toUpperCase()}
                </div>
                <div style={{ fontSize: '14px', color: '#6b7280', marginTop: '4px' }}>
                  Riesgo de {resultado.data.tipo_riesgo} — {(resultado.data.probabilidad * 100).toFixed(1)}% probabilidad
                </div>
              </div>
              <div style={styles.resultGrid}>
                <div style={styles.resultItem}>
                  <div style={styles.resultLabel}>Probabilidad</div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: NIVEL_COLOR[resultado.data.nivel] }}>
                    {(resultado.data.probabilidad * 100).toFixed(1)}%
                  </div>
                </div>
                <div style={styles.resultItem}>
                  <div style={styles.resultLabel}>Confianza</div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: '#22c55e' }}>
                    {(resultado.data.confianza * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
              {resultado.data.acciones?.length > 0 && (
                <div style={{ marginTop: '14px' }}>
                  <div style={{ fontSize: '11px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '8px' }}>Acciones recomendadas</div>
                  {resultado.data.acciones.map((a, i) => (
                    <div key={i} style={{ fontSize: '12px', color: '#fbbf24', marginBottom: '6px', display: 'flex', gap: '6px', background: 'rgba(251,191,36,0.05)', padding: '6px 10px', borderRadius: '6px' }}>
                      <span>→</span><span>{a}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          {resultado?.error && <div style={styles.errorCard}>{resultado.error}</div>}
        </div>
      )}

      {/* ── Modelos ── */}
      {activeTab === 'modelos' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {modelos.map(m => (
            <div key={m.id} style={styles.modeloCard}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: '15px', fontWeight: 600, color: '#f0fdf4' }}>{m.nombre}</div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '3px' }}>{m.descripcion}</div>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ fontSize: '11px', color: '#4b5563' }}>v{m.version}</span>
                  <span style={{ background: 'rgba(34,197,94,0.1)', color: '#22c55e', padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: 600, border: '1px solid rgba(34,197,94,0.2)' }}>
                    {m.estado}
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '10px' }}>
                {m.features?.map(f => (
                  <span key={f} style={{ background: 'rgba(96,165,250,0.08)', color: '#60a5fa', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', border: '1px solid rgba(96,165,250,0.15)' }}>
                    {f}
                  </span>
                ))}
              </div>
              {m.metricas && (
                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                  {Object.entries(m.metricas).map(([k, v]) => (
                    <div key={k} style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '14px', fontWeight: 700, color: '#a78bfa' }}>{typeof v === 'number' && v < 1 ? (v * 100).toFixed(0) + '%' : v}</div>
                      <div style={{ fontSize: '10px', color: '#4b5563', textTransform: 'uppercase' }}>{k}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const styles = {
  wrapper: { padding: '32px', maxWidth: '1100px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' },
  title: { fontFamily: "'Syne', sans-serif", fontSize: '26px', fontWeight: 700, color: '#f0fdf4' },
  subtitle: { fontSize: '13px', color: '#6b7280', marginTop: '4px' },
  kpiGrid: { display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px', marginBottom: '20px' },
  kpiCard: { background: '#0d1510', border: '1px solid rgba(34,197,94,0.1)', borderRadius: '12px', padding: '16px', textAlign: 'center' },
  tabsBar: { display: 'flex', gap: '4px', marginBottom: '20px', background: '#0d1510', borderRadius: '10px', padding: '4px', border: '1px solid rgba(34,197,94,0.1)' },
  tabBtn: { flex: 1, padding: '9px', borderRadius: '7px', border: 'none', background: 'transparent', color: '#6b7280', fontSize: '12px', fontWeight: 500, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s' },
  tabBtnActive: { background: 'rgba(34,197,94,0.15)', color: '#22c55e' },
  layout: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' },
  formCard: { background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '16px', padding: '22px' },
  formTitle: { fontFamily: "'Syne', sans-serif", fontSize: '14px', fontWeight: 600, color: '#f0fdf4', marginBottom: '6px' },
  formDesc: { fontSize: '12px', color: '#6b7280', marginBottom: '18px', lineHeight: 1.6 },
  formGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' },
  fieldGroup: { display: 'flex', flexDirection: 'column', gap: '5px' },
  label: { fontSize: '11px', fontWeight: 500, color: '#86efac', letterSpacing: '0.4px' },
  input: { padding: '9px 12px', background: 'rgba(6,12,7,0.8)', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#f0fdf4', fontSize: '13px', fontFamily: "'DM Sans', sans-serif" },
  submitBtn: { width: '100%', padding: '11px', background: 'linear-gradient(135deg, #16a34a, #15803d)', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  resultCard: { background: '#0d1510', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '16px', padding: '22px' },
  resultTitle: { fontFamily: "'Syne', sans-serif", fontSize: '13px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '16px' },
  resultMain: { textAlign: 'center', marginBottom: '16px', padding: '16px', background: 'rgba(6,12,7,0.6)', borderRadius: '10px' },
  resultGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '14px' },
  resultItem: { background: 'rgba(6,12,7,0.6)', borderRadius: '8px', padding: '12px', textAlign: 'center' },
  resultLabel: { fontSize: '10px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '6px' },
  resultExplicacion: { fontSize: '12px', color: '#9ca3af', lineHeight: 1.6, background: 'rgba(6,12,7,0.4)', padding: '10px', borderRadius: '8px' },
  errorCard: { background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.2)', borderRadius: '12px', padding: '16px', color: '#f87171', fontSize: '13px' },
  modeloCard: { background: '#0d1510', border: '1px solid rgba(34,197,94,0.1)', borderRadius: '14px', padding: '18px 20px' },
}