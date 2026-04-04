import { useState, useEffect } from 'react'
import { dispositivosAPI, parcelasAPI } from '../api/client'

const ESTADO_COLOR = { activo: '#22c55e', inactivo: '#6b7280', mantenimiento: '#fbbf24', desconectado: '#f87171' }

const CAT_STYLES = {
  suelo:     { color: '#a3e635', bg: 'rgba(163,230,53,0.12)',  border: 'rgba(163,230,53,0.3)'  },
  ambiental: { color: '#38bdf8', bg: 'rgba(56,189,248,0.12)', border: 'rgba(56,189,248,0.3)'  },
  agua:      { color: '#2dd4bf', bg: 'rgba(45,212,191,0.12)', border: 'rgba(45,212,191,0.3)'  },
  infra:     { color: '#c084fc', bg: 'rgba(192,132,252,0.12)',border: 'rgba(192,132,252,0.3)' },
}

const ID_PREFIJOS = {
  1:'SOIL_HUM', 2:'SOIL_PH',  3:'SOIL_EC',  4:'SOIL_TEMP',
  5:'AIR_TEMP', 6:'AIR_HUM',  7:'LUX',      8:'WIND',
  9:'RAIN',    10:'WAT_PH',  11:'WAT_FLOW', 12:'VALVE',
  13:'PUMP',   14:'MCU',     15:'ETH',      16:'BATT',
  17:'SOLAR',
}

const TIPO_SERIAL_ABBREV = {
  1:'HUM-CAP', 2:'PHS-450', 3:'ECS-100', 4:'TMP-S10',
  5:'TMP-A20', 6:'HUM-AIR', 7:'LUX-300', 8:'WND-200',
  9:'RAN-100',10:'PHS-WAT',11:'FLW-100',12:'VLV-100',
  13:'PMP-100',14:'MCU-ESP',15:'ETH-W5K',16:'BAT-LPO',
  17:'SOL-PNL',
}

const TIPO_OPCIONES = [
  {id:1, nombre:'Sensor Humedad Suelo',     categoria:'suelo'    },
  {id:2, nombre:'Sensor pH Suelo',          categoria:'suelo'    },
  {id:3, nombre:'Sensor EC Suelo',          categoria:'suelo'    },
  {id:4, nombre:'Sensor Temperatura Suelo', categoria:'suelo'    },
  {id:5, nombre:'Sensor Temperatura Aire',  categoria:'ambiental'},
  {id:6, nombre:'Sensor Humedad Aire',      categoria:'ambiental'},
  {id:7, nombre:'Sensor Luz',               categoria:'ambiental'},
  {id:8, nombre:'Sensor Viento',            categoria:'ambiental'},
  {id:9, nombre:'Sensor Lluvia',            categoria:'ambiental'},
  {id:10,nombre:'Sensor pH Agua',           categoria:'agua'     },
  {id:11,nombre:'Sensor Caudal',            categoria:'agua'     },
  {id:12,nombre:'Valvula Riego',            categoria:'agua'     },
  {id:13,nombre:'Bomba Agua',               categoria:'agua'     },
  {id:14,nombre:'Microcontrolador',         categoria:'infra'    },
  {id:15,nombre:'Modulo Ethernet',          categoria:'infra'    },
  {id:16,nombre:'Sensor Bateria',           categoria:'infra'    },
  {id:17,nombre:'Panel Solar',              categoria:'infra'    },
]

function generarIdLogico(tipoId, dispositivos) {
  const prefijo = ID_PREFIJOS[tipoId]
  if (!prefijo) return ''
  const existentes = dispositivos
    .filter(d => d.id_logico?.startsWith(prefijo + '_'))
    .map(d => { const m = d.id_logico.match(/(\d+)$/); return m ? parseInt(m[1]) : 0 })
  const siguiente = existentes.length > 0 ? Math.max(...existentes) + 1 : 1
  return `${prefijo}_${String(siguiente).padStart(2,'0')}`
}

function generarSerial(tipoId, dispositivos) {
  const abbrev = TIPO_SERIAL_ABBREV[tipoId] || 'SEN-GEN'
  const existentes = dispositivos
    .filter(d => d.numero_serial?.startsWith(`SN-${abbrev}-`))
    .map(d => { const m = d.numero_serial.match(/(\d{3})$/); return m ? parseInt(m[1]) : 0 })
  const siguiente = existentes.length > 0 ? Math.max(...existentes) + 1 : 1
  return `SN-${abbrev}-${String(siguiente).padStart(3,'0')}`
}

const REGEX_ID_LOGICO = /^[A-Z][A-Z0-9_]{2,19}(_\d{2,3})?$/
const REGEX_SERIAL    = /^SN-[A-Z0-9]{2,5}-[A-Z0-9]{2,5}-\d{3}$/

function validarCampos(form) {
  const errores = {}
  if (!REGEX_ID_LOGICO.test(form.id_logico))
    errores.id_logico = 'Formato invalido. Ej: SOIL_HUM_02'
  if (!REGEX_SERIAL.test(form.numero_serial))
    errores.numero_serial = 'Formato invalido. Debe ser SN-ABC-XYZ-001'
  return errores
}

export default function Dispositivos() {
  const [dispositivos, setDispositivos] = useState([])
  const [tipos, setTipos]               = useState([])
  const [parcelas, setParcelas]         = useState([])
  const [filtro, setFiltro]             = useState('')
  const [categoriaFiltro, setCategoriaFiltro] = useState('todos')
  const [estadoFiltro, setEstadoFiltro]       = useState('todos')
  const [loading, setLoading]           = useState(true)
  const [selected, setSelected]         = useState(null)
  const [metricas, setMetricas]         = useState(null)
  const [hojaVida, setHojaVida]         = useState(null)
  const [showForm, setShowForm]         = useState(false)
  const [activeTab, setActiveTab]       = useState('info')
  const [formMsg, setFormMsg]           = useState('')
  const [formLoading, setFormLoading]   = useState(false)
  const [formErrores, setFormErrores]   = useState({})
  const [editMsg, setEditMsg]           = useState('')

  const [form, setForm] = useState({
    tipo_dispositivo_id: 1,
    numero_serial: '', id_logico: '',
    version_firmware: '1.0.0', estado: 'activo',
    parcela_id: '', parcela_nombre: '', posicion_campo: '',
    limite_minimo: '', limite_maximo: '',
  })

  const [editForm, setEditForm] = useState({
    estado: '', limite_minimo: '', limite_maximo: '',
    parcela_id: '', parcela_nombre: '', posicion_campo: '',
    intervalo_muestreo: '', umbral_bateria: '',
  })

  const load = async () => {
    try {
      const [dispRes, tiposRes, parcelasRes] = await Promise.all([
        dispositivosAPI.listar(0, 100),
        dispositivosAPI.listarTipos(),
        parcelasAPI.listar(),
      ])
      setDispositivos(dispRes.data)
      setTipos(tiposRes.data)
      setParcelas(parcelasRes.data)
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    if (showForm) {
      setForm(prev => ({
        ...prev,
        id_logico:     generarIdLogico(prev.tipo_dispositivo_id, dispositivos),
        numero_serial: generarSerial(prev.tipo_dispositivo_id, dispositivos),
      }))
      setFormErrores({}); setFormMsg('')
    }
  }, [showForm])

  const handleTipoChange = (tipoId) => {
    const id = parseInt(tipoId)
    setForm(prev => ({
      ...prev,
      tipo_dispositivo_id: id,
      id_logico:     generarIdLogico(id, dispositivos),
      numero_serial: generarSerial(id, dispositivos),
    }))
    setFormErrores(prev => ({...prev, id_logico: '', numero_serial: ''}))
  }

  const handleParcela = (parcela_id, formSetter) => {
    const parcela = parcelas.find(p => p.id === parseInt(parcela_id))
    formSetter(prev => ({
      ...prev,
      parcela_id:     parcela_id,
      parcela_nombre: parcela ? parcela.nombre : '',
    }))
  }

  const handleSelect = async (d) => {
    setSelected(d)
    setEditMsg('')
    setHojaVida(null)
    setMetricas(null)
    setActiveTab('info')
    setEditForm({
      estado:             d.estado,
      limite_minimo:      d.configuracion?.limite_minimo ?? '',
      limite_maximo:      d.configuracion?.limite_maximo ?? '',
      parcela_id:         d.configuracion?.parcela_id ?? '',
      parcela_nombre:     d.configuracion?.parcela_nombre ?? '',
      posicion_campo:     d.configuracion?.posicion_campo ?? '',
      intervalo_muestreo: d.configuracion?.intervalo_muestreo ?? '',
      umbral_bateria:     d.configuracion?.umbral_bateria ?? '',
    })
    try {
      const res = await dispositivosAPI.metricas(d.id)
      setMetricas(res.data)
    } catch(e) {}
  }

  const handleCargarHojaVida = async () => {
    if (!selected) return
    try {
      const res = await dispositivosAPI.hojaVida(selected.id)
      setHojaVida(res.data)
    } catch(e) { console.error(e) }
  }

  const handleActualizar = async () => {
    if (!selected) return
    setEditMsg('')
    const payload = {}
    if (editForm.estado)             payload.estado = editForm.estado
    if (editForm.limite_minimo !== '') payload.limite_minimo = parseFloat(editForm.limite_minimo)
    if (editForm.limite_maximo !== '') payload.limite_maximo = parseFloat(editForm.limite_maximo)
    if (editForm.parcela_id !== '')   payload.parcela_id = parseInt(editForm.parcela_id)
    if (editForm.parcela_nombre)      payload.parcela_nombre = editForm.parcela_nombre
    if (editForm.posicion_campo)      payload.posicion_campo = editForm.posicion_campo
    if (editForm.intervalo_muestreo !== '') payload.intervalo_muestreo = parseInt(editForm.intervalo_muestreo)
    if (editForm.umbral_bateria !== '') payload.umbral_bateria = parseInt(editForm.umbral_bateria)
    try {
      await dispositivosAPI.actualizar(selected.id, payload)
      setEditMsg('Configuracion actualizada correctamente')
      await load()
      const updated = dispositivos.find(d => d.id === selected.id)
      if (updated) setSelected({...updated, ...payload})
    } catch(e) { setEditMsg('Error al actualizar') }
  }

  const handleRegistrar = async (e) => {
    e.preventDefault()
    const errores = validarCampos(form)
    if (Object.keys(errores).length > 0) { setFormErrores(errores); setFormMsg('Corrige los errores'); return }
    setFormLoading(true); setFormMsg('')
    try {
      const payload = {
        tipo_dispositivo_id: form.tipo_dispositivo_id,
        id_logico:           form.id_logico,
        numero_serial:       form.numero_serial,
        version_firmware:    form.version_firmware,
        estado:              form.estado,
      }
      if (form.parcela_id)     payload.parcela_id     = parseInt(form.parcela_id)
      if (form.parcela_nombre) payload.parcela_nombre = form.parcela_nombre
      if (form.posicion_campo) payload.posicion_campo = form.posicion_campo
      if (form.limite_minimo !== '') payload.limite_minimo = parseFloat(form.limite_minimo)
      if (form.limite_maximo !== '') payload.limite_maximo = parseFloat(form.limite_maximo)

      await dispositivosAPI.registrar(payload)
      setFormMsg('Sensor registrado exitosamente')
      await load()
      setTimeout(() => { setShowForm(false); setFormMsg('') }, 1500)
    } catch(e) {
      const detail = e?.response?.data?.detail
      setFormMsg(detail || 'Error al registrar el sensor')
    } finally { setFormLoading(false) }
  }

  const getTipo    = (id) => tipos.find(t => t.id === id)
  const categorias = ['todos', ...new Set(tipos.map(t => t.categoria))]

  const filtered = dispositivos.filter(d => {
    const tipo     = getTipo(d.tipo_dispositivo_id)
    const matchCat = categoriaFiltro === 'todos' || tipo?.categoria === categoriaFiltro
    const matchEst = estadoFiltro    === 'todos' || d.estado        === estadoFiltro
    const matchTxt = !filtro ||
      d.id_logico?.toLowerCase().includes(filtro.toLowerCase()) ||
      d.numero_serial?.toLowerCase().includes(filtro.toLowerCase())
    return matchCat && matchEst && matchTxt
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
          {showForm ? 'Cancelar' : '+ Registrar sensor'}
        </button>
      </div>

      {/* Formulario registro */}
      {showForm && (
        <div style={styles.formCard} className="animate-fade">
          <div style={styles.formTitle}>Registrar nuevo sensor</div>
          <p style={styles.formDesc}>ID logico y serial se generan automaticamente. Puedes asignar una parcela y configurar limites desde el inicio.</p>
          <form onSubmit={handleRegistrar} style={styles.formGrid}>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Tipo de sensor</label>
              <select value={form.tipo_dispositivo_id}
                onChange={e => handleTipoChange(e.target.value)} style={styles.input}>
                {TIPO_OPCIONES.map(t => <option key={t.id} value={t.id}>{t.nombre} ({t.categoria})</option>)}
              </select>
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>ID Logico * <span style={styles.hint}>formato: PREFIJO_NN</span></label>
              <input placeholder="ej: SOIL_HUM_02" value={form.id_logico}
                onChange={e => { setForm(p=>({...p,id_logico:e.target.value.toUpperCase()})); setFormErrores(p=>({...p,id_logico:''})) }}
                style={{...styles.input, borderColor: formErrores.id_logico ? '#f87171' : 'rgba(34,197,94,0.15)'}} />
              {formErrores.id_logico && <div style={styles.errorMsg}>{formErrores.id_logico}</div>}
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Serial * <span style={styles.hint}>SN-ABC-XYZ-001</span></label>
              <input placeholder="ej: SN-HUM-CAP-002" value={form.numero_serial}
                onChange={e => { setForm(p=>({...p,numero_serial:e.target.value.toUpperCase()})); setFormErrores(p=>({...p,numero_serial:''})) }}
                style={{...styles.input, borderColor: formErrores.numero_serial ? '#f87171' : 'rgba(34,197,94,0.15)'}} />
              {formErrores.numero_serial && <div style={styles.errorMsg}>{formErrores.numero_serial}</div>}
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Parcela asignada</label>
              <select value={form.parcela_id}
                onChange={e => handleParcela(e.target.value, setForm)} style={styles.input}>
                <option value="">Sin asignar</option>
                {parcelas.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
              </select>
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Posicion en campo</label>
              <input placeholder="ej: Sector norte, fila 3" value={form.posicion_campo}
                onChange={e => setForm(p=>({...p,posicion_campo:e.target.value}))} style={styles.input} />
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Firmware</label>
              <input placeholder="1.0.0" value={form.version_firmware}
                onChange={e => setForm(p=>({...p,version_firmware:e.target.value}))} style={styles.input} />
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Limite minimo personalizado</label>
              <input type="number" step="0.1" placeholder="Usa rango del tipo por defecto"
                value={form.limite_minimo}
                onChange={e => setForm(p=>({...p,limite_minimo:e.target.value}))} style={styles.input} />
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Limite maximo personalizado</label>
              <input type="number" step="0.1" placeholder="Usa rango del tipo por defecto"
                value={form.limite_maximo}
                onChange={e => setForm(p=>({...p,limite_maximo:e.target.value}))} style={styles.input} />
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Estado inicial</label>
              <select value={form.estado}
                onChange={e => setForm(p=>({...p,estado:e.target.value}))} style={styles.input}>
                <option value="activo">Activo</option>
                <option value="inactivo">Inactivo</option>
                <option value="mantenimiento">Mantenimiento</option>
              </select>
            </div>

            <div style={{display:'flex',alignItems:'flex-end'}}>
              <button type="submit" disabled={formLoading} style={styles.submitBtn}>
                {formLoading ? 'Registrando...' : 'Registrar sensor'}
              </button>
            </div>
          </form>
          {formMsg && <div style={{marginTop:'12px',fontSize:'13px',color:formMsg.includes('Error')||formMsg.includes('Corrige')?'#f87171':'#22c55e'}}>{formMsg}</div>}
        </div>
      )}

      {/* Filtros */}
      <div style={styles.filters}>
        <div style={styles.searchWrap}>
          <svg style={styles.searchIcon} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input placeholder="Buscar por ID o serial..." value={filtro}
            onChange={e => setFiltro(e.target.value)} style={styles.search} />
        </div>
        <select value={categoriaFiltro} onChange={e => setCategoriaFiltro(e.target.value)} style={styles.select}>
          <option value="todos">Todas las categorias</option>
          {categorias.filter(c=>c!=='todos').map(cat => (
            <option key={cat} value={cat}>{cat.charAt(0).toUpperCase()+cat.slice(1)}</option>
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
            <div style={{padding:'40px',textAlign:'center',color:'#4b5563'}}>Cargando sensores...</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID Logico</th><th>Tipo</th><th>Parcela</th>
                    <th>Serial</th><th>Estado</th><th>Limites</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((d, i) => {
                    const tipo     = getTipo(d.tipo_dispositivo_id)
                    const estColor = ESTADO_COLOR[d.estado] || '#6b7280'
                    const catStyle = CAT_STYLES[tipo?.categoria] || CAT_STYLES.infra
                    const config   = d.configuracion
                    return (
                      <tr key={d.id} onClick={() => handleSelect(d)} style={{
                        cursor: 'pointer',
                        background: selected?.id === d.id ? 'rgba(34,197,94,0.08)' : 'transparent',
                      }}>
                        <td><span style={{fontFamily:'monospace',color:'#4ade80',fontSize:'12px'}}>{d.id_logico}</span></td>
                        <td>
                          <span style={{...styles.catBadge,color:catStyle.color,background:catStyle.bg,border:`1px solid ${catStyle.border}`}}>
                            {tipo?.categoria || '—'}
                          </span>
                        </td>
                        <td style={{fontSize:'11px',color:'#9ca3af'}}>
                          {config?.parcela_nombre || <span style={{color:'#374151'}}>Sin asignar</span>}
                        </td>
                        <td style={{color:'#6b7280',fontSize:'11px',fontFamily:'monospace'}}>{d.numero_serial}</td>
                        <td>
                          <div style={{display:'flex',alignItems:'center',gap:'6px'}}>
                            <div style={{width:'7px',height:'7px',borderRadius:'50%',background:estColor}}/>
                            <span style={{color:estColor,fontSize:'12px',fontWeight:500}}>{d.estado}</span>
                          </div>
                        </td>
                        <td style={{fontSize:'11px',color:'#6b7280'}}>
                          {config?.limite_minimo != null && config?.limite_maximo != null
                            ? `${config.limite_minimo} — ${config.limite_maximo}`
                            : <span style={{color:'#374151'}}>Por defecto</span>
                          }
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Panel detalle */}
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
              {['info','editar','hoja-vida'].map(tab => (
                <button key={tab} onClick={() => { setActiveTab(tab); if(tab==='hoja-vida') handleCargarHojaVida() }} style={{
                  ...styles.tab,
                  ...(activeTab===tab ? styles.tabActive : {})
                }}>
                  {tab==='info'?'Info':tab==='editar'?'Editar':'Hoja de Vida'}
                </button>
              ))}
            </div>

            {/* Tab Info */}
            {activeTab === 'info' && (
              <>
                <div style={styles.detailGrid}>
                  {[
                    {label:'Estado',   value:selected.estado,  color:ESTADO_COLOR[selected.estado]},
                    {label:'Firmware', value:selected.version_firmware||'N/A'},
                    {label:'Parcela',  value:selected.configuracion?.parcela_nombre||'Sin asignar', color:'#4ade80'},
                    {label:'Posicion', value:selected.configuracion?.posicion_campo||'—'},
                    {label:'Lim. Min', value:selected.configuracion?.limite_minimo!=null?selected.configuracion.limite_minimo:'Por defecto'},
                    {label:'Lim. Max', value:selected.configuracion?.limite_maximo!=null?selected.configuracion.limite_maximo:'Por defecto'},
                  ].map(item => (
                    <div key={item.label} style={styles.detailItem}>
                      <div style={styles.detailLabel}>{item.label}</div>
                      <div style={{...styles.detailValue,color:item.color||'#f0fdf4'}}>{item.value}</div>
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
              </>
            )}

            {/* Tab Editar */}
            {activeTab === 'editar' && (
              <div style={{display:'flex',flexDirection:'column',gap:'10px'}}>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Estado</label>
                  <select value={editForm.estado}
                    onChange={e => setEditForm(p=>({...p,estado:e.target.value}))} style={styles.input}>
                    <option value="activo">Activo</option>
                    <option value="inactivo">Inactivo</option>
                    <option value="mantenimiento">Mantenimiento</option>
                    <option value="desconectado">Desconectado</option>
                  </select>
                </div>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Parcela asignada</label>
                  <select value={editForm.parcela_id}
                    onChange={e => handleParcela(e.target.value, setEditForm)} style={styles.input}>
                    <option value="">Sin asignar</option>
                    {parcelas.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
                  </select>
                </div>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Posicion en campo</label>
                  <input placeholder="ej: Sector norte" value={editForm.posicion_campo}
                    onChange={e => setEditForm(p=>({...p,posicion_campo:e.target.value}))} style={styles.input} />
                </div>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Limite minimo</label>
                  <input type="number" step="0.1" placeholder="Por defecto del tipo"
                    value={editForm.limite_minimo}
                    onChange={e => setEditForm(p=>({...p,limite_minimo:e.target.value}))} style={styles.input} />
                </div>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Limite maximo</label>
                  <input type="number" step="0.1" placeholder="Por defecto del tipo"
                    value={editForm.limite_maximo}
                    onChange={e => setEditForm(p=>({...p,limite_maximo:e.target.value}))} style={styles.input} />
                </div>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Intervalo muestreo (seg)</label>
                  <input type="number" placeholder="300"
                    value={editForm.intervalo_muestreo}
                    onChange={e => setEditForm(p=>({...p,intervalo_muestreo:e.target.value}))} style={styles.input} />
                </div>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Umbral bateria (%)</label>
                  <input type="number" placeholder="20"
                    value={editForm.umbral_bateria}
                    onChange={e => setEditForm(p=>({...p,umbral_bateria:e.target.value}))} style={styles.input} />
                </div>
                <button onClick={handleActualizar} style={styles.submitBtn}>
                  Guardar cambios
                </button>
                {editMsg && (
                  <div style={{fontSize:'13px',color:editMsg.includes('Error')?'#f87171':'#22c55e'}}>
                    {editMsg}
                  </div>
                )}
              </div>
            )}

            {/* Tab Hoja de Vida */}
            {activeTab === 'hoja-vida' && (
              <div style={{display:'flex',flexDirection:'column',gap:'12px'}}>
                {!hojaVida ? (
                  <div style={{textAlign:'center',padding:'30px',color:'#4b5563',fontSize:'13px'}}>
                    Cargando hoja de vida...
                  </div>
                ) : (
                  <>
                    <div style={styles.hvSection}>
                      <div style={styles.hvTitle}>Resumen</div>
                      <div style={styles.detailGrid}>
                        {[
                          {label:'Tipo',        value:hojaVida.tipo},
                          {label:'Categoria',   value:hojaVida.categoria},
                          {label:'Registrado',  value:hojaVida.registrado_en ? new Date(hojaVida.registrado_en).toLocaleDateString('es-CO') : '—'},
                          {label:'Cambios estado', value:hojaVida.total_cambios_estado},
                          {label:'Despliegues', value:hojaVida.total_despliegues},
                          {label:'Ultima conexion', value:hojaVida.ultima_conexion ? new Date(hojaVida.ultima_conexion).toLocaleDateString('es-CO') : 'Nunca'},
                        ].map(item => (
                          <div key={item.label} style={styles.detailItem}>
                            <div style={styles.detailLabel}>{item.label}</div>
                            <div style={styles.detailValue}>{item.value}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {hojaVida.historial_estados?.length > 0 && (
                      <div style={styles.hvSection}>
                        <div style={styles.hvTitle}>Historial de estados ({hojaVida.historial_estados.length})</div>
                        <div style={{display:'flex',flexDirection:'column',gap:'6px',maxHeight:'160px',overflowY:'auto'}}>
                          {hojaVida.historial_estados.map((h, i) => (
                            <div key={i} style={styles.hvItem}>
                              <div style={{display:'flex',gap:'6px',alignItems:'center'}}>
                                <span style={{fontSize:'11px',color:'#6b7280'}}>{h.estado_anterior||'inicio'}</span>
                                <span style={{color:'#4ade80'}}>→</span>
                                <span style={{fontSize:'11px',fontWeight:600,color:ESTADO_COLOR[h.estado_nuevo]||'#f0fdf4'}}>{h.estado_nuevo}</span>
                              </div>
                              <div style={{fontSize:'10px',color:'#4b5563'}}>
                                {h.cambiado_en ? new Date(h.cambiado_en).toLocaleString('es-CO') : '—'}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {hojaVida.despliegues?.length > 0 && (
                      <div style={styles.hvSection}>
                        <div style={styles.hvTitle}>Despliegues ({hojaVida.despliegues.length})</div>
                        <div style={{display:'flex',flexDirection:'column',gap:'6px',maxHeight:'160px',overflowY:'auto'}}>
                          {hojaVida.despliegues.map((d, i) => (
                            <div key={i} style={styles.hvItem}>
                              <div style={{display:'flex',justifyContent:'space-between'}}>
                                <span style={{fontSize:'12px',fontWeight:600,color:'#f0fdf4'}}>Lote: {d.lote_id}</span>
                                <span style={{fontSize:'11px',fontWeight:600,color:d.estado==='activo'?'#22c55e':'#6b7280'}}>{d.estado}</span>
                              </div>
                              {d.posicion && <div style={{fontSize:'11px',color:'#9ca3af'}}>Pos: {d.posicion}</div>}
                              <div style={{fontSize:'10px',color:'#4b5563'}}>
                                Instalado: {d.instalado_en ? new Date(d.instalado_en).toLocaleDateString('es-CO') : '—'}
                                {d.retirado_en && ` · Retirado: ${new Date(d.retirado_en).toLocaleDateString('es-CO')}`}
                              </div>
                              {d.motivo_retiro && <div style={{fontSize:'11px',color:'#f87171'}}>Motivo: {d.motivo_retiro}</div>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {hojaVida.configuracion && (
                      <div style={styles.hvSection}>
                        <div style={styles.hvTitle}>Configuracion actual</div>
                        <div style={styles.detailGrid}>
                          {[
                            {label:'Intervalo',    value:`${hojaVida.configuracion.intervalo_muestreo||300}s`},
                            {label:'Protocolo',    value:hojaVida.configuracion.protocolo_transmision||'HTTP'},
                            {label:'Bateria min',  value:`${hojaVida.configuracion.umbral_bateria||20}%`},
                            {label:'Lim. Min',     value:hojaVida.configuracion.limite_minimo??'Defecto'},
                            {label:'Lim. Max',     value:hojaVida.configuracion.limite_maximo??'Defecto'},
                            {label:'Parcela',      value:hojaVida.configuracion.parcela_nombre||'Sin asignar'},
                          ].map(item => (
                            <div key={item.label} style={styles.detailItem}>
                              <div style={styles.detailLabel}>{item.label}</div>
                              <div style={styles.detailValue}>{item.value}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
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
  hint: { color: '#4b5563', fontWeight: 400, fontSize: '10px' },
  input: { padding: '9px 12px', background: 'rgba(6,12,7,0.8)', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#f0fdf4', fontSize: '13px', fontFamily: "'DM Sans', sans-serif" },
  errorMsg: { fontSize: '11px', color: '#f87171', marginTop: '3px' },
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
  detailPanel: { width: '300px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '16px', padding: '18px', height: 'fit-content', maxHeight: '90vh', overflowY: 'auto' },
  detailHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' },
  detailId: { fontFamily: 'monospace', color: '#4ade80', fontSize: '14px', fontWeight: 700 },
  detailSerial: { fontSize: '11px', color: '#6b7280', marginTop: '2px' },
  closeBtn: { background: 'none', border: 'none', color: '#4b5563', cursor: 'pointer', fontSize: '14px' },
  tabs: { display: 'flex', gap: '3px', marginBottom: '14px', background: 'rgba(6,12,7,0.6)', borderRadius: '8px', padding: '4px' },
  tab: { flex: 1, padding: '6px', borderRadius: '6px', border: 'none', background: 'transparent', color: '#6b7280', fontSize: '11px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s' },
  tabActive: { background: 'rgba(34,197,94,0.15)', color: '#22c55e' },
  detailGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' },
  detailItem: { background: 'rgba(6,12,7,0.6)', borderRadius: '8px', padding: '8px 10px' },
  detailLabel: { fontSize: '10px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '3px' },
  detailValue: { fontSize: '12px', fontWeight: 600, color: '#f0fdf4' },
  metricasCard: { background: 'rgba(6,12,7,0.6)', borderRadius: '8px', padding: '10px', marginBottom: '10px' },
  metricasTitle: { fontSize: '11px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '8px' },
  metricasList: { display: 'flex', flexWrap: 'wrap', gap: '5px' },
  metricaTag: { background: 'rgba(34,197,94,0.1)', color: '#4ade80', padding: '2px 8px', borderRadius: '4px', fontSize: '11px' },
  hvSection: { background: 'rgba(6,12,7,0.5)', borderRadius: '10px', padding: '12px', border: '1px solid rgba(34,197,94,0.08)' },
  hvTitle: { fontFamily: "'Syne', sans-serif", fontSize: '12px', fontWeight: 600, color: '#86efac', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.6px' },
  hvItem: { background: 'rgba(6,12,7,0.6)', borderRadius: '6px', padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: '3px' },
}