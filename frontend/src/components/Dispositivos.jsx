import { useState, useEffect } from 'react'
import { dispositivosAPI } from '../api/client'

const ESTADO_COLOR = { activo: '#22c55e', inactivo: '#6b7280', mantenimiento: '#fbbf24', desconectado: '#f87171' }

const CAT_STYLES = {
  suelo:     { color: '#a3e635', bg: 'rgba(163,230,53,0.12)',  border: 'rgba(163,230,53,0.3)'  },
  ambiental: { color: '#38bdf8', bg: 'rgba(56,189,248,0.12)', border: 'rgba(56,189,248,0.3)'  },
  agua:      { color: '#2dd4bf', bg: 'rgba(45,212,191,0.12)', border: 'rgba(45,212,191,0.3)'  },
  infra:     { color: '#c084fc', bg: 'rgba(192,132,252,0.12)',border: 'rgba(192,132,252,0.3)' },
}

const ID_PREFIJOS = {
  1:  'SOIL_HUM',  2:  'SOIL_PH',   3:  'SOIL_EC',   4:  'SOIL_TEMP',
  5:  'AIR_TEMP',  6:  'AIR_HUM',   7:  'LUX',        8:  'WIND',
  9:  'RAIN',      10: 'WAT_PH',    11: 'WAT_FLOW',   12: 'VALVE',
  13: 'PUMP',      14: 'MCU',       15: 'ETH',         16: 'BATT',
  17: 'SOLAR',
}

const TIPO_SERIAL_ABBREV = {
  1:  'HUM-CAP', 2:  'PHS-450', 3:  'ECS-100', 4:  'TMP-S10',
  5:  'TMP-A20', 6:  'HUM-AIR', 7:  'LUX-300', 8:  'WND-200',
  9:  'RAN-100', 10: 'PHS-WAT', 11: 'FLW-100', 12: 'VLV-100',
  13: 'PMP-100', 14: 'MCU-ESP', 15: 'ETH-W5K', 16: 'BAT-LPO',
  17: 'SOL-PNL',
}

const TIPO_OPCIONES = [
  { id:1,  nombre:'Sensor Humedad Suelo',     categoria:'suelo'     },
  { id:2,  nombre:'Sensor pH Suelo',          categoria:'suelo'     },
  { id:3,  nombre:'Sensor EC Suelo',          categoria:'suelo'     },
  { id:4,  nombre:'Sensor Temperatura Suelo', categoria:'suelo'     },
  { id:5,  nombre:'Sensor Temperatura Aire',  categoria:'ambiental' },
  { id:6,  nombre:'Sensor Humedad Aire',      categoria:'ambiental' },
  { id:7,  nombre:'Sensor Luz',               categoria:'ambiental' },
  { id:8,  nombre:'Sensor Viento',            categoria:'ambiental' },
  { id:9,  nombre:'Sensor Lluvia',            categoria:'ambiental' },
  { id:10, nombre:'Sensor pH Agua',           categoria:'agua'      },
  { id:11, nombre:'Sensor Caudal',            categoria:'agua'      },
  { id:12, nombre:'Valvula Riego',            categoria:'agua'      },
  { id:13, nombre:'Bomba Agua',               categoria:'agua'      },
  { id:14, nombre:'Microcontrolador',         categoria:'infra'     },
  { id:15, nombre:'Modulo Ethernet',          categoria:'infra'     },
  { id:16, nombre:'Sensor Bateria',           categoria:'infra'     },
  { id:17, nombre:'Panel Solar',              categoria:'infra'     },
]

function generarIdLogico(tipoId, dispositivos) {
  const prefijo = ID_PREFIJOS[tipoId]
  if (!prefijo) return ''
  const existentes = dispositivos
    .filter(d => d.id_logico?.startsWith(prefijo + '_') || d.id_logico === prefijo)
    .map(d => {
      const match = d.id_logico.match(/(\d+)$/)
      return match ? parseInt(match[1]) : 0
    })
  const siguiente = existentes.length > 0 ? Math.max(...existentes) + 1 : 1
  return `${prefijo}_${String(siguiente).padStart(2, '0')}`
}

function generarSerial(tipoId, dispositivos) {
  const abbrev = TIPO_SERIAL_ABBREV[tipoId] || 'SEN-GEN'
  const existentes = dispositivos
    .filter(d => d.numero_serial?.startsWith(`SN-${abbrev}-`))
    .map(d => {
      const match = d.numero_serial.match(/(\d{3})$/)
      return match ? parseInt(match[1]) : 0
    })
  const siguiente = existentes.length > 0 ? Math.max(...existentes) + 1 : 1
  return `SN-${abbrev}-${String(siguiente).padStart(3, '0')}`
}

const REGEX_ID_LOGICO = /^[A-Z][A-Z0-9_]{2,19}(_\d{2,3})?$/
const REGEX_SERIAL    = /^SN-[A-Z0-9]{2,5}-[A-Z0-9]{2,5}-\d{3}$/

function validarCampos(form) {
  const errores = {}
  if (!REGEX_ID_LOGICO.test(form.id_logico)) {
    errores.id_logico = 'Formato invalido. Ej: SOIL_HUM_02 — solo mayusculas, numeros y guion bajo'
  }
  if (!REGEX_SERIAL.test(form.numero_serial)) {
    errores.numero_serial = 'Formato invalido. Debe ser SN-ABC-XYZ-001 ej: SN-HUM-CAP-002'
  }
  return errores
}

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
  const [activeTab, setActiveTab]       = useState('lista')
  const [formMsg, setFormMsg]           = useState('')
  const [formLoading, setFormLoading]   = useState(false)
  const [formErrores, setFormErrores]   = useState({})
  const [editEstado, setEditEstado]     = useState('')
  const [editMsg, setEditMsg]           = useState('')
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

  useEffect(() => {
    if (showForm && dispositivos.length >= 0) {
      setForm(prev => ({
        ...prev,
        id_logico:     generarIdLogico(prev.tipo_dispositivo_id, dispositivos),
        numero_serial: generarSerial(prev.tipo_dispositivo_id, dispositivos),
      }))
      setFormErrores({})
      setFormMsg('')
    }
  }, [showForm])

  const handleTipoChange = (tipoId) => {
    const id          = parseInt(tipoId)
    const nuevoId     = generarIdLogico(id, dispositivos)
    const nuevoSerial = generarSerial(id, dispositivos)
    setForm(prev => ({ ...prev, tipo_dispositivo_id: id, id_logico: nuevoId, numero_serial: nuevoSerial }))
    setFormErrores(prev => ({ ...prev, id_logico: '', numero_serial: '' }))
  }

  const handleBlur = (campo) => {
    const errores = validarCampos(form)
    setFormErrores(prev => ({ ...prev, [campo]: errores[campo] || '' }))
  }

  const handleSelect = async (d) => {
    setSelected(d)
    setEditEstado(d.estado)
    setEditMsg('')
    setMetricas(null)
    try {
      const res = await dispositivosAPI.metricas(d.id)
      setMetricas(res.data)
    } catch(e) {}
  }

  const handleActualizar = async () => {
    if (!selected) return
    setEditMsg('')
    try {
      await dispositivosAPI.actualizar(selected.id, { estado: editEstado })
      setEditMsg('✅ Estado actualizado')
      await load()
      setSelected(prev => ({ ...prev, estado: editEstado }))
    } catch(e) { setEditMsg('❌ Error al actualizar') }
  }

  const handleRegistrar = async (e) => {
    e.preventDefault()
    const errores = validarCampos(form)
    if (Object.keys(errores).length > 0) {
      setFormErrores(errores)
      setFormMsg('Corrige los errores antes de continuar')
      return
    }
    setFormLoading(true); setFormMsg('')
    try {
      await dispositivosAPI.registrar(form)
      setFormMsg('✅ Sensor registrado exitosamente')
      await load()
      setTimeout(() => { setShowForm(false); setFormMsg('') }, 1500)
    } catch(e) {
      const detail = e?.response?.data?.detail
      setFormMsg(`❌ ${detail || 'Error al registrar el sensor'}`)
    } finally { setFormLoading(false) }
  }

  const getTipo    = (id) => tipos.find(t => t.id === id)
  const categorias = ['todos', ...new Set(tipos.map(t => t.categoria))]

  const filtered = dispositivos.filter(d => {
    const tipo      = getTipo(d.tipo_dispositivo_id)
    const matchCat  = categoriaFiltro === 'todos' || tipo?.categoria === categoriaFiltro
    const matchEst  = estadoFiltro === 'todos' || d.estado === estadoFiltro
    const matchText = !filtro ||
      d.id_logico?.toLowerCase().includes(filtro.toLowerCase()) ||
      d.numero_serial?.toLowerCase().includes(filtro.toLowerCase())
    return matchCat && matchEst && matchText
  })

  const activos       = dispositivos.filter(d => d.estado === 'activo').length
  const inactivos     = dispositivos.filter(d => d.estado === 'inactivo').length
  const mantenimiento = dispositivos.filter(d => d.estado === 'mantenimiento').length

  return (
    <div style={styles.wrapper} className="animate-fade">
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Dispositivos IoT</h1>
          <p style={styles.subtitle}>{dispositivos.length} sensores · {activos} activos · {inactivos} inactivos · {mantenimiento} en mantenimiento</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} style={{
          ...styles.addBtn,
          background:  showForm ? 'rgba(248,113,113,0.1)' : 'rgba(34,197,94,0.12)',
          color:       showForm ? '#f87171' : '#22c55e',
          borderColor: showForm ? 'rgba(248,113,113,0.3)' : 'rgba(34,197,94,0.25)',
        }}>
          {showForm ? (
            <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>Cancelar</>
          ) : (
            <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>Registrar sensor</>
          )}
        </button>
      </div>

      {/* Formulario de registro */}
      {showForm && (
        <div style={styles.formCard} className="animate-fade">
          <div style={styles.formTitle}>Registrar nuevo sensor</div>
          <p style={styles.formDesc}>
            El ID logico y serial se generan automaticamente segun el tipo seleccionado.
            Puedes editarlos manualmente respetando el formato indicado.
          </p>
          <form onSubmit={handleRegistrar} style={styles.formGrid}>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Tipo de sensor</label>
              <select
                value={form.tipo_dispositivo_id}
                onChange={e => handleTipoChange(e.target.value)}
                style={styles.input}
              >
                {TIPO_OPCIONES.map(t => (
                  <option key={t.id} value={t.id}>{t.nombre} ({t.categoria})</option>
                ))}
              </select>
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>
                ID Logico *
                <span style={styles.formatHint}> formato: PREFIJO_NN</span>
              </label>
              <input
                placeholder="ej: SOIL_HUM_02"
                value={form.id_logico}
                onChange={e => {
                  setForm(p => ({ ...p, id_logico: e.target.value.toUpperCase() }))
                  setFormErrores(p => ({ ...p, id_logico: '' }))
                }}
                onBlur={() => handleBlur('id_logico')}
                style={{ ...styles.input, borderColor: formErrores.id_logico ? '#f87171' : 'rgba(34,197,94,0.15)' }}
              />
              {formErrores.id_logico && <div style={styles.errorMsg}>{formErrores.id_logico}</div>}
              <div style={styles.ejemplos}>Ej: SOIL_HUM_02 · AIR_TEMP_03 · LUX_02 · BATT_02</div>
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>
                Numero Serial *
                <span style={styles.formatHint}> formato: SN-ABC-XYZ-001</span>
              </label>
              <input
                placeholder="ej: SN-HUM-CAP-002"
                value={form.numero_serial}
                onChange={e => {
                  setForm(p => ({ ...p, numero_serial: e.target.value.toUpperCase() }))
                  setFormErrores(p => ({ ...p, numero_serial: '' }))
                }}
                onBlur={() => handleBlur('numero_serial')}
                style={{ ...styles.input, borderColor: formErrores.numero_serial ? '#f87171' : 'rgba(34,197,94,0.15)' }}
              />
              {formErrores.numero_serial && <div style={styles.errorMsg}>{formErrores.numero_serial}</div>}
              <div style={styles.ejemplos}>Ej: SN-HUM-CAP-002 · SN-TMP-A20-003 · SN-BAT-LPO-002</div>
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Firmware</label>
              <input
                placeholder="1.0.0"
                value={form.version_firmware}
                onChange={e => setForm(p => ({ ...p, version_firmware: e.target.value }))}
                style={styles.input}
              />
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Estado inicial</label>
              <select
                value={form.estado}
                onChange={e => setForm(p => ({ ...p, estado: e.target.value }))}
                style={styles.input}
              >
                <option value="activo">Activo</option>
                <option value="inactivo">Inactivo</option>
                <option value="mantenimiento">Mantenimiento</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button type="submit" disabled={formLoading} style={styles.submitBtn}>
                {formLoading ? 'Registrando...' : 'Registrar sensor'}
              </button>
            </div>
          </form>
          {formMsg && (
            <div style={{ marginTop: '12px', fontSize: '13px', color: formMsg.startsWith('✅') ? '#22c55e' : '#f87171' }}>
              {formMsg}
            </div>
          )}
        </div>
      )}

      {/* Filtros */}
      <div style={styles.filters}>
        <div style={styles.searchWrap}>
          <svg style={styles.searchIcon} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            placeholder="Buscar por ID logico o serial..."
            value={filtro}
            onChange={e => setFiltro(e.target.value)}
            style={styles.search}
          />
        </div>
        <select value={categoriaFiltro} onChange={e => setCategoriaFiltro(e.target.value)} style={styles.select}>
          <option value="todos">Todas las categorias</option>
          {categorias.filter(c => c !== 'todos').map(cat => (
            <option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
          ))}
        </select>
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
        {/* Tabla */}
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

        {/* Panel de detalle */}
        {selected && (
          <div style={styles.detailPanel} className="animate-slide">
            <div style={styles.detailHeader}>
              <div>
                <div style={styles.detailId}>{selected.id_logico}</div>
                <div style={styles.detailSerial}>{selected.numero_serial}</div>
              </div>
              <button onClick={() => setSelected(null)} style={styles.closeBtn}>✕</button>
            </div>

            <div style={styles.tabs}>
              {['info', 'editar'].map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)} style={{
                  ...styles.tab,
                  ...(activeTab === tab ? styles.tabActive : {})
                }}>
                  {tab === 'info' ? 'Informacion' : 'Editar estado'}
                </button>
              ))}
            </div>

            {activeTab === 'info' && (
              <>
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
              </>
            )}

            {activeTab === 'editar' && (
              <div style={styles.editPanel}>
                <div style={styles.editTitle}>Actualizar estado del sensor</div>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Nuevo estado</label>
                  <select value={editEstado} onChange={e => setEditEstado(e.target.value)} style={styles.input}>
                    <option value="activo">Activo</option>
                    <option value="inactivo">Inactivo</option>
                    <option value="mantenimiento">Mantenimiento</option>
                    <option value="desconectado">Desconectado</option>
                  </select>
                </div>
                <button onClick={handleActualizar} style={styles.submitBtn}>Actualizar</button>
                {editMsg && (
                  <div style={{ marginTop: '10px', fontSize: '13px', color: editMsg.startsWith('✅') ? '#22c55e' : '#f87171' }}>
                    {editMsg}
                  </div>
                )}
              </div>
            )}
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
  formCard: { background: '#0d1510', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '16px', padding: '22px 24px', marginBottom: '20px' },
  formTitle: { fontFamily: "'Syne', sans-serif", fontSize: '14px', fontWeight: 600, color: '#f0fdf4', marginBottom: '6px' },
  formDesc: { fontSize: '12px', color: '#6b7280', marginBottom: '18px', lineHeight: 1.6 },
  formGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' },
  fieldGroup: { display: 'flex', flexDirection: 'column', gap: '5px' },
  label: { fontSize: '11px', fontWeight: 500, color: '#86efac', letterSpacing: '0.4px' },
  formatHint: { color: '#4b5563', fontWeight: 400, fontSize: '10px' },
  input: { padding: '9px 12px', background: 'rgba(6,12,7,0.8)', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#f0fdf4', fontSize: '13px', fontFamily: "'DM Sans', sans-serif", transition: 'border-color 0.2s' },
  errorMsg: { fontSize: '11px', color: '#f87171', marginTop: '3px' },
  ejemplos: { fontSize: '10px', color: '#4b5563', marginTop: '3px' },
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
  detailPanel: { width: '290px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '16px', padding: '20px', height: 'fit-content' },
  detailHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' },
  detailId: { fontFamily: 'monospace', color: '#4ade80', fontSize: '14px', fontWeight: 700 },
  detailSerial: { fontSize: '11px', color: '#6b7280', marginTop: '2px' },
  closeBtn: { background: 'none', border: 'none', color: '#4b5563', cursor: 'pointer', fontSize: '14px' },
  tabs: { display: 'flex', gap: '4px', marginBottom: '14px', background: 'rgba(6,12,7,0.6)', borderRadius: '8px', padding: '4px' },
  tab: { flex: 1, padding: '7px', borderRadius: '6px', border: 'none', background: 'transparent', color: '#6b7280', fontSize: '12px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s' },
  tabActive: { background: 'rgba(34,197,94,0.15)', color: '#22c55e' },
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
  editPanel: { display: 'flex', flexDirection: 'column', gap: '12px' },
  editTitle: { fontSize: '13px', color: '#9ca3af' },
}