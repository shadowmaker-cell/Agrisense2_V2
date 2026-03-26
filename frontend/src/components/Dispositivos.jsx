import { useState, useEffect } from 'react'
import { dispositivosAPI } from '../api/client'

const ESTADO_COLOR = { activo: '#22c55e', inactivo: '#6b7280', mantenimiento: '#fbbf24', desconectado: '#f87171' }

const CAT_STYLES = {
  suelo:     { color: '#a3e635', bg: 'rgba(163,230,53,0.12)',  border: 'rgba(163,230,53,0.3)'  },
  ambiental: { color: '#38bdf8', bg: 'rgba(56,189,248,0.12)', border: 'rgba(56,189,248,0.3)'  },
  agua:      { color: '#2dd4bf', bg: 'rgba(45,212,191,0.12)', border: 'rgba(45,212,191,0.3)'  },
  infra:     { color: '#c084fc', bg: 'rgba(192,132,252,0.12)',border: 'rgba(192,132,252,0.3)' },
}

const TIPO_OPCIONES = [
  { id: 1,  nombre: 'Sensor Humedad Suelo',      categoria: 'suelo'     },
  { id: 2,  nombre: 'Sensor pH Suelo',           categoria: 'suelo'     },
  { id: 3,  nombre: 'Sensor EC Suelo',           categoria: 'suelo'     },
  { id: 4,  nombre: 'Sensor Temperatura Suelo',  categoria: 'suelo'     },
  { id: 5,  nombre: 'Sensor Temperatura Aire',   categoria: 'ambiental' },
  { id: 6,  nombre: 'Sensor Humedad Aire',       categoria: 'ambiental' },
  { id: 7,  nombre: 'Sensor Luz',                categoria: 'ambiental' },
  { id: 8,  nombre: 'Sensor Viento',             categoria: 'ambiental' },
  { id: 9,  nombre: 'Sensor Lluvia',             categoria: 'ambiental' },
  { id: 10, nombre: 'Sensor pH Agua',            categoria: 'agua'      },
  { id: 11, nombre: 'Sensor Caudal',             categoria: 'agua'      },
  { id: 12, nombre: 'Valvula Riego',             categoria: 'agua'      },
  { id: 13, nombre: 'Bomba Agua',                categoria: 'agua'      },
  { id: 14, nombre: 'Microcontrolador',          categoria: 'infra'     },
  { id: 15, nombre: 'Modulo Ethernet',           categoria: 'infra'     },
  { id: 16, nombre: 'Sensor Bateria',            categoria: 'infra'     },
  { id: 17, nombre: 'Panel Solar',               categoria: 'infra'     },
]

export default function Dispositivos() {
  const [dispositivos, setDispositivos] = useState([])
  const [tipos, setTipos]               = useState([])
  const [filtro, setFiltro]             = useState('')
  const [categoriaFiltro, setCategoriaFiltro] = useState('todos')
  const [estadoFiltro, setEstadoFiltro]       = useState('todos')
  const [loading, setLoading]           = useState(true)
  const [selected, setSelected]         = useState(null)
  const [metricas, setMetricas]         = useState(null)
  const [showForm, setShowForm]         = useState(false)
  const [formMsg, setFormMsg]           = useState('')
  const [formLoading, setFormLoading]   = useState(false)
  const [form, setForm] = useState({
    tipo_dispositivo_id: 1,
    numero_serial: '',
    id_logico: '',
    version_firmware: '1.0.0',
    estado: 'activo',
  })

  const load = async () => {
    try {
      const [dispRes, tiposRes] = await Promise.all([
        dispositivosAPI.listar(0, 100),
        dispositivosAPI.listarTipos(),
      ])
      setDispositivos(dispRes.data)
      setTipos(tiposRes.data)
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleSelect = async (d) => {
    setSelected(d)
    setMetricas(null)
    try {
      const res = await dispositivosAPI.metricas(d.id)
      setMetricas(res.data)
    } catch(e) {}
  }

  const handleRegistrar = async (e) => {
    e.preventDefault()
    if (!form.numero_serial || !form.id_logico) {
      setFormMsg('Completa serial e ID logico')
      return
    }
    setFormLoading(true)
    setFormMsg('')
    try {
      await dispositivosAPI.registrar(form)
      setFormMsg('✅ Sensor registrado exitosamente')
      setForm({ tipo_dispositivo_id: 1, numero_serial: '', id_logico: '', version_firmware: '1.0.0', estado: 'activo' })
      await load()
      setTimeout(() => { setShowForm(false); setFormMsg('') }, 1500)
    } catch(e) {
      setFormMsg('❌ Error al registrar el sensor')
    } finally { setFormLoading(false) }
  }

  const getTipo    = (id) => tipos.find(t => t.id === id)
  const categorias = ['todos', ...new Set(tipos.map(t => t.categoria))]

  const filtered = dispositivos.filter(d => {
    const tipo      = getTipo(d.tipo_dispositivo_id)
    const matchCat  = categoriaFiltro === 'todos' || tipo?.categoria === categoriaFiltro
    const matchEst  = estadoFiltro === 'todos' || d.estado === estadoFiltro
    const matchText = !filtro || d.id_logico?.toLowerCase().includes(filtro.toLowerCase()) || d.numero_serial?.toLowerCase().includes(filtro.toLowerCase())
    return matchCat && matchEst && matchText
  })

  return (
    <div style={styles.wrapper} className="animate-fade">
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Dispositivos IoT</h1>
          <p style={styles.subtitle}>{dispositivos.length} sensores registrados · {dispositivos.filter(d=>d.estado==='activo').length} activos</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} style={{ ...styles.addBtn, background: showForm ? 'rgba(248,113,113,0.1)' : 'rgba(34,197,94,0.12)', color: showForm ? '#f87171' : '#22c55e', borderColor: showForm ? 'rgba(248,113,113,0.3)' : 'rgba(34,197,94,0.25)' }}>
          {showForm ? (
            <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Cancelar</>
          ) : (
            <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Registrar sensor</>
          )}
        </button>
      </div>

      {/* Registro form */}
      {showForm && (
        <div style={styles.formCard} className="animate-fade">
          <div style={styles.formTitle}>Registrar nuevo sensor</div>
          <form onSubmit={handleRegistrar} style={styles.formGrid}>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Tipo de sensor</label>
              <select value={form.tipo_dispositivo_id} onChange={e => setForm(p=>({...p, tipo_dispositivo_id: parseInt(e.target.value)}))} style={styles.input}>
                {TIPO_OPCIONES.map(t => <option key={t.id} value={t.id}>{t.nombre} ({t.categoria})</option>)}
              </select>
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>ID Logico *</label>
              <input placeholder="ej: SOIL_HUM_02" value={form.id_logico} onChange={e => setForm(p=>({...p, id_logico: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Numero Serial *</label>
              <input placeholder="ej: SN-20260001" value={form.numero_serial} onChange={e => setForm(p=>({...p, numero_serial: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Firmware</label>
              <input placeholder="1.0.0" value={form.version_firmware} onChange={e => setForm(p=>({...p, version_firmware: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Estado inicial</label>
              <select value={form.estado} onChange={e => setForm(p=>({...p, estado: e.target.value}))} style={styles.input}>
                <option value="activo">Activo</option>
                <option value="inactivo">Inactivo</option>
                <option value="mantenimiento">Mantenimiento</option>
              </select>
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button type="submit" disabled={formLoading} style={styles.submitBtn}>
                {formLoading ? 'Registrando...' : 'Registrar'}
              </button>
            </div>
          </form>
          {formMsg && <div style={{ marginTop: '10px', fontSize: '13px', color: formMsg.startsWith('✅') ? '#22c55e' : '#f87171' }}>{formMsg}</div>}
        </div>
      )}

      {/* Filters */}
      <div style={styles.filters}>
        <div style={styles.searchWrap}>
          <svg style={styles.searchIcon} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input placeholder="Buscar por ID logico o serial..." value={filtro} onChange={e => setFiltro(e.target.value)} style={styles.search} />
        </div>

        {/* Categoria filter */}
        <select value={categoriaFiltro} onChange={e => setCategoriaFiltro(e.target.value)} style={styles.select}>
          <option value="todos">Todas las categorias</option>
          {categorias.filter(c => c !== 'todos').map(cat => (
            <option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
          ))}
        </select>

        {/* Estado filter */}
        <select value={estadoFiltro} onChange={e => setEstadoFiltro(e.target.value)} style={styles.select}>
          <option value="todos">Todos los estados</option>
          <option value="activo">Activo</option>
          <option value="inactivo">Inactivo</option>
          <option value="mantenimiento">Mantenimiento</option>
          <option value="desconectado">Desconectado</option>
        </select>

        <div style={styles.countTag}>{filtered.length} resultados</div>
      </div>

      <div style={styles.layout}>
        <div style={styles.tableCard}>
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#4b5563' }}>Cargando sensores...</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID Logico</th><th>Tipo</th><th>Categoria</th>
                    <th>Serial</th><th>Estado</th><th>Firmware</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((d, i) => {
                    const tipo     = getTipo(d.tipo_dispositivo_id)
                    const estColor = ESTADO_COLOR[d.estado] || '#6b7280'
                    const catStyle = CAT_STYLES[tipo?.categoria] || CAT_STYLES.infra
                    return (
                      <tr key={d.id} onClick={() => handleSelect(d)} style={{
                        cursor: 'pointer',
                        background: selected?.id === d.id ? 'rgba(34,197,94,0.08)' : 'transparent',
                        animation: `fadeIn 0.3s ease ${i * 0.02}s both`,
                      }}>
                        <td><span style={{ fontFamily: 'monospace', color: '#4ade80', fontSize: '12px' }}>{d.id_logico}</span></td>
                        <td style={{ color: '#f0fdf4', fontSize: '12px' }}>{tipo?.nombre || '—'}</td>
                        <td>
                          <span style={{ ...styles.catBadge, color: catStyle.color, background: catStyle.bg, border: `1px solid ${catStyle.border}` }}>
                            {tipo?.categoria || '—'}
                          </span>
                        </td>
                        <td style={{ color: '#6b7280', fontSize: '11px', fontFamily: 'monospace' }}>{d.numero_serial}</td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: estColor }} />
                            <span style={{ color: estColor, fontSize: '12px', fontWeight: 500 }}>{d.estado}</span>
                          </div>
                        </td>
                        <td style={{ color: '#6b7280', fontSize: '11px' }}>{d.version_firmware || '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {selected && (
          <div style={styles.detailPanel} className="animate-slide">
            <div style={styles.detailHeader}>
              <div>
                <div style={styles.detailId}>{selected.id_logico}</div>
                <div style={styles.detailSerial}>{selected.numero_serial}</div>
              </div>
              <button onClick={() => setSelected(null)} style={styles.closeBtn}>✕</button>
            </div>
            <div style={styles.detailGrid}>
              {[
                { label: 'Estado',     value: selected.estado,           color: ESTADO_COLOR[selected.estado] },
                { label: 'Tipo ID',    value: `#${selected.tipo_dispositivo_id}` },
                { label: 'Firmware',   value: selected.version_firmware || 'N/A' },
                { label: 'Registrado', value: selected.registrado_en ? new Date(selected.registrado_en).toLocaleDateString('es-CO') : 'N/A' },
              ].map(item => (
                <div key={item.label} style={styles.detailItem}>
                  <div style={styles.detailLabel}>{item.label}</div>
                  <div style={{ ...styles.detailValue, color: item.color || '#f0fdf4' }}>{item.value}</div>
                </div>
              ))}
            </div>
            {metricas && (
              <div style={styles.metricasCard}>
                <div style={styles.metricasTitle}>Metricas permitidas</div>
                <div style={styles.metricasList}>
                  {metricas.metricas_permitidas?.map(m => (
                    <span key={m} style={styles.metricaTag}>{m}</span>
                  ))}
                </div>
              </div>
            )}
            {(() => {
              const tipo = getTipo(selected.tipo_dispositivo_id)
              if (!tipo) return null
              return (
                <div style={styles.tipo}>
                  <div style={styles.tipoNombre}>{tipo.nombre}</div>
                  {tipo.umbral_alerta && <div style={styles.umbral}>Alerta: {tipo.umbral_alerta}</div>}
                  {tipo.rango_minimo !== null && <div style={styles.rango}>Rango: {tipo.rango_minimo} - {tipo.rango_maximo} {tipo.unidad}</div>}
                </div>
              )
            })()}
          </div>
        )}
      </div>
    </div>
  )
}

const styles = {
  wrapper: { padding: '32px', maxWidth: '1200px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' },
  title: { fontFamily: "'Syne', sans-serif", fontSize: '26px', fontWeight: 700, color: '#f0fdf4' },
  subtitle: { fontSize: '13px', color: '#6b7280', marginTop: '4px' },
  addBtn: { display: 'flex', alignItems: 'center', gap: '6px', padding: '9px 16px', borderRadius: '10px', border: '1px solid', fontSize: '13px', fontWeight: 600, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.2s' },
  formCard: { background: '#0d1510', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '16px', padding: '20px 24px', marginBottom: '20px' },
  formTitle: { fontFamily: "'Syne', sans-serif", fontSize: '14px', fontWeight: 600, color: '#f0fdf4', marginBottom: '16px' },
  formGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' },
  fieldGroup: { display: 'flex', flexDirection: 'column', gap: '5px' },
  label: { fontSize: '11px', fontWeight: 500, color: '#86efac', letterSpacing: '0.4px' },
  input: { padding: '9px 12px', background: 'rgba(6,12,7,0.8)', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#f0fdf4', fontSize: '13px', fontFamily: "'DM Sans', sans-serif" },
  submitBtn: { width: '100%', padding: '10px', background: 'linear-gradient(135deg, #16a34a, #15803d)', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  filters: { display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap', alignItems: 'center' },
  searchWrap: { position: 'relative', flex: 1, minWidth: '200px' },
  searchIcon: { position: 'absolute', left: '11px', top: '50%', transform: 'translateY(-50%)', color: '#4ade80' },
  search: { width: '100%', padding: '9px 14px 9px 34px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#f0fdf4', fontSize: '13px', fontFamily: "'DM Sans', sans-serif" },
  select: { padding: '9px 12px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#9ca3af', fontSize: '13px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  countTag: { background: 'rgba(34,197,94,0.08)', color: '#4ade80', padding: '6px 12px', borderRadius: '20px', fontSize: '12px', border: '1px solid rgba(34,197,94,0.15)' },
  catBadge: { padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: 600 },
  layout: { display: 'flex', gap: '16px' },
  tableCard: { flex: 1, background: '#0d1510', border: '1px solid rgba(34,197,94,0.1)', borderRadius: '16px', overflow: 'hidden' },
  detailPanel: { width: '280px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '16px', padding: '20px', height: 'fit-content' },
  detailHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' },
  detailId: { fontFamily: 'monospace', color: '#4ade80', fontSize: '14px', fontWeight: 700 },
  detailSerial: { fontSize: '11px', color: '#6b7280', marginTop: '2px' },
  closeBtn: { background: 'none', border: 'none', color: '#4b5563', cursor: 'pointer', fontSize: '14px' },
  detailGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' },
  detailItem: { background: 'rgba(6,12,7,0.6)', borderRadius: '8px', padding: '10px 12px' },
  detailLabel: { fontSize: '10px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '4px' },
  detailValue: { fontSize: '13px', fontWeight: 600 },
  metricasCard: { background: 'rgba(6,12,7,0.6)', borderRadius: '8px', padding: '12px', marginBottom: '12px' },
  metricasTitle: { fontSize: '11px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '8px' },
  metricasList: { display: 'flex', flexWrap: 'wrap', gap: '5px' },
  metricaTag: { background: 'rgba(34,197,94,0.1)', color: '#4ade80', padding: '2px 8px', borderRadius: '4px', fontSize: '11px' },
  tipo: { background: 'rgba(34,197,94,0.05)', border: '1px solid rgba(34,197,94,0.1)', borderRadius: '8px', padding: '12px' },
  tipoNombre: { fontSize: '13px', fontWeight: 600, color: '#f0fdf4', marginBottom: '6px' },
  umbral: { fontSize: '11px', color: '#fbbf24', marginBottom: '4px' },
  rango: { fontSize: '11px', color: '#6b7280' },
}