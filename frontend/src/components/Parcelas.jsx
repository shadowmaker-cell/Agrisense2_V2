import { useState, useEffect } from 'react'
import { parcelasAPI, dispositivosAPI } from '../api/client'

const ESTADO_COLOR = {
  activa:         { color: '#22c55e', bg: 'rgba(34,197,94,0.1)',   border: 'rgba(34,197,94,0.3)'   },
  inactiva:       { color: '#6b7280', bg: 'rgba(107,114,128,0.1)', border: 'rgba(107,114,128,0.3)' },
  en_preparacion: { color: '#fbbf24', bg: 'rgba(251,191,36,0.1)',  border: 'rgba(251,191,36,0.3)'  },
}

const ETAPAS      = ['germinacion','vegetativo','floracion','fructificacion','maduracion','cosecha']
const TIPOS_SUELO = ['arcilloso','arenoso','limoso','franco','otro']

const cardStyle = {
  background: 'rgba(6,12,7,0.6)',
  borderRadius: '8px',
  padding: '10px 12px',
}

const cardFullStyle = {
  background: 'rgba(6,12,7,0.6)',
  borderRadius: '8px',
  padding: '10px 12px',
  gridColumn: '1 / -1',
}

function InfoTab({ selected, styles }) {
  const est = ESTADO_COLOR[selected.estado] || ESTADO_COLOR.inactiva
  const mapsUrl = 'https://www.google.com/maps?q=' + selected.latitud + ',' + selected.longitud

  return (
    <div style={styles.infoGrid}>
      <div style={cardStyle}>
        <div style={styles.infoLabel}>Estado</div>
        <div style={{ fontSize: '13px', fontWeight: 600, color: est.color }}>{selected.estado}</div>
      </div>
      <div style={cardStyle}>
        <div style={styles.infoLabel}>Area</div>
        <div style={styles.infoValue}>{selected.area_hectareas} ha</div>
      </div>
      <div style={cardStyle}>
        <div style={styles.infoLabel}>Tipo suelo</div>
        <div style={styles.infoValue}>{selected.tipo_suelo || '—'}</div>
      </div>
      <div style={cardStyle}>
        <div style={styles.infoLabel}>Altitud</div>
        <div style={styles.infoValue}>{selected.altitud_msnm ? selected.altitud_msnm + ' msnm' : '—'}</div>
      </div>
      <div style={cardStyle}>
        <div style={styles.infoLabel}>Departamento</div>
        <div style={styles.infoValue}>{selected.departamento || '—'}</div>
      </div>
      <div style={cardStyle}>
        <div style={styles.infoLabel}>Municipio</div>
        <div style={styles.infoValue}>{selected.municipio || '—'}</div>
      </div>
      <div style={cardStyle}>
        <div style={styles.infoLabel}>Vereda</div>
        <div style={styles.infoValue}>{selected.vereda || '—'}</div>
      </div>
      <div style={cardStyle}>
        <div style={styles.infoLabel}>Creada</div>
        <div style={styles.infoValue}>{new Date(selected.creada_en).toLocaleDateString('es-CO')}</div>
      </div>
      <div style={cardFullStyle}>
        <div style={styles.infoLabel}>Coordenadas GPS</div>
        {selected.latitud && selected.longitud ? (
          <div>
            <div style={{ fontFamily: 'monospace', color: '#4ade80', fontSize: '12px', marginTop: '4px' }}>
              {selected.latitud}, {selected.longitud}
            </div>
            <a href={mapsUrl} target="_blank" rel="noopener noreferrer" style={styles.mapsLink}>
              Ver en Google Maps
            </a>
          </div>
        ) : (
          <div style={styles.infoValue}>—</div>
        )}
      </div>
      <div style={cardFullStyle}>
        <div style={styles.infoLabel}>Descripcion</div>
        <div style={{ fontSize: '12px', color: '#9ca3af', lineHeight: 1.5, marginTop: '4px' }}>
          {selected.descripcion || '—'}
        </div>
      </div>
    </div>
  )
}

function SensoresTab({ selected, sensoresDisp, sensorForm, setSensorForm, sensorMsg, handleAsignarSensor, handleDesasignar, styles }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <form onSubmit={handleAsignarSensor} style={styles.miniForm}>
        <div style={styles.miniFormTitle}>Asignar sensor activo</div>
        <select value={sensorForm.id_logico}
          onChange={e => setSensorForm(p => ({...p, id_logico: e.target.value}))}
          style={styles.input}>
          <option value="">Selecciona un sensor activo</option>
          {sensoresDisp.map(s => (
            <option key={s.id} value={s.id_logico}>{s.id_logico}</option>
          ))}
        </select>
        <input
          placeholder="Notas de instalacion (opcional)"
          value={sensorForm.notas}
          onChange={e => setSensorForm(p => ({...p, notas: e.target.value}))}
          style={styles.input}
        />
        <button type="submit" style={styles.submitBtn}>Asignar</button>
        {sensorMsg ? (
          <div style={{ fontSize: '12px', color: sensorMsg.includes('Error') ? '#f87171' : '#22c55e' }}>
            {sensorMsg}
          </div>
        ) : null}
      </form>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {selected.sensores?.filter(s => s.activo).length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px', color: '#4b5563', fontSize: '13px' }}>
            Sin sensores asignados
          </div>
        ) : (
          selected.sensores?.filter(s => s.activo).map(s => (
            <div key={s.id} style={styles.sensorItem}>
              <div>
                <div style={{ fontFamily: 'monospace', color: '#4ade80', fontSize: '12px' }}>{s.id_logico}</div>
                {s.notas ? (
                  <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>{s.notas}</div>
                ) : null}
                <div style={{ fontSize: '10px', color: '#4b5563', marginTop: '2px' }}>
                  Instalado: {new Date(s.fecha_instalacion).toLocaleDateString('es-CO')}
                </div>
              </div>
              <button onClick={() => handleDesasignar(s.id)} style={styles.desasignarBtn}>
                Quitar
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function HistorialTab({ selected, tipos, histForm, setHistForm, histMsg, handleAgregarHistorial, styles }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <form onSubmit={handleAgregarHistorial} style={styles.miniForm}>
        <div style={styles.miniFormTitle}>Agregar cultivo</div>
        <div style={styles.fieldGroup}>
          <label style={styles.label}>Tipo de cultivo</label>
          <select value={histForm.tipo_cultivo_id}
            onChange={e => setHistForm(p => ({...p, tipo_cultivo_id: e.target.value}))}
            style={styles.input}>
            {tipos.map(t => <option key={t.id} value={t.id}>{t.nombre}</option>)}
          </select>
        </div>
        <div style={styles.fieldGroup}>
          <label style={styles.label}>Fecha de siembra *</label>
          <input type="datetime-local" value={histForm.fecha_siembra}
            onChange={e => setHistForm(p => ({...p, fecha_siembra: e.target.value}))}
            style={styles.input} />
        </div>
        <div style={styles.fieldGroup}>
          <label style={styles.label}>Etapa fenologica</label>
          <select value={histForm.etapa_fenologica}
            onChange={e => setHistForm(p => ({...p, etapa_fenologica: e.target.value}))}
            style={styles.input}>
            {ETAPAS.map(et => (
              <option key={et} value={et}>{et.charAt(0).toUpperCase() + et.slice(1)}</option>
            ))}
          </select>
        </div>
        <div style={styles.fieldGroup}>
          <label style={styles.label}>Observaciones</label>
          <input placeholder="Notas del cultivo" value={histForm.observaciones}
            onChange={e => setHistForm(p => ({...p, observaciones: e.target.value}))}
            style={styles.input} />
        </div>
        <button type="submit" style={styles.submitBtn}>Agregar cultivo</button>
        {histMsg ? (
          <div style={{ fontSize: '12px', color: histMsg.includes('Error') ? '#f87171' : '#22c55e' }}>
            {histMsg}
          </div>
        ) : null}
      </form>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {selected.historial?.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px', color: '#4b5563', fontSize: '13px' }}>
            Sin historial de cultivos
          </div>
        ) : (
          selected.historial?.map(h => {
            const borderColor = h.estado === 'activo' ? '#22c55e' : h.estado === 'perdido' ? '#f87171' : '#6b7280'
            const textColor   = h.estado === 'activo' ? '#22c55e' : h.estado === 'perdido' ? '#f87171' : '#6b7280'
            return (
              <div key={h.id} style={{
                padding: '10px 12px',
                background: 'rgba(6,12,7,0.6)',
                borderRadius: '8px',
                border: '1px solid rgba(34,197,94,0.06)',
                borderLeft: '3px solid ' + borderColor,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: '#f0fdf4' }}>
                    {h.tipo_cultivo_nombre || 'Cultivo #' + h.tipo_cultivo_id}
                  </span>
                  <span style={{ fontSize: '10px', fontWeight: 600, color: textColor }}>
                    {h.estado.toUpperCase()}
                  </span>
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280' }}>
                  {'Siembra: ' + new Date(h.fecha_siembra).toLocaleDateString('es-CO')}
                  {h.etapa_fenologica ? ' - Etapa: ' + h.etapa_fenologica : ''}
                  {h.rendimiento_kg ? ' - ' + h.rendimiento_kg + ' kg' : ''}
                </div>
                {h.observaciones ? (
                  <div style={{ fontSize: '11px', color: '#4b5563', marginTop: '3px' }}>
                    {h.observaciones}
                  </div>
                ) : null}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

export default function Parcelas() {
  const [parcelas, setParcelas]         = useState([])
  const [tipos, setTipos]               = useState([])
  const [sensoresDisp, setSensoresDisp] = useState([])
  const [loading, setLoading]           = useState(true)
  const [selected, setSelected]         = useState(null)
  const [activeTab, setActiveTab]       = useState('info')
  const [showForm, setShowForm]         = useState(false)
  const [filtroEstado, setFiltroEstado] = useState('todos')
  const [formMsg, setFormMsg]           = useState('')
  const [formLoading, setFormLoading]   = useState(false)

  const [form, setForm] = useState({
    nombre: '', descripcion: '', area_hectareas: '',
    tipo_suelo: 'arcilloso', latitud: '', longitud: '',
    altitud_msnm: '', departamento: 'Cordoba',
    municipio: 'Monteria', vereda: '', estado: 'activa',
  })

  const [sensorForm, setSensorForm] = useState({ id_logico: '', dispositivo_id: 1, notas: '' })
  const [sensorMsg, setSensorMsg]   = useState('')
  const [histForm, setHistForm]     = useState({
    tipo_cultivo_id: 1, fecha_siembra: '', etapa_fenologica: 'vegetativo',
    rendimiento_kg: '', observaciones: '', estado: 'activo',
  })
  const [histMsg, setHistMsg] = useState('')

  const load = async () => {
    try {
      const [pRes, tRes, dRes] = await Promise.all([
        parcelasAPI.listar(),
        parcelasAPI.tiposCultivo(),
        dispositivosAPI.listar(0, 200),
      ])
      setParcelas(pRes.data)
      setTipos(tRes.data)
      setSensoresDisp(dRes.data.filter(d => d.estado === 'activo'))
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleCrearParcela = async (e) => {
    e.preventDefault()
    if (!form.nombre || !form.area_hectareas) { setFormMsg('Nombre y area son obligatorios'); return }
    setFormLoading(true); setFormMsg('')
    try {
      await parcelasAPI.crear({
        ...form,
        area_hectareas: parseFloat(form.area_hectareas),
        latitud:        form.latitud      ? parseFloat(form.latitud)      : null,
        longitud:       form.longitud     ? parseFloat(form.longitud)     : null,
        altitud_msnm:   form.altitud_msnm ? parseFloat(form.altitud_msnm) : null,
      })
      setFormMsg('Parcela creada exitosamente')
      await load()
      setTimeout(() => { setShowForm(false); setFormMsg('') }, 1500)
    } catch(e) {
      setFormMsg('Error al crear la parcela')
    } finally { setFormLoading(false) }
  }

  const handleAsignarSensor = async (e) => {
    e.preventDefault()
    if (!sensorForm.id_logico) { setSensorMsg('Selecciona un sensor'); return }
    setSensorMsg('')
    try {
      await parcelasAPI.asignarSensor(selected.id, sensorForm)
      setSensorMsg('Sensor asignado correctamente')
      const res = await parcelasAPI.obtener(selected.id)
      setSelected(res.data)
      await load()
    } catch(e) {
      const detail = e?.response?.data?.detail
      setSensorMsg(detail || 'Error al asignar sensor')
    }
  }

  const handleDesasignar = async (sensorId) => {
    try {
      await parcelasAPI.desasignarSensor(selected.id, sensorId)
      const res = await parcelasAPI.obtener(selected.id)
      setSelected(res.data)
      await load()
    } catch(e) { console.error(e) }
  }

  const handleAgregarHistorial = async (e) => {
    e.preventDefault()
    if (!histForm.fecha_siembra) { setHistMsg('La fecha de siembra es obligatoria'); return }
    setHistMsg('')
    try {
      await parcelasAPI.agregarHistorial(selected.id, {
        ...histForm,
        tipo_cultivo_id: parseInt(histForm.tipo_cultivo_id),
        rendimiento_kg:  histForm.rendimiento_kg ? parseFloat(histForm.rendimiento_kg) : null,
        fecha_cosecha:   null,
      })
      setHistMsg('Historial agregado correctamente')
      const res = await parcelasAPI.obtener(selected.id)
      setSelected(res.data)
    } catch(e) { setHistMsg('Error al agregar historial') }
  }

  const handleEliminar = async (id) => {
    try {
      await parcelasAPI.eliminar(id)
      setSelected(null)
      await load()
    } catch(e) { console.error(e) }
  }

  const filtered = parcelas.filter(p => filtroEstado === 'todos' || p.estado === filtroEstado)

  return (
    <div style={styles.wrapper} className="animate-fade">
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Parcelas Agricolas</h1>
          <p style={styles.subtitle}>{parcelas.length} parcelas registradas</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} style={{
          ...styles.addBtn,
          background:  showForm ? 'rgba(248,113,113,0.1)' : 'rgba(34,197,94,0.12)',
          color:       showForm ? '#f87171' : '#22c55e',
          borderColor: showForm ? 'rgba(248,113,113,0.3)' : 'rgba(34,197,94,0.25)',
        }}>
          {showForm ? 'Cancelar' : 'Nueva parcela'}
        </button>
      </div>

      {showForm ? (
        <div style={styles.formCard} className="animate-fade">
          <div style={styles.formTitle}>Registrar nueva parcela</div>
          <form onSubmit={handleCrearParcela} style={styles.formGrid}>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Nombre *</label>
              <input placeholder="ej: Parcela La Esperanza" value={form.nombre}
                onChange={e => setForm(p => ({...p, nombre: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Area (hectareas) *</label>
              <input type="number" step="0.1" placeholder="ej: 12.5" value={form.area_hectareas}
                onChange={e => setForm(p => ({...p, area_hectareas: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Tipo de suelo</label>
              <select value={form.tipo_suelo}
                onChange={e => setForm(p => ({...p, tipo_suelo: e.target.value}))} style={styles.input}>
                {TIPOS_SUELO.map(t => (
                  <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                ))}
              </select>
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Departamento</label>
              <input placeholder="ej: Cordoba" value={form.departamento}
                onChange={e => setForm(p => ({...p, departamento: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Municipio</label>
              <input placeholder="ej: Monteria" value={form.municipio}
                onChange={e => setForm(p => ({...p, municipio: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Vereda</label>
              <input placeholder="ej: El Vidrial" value={form.vereda}
                onChange={e => setForm(p => ({...p, vereda: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Latitud</label>
              <input type="number" step="0.0001" placeholder="ej: 8.7534" value={form.latitud}
                onChange={e => setForm(p => ({...p, latitud: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Longitud</label>
              <input type="number" step="0.0001" placeholder="ej: -75.8811" value={form.longitud}
                onChange={e => setForm(p => ({...p, longitud: e.target.value}))} style={styles.input} />
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Estado</label>
              <select value={form.estado}
                onChange={e => setForm(p => ({...p, estado: e.target.value}))} style={styles.input}>
                <option value="activa">Activa</option>
                <option value="inactiva">Inactiva</option>
                <option value="en_preparacion">En preparacion</option>
              </select>
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={styles.label}>Descripcion</label>
              <textarea placeholder="Descripcion de la parcela..." value={form.descripcion}
                onChange={e => setForm(p => ({...p, descripcion: e.target.value}))}
                style={{ ...styles.input, height: '70px', resize: 'vertical', width: '100%' }} />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <button type="submit" disabled={formLoading} style={styles.submitBtn}>
                {formLoading ? 'Creando...' : 'Crear parcela'}
              </button>
            </div>
          </form>
          {formMsg ? (
            <div style={{ marginTop: '10px', fontSize: '13px', color: formMsg.includes('Error') ? '#f87171' : '#22c55e' }}>
              {formMsg}
            </div>
          ) : null}
        </div>
      ) : null}

      <div style={styles.filters}>
        {['todos', 'activa', 'inactiva', 'en_preparacion'].map(e => (
          <button key={e} onClick={() => setFiltroEstado(e)} style={{
            ...styles.filterBtn,
            ...(filtroEstado === e ? styles.filterBtnActive : {})
          }}>
            {e === 'todos' ? 'Todas' : e === 'en_preparacion' ? 'En preparacion' : e.charAt(0).toUpperCase() + e.slice(1)}
          </button>
        ))}
        <div style={styles.countTag}>{filtered.length} parcelas</div>
      </div>

      <div style={styles.layout}>
        <div style={styles.listaCol}>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[...Array(3)].map((_, i) => (
                <div key={i} className="skeleton" style={{ height: '100px', borderRadius: '12px' }} />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div style={styles.empty}>
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#374151" strokeWidth="1.5" style={{ marginBottom: '10px' }}>
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9 22 9 12 15 12 15 22"/>
              </svg>
              <div style={styles.emptyText}>No hay parcelas registradas</div>
              <div style={styles.emptySub}>Crea tu primera parcela con el boton de arriba</div>
            </div>
          ) : (
            filtered.map((p) => {
              const est = ESTADO_COLOR[p.estado] || ESTADO_COLOR.inactiva
              const sensoresActivos = p.sensores ? p.sensores.filter(s => s.activo).length : 0
              const cultivoActivo   = p.historial ? p.historial.find(h => h.estado === 'activo') : null
              const isSelected      = selected && selected.id === p.id
              return (
                <div key={p.id} onClick={() => { setSelected(p); setActiveTab('info') }} style={{
                  padding: '16px 18px',
                  borderRadius: '14px',
                  border: '1px solid ' + (isSelected ? est.color : 'rgba(34,197,94,0.1)'),
                  background: isSelected ? est.color + '08' : '#0d1510',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  marginBottom: '2px',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <div style={{ fontFamily: "'Syne', sans-serif", fontSize: '15px', fontWeight: 600, color: '#f0fdf4' }}>{p.nombre}</div>
                    <span style={{ padding: '2px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: 600, color: est.color, background: est.bg, border: '1px solid ' + est.border }}>
                      {p.estado === 'en_preparacion' ? 'En prep.' : p.estado}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '12px', color: '#6b7280' }}>{p.area_hectareas} ha</span>
                    {p.municipio ? <span style={{ fontSize: '12px', color: '#6b7280' }}>{p.municipio}</span> : null}
                    <span style={{ fontSize: '12px', color: '#6b7280' }}>{sensoresActivos} sensores</span>
                    {cultivoActivo ? (
                      <span style={{ fontSize: '12px', color: '#4ade80' }}>
                        {cultivoActivo.tipo_cultivo_nombre || 'Cultivo activo'}
                      </span>
                    ) : null}
                  </div>
                  {p.latitud && p.longitud ? (
                    <div style={{ marginTop: '6px', fontFamily: 'monospace', fontSize: '10px', color: '#4b5563' }}>
                      {p.latitud.toFixed(4)}, {p.longitud.toFixed(4)}
                    </div>
                  ) : null}
                </div>
              )
            })
          )}
        </div>

        {selected ? (
          <div style={styles.detailPanel}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
              <div>
                <div style={{ fontFamily: "'Syne', sans-serif", fontSize: '15px', fontWeight: 700, color: '#f0fdf4' }}>{selected.nombre}</div>
                <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>{selected.municipio} · {selected.area_hectareas} ha</div>
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button onClick={() => handleEliminar(selected.id)} style={styles.deleteBtn}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                  </svg>
                </button>
                <button onClick={() => setSelected(null)} style={styles.closeBtn}>x</button>
              </div>
            </div>

            <div style={styles.tabs}>
              {[
                { id: 'info',      label: 'Info' },
                { id: 'sensores',  label: 'Sensores (' + (selected.sensores ? selected.sensores.filter(s => s.activo).length : 0) + ')' },
                { id: 'historial', label: 'Historial' },
              ].map(t => (
                <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
                  ...styles.tab,
                  ...(activeTab === t.id ? styles.tabActive : {})
                }}>{t.label}</button>
              ))}
            </div>

            {activeTab === 'info' ? (
              <InfoTab selected={selected} styles={styles} />
            ) : activeTab === 'sensores' ? (
              <SensoresTab
                selected={selected}
                sensoresDisp={sensoresDisp}
                sensorForm={sensorForm}
                setSensorForm={setSensorForm}
                sensorMsg={sensorMsg}
                handleAsignarSensor={handleAsignarSensor}
                handleDesasignar={handleDesasignar}
                styles={styles}
              />
            ) : (
              <HistorialTab
                selected={selected}
                tipos={tipos}
                histForm={histForm}
                setHistForm={setHistForm}
                histMsg={histMsg}
                handleAgregarHistorial={handleAgregarHistorial}
                styles={styles}
              />
            )}
          </div>
        ) : null}
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
  formTitle: { fontFamily: "'Syne', sans-serif", fontSize: '14px', fontWeight: 600, color: '#f0fdf4', marginBottom: '16px' },
  formGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' },
  fieldGroup: { display: 'flex', flexDirection: 'column', gap: '5px' },
  label: { fontSize: '11px', fontWeight: 500, color: '#86efac', letterSpacing: '0.4px' },
  input: { padding: '9px 12px', background: 'rgba(6,12,7,0.8)', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#f0fdf4', fontSize: '13px', fontFamily: "'DM Sans', sans-serif" },
  submitBtn: { width: '100%', padding: '10px', background: 'linear-gradient(135deg, #16a34a, #15803d)', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  filters: { display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap', alignItems: 'center' },
  filterBtn: { padding: '7px 14px', borderRadius: '20px', border: '1px solid rgba(34,197,94,0.15)', background: 'transparent', color: '#6b7280', fontSize: '12px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  filterBtnActive: { background: 'rgba(34,197,94,0.15)', color: '#22c55e', borderColor: 'rgba(34,197,94,0.4)' },
  countTag: { background: 'rgba(34,197,94,0.08)', color: '#4ade80', padding: '6px 12px', borderRadius: '20px', fontSize: '12px', border: '1px solid rgba(34,197,94,0.15)', marginLeft: 'auto' },
  layout: { display: 'flex', gap: '16px' },
  listaCol: { flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' },
  empty: { textAlign: 'center', padding: '60px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#0d1510', borderRadius: '16px', border: '1px solid rgba(34,197,94,0.08)' },
  emptyText: { fontSize: '16px', fontWeight: 600, color: '#f0fdf4', fontFamily: "'Syne', sans-serif", marginBottom: '6px' },
  emptySub: { fontSize: '13px', color: '#6b7280' },
  detailPanel: { width: '320px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '16px', padding: '20px', height: 'fit-content', maxHeight: '85vh', overflowY: 'auto' },
  deleteBtn: { background: 'rgba(248,113,113,0.1)', border: '1px solid rgba(248,113,113,0.2)', color: '#f87171', cursor: 'pointer', padding: '5px 8px', borderRadius: '6px' },
  closeBtn: { background: 'none', border: 'none', color: '#4b5563', cursor: 'pointer', fontSize: '14px', padding: '5px 8px' },
  tabs: { display: 'flex', gap: '4px', marginBottom: '16px', background: 'rgba(6,12,7,0.6)', borderRadius: '8px', padding: '4px' },
  tab: { flex: 1, padding: '7px', borderRadius: '6px', border: 'none', background: 'transparent', color: '#6b7280', fontSize: '11px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s' },
  tabActive: { background: 'rgba(34,197,94,0.15)', color: '#22c55e' },
  infoGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' },
  infoLabel: { fontSize: '10px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '4px' },
  infoValue: { fontSize: '13px', fontWeight: 600, color: '#f0fdf4' },
  mapsLink: { display: 'inline-block', marginTop: '6px', fontSize: '11px', color: '#60a5fa', textDecoration: 'none' },
  miniForm: { background: 'rgba(6,12,7,0.5)', borderRadius: '10px', padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px', border: '1px solid rgba(34,197,94,0.08)' },
  miniFormTitle: { fontSize: '12px', fontWeight: 600, color: '#86efac', marginBottom: '4px' },
  sensorItem: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', background: 'rgba(6,12,7,0.6)', borderRadius: '8px', border: '1px solid rgba(34,197,94,0.1)' },
  desasignarBtn: { padding: '4px 10px', borderRadius: '6px', border: '1px solid rgba(248,113,113,0.2)', background: 'rgba(248,113,113,0.08)', color: '#f87171', fontSize: '11px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
}