import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── Auth :8008 ────────────────────────────────────────
export const authAPI = {
  registro:           (data) => api.post('/auth/api/v1/auth/registro', data),
  login:              (data) => api.post('/auth/api/v1/auth/login', data),
  refresh:            (data) => api.post('/auth/api/v1/auth/refresh', data),
  logout:             (data) => api.post('/auth/api/v1/auth/logout', data),
  verificar:          ()     => api.get('/auth/api/v1/auth/verificar'),
  cambiarPassword:    (data) => api.put('/auth/api/v1/auth/cambiar-password', data),
  me:                 ()     => api.get('/auth/api/v1/usuarios/me'),
  actualizarMe:       (data) => api.put('/auth/api/v1/usuarios/me', data),
  miPerfil:           ()     => api.get('/auth/api/v1/usuarios/me/perfil'),
  actualizarMiPerfil: (data) => api.put('/auth/api/v1/usuarios/me/perfil', data),
}

// ── Dispositivos :8001 ────────────────────────────────
export const dispositivosAPI = {
  health:      ()              => api.get('/dispositivos/health'),
  listar:      (skip=0,limit=100) => api.get(`/dispositivos/api/v1/dispositivos/?skip=${skip}&limit=${limit}`),
  obtener:     (id)            => api.get(`/dispositivos/api/v1/dispositivos/${id}`),
  listarTipos: ()              => api.get('/dispositivos/api/v1/dispositivos/tipos'),
  metricas:    (id)            => api.get(`/dispositivos/api/v1/dispositivos/${id}/metricas`),
  registrar:   (data)          => api.post('/dispositivos/api/v1/dispositivos/', data),
  actualizar:  (id, data)      => api.put(`/dispositivos/api/v1/dispositivos/${id}`, data),
  hojaVida:    (id)            => api.get(`/dispositivos/api/v1/dispositivos/${id}/hoja-de-vida`),
}

// ── Ingesta :8002 ─────────────────────────────────────
export const ingestaAPI = {
  health:          ()              => api.get('/ingesta/health'),
  enviarLectura:   (data)          => api.post('/ingesta/api/v1/telemetria/', data),
  enviarLote:      (data)          => api.post('/ingesta/api/v1/telemetria/lote', data),
  ultimasLecturas: (id, limite=10) => api.get(`/ingesta/api/v1/telemetria/ultimas/${id}?limite=${limite}`),
  alertas:         (severidad)     => api.get(`/ingesta/api/v1/telemetria/alertas${severidad ? '?severidad='+severidad : ''}`),
  alertasSensor:   (id)            => api.get(`/ingesta/api/v1/telemetria/alertas/${id}`),
  promedios:       (id, ventana='1h') => api.get(`/ingesta/api/v1/telemetria/promedios/${id}?ventana=${ventana}`),
  exportExcel:     (id, dias=7)    => api.get(`/ingesta/api/v1/telemetria/export/${id}/excel?dias=${dias}`, { responseType: 'blob' }),
}

// ── Procesamiento :8003 ───────────────────────────────
export const procesamientoAPI = {
  health:         ()           => api.get('/procesamiento/health'),
  procesarManual: (data)       => api.post('/procesamiento/api/v1/procesamiento/manual', data),
  eventos:        (id, lim=20) => api.get(`/procesamiento/api/v1/procesamiento/eventos${id ? '/'+id : ''}?limite=${lim}`),
  alertas:        (sev, tipo)  => api.get(`/procesamiento/api/v1/procesamiento/alertas${sev||tipo ? '?'+(sev?'severidad='+sev:'')+(tipo?'&tipo_alerta='+tipo:'') : ''}`),
  alertasSensor:  (id)         => api.get(`/procesamiento/api/v1/procesamiento/alertas/${id}`),
  resumen:        ()           => api.get('/procesamiento/api/v1/procesamiento/resumen'),
}

// ── Notificaciones :8004 ──────────────────────────────
export const notificacionesAPI = {
  health:         ()           => api.get('/notificaciones/health'),
  listar:         (est, sev)   => api.get(`/notificaciones/api/v1/notificaciones/${est||sev ? '?'+(est?'estado='+est:'')+(sev?'&severidad='+sev:'') : ''}`),
  obtener:        (id)         => api.get(`/notificaciones/api/v1/notificaciones/${id}`),
  marcarLeida:    (id)         => api.put(`/notificaciones/api/v1/notificaciones/${id}/leer`),
  porDispositivo: (id)         => api.get(`/notificaciones/api/v1/notificaciones/dispositivo/${id}`),
  resumen:        ()           => api.get('/notificaciones/api/v1/notificaciones/resumen/general'),
  enviar:         (data)       => api.post('/notificaciones/api/v1/notificaciones/enviar', data),
  guardarPrefs:   (uid, data)  => api.post(`/notificaciones/api/v1/notificaciones/preferencias/${uid}`, data),
}

// ── Parcelas :8005 ────────────────────────────────────
export const parcelasAPI = {
  health:              ()           => api.get('/parcelas/health'),
  listar:              (estado)     => api.get(`/parcelas/api/v1/parcelas/${estado ? '?estado='+estado : ''}`),
  obtener:             (id)         => api.get(`/parcelas/api/v1/parcelas/${id}`),
  crear:               (data)       => api.post('/parcelas/api/v1/parcelas/', data),
  actualizar:          (id, data)   => api.put(`/parcelas/api/v1/parcelas/${id}`, data),
  eliminar:            (id)         => api.delete(`/parcelas/api/v1/parcelas/${id}`),
  resumen:             ()           => api.get('/parcelas/api/v1/parcelas/resumen'),
  tiposCultivo:        ()           => api.get('/parcelas/api/v1/parcelas/tipos-cultivo'),
  asignarSensor:       (id, data)   => api.post(`/parcelas/api/v1/parcelas/${id}/sensores`, data),
  sensores:            (id)         => api.get(`/parcelas/api/v1/parcelas/${id}/sensores`),
  desasignarSensor:    (id, sid)    => api.delete(`/parcelas/api/v1/parcelas/${id}/sensores/${sid}`),
  historial:           (id)         => api.get(`/parcelas/api/v1/parcelas/${id}/historial`),
  agregarHistorial:    (id, data)   => api.post(`/parcelas/api/v1/parcelas/${id}/historial`, data),
  actualizarHistorial: (id, hid, d) => api.put(`/parcelas/api/v1/parcelas/${id}/historial/${hid}`, d),
}

// ── ML :8006 ──────────────────────────────────────────
export const mlAPI = {
  health:              ()      => api.get('/ml/health'),
  modelos:             ()      => api.get('/ml/api/v1/ml/modelos'),
  resumen:             ()      => api.get('/ml/api/v1/ml/resumen'),
  predecirAgua:        (data)  => api.post('/ml/api/v1/ml/predicciones/agua', data),
  predecirRendimiento: (data)  => api.post('/ml/api/v1/ml/predicciones/rendimiento', data),
  predecirRiesgo:      (data)  => api.post('/ml/api/v1/ml/predicciones/riesgo', data),
  historial:           (tipo)  => api.get(`/ml/api/v1/ml/predicciones${tipo ? '?tipo='+tipo : ''}`),
  resultado:           (id)    => api.get(`/ml/api/v1/ml/predicciones/${id}/resultado`),
}

// ── Recomendaciones :8007 ─────────────────────────────
export const recomendacionesAPI = {
  health:           ()          => api.get('/recomendaciones/health'),
  categorias:       ()          => api.get('/recomendaciones/api/v1/recomendaciones/categorias'),
  generar:          (data)      => api.post('/recomendaciones/api/v1/recomendaciones/generar', data),
  listar:           (params)    => api.get('/recomendaciones/api/v1/recomendaciones/', { params }),
  activas:          (pid)       => api.get(`/recomendaciones/api/v1/recomendaciones/activas${pid ? '?parcela_id='+pid : ''}`),
  obtener:          (id)        => api.get(`/recomendaciones/api/v1/recomendaciones/${id}`),
  crear:            (data)      => api.post('/recomendaciones/api/v1/recomendaciones/', data),
  actualizarEstado: (id, est)   => api.put(`/recomendaciones/api/v1/recomendaciones/${id}/estado`, { estado: est }),
  porParcela:       (id)        => api.get(`/recomendaciones/api/v1/recomendaciones/parcela/${id}`),
  porSensor:        (id)        => api.get(`/recomendaciones/api/v1/recomendaciones/sensor/${id}`),
  resumen:          ()          => api.get('/recomendaciones/api/v1/recomendaciones/resumen'),
}