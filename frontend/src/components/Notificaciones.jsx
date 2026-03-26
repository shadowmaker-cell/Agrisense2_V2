import { useState, useEffect } from 'react'
import { notificacionesAPI } from '../api/client'

const SEV_COLOR  = { critica: '#f87171', alta: '#fbbf24', media: '#60a5fa', baja: '#22c55e' }
const CANAL_ICON = { push: '📱', email: '📧', sms: '💬', sistema: '🖥️' }

export default function Notificaciones() {
  const [notifs, setNotifs]             = useState([])
  const [resumen, setResumen]           = useState(null)
  const [loading, setLoading]           = useState(true)
  const [filtroEstado, setFiltroEstado] = useState('todos')
  const [filtroSev, setFiltroSev]       = useState('todos')
  const [leidas, setLeidas]             = useState(new Set())
  const [activeTab, setActiveTab]       = useState('lista')

  // Envio manual
  const [envioForm, setEnvioForm] = useState({
    dispositivo_id: 1, id_logico: 'AIR_TEMP_01',
    tipo_alerta: 'helada', tipo_metrica: 'temperatura_aire',
    valor: -3.0, condicion: '< 0C — Helada inminente',
    severidad: 'critica', canal: 'push',
  })
  const [envioMsg, setEnvioMsg]     = useState('')
  const [envioLoading, setEnvioLoading] = useState(false)

  // Preferencias
  const [prefs, setPrefs] = useState({
    canal_preferido: 'sistema', activo: true,
    alertas_criticas: true, alertas_altas: true,
    alertas_medias: false, alertas_bajas: false,
  })
  const [prefsMsg, setPrefsMsg]       = useState('')
  const [prefsLoading, setPrefsLoading] = useState(false)

  // Por dispositivo
  const [idLogicoBuscar, setIdLogicoBuscar] = useState('')
  const [notifsSensor, setNotifsSensor]     = useState([])
  const [buscarMsg, setBuscarMsg]           = useState('')

  const load = async () => {
    try {
      const [nRes, rRes] = await Promise.all([
        notificacionesAPI.listar(
          filtroEstado !== 'todos' ? filtroEstado : null,
          filtroSev    !== 'todos' ? filtroSev    : null,
        ),
        notificacionesAPI.resumen(),
      ])
      setNotifs(nRes.data)
      setResumen(rRes.data)
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [filtroEstado, filtroSev])

  const marcarLeida = async (id) => {
    try {
      await notificacionesAPI.marcarLeida(id)
      setLeidas(prev => new Set([...prev, id]))
      setResumen(prev => prev ? { ...prev, no_leidas: Math.max(0, prev.no_leidas - 1) } : prev)
    } catch(e) {}
  }

  const handleEnviar = async (e) => {
    e.preventDefault()
    setEnvioLoading(true); setEnvioMsg('')
    try {
      const res = await notificacionesAPI.enviar(envioForm)
      setEnvioMsg(`✅ Notificacion enviada — ID: ${res.data.notificacion_id} · Canal: ${res.data.canal}`)
      await load()
    } catch(e) { setEnvioMsg('❌ Error al enviar notificacion') }
    finally { setEnvioLoading(false) }
  }

  const handleGuardarPrefs = async (e) => {
    e.preventDefault()
    setPrefsLoading(true); setPrefsMsg('')
    try {
      await notificacionesAPI.guardarPrefs(1, prefs)
      setPrefsMsg('✅ Preferencias guardadas exitosamente')
    } catch(e) { setPrefsMsg('❌ Error al guardar preferencias') }
    finally { setPrefsLoading(false) }
  }

  const handleBuscarSensor = async () => {
    if (!idLogicoBuscar.trim()) return
    setBuscarMsg('')
    try {
      const res = await notificacionesAPI.porDispositivo(idLogicoBuscar.trim())
      setNotifsSensor(res.data)
      if (res.data.length === 0) setBuscarMsg('Sin notificaciones para ese sensor')
    } catch(e) { setBuscarMsg('Sensor sin notificaciones registradas'); setNotifsSensor([]) }
  }

  const TABS = [
    { id: 'lista',      label: 'Historial'    },
    { id: 'sensor',     label: 'Por sensor'   },
    { id: 'enviar',     label: 'Enviar alerta'},
    { id: 'preferencias', label: 'Preferencias'},
  ]

  return (
    <div style={styles.wrapper} className="animate-fade">
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Notificaciones</h1>
          <p style={styles.subtitle}>Centro de alertas y comunicaciones del sistema</p>
        </div>
        <button onClick={load} className="btn btn-ghost" style={{ fontSize: '12px' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          Actualizar
        </button>
      </div>

      {/* Resumen */}
      {resumen && (
        <div style={styles.resumenGrid}>
          {[
            { label: 'Total',      val: resumen.total,      color: '#f0fdf4', bg: 'rgba(255,255,255,0.04)' },
            { label: 'Enviadas',   val: resumen.enviadas,   color: '#22c55e', bg: 'rgba(34,197,94,0.08)'   },
            { label: 'Pendientes', val: resumen.pendientes, color: '#fbbf24', bg: 'rgba(251,191,36,0.08)'  },
            { label: 'Sin leer',   val: resumen.no_leidas,  color: '#60a5fa', bg: 'rgba(96,165,250,0.08)'  },
            { label: 'Criticas',   val: resumen.criticas,   color: '#f87171', bg: 'rgba(248,113,113,0.08)' },
          ].map(item => (
            <div key={item.label} style={{ ...styles.resumenCard, background: item.bg }}>
              <div style={{ ...styles.resumenVal, color: item.color }}>{item.val}</div>
              <div style={styles.resumenLabel}>{item.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div style={styles.tabsBar}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            ...styles.tabBtn,
            ...(activeTab === t.id ? styles.tabBtnActive : {})
          }}>{t.label}</button>
        ))}
      </div>

      {/* ── TAB: Historial ── */}
      {activeTab === 'lista' && (
        <>
          <div style={styles.filters}>
            <div style={styles.filterItem}>
              <label style={styles.filterLabel}>Estado</label>
              <select value={filtroEstado} onChange={e => setFiltroEstado(e.target.value)} style={styles.select}>
                <option value="todos">Todos los estados</option>
                <option value="enviada">Enviada</option>
                <option value="pendiente">Pendiente</option>
                <option value="fallida">Fallida</option>
              </select>
            </div>
            <div style={styles.filterItem}>
              <label style={styles.filterLabel}>Severidad</label>
              <select value={filtroSev} onChange={e => setFiltroSev(e.target.value)} style={styles.select}>
                <option value="todos">Todas las severidades</option>
                <option value="critica">Critica</option>
                <option value="alta">Alta</option>
                <option value="media">Media</option>
                <option value="baja">Baja</option>
              </select>
            </div>
            <div style={styles.countTag}>{notifs.length} resultados</div>
          </div>

          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: '100px', borderRadius: '12px' }} />)}
            </div>
          ) : notifs.length === 0 ? (
            <div style={styles.empty}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#374151" strokeWidth="1.5" style={{ marginBottom: '10px' }}>
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
              <div style={styles.emptyText}>Sin notificaciones</div>
              <div style={styles.emptySub}>No hay notificaciones con los filtros seleccionados</div>
            </div>
          ) : (
            <div style={styles.notifList}>
              {notifs.map((n, i) => {
                const isLeida  = n.leida || leidas.has(n.id)
                const sevColor = SEV_COLOR[n.severidad] || '#6b7280'
                return (
                  <div key={n.id} style={{
                    ...styles.notifCard,
                    opacity: isLeida ? 0.55 : 1,
                    borderLeft: `4px solid ${isLeida ? '#374151' : sevColor}`,
                    animationDelay: `${i * 0.03}s`,
                  }} className="animate-fade">
                    <div style={styles.notifLeft}>
                      <div style={styles.notifTop}>
                        <span style={{ ...styles.sevBadge, color: sevColor, background: `${sevColor}12`, border: `1px solid ${sevColor}35` }}>{n.severidad?.toUpperCase()}</span>
                        <span style={styles.canalTag}>{CANAL_ICON[n.canal] || ''} {n.canal}</span>
                        <span style={{ fontSize: '11px', fontWeight: 600, color: n.estado === 'enviada' ? '#22c55e' : n.estado === 'fallida' ? '#f87171' : '#fbbf24' }}>
                          {n.estado === 'enviada' ? 'Enviada' : n.estado === 'fallida' ? 'Fallida' : 'Pendiente'}
                        </span>
                        {!isLeida && <span style={styles.nuevaTag}>Nueva</span>}
                      </div>
                      <div style={styles.notifTitulo}>{n.titulo}</div>
                      <div style={styles.notifMeta}>
                        <span style={{ fontFamily: 'monospace', color: '#4ade80', fontSize: '11px' }}>{n.id_logico}</span>
                        <span style={styles.metaDot}>·</span>
                        <span style={styles.metaItem}>{n.tipo}</span>
                        <span style={styles.metaDot}>·</span>
                        <span style={styles.metaItem}>{new Date(n.creada_en).toLocaleString('es-CO')}</span>
                      </div>
                    </div>
                    {!isLeida && (
                      <button onClick={() => marcarLeida(n.id)} style={styles.leerBtn}>Marcar leida</button>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}

      {/* ── TAB: Por sensor ── */}
      {activeTab === 'sensor' && (
        <div style={styles.sensorPanel}>
          <div style={styles.sectionTitle}>Buscar notificaciones por sensor</div>
          <div style={styles.buscarRow}>
            <input
              placeholder="ID logico del sensor ej: AIR_TEMP_01"
              value={idLogicoBuscar}
              onChange={e => setIdLogicoBuscar(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleBuscarSensor()}
              style={styles.buscarInput}
            />
            <button onClick={handleBuscarSensor} className="btn btn-primary">Buscar</button>
          </div>
          {buscarMsg && <div style={{ fontSize: '13px', color: '#6b7280', margin: '10px 0' }}>{buscarMsg}</div>}
          {notifsSensor.length > 0 && (
            <div style={styles.notifList}>
              {notifsSensor.map((n, i) => {
                const sevColor = SEV_COLOR[n.severidad] || '#6b7280'
                return (
                  <div key={n.id} style={{ ...styles.notifCard, borderLeft: `4px solid ${sevColor}`, animationDelay: `${i * 0.03}s` }} className="animate-fade">
                    <div style={styles.notifLeft}>
                      <div style={styles.notifTop}>
                        <span style={{ ...styles.sevBadge, color: sevColor, background: `${sevColor}12`, border: `1px solid ${sevColor}35` }}>{n.severidad?.toUpperCase()}</span>
                        <span style={styles.canalTag}>{CANAL_ICON[n.canal] || ''} {n.canal}</span>
                      </div>
                      <div style={styles.notifTitulo}>{n.titulo}</div>
                      <div style={styles.notifMeta}>
                        <span style={styles.metaItem}>{n.tipo}</span>
                        <span style={styles.metaDot}>·</span>
                        <span style={styles.metaItem}>{new Date(n.creada_en).toLocaleString('es-CO')}</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* ── TAB: Enviar alerta ── */}
      {activeTab === 'enviar' && (
        <div style={styles.formCard}>
          <div style={styles.sectionTitle}>Enviar notificacion manual</div>
          <p style={{ fontSize: '13px', color: '#6b7280', marginBottom: '20px' }}>
            Genera una notificacion directamente hacia el agricultor sin pasar por el flujo de Kafka.
          </p>
          <form onSubmit={handleEnviar} style={styles.envioGrid}>
            {[
              { label: 'Dispositivo ID', key: 'dispositivo_id', type: 'number', placeholder: '1' },
              { label: 'ID Logico',      key: 'id_logico',      type: 'text',   placeholder: 'AIR_TEMP_01' },
              { label: 'Tipo de alerta', key: 'tipo_alerta',    type: 'text',   placeholder: 'helada' },
              { label: 'Tipo metrica',   key: 'tipo_metrica',   type: 'text',   placeholder: 'temperatura_aire' },
              { label: 'Valor',          key: 'valor',          type: 'number', placeholder: '-3.0', step: '0.1' },
              { label: 'Condicion',      key: 'condicion',      type: 'text',   placeholder: '< 0C — Helada inminente' },
            ].map(field => (
              <div key={field.key} style={styles.fieldGroup}>
                <label style={styles.label}>{field.label}</label>
                <input
                  type={field.type}
                  step={field.step}
                  placeholder={field.placeholder}
                  value={envioForm[field.key]}
                  onChange={e => setEnvioForm(p => ({ ...p, [field.key]: field.type === 'number' ? parseFloat(e.target.value) || e.target.value : e.target.value }))}
                  style={styles.input}
                />
              </div>
            ))}
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Severidad</label>
              <select value={envioForm.severidad} onChange={e => setEnvioForm(p=>({...p, severidad: e.target.value}))} style={styles.input}>
                <option value="critica">Critica</option>
                <option value="alta">Alta</option>
                <option value="media">Media</option>
                <option value="baja">Baja</option>
              </select>
            </div>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Canal</label>
              <select value={envioForm.canal} onChange={e => setEnvioForm(p=>({...p, canal: e.target.value}))} style={styles.input}>
                <option value="sistema">Sistema</option>
                <option value="push">Push</option>
                <option value="email">Email</option>
                <option value="sms">SMS</option>
              </select>
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <button type="submit" disabled={envioLoading} style={{ ...styles.submitBtn, width: 'auto', padding: '10px 28px' }}>
                {envioLoading ? 'Enviando...' : 'Enviar notificacion'}
              </button>
            </div>
          </form>
          {envioMsg && <div style={{ marginTop: '14px', fontSize: '13px', color: envioMsg.startsWith('✅') ? '#22c55e' : '#f87171' }}>{envioMsg}</div>}
        </div>
      )}

      {/* ── TAB: Preferencias ── */}
      {activeTab === 'preferencias' && (
        <div style={styles.formCard}>
          <div style={styles.sectionTitle}>Preferencias de notificacion</div>
          <p style={{ fontSize: '13px', color: '#6b7280', marginBottom: '20px' }}>
            Configura como y cuando quieres recibir alertas del sistema.
          </p>
          <form onSubmit={handleGuardarPrefs} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Canal preferido</label>
              <select value={prefs.canal_preferido} onChange={e => setPrefs(p=>({...p, canal_preferido: e.target.value}))} style={{ ...styles.input, maxWidth: '240px' }}>
                <option value="sistema">Sistema</option>
                <option value="push">Push</option>
                <option value="email">Email</option>
                <option value="sms">SMS</option>
              </select>
            </div>

            <div style={styles.prefsGrid}>
              {[
                { key: 'activo',           label: 'Notificaciones activas',       desc: 'Recibir notificaciones del sistema' },
                { key: 'alertas_criticas', label: 'Alertas criticas',             desc: 'Heladas, sequias extremas, fallos criticos' },
                { key: 'alertas_altas',    label: 'Alertas altas',                desc: 'Condiciones que requieren atencion pronta' },
                { key: 'alertas_medias',   label: 'Alertas medias',               desc: 'Condiciones a monitorear' },
                { key: 'alertas_bajas',    label: 'Alertas bajas',                desc: 'Informacion general del sistema' },
              ].map(item => (
                <div key={item.key} style={styles.prefItem} onClick={() => setPrefs(p => ({ ...p, [item.key]: !p[item.key] }))}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: '#f0fdf4' }}>{item.label}</div>
                    <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>{item.desc}</div>
                  </div>
                  <div style={{ ...styles.toggle, background: prefs[item.key] ? '#16a34a' : '#374151' }}>
                    <div style={{ ...styles.toggleThumb, transform: prefs[item.key] ? 'translateX(20px)' : 'translateX(2px)' }} />
                  </div>
                </div>
              ))}
            </div>

            <div>
              <button type="submit" disabled={prefsLoading} style={{ ...styles.submitBtn, width: 'auto', padding: '10px 28px' }}>
                {prefsLoading ? 'Guardando...' : 'Guardar preferencias'}
              </button>
            </div>
          </form>
          {prefsMsg && <div style={{ marginTop: '14px', fontSize: '13px', color: prefsMsg.startsWith('✅') ? '#22c55e' : '#f87171' }}>{prefsMsg}</div>}
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
  resumenGrid: { display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px', marginBottom: '20px' },
  resumenCard: { borderRadius: '12px', padding: '16px', border: '1px solid rgba(34,197,94,0.08)', textAlign: 'center' },
  resumenVal: { fontFamily: "'Syne', sans-serif", fontSize: '28px', fontWeight: 800, lineHeight: 1 },
  resumenLabel: { fontSize: '11px', color: '#6b7280', marginTop: '5px' },
  tabsBar: { display: 'flex', gap: '4px', marginBottom: '20px', background: '#0d1510', borderRadius: '10px', padding: '4px', border: '1px solid rgba(34,197,94,0.1)' },
  tabBtn: { flex: 1, padding: '8px', borderRadius: '7px', border: 'none', background: 'transparent', color: '#6b7280', fontSize: '12px', fontWeight: 500, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", transition: 'all 0.15s' },
  tabBtnActive: { background: 'rgba(34,197,94,0.15)', color: '#22c55e' },
  filters: { display: 'flex', gap: '12px', marginBottom: '20px', alignItems: 'flex-end', flexWrap: 'wrap' },
  filterItem: { display: 'flex', flexDirection: 'column', gap: '5px' },
  filterLabel: { fontSize: '11px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px' },
  select: { padding: '9px 14px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#9ca3af', fontSize: '13px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", minWidth: '180px' },
  countTag: { background: 'rgba(34,197,94,0.08)', color: '#4ade80', padding: '6px 12px', borderRadius: '20px', fontSize: '12px', border: '1px solid rgba(34,197,94,0.15)', alignSelf: 'flex-end' },
  notifList: { display: 'flex', flexDirection: 'column', gap: '10px' },
  notifCard: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', borderRadius: '12px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.08)', transition: 'opacity 0.3s' },
  notifLeft: { flex: 1 },
  notifTop: { display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '7px', flexWrap: 'wrap' },
  sevBadge: { padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 700, letterSpacing: '0.5px' },
  canalTag: { fontSize: '11px', color: '#6b7280', background: 'rgba(107,114,128,0.1)', padding: '2px 8px', borderRadius: '4px' },
  nuevaTag: { background: 'rgba(96,165,250,0.15)', color: '#60a5fa', padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 600, border: '1px solid rgba(96,165,250,0.25)' },
  notifTitulo: { fontSize: '13px', color: '#f0fdf4', fontWeight: 500, marginBottom: '5px', lineHeight: 1.4 },
  notifMeta: { display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap' },
  metaDot: { color: '#374151', fontSize: '11px' },
  metaItem: { fontSize: '11px', color: '#4b5563' },
  leerBtn: { marginLeft: '16px', padding: '7px 14px', background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '8px', color: '#22c55e', fontSize: '12px', cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", whiteSpace: 'nowrap' },
  sensorPanel: { display: 'flex', flexDirection: 'column', gap: '16px' },
  sectionTitle: { fontFamily: "'Syne', sans-serif", fontSize: '15px', fontWeight: 600, color: '#f0fdf4', marginBottom: '4px' },
  buscarRow: { display: 'flex', gap: '10px' },
  buscarInput: { flex: 1, padding: '10px 14px', background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#f0fdf4', fontSize: '13px', fontFamily: "'DM Sans', sans-serif" },
  formCard: { background: '#0d1510', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '16px', padding: '24px' },
  envioGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' },
  fieldGroup: { display: 'flex', flexDirection: 'column', gap: '5px' },
  label: { fontSize: '11px', fontWeight: 500, color: '#86efac', letterSpacing: '0.4px' },
  input: { padding: '9px 12px', background: 'rgba(6,12,7,0.8)', border: '1px solid rgba(34,197,94,0.15)', borderRadius: '8px', color: '#f0fdf4', fontSize: '13px', fontFamily: "'DM Sans', sans-serif" },
  submitBtn: { width: '100%', padding: '10px', background: 'linear-gradient(135deg, #16a34a, #15803d)', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', fontFamily: "'DM Sans', sans-serif" },
  prefsGrid: { display: 'flex', flexDirection: 'column', gap: '8px' },
  prefItem: { display: 'flex', alignItems: 'center', gap: '14px', padding: '12px 16px', background: 'rgba(6,12,7,0.6)', borderRadius: '10px', border: '1px solid rgba(34,197,94,0.08)', cursor: 'pointer', transition: 'border-color 0.15s' },
  toggle: { width: '44px', height: '24px', borderRadius: '12px', position: 'relative', transition: 'background 0.2s', flexShrink: 0 },
  toggleThumb: { position: 'absolute', top: '2px', width: '20px', height: '20px', borderRadius: '50%', background: '#fff', transition: 'transform 0.2s' },
  empty: { textAlign: 'center', padding: '80px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center' },
  emptyText: { fontSize: '18px', fontWeight: 600, color: '#f0fdf4', fontFamily: "'Syne', sans-serif", marginBottom: '6px' },
  emptySub: { fontSize: '13px', color: '#6b7280' },
}