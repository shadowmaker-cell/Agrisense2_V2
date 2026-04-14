import { useState, useEffect } from 'react'
import { dispositivosAPI, parcelasAPI } from '../api/client'

const ESTADO_COLOR = { activo: '#22c55e', inactivo: '#6b7280', mantenimiento: '#fbbf24', desconectado: '#f87171' }

const CAT_STYLES = {
  suelo:              { color: '#a3e635', bg: 'rgba(163,230,53,0.12)',  border: 'rgba(163,230,53,0.3)'  },
  ambiental:          { color: '#38bdf8', bg: 'rgba(56,189,248,0.12)', border: 'rgba(56,189,248,0.3)'  },
  agua:               { color: '#2dd4bf', bg: 'rgba(45,212,191,0.12)', border: 'rgba(45,212,191,0.3)'  },
  planta:             { color: '#86efac', bg: 'rgba(134,239,172,0.12)',border: 'rgba(134,239,172,0.3)' },
  actuador_riego:     { color: '#60a5fa', bg: 'rgba(96,165,250,0.12)', border: 'rgba(96,165,250,0.3)'  },
  actuador_bombeo:    { color: '#818cf8', bg: 'rgba(129,140,248,0.12)',border: 'rgba(129,140,248,0.3)' },
  actuador_clima:     { color: '#fb923c', bg: 'rgba(251,146,60,0.12)', border: 'rgba(251,146,60,0.3)'  },
  actuador_iluminacion:{ color: '#fbbf24', bg: 'rgba(251,191,36,0.12)',border: 'rgba(251,191,36,0.3)' },
  computacion:        { color: '#c084fc', bg: 'rgba(192,132,252,0.12)',border: 'rgba(192,132,252,0.3)' },
  infraestructura:    { color: '#94a3b8', bg: 'rgba(148,163,184,0.12)',border: 'rgba(148,163,184,0.3)' },
  energia:            { color: '#facc15', bg: 'rgba(250,204,21,0.12)', border: 'rgba(250,204,21,0.3)'  },
}

const TIPO_COLOR = {
  correctivo: '#f87171', preventivo: '#22c55e',
  calibracion: '#60a5fa', inspeccion: '#fbbf24',
}
const RESULT_COLOR = {
  exitoso: '#22c55e', parcial: '#fbbf24',
  fallido: '#f87171', pendiente: '#6b7280',
}

const REGEX_ID_LOGICO = /^[A-Z][A-Z0-9_]{2,29}$/
const REGEX_SERIAL    = /^SN-[A-Z0-9]{2,8}-[A-Z0-9]{2,8}-\d{3}$/

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
  const [mantenimientos, setMantenimientos] = useState([])
  const [mantMsg, setMantMsg]           = useState('')
  const [mantLoading, setMantLoading]   = useState(false)

  const [form, setForm] = useState({
    tipo_dispositivo_id: '', numero_serial: '', id_logico: '',
    version_firmware: '1.0.0', estado: 'activo',
    parcela_id: '', parcela_nombre: '', posicion_campo: '',
    limite_minimo: '', limite_maximo: '',
  })

  const [editForm, setEditForm] = useState({
    estado: '', limite_minimo: '', limite_maximo: '',
    parcela_id: '', parcela_nombre: '', posicion_campo: '',
    intervalo_muestreo: '', umbral_bateria: '',
  })

  const [mantForm, setMantForm] = useState({
    tipo: 'preventivo', titulo: '', descripcion: '',
    causa: '', acciones: '', resultado: 'exitoso',
    tecnico: '', costo: '', fecha_inicio: '', fecha_fin: '',
    proxima_revision: '',
  })

  const load = async () => {
    try {
      const [dispRes, tiposRes] = await Promise.all([
        dispositivosAPI.listar(0, 200),
        dispositivosAPI.listarTipos(),
      ])
      setDispositivos(dispRes.data)
      setTipos(tiposRes.data)
    } catch(e) {
      console.error('Error cargando dispositivos:', e)
    } finally {
      setLoading(false)
    }
    try {
      const parcelasRes = await parcelasAPI.listar()
      setParcelas(parcelasRes.data)
    } catch(e) {
      setParcelas([])
    }
  }

  useEffect(() => { load() }, [])

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
    setEditMsg(''); setHojaVida(null); setMetricas(null)
    setMantenimientos([]); setActiveTab('info')
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
    setHojaVida(null)
    try {
      const res = await dispositivosAPI.hojaVida(selected.id)
      setHojaVida(res.data)
    } catch(e) { setHojaVida({ error: true }) }
  }

  const handleCargarMantenimientos = async () => {
    if (!selected) return
    try {
      const res = await dispositivosAPI.mantenimientos(selected.id)
      setMantenimientos(res.data)
    } catch(e) { setMantenimientos([]) }
  }

  const handleRegistrarMantenimiento = async (e) => {
    e.preventDefault()
    if (!mantForm.titulo) { setMantMsg('El titulo es obligatorio'); return }
    setMantLoading(true); setMantMsg('')
    try {
      await dispositivosAPI.registrarMant(selected.id, {
        ...mantForm,
        costo:            mantForm.costo            ? parseFloat(mantForm.costo) : null,
        fecha_inicio:     mantForm.fecha_inicio     || null,
        fecha_fin:        mantForm.fecha_fin        || null,
        proxima_revision: mantForm.proxima_revision || null,
      })
      setMantMsg('Mantenimiento registrado correctamente')
      await handleCargarMantenimientos()
      await load()
      setMantForm({
        tipo: 'preventivo', titulo: '', descripcion: '',
        causa: '', acciones: '', resultado: 'exitoso',
        tecnico: '', costo: '', fecha_inicio: '', fecha_fin: '',
        proxima_revision: '',
      })
    } catch(e) { setMantMsg('Error al registrar mantenimiento') }
    finally { setMantLoading(false) }
  }

  const descargarHojaVida = () => {
    if (!hojaVida || hojaVida.error) return
    const hv        = hojaVida
    const config    = hv.configuracion || {}
    const historial = hv.historial_estados || []
    const despliegues = hv.despliegues || []
    const mantos    = hv.mantenimientos || []

    const html = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Hoja de Vida — ${hv.id_logico}</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',Arial,sans-serif; background:#fff; color:#1a1a1a; padding:40px; max-width:860px; margin:auto; }
  .logo { display:flex; align-items:center; gap:12px; margin-bottom:32px; padding-bottom:20px; border-bottom:3px solid #16a34a; }
  .logo-icon { width:48px; height:48px; background:#16a34a; border-radius:10px; display:flex; align-items:center; justify-content:center; color:white; font-size:22px; }
  .logo-text { font-size:22px; font-weight:800; color:#16a34a; }
  .logo-sub { font-size:12px; color:#6b7280; }
  h1 { font-size:20px; font-weight:700; color:#111; margin-bottom:4px; }
  .subtitle { font-size:13px; color:#6b7280; margin-bottom:28px; }
  .section { margin-bottom:24px; }
  .section-title { font-size:12px; font-weight:700; color:#16a34a; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px; padding-bottom:4px; border-bottom:1px solid #d1fae5; }
  .grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
  .item { background:#f9fafb; border-radius:8px; padding:10px 12px; border-left:3px solid #16a34a; }
  .item-label { font-size:10px; color:#6b7280; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:3px; }
  .item-value { font-size:13px; font-weight:600; color:#111; }
  .table { width:100%; border-collapse:collapse; font-size:12px; }
  .table th { background:#f0fdf4; padding:8px 10px; text-align:left; font-weight:600; color:#16a34a; border-bottom:1px solid #d1fae5; }
  .table td { padding:7px 10px; border-bottom:1px solid #f3f4f6; color:#374151; }
  .badge { display:inline-block; padding:2px 8px; border-radius:20px; font-size:10px; font-weight:600; }
  .badge-activo { background:#d1fae5; color:#065f46; }
  .badge-retirado,.badge-inactivo { background:#f3f4f6; color:#6b7280; }
  .badge-mantenimiento { background:#fef3c7; color:#92400e; }
  .badge-correctivo { background:#fee2e2; color:#991b1b; }
  .badge-preventivo { background:#d1fae5; color:#065f46; }
  .badge-calibracion { background:#dbeafe; color:#1e40af; }
  .badge-inspeccion  { background:#fef9c3; color:#854d0e; }
  .badge-exitoso { background:#d1fae5; color:#065f46; }
  .badge-fallido { background:#fee2e2; color:#991b1b; }
  .badge-parcial { background:#fef3c7; color:#92400e; }
  .footer { margin-top:40px; padding-top:16px; border-top:1px solid #e5e7eb; font-size:11px; color:#9ca3af; display:flex; justify-content:space-between; }
  @media print { body { padding:20px; } }
</style>
</head>
<body>
  <div class="logo">
    <div class="logo-icon">🌿</div>
    <div>
      <div class="logo-text">AgriSense</div>
      <div class="logo-sub">Plataforma de Agricultura de Precision</div>
    </div>
  </div>
  <h1>Hoja de Vida del Sensor</h1>
  <div class="subtitle">Generado el ${new Date().toLocaleString('es-CO')} · ID: ${hv.id_logico}</div>
  <div class="section">
    <div class="section-title">Datos del Sensor</div>
    <div class="grid">
      <div class="item"><div class="item-label">ID Logico</div><div class="item-value">${hv.id_logico}</div></div>
      <div class="item"><div class="item-label">Serial</div><div class="item-value">${hv.numero_serial}</div></div>
      <div class="item"><div class="item-label">Estado</div><div class="item-value">${hv.estado}</div></div>
      <div class="item"><div class="item-label">Tipo</div><div class="item-value">${hv.tipo}</div></div>
      <div class="item"><div class="item-label">Categoria</div><div class="item-value">${hv.categoria}</div></div>
      <div class="item"><div class="item-label">Firmware</div><div class="item-value">${hv.version_firmware || 'N/A'}</div></div>
      <div class="item"><div class="item-label">Registrado</div><div class="item-value">${hv.registrado_en ? new Date(hv.registrado_en).toLocaleDateString('es-CO') : '—'}</div></div>
      <div class="item"><div class="item-label">Ultima conexion</div><div class="item-value">${hv.ultima_conexion ? new Date(hv.ultima_conexion).toLocaleDateString('es-CO') : 'Nunca'}</div></div>
      <div class="item"><div class="item-label">Mantenimientos</div><div class="item-value">${hv.total_mantenimientos || 0}</div></div>
    </div>
  </div>
  ${config ? `
  <div class="section">
    <div class="section-title">Configuracion Actual</div>
    <div class="grid">
      <div class="item"><div class="item-label">Intervalo</div><div class="item-value">${config.intervalo_muestreo || 300} seg</div></div>
      <div class="item"><div class="item-label">Protocolo</div><div class="item-value">${config.protocolo_transmision || 'HTTP'}</div></div>
      <div class="item"><div class="item-label">Umbral bateria</div><div class="item-value">${config.umbral_bateria || 20}%</div></div>
      <div class="item"><div class="item-label">Limite minimo</div><div class="item-value">${config.limite_minimo != null ? config.limite_minimo : 'Defecto'}</div></div>
      <div class="item"><div class="item-label">Limite maximo</div><div class="item-value">${config.limite_maximo != null ? config.limite_maximo : 'Defecto'}</div></div>
      <div class="item"><div class="item-label">Parcela</div><div class="item-value">${config.parcela_nombre || 'Sin asignar'}</div></div>
    </div>
  </div>` : ''}
  ${mantos.length > 0 ? `
  <div class="section">
    <div class="section-title">Historial de Mantenimientos (${mantos.length})</div>
    <table class="table">
      <thead><tr><th>Tipo</th><th>Titulo</th><th>Causa</th><th>Acciones</th><th>Resultado</th><th>Tecnico</th><th>Fecha</th></tr></thead>
      <tbody>${mantos.map(m => `
        <tr>
          <td><span class="badge badge-${m.tipo}">${m.tipo}</span></td>
          <td>${m.titulo}</td>
          <td>${m.causa || '—'}</td>
          <td>${m.acciones || '—'}</td>
          <td><span class="badge badge-${m.resultado}">${m.resultado}</span></td>
          <td>${m.tecnico || '—'}</td>
          <td>${m.fecha_inicio ? new Date(m.fecha_inicio).toLocaleDateString('es-CO') : '—'}</td>
        </tr>`).join('')}
      </tbody>
    </table>
  </div>` : ''}
  ${historial.length > 0 ? `
  <div class="section">
    <div class="section-title">Historial de Estados</div>
    <table class="table">
      <thead><tr><th>Anterior</th><th>Nuevo</th><th>Fecha</th></tr></thead>
      <tbody>${historial.map(h => `
        <tr>
          <td>${h.estado_anterior || 'inicio'}</td>
          <td><span class="badge badge-${h.estado_nuevo}">${h.estado_nuevo}</span></td>
          <td>${h.cambiado_en ? new Date(h.cambiado_en).toLocaleString('es-CO') : '—'}</td>
        </tr>`).join('')}
      </tbody>
    </table>
  </div>` : ''}
  ${despliegues.length > 0 ? `
  <div class="section">
    <div class="section-title">Historial de Despliegues</div>
    <table class="table">
      <thead><tr><th>Lote</th><th>Posicion</th><th>Estado</th><th>Instalado</th><th>Retirado</th></tr></thead>
      <tbody>${despliegues.map(d => `
        <tr>
          <td>${d.lote_id}</td>
          <td>${d.posicion || '—'}</td>
          <td><span class="badge badge-${d.estado}">${d.estado}</span></td>
          <td>${d.instalado_en ? new Date(d.instalado_en).toLocaleDateString('es-CO') : '—'}</td>
          <td>${d.retirado_en ? new Date(d.retirado_en).toLocaleDateString('es-CO') : 'Activo'}</td>
        </tr>`).join('')}
      </tbody>
    </table>
  </div>` : ''}
  <div class="footer">
    <span>AgriSense — Plataforma de Agricultura de Precision</span>
    <span>Generado: ${new Date().toLocaleString('es-CO')}</span>
  </div>
</body>
</html>`

    const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    const url  = URL.createObjectURL(blob)
    const win  = window.open(url, '_blank')
    if (win) win.onload = () => setTimeout(() => win.print(), 600)
  }

  const handleActualizar = async () => {
    if (!selected) return
    setEditMsg('')
    const payload = {}
    if (editForm.estado)                   payload.estado             = editForm.estado
    if (editForm.limite_minimo !== '')      payload.limite_minimo      = parseFloat(editForm.limite_minimo)
    if (editForm.limite_maximo !== '')      payload.limite_maximo      = parseFloat(editForm.limite_maximo)
    if (editForm.parcela_id !== '')         payload.parcela_id         = parseInt(editForm.parcela_id)
    if (editForm.parcela_nombre)            payload.parcela_nombre     = editForm.parcela_nombre
    if (editForm.posicion_campo)            payload.posicion_campo     = editForm.posicion_campo
    if (editForm.intervalo_muestreo !== '') payload.intervalo_muestreo = parseInt(editForm.intervalo_muestreo)
    if (editForm.umbral_bateria !== '')     payload.umbral_bateria     = parseInt(editForm.umbral_bateria)
    try {
      await dispositivosAPI.actualizar(selected.id, payload)
      setEditMsg('Configuracion actualizada correctamente')
      await load()
    } catch(e) { setEditMsg('Error al actualizar') }
  }

  const handleRegistrar = async (e) => {
    e.preventDefault()
    const errores = validarCampos(form)
    if (Object.keys(errores).length > 0) { setFormErrores(errores); setFormMsg('Corrige los errores'); return }
    if (!form.tipo_dispositivo_id) { setFormMsg('Selecciona un tipo de dispositivo'); return }
    setFormLoading(true); setFormMsg('')
    try {
      const payload = {
        tipo_dispositivo_id: parseInt(form.tipo_dispositivo_id),
        id_logico:           form.id_logico,
        numero_serial:       form.numero_serial,
        version_firmware:    form.version_firmware,
        estado:              form.estado,
      }
      if (form.parcela_id)           payload.parcela_id     = parseInt(form.parcela_id)
      if (form.parcela_nombre)       payload.parcela_nombre = form.parcela_nombre
      if (form.posicion_campo)       payload.posicion_campo = form.posicion_campo
      if (form.limite_minimo !== '') payload.limite_minimo  = parseFloat(form.limite_minimo)
      if (form.limite_maximo !== '') payload.limite_maximo  = parseFloat(form.limite_maximo)
      await dispositivosAPI.registrar(payload)
      setFormMsg('Sensor registrado exitosamente')
      await load()
      setTimeout(() => { setShowForm(false); setFormMsg('') }, 1500)
    } catch(e) {
      setFormMsg(e?.response?.data?.detail || 'Error al registrar el sensor')
    } finally { setFormLoading(false) }
  }

  const getTipo    = (id) => tipos.find(t => t.id === id)
  const categorias = ['todos', ...new Set(tipos.map(t => t.categoria).filter(Boolean))]

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
  const enMant        = dispositivos.filter(d => d.estado === 'mantenimiento').length

  return (
    <div style={styles.wrapper} className="animate-fade">
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Dispositivos IoT</h1>
          <p style={styles.subtitle}>
            {dispositivos.length} sensores · {activos} activos · {inactivos} inactivos · {enMant} en mantenimiento
          </p>
        </div>
        <button onClick={() => setShowForm(!showForm)} style={{
          ...styles.addBtn,
          background:  showForm ? 'rgba(248,113,113,0.1)' : 'rgba(34,197,94,0.12)',
          color:       showForm ? '#f87171' : '#22c55e',
          borderColor: showForm ? 'rgba(248,113,113,0.3)' : 'rgba(34,197,94,0.25)',
        }}>
          {showForm ? '✕ Cancelar' : '+ Registrar sensor'}
        </button>
      </div>

      {/* Formulario registro */}
      {showForm && (
        <div style={styles.formCard} className="animate-fade">
          <div style={styles.formTitle}>Registrar nuevo sensor</div>
          <p style={styles.formDesc}>
            Selecciona el tipo de dispositivo, completa el ID lógico y serial, y opcionalmente asigna una parcela.
          </p>
          <form onSubmit={handleRegistrar} style={styles.formGrid}>
            <div style={{...styles.fieldGroup, gridColumn:'1/-1'}}>
              <label style={styles.label}>Tipo de dispositivo *</label>
              <select value={form.tipo_dispositivo_id}
                onChange={e => setForm(p=>({...p, tipo_dispositivo_id: e.target.value}))}
                style={styles.input}>
                <option value="">— Selecciona un tipo —</option>
                {categorias.filter(c=>c!=='todos').map(cat => (
                  <optgroup key={cat} label={cat.charAt(0).toUpperCase()+cat.slice(1).replace('_',' ')}>
                    {tipos.filter(t=>t.categoria===cat).map(t => (
                      <option key={t.id} value={t.id}>{t.nombre}</option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>ID Lógico * <span style={styles.hint}>Ej: SOIL_HUM_02</span></label>
              <input placeholder="SOIL_HUM_02" value={form.id_logico}
                onChange={e => { setForm(p=>({...p,id_logico:e.target.value.toUpperCase()})); setFormErrores(p=>({...p,id_logico:''})) }}
                style={{...styles.input, borderColor: formErrores.id_logico ? '#f87171' : 'rgba(34,197,94,0.15)'}} />
              {formErrores.id_logico && <div style={styles.errorMsg}>{formErrores.id_logico}</div>}
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Serial * <span style={styles.hint}>SN-ABC-XYZ-001</span></label>
              <input placeholder="SN-HUM-CAP-002" value={form.numero_serial}
                onChange={e => { setForm(p=>({...p,numero_serial:e.target.value.toUpperCase()})); setFormErrores(p=>({...p,numero_serial:''})) }}
                style={{...styles.input, borderColor: formErrores.numero_serial ? '#f87171' : 'rgba(34,197,94,0.15)'}} />
              {formErrores.numero_serial && <div style={styles.errorMsg}>{formErrores.numero_serial}</div>}
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Firmware</label>
              <input placeholder="1.0.0" value={form.version_firmware}
                onChange={e => setForm(p=>({...p,version_firmware:e.target.value}))} style={styles.input} />
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
              <label style={styles.label}>Posición en campo</label>
              <input placeholder="ej: Sector norte, fila 3" value={form.posicion_campo}
                onChange={e => setForm(p=>({...p,posicion_campo:e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Límite mínimo</label>
              <input type="number" step="0.1" placeholder="Por defecto del tipo"
                value={form.limite_minimo}
                onChange={e => setForm(p=>({...p,limite_minimo:e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Límite máximo</label>
              <input type="number" step="0.1" placeholder="Por defecto del tipo"
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
            <option key={cat} value={cat}>{cat.charAt(0).toUpperCase()+cat.slice(1).replace('_',' ')}</option>
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
          ) : filtered.length === 0 ? (
            <div style={{padding:'40px',textAlign:'center',color:'#4b5563',fontSize:'13px'}}>
              <div style={{fontSize:'28px',marginBottom:'8px'}}>📡</div>
              <div>No hay sensores registrados</div>
              <div style={{marginTop:'6px',fontSize:'12px'}}>Haz clic en "+ Registrar sensor" para agregar el primero</div>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID Lógico</th><th>Categoría</th><th>Tipo</th>
                    <th>Parcela</th><th>Estado</th><th>Límites</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(d => {
                    const tipo     = getTipo(d.tipo_dispositivo_id)
                    const estColor = ESTADO_COLOR[d.estado] || '#6b7280'
                    const catStyle = CAT_STYLES[tipo?.categoria] || CAT_STYLES.infraestructura
                    const config   = d.configuracion
                    return (
                      <tr key={d.id} onClick={() => handleSelect(d)} style={{
                        cursor: 'pointer',
                        background: selected?.id === d.id ? 'rgba(34,197,94,0.08)' : 'transparent',
                      }}>
                        <td><span style={{fontFamily:'monospace',color:'#4ade80',fontSize:'12px'}}>{d.id_logico}</span></td>
                        <td>
                          <span style={{...styles.catBadge,color:catStyle.color,background:catStyle.bg,border:`1px solid ${catStyle.border}`}}>
                            {tipo?.categoria?.replace('_',' ') || '—'}
                          </span>
                        </td>
                        <td style={{fontSize:'11px',color:'#9ca3af',maxWidth:'140px',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>
                          {tipo?.nombre || '—'}
                        </td>
                        <td style={{fontSize:'11px',color:'#9ca3af'}}>
                          {config?.parcela_nombre || <span style={{color:'#374151'}}>Sin asignar</span>}
                        </td>
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
              {[
                { id:'info',          label:'Info'          },
                { id:'editar',        label:'Editar'        },
                { id:'mantenimiento', label:'Mant.'         },
                { id:'hoja-vida',     label:'Hoja de Vida'  },
              ].map(t => (
                <button key={t.id} onClick={() => {
                  setActiveTab(t.id)
                  if (t.id === 'hoja-vida')     handleCargarHojaVida()
                  if (t.id === 'mantenimiento') handleCargarMantenimientos()
                }} style={{...styles.tab, ...(activeTab===t.id ? styles.tabActive : {})}}>
                  {t.label}
                </button>
              ))}
            </div>

            {/* Tab Info */}
            {activeTab === 'info' && (
              <>
                <div style={styles.detailGrid}>
                  {[
                    {label:'Estado',   value:selected.estado,                                           color:ESTADO_COLOR[selected.estado]},
                    {label:'Firmware', value:selected.version_firmware||'N/A'},
                    {label:'Parcela',  value:selected.configuracion?.parcela_nombre||'Sin asignar',     color:'#4ade80'},
                    {label:'Posición', value:selected.configuracion?.posicion_campo||'—'},
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
                    <div style={styles.metricasTitle}>Métricas permitidas</div>
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
                  <label style={styles.label}>Posición en campo</label>
                  <input placeholder="ej: Sector norte" value={editForm.posicion_campo}
                    onChange={e => setEditForm(p=>({...p,posicion_campo:e.target.value}))} style={styles.input} />
                </div>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Límite mínimo</label>
                  <input type="number" step="0.1" value={editForm.limite_minimo}
                    onChange={e => setEditForm(p=>({...p,limite_minimo:e.target.value}))} style={styles.input} />
                </div>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Límite máximo</label>
                  <input type="number" step="0.1" value={editForm.limite_maximo}
                    onChange={e => setEditForm(p=>({...p,limite_maximo:e.target.value}))} style={styles.input} />
                </div>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Intervalo muestreo (seg)</label>
                  <input type="number" placeholder="300" value={editForm.intervalo_muestreo}
                    onChange={e => setEditForm(p=>({...p,intervalo_muestreo:e.target.value}))} style={styles.input} />
                </div>
                <div style={styles.fieldGroup}>
                  <label style={styles.label}>Umbral batería (%)</label>
                  <input type="number" placeholder="20" value={editForm.umbral_bateria}
                    onChange={e => setEditForm(p=>({...p,umbral_bateria:e.target.value}))} style={styles.input} />
                </div>
                <button onClick={handleActualizar} style={styles.submitBtn}>Guardar cambios</button>
                {editMsg && <div style={{fontSize:'13px',color:editMsg.includes('Error')?'#f87171':'#22c55e'}}>{editMsg}</div>}
              </div>
            )}

            {/* Tab Mantenimiento */}
            {activeTab === 'mantenimiento' && (
              <div style={{display:'flex',flexDirection:'column',gap:'12px'}}>
                <form onSubmit={handleRegistrarMantenimiento} style={styles.miniForm}>
                  <div style={styles.miniFormTitle}>🔧 Registrar mantenimiento</div>
                  <div style={styles.fieldGroup}>
                    <label style={styles.label}>Tipo</label>
                    <select value={mantForm.tipo}
                      onChange={e => setMantForm(p=>({...p,tipo:e.target.value}))} style={styles.input}>
                      <option value="preventivo">Preventivo</option>
                      <option value="correctivo">Correctivo</option>
                      <option value="calibracion">Calibración</option>
                      <option value="inspeccion">Inspección</option>
                    </select>
                  </div>
                  <div style={styles.fieldGroup}>
                    <label style={styles.label}>Título *</label>
                    <input placeholder="ej: Limpieza de contactos" value={mantForm.titulo}
                      onChange={e => setMantForm(p=>({...p,titulo:e.target.value}))} style={styles.input} />
                  </div>
                  <div style={styles.fieldGroup}>
                    <label style={styles.label}>Causa del mantenimiento</label>
                    <input placeholder="ej: Lectura fuera de rango" value={mantForm.causa}
                      onChange={e => setMantForm(p=>({...p,causa:e.target.value}))} style={styles.input} />
                  </div>
                  <div style={styles.fieldGroup}>
                    <label style={styles.label}>Descripción</label>
                    <input placeholder="Descripción detallada" value={mantForm.descripcion}
                      onChange={e => setMantForm(p=>({...p,descripcion:e.target.value}))} style={styles.input} />
                  </div>
                  <div style={styles.fieldGroup}>
                    <label style={styles.label}>Acciones realizadas</label>
                    <input placeholder="ej: Se limpió y recalibró el sensor" value={mantForm.acciones}
                      onChange={e => setMantForm(p=>({...p,acciones:e.target.value}))} style={styles.input} />
                  </div>
                  <div style={styles.fieldGroup}>
                    <label style={styles.label}>Resultado</label>
                    <select value={mantForm.resultado}
                      onChange={e => setMantForm(p=>({...p,resultado:e.target.value}))} style={styles.input}>
                      <option value="exitoso">Exitoso</option>
                      <option value="parcial">Parcial</option>
                      <option value="fallido">Fallido</option>
                      <option value="pendiente">Pendiente</option>
                    </select>
                  </div>
                  <div style={styles.fieldGroup}>
                    <label style={styles.label}>Técnico responsable</label>
                    <input placeholder="Nombre del técnico" value={mantForm.tecnico}
                      onChange={e => setMantForm(p=>({...p,tecnico:e.target.value}))} style={styles.input} />
                  </div>
                  <div style={styles.fieldGroup}>
                    <label style={styles.label}>Costo (opcional)</label>
                    <input type="number" step="0.01" placeholder="0.00" value={mantForm.costo}
                      onChange={e => setMantForm(p=>({...p,costo:e.target.value}))} style={styles.input} />
                  </div>
                  <div style={styles.fieldGroup}>
                    <label style={styles.label}>Fecha inicio</label>
                    <input type="datetime-local" value={mantForm.fecha_inicio}
                      onChange={e => setMantForm(p=>({...p,fecha_inicio:e.target.value}))} style={styles.input} />
                  </div>
                  <div style={styles.fieldGroup}>
                    <label style={styles.label}>Fecha fin</label>
                    <input type="datetime-local" value={mantForm.fecha_fin}
                      onChange={e => setMantForm(p=>({...p,fecha_fin:e.target.value}))} style={styles.input} />
                  </div>
                  <div style={styles.fieldGroup}>
                    <label style={styles.label}>Próxima revisión</label>
                    <input type="datetime-local" value={mantForm.proxima_revision}
                      onChange={e => setMantForm(p=>({...p,proxima_revision:e.target.value}))} style={styles.input} />
                  </div>
                  <button type="submit" disabled={mantLoading} style={styles.submitBtn}>
                    {mantLoading ? 'Registrando...' : 'Registrar mantenimiento'}
                  </button>
                  {mantMsg && <div style={{fontSize:'12px',color:mantMsg.includes('Error')?'#f87171':'#22c55e'}}>{mantMsg}</div>}
                </form>

                {/* Historial */}
                <div style={{display:'flex',flexDirection:'column',gap:'8px'}}>
                  <div style={{fontSize:'11px',color:'#6b7280',textTransform:'uppercase',letterSpacing:'0.6px'}}>
                    Historial ({mantenimientos.length})
                  </div>
                  {mantenimientos.length === 0 ? (
                    <div style={{textAlign:'center',padding:'20px',color:'#4b5563',fontSize:'12px'}}>
                      Sin mantenimientos registrados
                    </div>
                  ) : mantenimientos.map(m => (
                    <div key={m.id} style={{
                      background:'rgba(6,12,7,0.6)', borderRadius:'8px',
                      padding:'10px 12px', border:'1px solid rgba(34,197,94,0.08)',
                      borderLeft:`3px solid ${TIPO_COLOR[m.tipo]||'#6b7280'}`
                    }}>
                      <div style={{display:'flex',justifyContent:'space-between',marginBottom:'4px'}}>
                        <span style={{fontSize:'11px',fontWeight:700,color:TIPO_COLOR[m.tipo],textTransform:'uppercase'}}>
                          {m.tipo}
                        </span>
                        <span style={{fontSize:'10px',fontWeight:600,color:RESULT_COLOR[m.resultado]}}>
                          {m.resultado}
                        </span>
                      </div>
                      <div style={{fontSize:'13px',fontWeight:600,color:'#f0fdf4',marginBottom:'4px'}}>{m.titulo}</div>
                      {m.causa       && <div style={{fontSize:'11px',color:'#9ca3af'}}>Causa: {m.causa}</div>}
                      {m.acciones    && <div style={{fontSize:'11px',color:'#9ca3af'}}>Acciones: {m.acciones}</div>}
                      {m.tecnico     && <div style={{fontSize:'11px',color:'#4ade80'}}>Técnico: {m.tecnico}</div>}
                      {m.costo       && <div style={{fontSize:'11px',color:'#6b7280'}}>Costo: ${m.costo}</div>}
                      <div style={{fontSize:'10px',color:'#4b5563',marginTop:'4px'}}>
                        {m.fecha_inicio ? new Date(m.fecha_inicio).toLocaleString('es-CO') : '—'}
                        {m.proxima_revision && ` · Próx. revisión: ${new Date(m.proxima_revision).toLocaleDateString('es-CO')}`}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tab Hoja de Vida */}
            {activeTab === 'hoja-vida' && (
              <div style={{display:'flex',flexDirection:'column',gap:'12px'}}>
                {!hojaVida ? (
                  <div style={{textAlign:'center',padding:'30px',color:'#4b5563',fontSize:'13px'}}>
                    Cargando hoja de vida...
                  </div>
                ) : hojaVida.error ? (
                  <div style={{textAlign:'center',padding:'30px',color:'#f87171',fontSize:'13px'}}>
                    Error cargando la hoja de vida.
                  </div>
                ) : (
                  <>
                    <button onClick={descargarHojaVida} style={{
                      width:'100%', padding:'11px',
                      background:'linear-gradient(135deg,#16a34a,#15803d)',
                      color:'#fff', border:'none', borderRadius:'8px',
                      fontSize:'13px', fontWeight:600, cursor:'pointer',
                      display:'flex', alignItems:'center', justifyContent:'center', gap:'8px',
                    }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                      </svg>
                      Descargar / Imprimir PDF
                    </button>

                    <div style={styles.hvSection}>
                      <div style={styles.hvTitle}>Resumen</div>
                      <div style={styles.detailGrid}>
                        {[
                          {label:'Tipo',            value:hojaVida.tipo},
                          {label:'Categoría',       value:hojaVida.categoria},
                          {label:'Registrado',      value:hojaVida.registrado_en?new Date(hojaVida.registrado_en).toLocaleDateString('es-CO'):'—'},
                          {label:'Cambios estado',  value:hojaVida.total_cambios_estado},
                          {label:'Despliegues',     value:hojaVida.total_despliegues},
                          {label:'Mantenimientos',  value:hojaVida.total_mantenimientos||0},
                        ].map(item => (
                          <div key={item.label} style={styles.detailItem}>
                            <div style={styles.detailLabel}>{item.label}</div>
                            <div style={styles.detailValue}>{item.value}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {hojaVida.mantenimientos?.length > 0 && (
                      <div style={styles.hvSection}>
                        <div style={styles.hvTitle}>Mantenimientos ({hojaVida.mantenimientos.length})</div>
                        <div style={{display:'flex',flexDirection:'column',gap:'6px',maxHeight:'200px',overflowY:'auto'}}>
                          {hojaVida.mantenimientos.map((m,i) => (
                            <div key={i} style={{...styles.hvItem, borderLeft:`3px solid ${TIPO_COLOR[m.tipo]||'#6b7280'}`}}>
                              <div style={{display:'flex',justifyContent:'space-between'}}>
                                <span style={{fontSize:'11px',fontWeight:700,color:TIPO_COLOR[m.tipo]}}>{m.tipo}</span>
                                <span style={{fontSize:'10px',color:RESULT_COLOR[m.resultado]}}>{m.resultado}</span>
                              </div>
                              <div style={{fontSize:'12px',fontWeight:600,color:'#f0fdf4'}}>{m.titulo}</div>
                              {m.tecnico && <div style={{fontSize:'10px',color:'#4ade80'}}>Técnico: {m.tecnico}</div>}
                              <div style={{fontSize:'10px',color:'#4b5563'}}>
                                {m.fecha_inicio?new Date(m.fecha_inicio).toLocaleDateString('es-CO'):'—'}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {hojaVida.historial_estados?.length > 0 && (
                      <div style={styles.hvSection}>
                        <div style={styles.hvTitle}>Historial de estados ({hojaVida.historial_estados.length})</div>
                        <div style={{display:'flex',flexDirection:'column',gap:'6px',maxHeight:'160px',overflowY:'auto'}}>
                          {hojaVida.historial_estados.map((h,i) => (
                            <div key={i} style={styles.hvItem}>
                              <div style={{display:'flex',gap:'6px',alignItems:'center'}}>
                                <span style={{fontSize:'11px',color:'#6b7280'}}>{h.estado_anterior||'inicio'}</span>
                                <span style={{color:'#4ade80'}}>→</span>
                                <span style={{fontSize:'11px',fontWeight:600,color:ESTADO_COLOR[h.estado_nuevo]||'#f0fdf4'}}>{h.estado_nuevo}</span>
                              </div>
                              <div style={{fontSize:'10px',color:'#4b5563'}}>
                                {h.cambiado_en?new Date(h.cambiado_en).toLocaleString('es-CO'):'—'}
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
                          {hojaVida.despliegues.map((d,i) => (
                            <div key={i} style={styles.hvItem}>
                              <div style={{display:'flex',justifyContent:'space-between'}}>
                                <span style={{fontSize:'12px',fontWeight:600,color:'#f0fdf4'}}>Lote: {d.lote_id}</span>
                                <span style={{fontSize:'11px',fontWeight:600,color:d.estado==='activo'?'#22c55e':'#6b7280'}}>{d.estado}</span>
                              </div>
                              {d.posicion&&<div style={{fontSize:'11px',color:'#9ca3af'}}>Pos: {d.posicion}</div>}
                              <div style={{fontSize:'10px',color:'#4b5563'}}>
                                Instalado: {d.instalado_en?new Date(d.instalado_en).toLocaleDateString('es-CO'):'—'}
                                {d.retirado_en&&` · Retirado: ${new Date(d.retirado_en).toLocaleDateString('es-CO')}`}
                              </div>
                              {d.motivo_retiro&&<div style={{fontSize:'11px',color:'#f87171'}}>Motivo: {d.motivo_retiro}</div>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {hojaVida.configuracion && (
                      <div style={styles.hvSection}>
                        <div style={styles.hvTitle}>Configuración actual</div>
                        <div style={styles.detailGrid}>
                          {[
                            {label:'Intervalo',   value:`${hojaVida.configuracion.intervalo_muestreo||300}s`},
                            {label:'Protocolo',   value:hojaVida.configuracion.protocolo_transmision||'HTTP'},
                            {label:'Batería min', value:`${hojaVida.configuracion.umbral_bateria||20}%`},
                            {label:'Lím. Min',    value:hojaVida.configuracion.limite_minimo??'Defecto'},
                            {label:'Lím. Max',    value:hojaVida.configuracion.limite_maximo??'Defecto'},
                            {label:'Parcela',     value:hojaVida.configuracion.parcela_nombre||'Sin asignar'},
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
  wrapper:       { padding: '24px', maxWidth: '1300px' },
  header:        { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' },
  title:         { fontFamily: "'Syne', sans-serif", fontSize: '24px', fontWeight: 700, color: '#f0fdf4' },
  subtitle:      { fontSize: '13px', color: '#6b7280', marginTop: '4px' },
  addBtn:        { display: 'flex', alignItems: 'center', gap: '6px', padding: '9px 16px', borderRadius: '10px', border: '1px solid', fontSize: '13px', fontWeight: 600, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.2s', whiteSpace: 'nowrap' },
  formCard:      { background: '#0d1510', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '16px', padding: '20px', marginBottom: '20px' },
  formTitle:     { fontFamily: "'Syne', sans-serif", fontSize: '14px', fontWeight: 600, color: '#f0fdf4', marginBottom: '6px' },
  formDesc:      { fontSize: '12px', color: '#6b7280', marginBottom: '16px', lineHeight: 1.6 },
  formGrid:      { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' },
  fieldGroup:    { display: 'flex', flexDirection: 'column', gap: '5px' },
  label:         { fontSize: '11px', fontWeight: 500, color: '#86efac', letterSpacing: '0.4px' },
  hint:          { color: '#4b5563', fontWeight: 400, fontSize: '10px' },
  input:         { padding: '9px 12px', background: 'rgba(6,12,7,0.8)', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#f0fdf4', fontSize: '13px', fontFamily: "'DM Sans', sans-serif" },
  errorMsg:      { fontSize: '11px', color: '#f87171', marginTop: '3px' },
  submitBtn:     { width: '100%', padding: '10px', background: 'linear-gradient(135deg, #16a34a, #15803d)', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  filters:       { display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap', alignItems: 'center' },
  searchWrap:    { position: 'relative', flex: 1, minWidth: '180px' },
  searchIcon:    { position: 'absolute', left: '11px', top: '50%', transform: 'translateY(-50%)', color: '#4ade80' },
  search:        { width: '100%', padding: '9px 14px 9px 34px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#f0fdf4', fontSize: '13px', fontFamily: "'DM Sans', sans-serif" },
  select:        { padding: '9px 12px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#9ca3af', fontSize: '13px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  countTag:      { background: 'rgba(34,197,94,0.08)', color: '#4ade80', padding: '6px 12px', borderRadius: '20px', fontSize: '12px', border: '1px solid rgba(34,197,94,0.15)', whiteSpace: 'nowrap' },
  catBadge:      { padding: '3px 8px', borderRadius: '20px', fontSize: '10px', fontWeight: 600, whiteSpace: 'nowrap' },
  layout:        { display: 'flex', gap: '16px', flexWrap: 'wrap' },
  tableCard:     { flex: 1, minWidth: '300px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.1)', borderRadius: '16px', overflow: 'hidden' },
  detailPanel:   { width: '320px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '16px', padding: '18px', height: 'fit-content', maxHeight: '90vh', overflowY: 'auto' },
  detailHeader:  { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' },
  detailId:      { fontFamily: 'monospace', color: '#4ade80', fontSize: '14px', fontWeight: 700 },
  detailSerial:  { fontSize: '11px', color: '#6b7280', marginTop: '2px' },
  closeBtn:      { background: 'none', border: 'none', color: '#4b5563', cursor: 'pointer', fontSize: '14px' },
  tabs:          { display: 'flex', gap: '2px', marginBottom: '14px', background: 'rgba(6,12,7,0.6)', borderRadius: '8px', padding: '4px' },
  tab:           { flex: 1, padding: '6px 4px', borderRadius: '6px', border: 'none', background: 'transparent', color: '#6b7280', fontSize: '10px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s', whiteSpace: 'nowrap' },
  tabActive:     { background: 'rgba(34,197,94,0.15)', color: '#22c55e' },
  detailGrid:    { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' },
  detailItem:    { background: 'rgba(6,12,7,0.6)', borderRadius: '8px', padding: '8px 10px' },
  detailLabel:   { fontSize: '10px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '3px' },
  detailValue:   { fontSize: '12px', fontWeight: 600, color: '#f0fdf4' },
  metricasCard:  { background: 'rgba(6,12,7,0.6)', borderRadius: '8px', padding: '10px', marginBottom: '10px' },
  metricasTitle: { fontSize: '11px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '8px' },
  metricasList:  { display: 'flex', flexWrap: 'wrap', gap: '5px' },
  metricaTag:    { background: 'rgba(34,197,94,0.1)', color: '#4ade80', padding: '2px 8px', borderRadius: '4px', fontSize: '11px' },
  hvSection:     { background: 'rgba(6,12,7,0.5)', borderRadius: '10px', padding: '12px', border: '1px solid rgba(34,197,94,0.08)' },
  hvTitle:       { fontFamily: "'Syne', sans-serif", fontSize: '11px', fontWeight: 600, color: '#86efac', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.6px' },
  hvItem:        { background: 'rgba(6,12,7,0.6)', borderRadius: '6px', padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: '3px' },
  miniForm:      { background: 'rgba(6,12,7,0.5)', borderRadius: '10px', padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px', border: '1px solid rgba(34,197,94,0.08)' },
  miniFormTitle: { fontSize: '12px', fontWeight: 600, color: '#86efac', marginBottom: '4px' },
}