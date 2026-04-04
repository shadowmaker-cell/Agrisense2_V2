import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Device Management Service :8001 ──────────────────
export const dispositivosAPI = {
  health:      () => api.get('/dispositivos/health'),
  listar:      (skip = 0, limit = 100) => api.get(`/dispositivos/api/v1/dispositivos/?skip=${skip}&limit=${limit}`),
  obtener:     (id) => api.get(`/dispositivos/api/v1/dispositivos/${id}`),
  listarTipos: () => api.get('/dispositivos/api/v1/dispositivos/tipos'),
  metricas:    (id) => api.get(`/dispositivos/api/v1/dispositivos/${id}/metricas`),
  registrar:   (data) => api.post('/dispositivos/api/v1/dispositivos/', data),
  actualizar:  (id, data) => api.put(`/dispositivos/api/v1/dispositivos/${id}`, data),
  hojaVida:    (id) => api.get(`/dispositivos/api/v1/dispositivos/${id}/hoja-de-vida`),
}
// ── IoT Ingestion Service :8002 ───────────────────────
export const ingestaAPI = {
  health:         () => api.get('/ingesta/health'),
  enviarLectura:  (data) => api.post('/ingesta/api/v1/telemetria/', data),
  enviarLote:     (data) => api.post('/ingesta/api/v1/telemetria/lote', data),
  ultimasLecturas:(id, limite = 10) => api.get(`/ingesta/api/v1/telemetria/ultimas/${id}?limite=${limite}`),
  alertas:        (severidad) => api.get(`/ingesta/api/v1/telemetria/alertas${severidad ? '?severidad=' + severidad : ''}`),
  alertasSensor:  (id) => api.get(`/ingesta/api/v1/telemetria/alertas/${id}`),
}

// ── Stream Processor Service :8003 ───────────────────
export const procesamientoAPI = {
  health:         () => api.get('/procesamiento/health'),
  procesarManual: (data) => api.post('/procesamiento/api/v1/procesamiento/manual', data),
  eventos:        (id, limite = 20) => api.get(`/procesamiento/api/v1/procesamiento/eventos${id ? '/' + id : ''}?limite=${limite}`),
  alertas:        (severidad, tipo) => api.get(`/procesamiento/api/v1/procesamiento/alertas${severidad || tipo ? '?' + (severidad ? 'severidad=' + severidad : '') + (tipo ? '&tipo_alerta=' + tipo : '') : ''}`),
  alertasSensor:  (id) => api.get(`/procesamiento/api/v1/procesamiento/alertas/${id}`),
  resumen:        () => api.get('/procesamiento/api/v1/procesamiento/resumen'),
}

// ── Notification Service :8004 ────────────────────────
export const notificacionesAPI = {
  health:       () => api.get('/notificaciones/health'),
  listar:       (estado, severidad) => api.get(`/notificaciones/api/v1/notificaciones/${estado || severidad ? '?' + (estado ? 'estado=' + estado : '') + (severidad ? '&severidad=' + severidad : '') : ''}`),
  obtener:      (id) => api.get(`/notificaciones/api/v1/notificaciones/${id}`),
  marcarLeida:  (id) => api.put(`/notificaciones/api/v1/notificaciones/${id}/leer`),
  porDispositivo:(id) => api.get(`/notificaciones/api/v1/notificaciones/dispositivo/${id}`),
  resumen:      () => api.get('/notificaciones/api/v1/notificaciones/resumen/general'),
  enviar:       (data) => api.post('/notificaciones/api/v1/notificaciones/enviar', data),
  guardarPrefs: (userId, data) => api.post(`/notificaciones/api/v1/notificaciones/preferencias/${userId}`, data),
}

// ── Parcel Management Service :8005 ──────────────────
export const parcelasAPI = {
  health:          () => api.get('/parcelas/health'),
  listar:          (estado) => api.get(`/parcelas/api/v1/parcelas/${estado ? '?estado=' + estado : ''}`),
  obtener:         (id) => api.get(`/parcelas/api/v1/parcelas/${id}`),
  crear:           (data) => api.post('/parcelas/api/v1/parcelas/', data),
  actualizar:      (id, data) => api.put(`/parcelas/api/v1/parcelas/${id}`, data),
  eliminar:        (id) => api.delete(`/parcelas/api/v1/parcelas/${id}`),
  resumen:         () => api.get('/parcelas/api/v1/parcelas/resumen'),
  tiposCultivo:    () => api.get('/parcelas/api/v1/parcelas/tipos-cultivo'),
  asignarSensor:   (id, data) => api.post(`/parcelas/api/v1/parcelas/${id}/sensores`, data),
  sensores:        (id) => api.get(`/parcelas/api/v1/parcelas/${id}/sensores`),
  desasignarSensor:(id, sensorId) => api.delete(`/parcelas/api/v1/parcelas/${id}/sensores/${sensorId}`),
  historial:       (id) => api.get(`/parcelas/api/v1/parcelas/${id}/historial`),
  agregarHistorial:(id, data) => api.post(`/parcelas/api/v1/parcelas/${id}/historial`, data),
  actualizarHistorial:(id, histId, data) => api.put(`/parcelas/api/v1/parcelas/${id}/historial/${histId}`, data),
}

// ── ML Prediction Service :8006 ───────────────────────
export const mlAPI = {
  health:              () => api.get('/ml/health'),
  modelos:             () => api.get('/ml/api/v1/ml/modelos'),
  resumen:             () => api.get('/ml/api/v1/ml/resumen'),
  predecirAgua:        (data) => api.post('/ml/api/v1/ml/predicciones/agua', data),
  predecirRendimiento: (data) => api.post('/ml/api/v1/ml/predicciones/rendimiento', data),
  predecirRiesgo:      (data) => api.post('/ml/api/v1/ml/predicciones/riesgo', data),
  historial:           (tipo) => api.get(`/ml/api/v1/ml/predicciones${tipo ? '?tipo=' + tipo : ''}`),
  resultado:           (id) => api.get(`/ml/api/v1/ml/predicciones/${id}/resultado`),
}

// ── Recommendation Engine :8007 ───────────────────────
export const recomendacionesAPI = {
  health:     () => api.get('/recomendaciones/health'),
  categorias: () => api.get('/recomendaciones/api/v1/recomendaciones/categorias'),
  generar:    (data) => api.post('/recomendaciones/api/v1/recomendaciones/generar', data),
  listar:     (params) => api.get('/recomendaciones/api/v1/recomendaciones/', { params }),
  activas:    (parcela_id) => api.get(`/recomendaciones/api/v1/recomendaciones/activas${parcela_id ? '?parcela_id=' + parcela_id : ''}`),
  obtener:    (id) => api.get(`/recomendaciones/api/v1/recomendaciones/${id}`),
  crear:      (data) => api.post('/recomendaciones/api/v1/recomendaciones/', data),
  actualizarEstado: (id, estado) => api.put(`/recomendaciones/api/v1/recomendaciones/${id}/estado`, { estado }),
  porParcela: (id) => api.get(`/recomendaciones/api/v1/recomendaciones/parcela/${id}`),
  porSensor:  (id) => api.get(`/recomendaciones/api/v1/recomendaciones/sensor/${id}`),
  resumen:    () => api.get('/recomendaciones/api/v1/recomendaciones/resumen'),
}