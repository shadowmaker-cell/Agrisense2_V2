import axios from 'axios'

const BASE = '/api'
const api  = axios.create({ baseURL: BASE, timeout: 8000 })

// ── Device Management Service :8001 ──────────────────
export const dispositivosAPI = {
  health:       () => api.get('/dispositivos/health'),
  listarTipos:  () => api.get('/dispositivos/api/v1/dispositivos/tipos'),
  listar:       (skip=0, limit=50) => api.get(`/dispositivos/api/v1/dispositivos/?skip=${skip}&limit=${limit}`),
  obtener:      (id) => api.get(`/dispositivos/api/v1/dispositivos/${id}`),
  metricas:     (id) => api.get(`/dispositivos/api/v1/dispositivos/${id}/metricas`),
  registrar:    (data) => api.post('/dispositivos/api/v1/dispositivos/', data),
  actualizar:   (id, data) => api.put(`/dispositivos/api/v1/dispositivos/${id}`, data),
}

// ── IoT Ingestion Service :8002 ───────────────────────
export const ingestaAPI = {
  health:          () => api.get('/ingesta/health'),
  enviarLectura:   (data) => api.post('/ingesta/api/v1/telemetria/', data),
  enviarLote:      (lecturas) => api.post('/ingesta/api/v1/telemetria/lote', { lecturas }),
  ultimasLecturas: (id_logico, limite=20) => api.get(`/ingesta/api/v1/telemetria/ultimas/${id_logico}?limite=${limite}`),
  alertas:         (severidad) => api.get(`/ingesta/api/v1/telemetria/alertas${severidad ? `?severidad=${severidad}` : ''}`),
  alertasSensor:   (id_logico) => api.get(`/ingesta/api/v1/telemetria/alertas/${id_logico}`),
}

// ── Stream Processor Service :8003 ───────────────────
export const procesamientoAPI = {
  health:          () => api.get('/procesamiento/health'),
  procesarManual:  (data) => api.post('/procesamiento/api/v1/procesamiento/manual', data),
  eventos:         (con_alerta, limite=50) => api.get(`/procesamiento/api/v1/procesamiento/eventos?limite=${limite}${con_alerta !== undefined ? `&con_alerta=${con_alerta}` : ''}`),
  eventosSensor:   (id_logico, limite=20) => api.get(`/procesamiento/api/v1/procesamiento/eventos/${id_logico}?limite=${limite}`),
  alertas:         (severidad, tipo) => {
    let url = '/procesamiento/api/v1/procesamiento/alertas?limite=100'
    if (severidad) url += `&severidad=${severidad}`
    if (tipo)      url += `&tipo_alerta=${tipo}`
    return api.get(url)
  },
  alertasSensor:   (id_logico) => api.get(`/procesamiento/api/v1/procesamiento/alertas/${id_logico}`),
  resumen:         () => api.get('/procesamiento/api/v1/procesamiento/resumen'),
}

// ── Notification Service :8004 ───────────────────────
export const notificacionesAPI = {
  health:          () => api.get('/notificaciones/health'),
  listar:          (estado, severidad) => {
    let url = '/notificaciones/api/v1/notificaciones/?limite=100'
    if (estado)    url += `&estado=${estado}`
    if (severidad) url += `&severidad=${severidad}`
    return api.get(url)
  },
  obtener:         (id) => api.get(`/notificaciones/api/v1/notificaciones/${id}`),
  marcarLeida:     (id) => api.put(`/notificaciones/api/v1/notificaciones/${id}/leer`),
  porDispositivo:  (id_logico) => api.get(`/notificaciones/api/v1/notificaciones/dispositivo/${id_logico}`),
  resumen:         () => api.get('/notificaciones/api/v1/notificaciones/resumen/general'),
  enviar:          (data) => api.post('/notificaciones/api/v1/notificaciones/enviar', data),
  guardarPrefs:    (userId, data) => api.post(`/notificaciones/api/v1/notificaciones/preferencias/${userId}`, data),
}

export default api