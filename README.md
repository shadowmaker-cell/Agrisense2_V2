# AgriSense2 — Plataforma de Agricultura de Precision

Sistema IoT de monitoreo agricola en tiempo real con microservicios, Machine Learning y alertas automaticas.

Ingenieria de Sistemas · 2026

---

## Integrantes

| Nombre | Rol |
|---|---|
| Samuel Duran | Arquitectura, Backend, DevOps |
| Manuel Babilonia | Backend, Base de Datos |
| Jose Bello | Frontend, Integracion |
| Jeronimo Licona | ML, Procesamiento de Datos |

---

## Que es AgriSense2

AgriSense2 es una plataforma tecnologica disenada para optimizar la produccion agricola mediante sensores IoT, analisis de datos en tiempo real y modelos de Machine Learning. El sistema monitorea variables del cultivo como temperatura, humedad, radiacion solar y estado del suelo para generar alertas y recomendaciones automaticas para los agricultores.

### Problema que resuelve

La mayoria de los agricultores no disponen de sistemas que analicen datos del cultivo en tiempo real. Esto genera decisiones basadas en estimaciones y produce perdidas significativas por sequias, plagas o condiciones climaticas extremas no detectadas a tiempo.

### Solucion

Una plataforma con 8 microservicios independientes que procesan lecturas de sensores IoT, detectan condiciones criticas, generan alertas automaticas, envian notificaciones por email y producen recomendaciones agronomicas personalizadas.

---

## Arquitectura del Sistema

```
+-------------------------------------------------------------+
|                    FRONTEND (Vercel)                        |
|              React 18 + Vite + Leaflet                      |
|          https://agrisense2-v2.vercel.app                   |
+--------------------+----------------------------------------+
                     | /api/* -> rewrites
+--------------------v----------------------------------------+
|                 API GATEWAY (Render)                        |
|                    nginx :8000                              |
|         https://agrisense-gateway.onrender.com              |
+--+------+------+------+------+------+------+------+--------+
   |      |      |      |      |      |      |      |
   v      v      v      v      v      v      v      v
 Auth  Disp  Inge  Proc  Noti  Parc   ML   Reco
:8008 :8001 :8002 :8003 :8004 :8005 :8006 :8007
   |      |      |      |      |      |      |      |
   +------+------+------+------+------+------+------+
                         |
              +----------v----------+
              |   Neon PostgreSQL   |
              |  8 bases de datos   |
              |  independientes     |
              +---------------------+
```

### Flujo de datos

```
Sensor IoT -> Ingesta -> Procesamiento -> Alerta detectada?
                                                |
                           +--------------------+--------------------+
                           v                    v                    v
                     Notificacion         Recomendacion          Registro
                     (Email SMTP)         (Automatica)           (Dashboard)
```

---

## Microservicios

### 1. servicio_auth — Autenticacion :8008

Gestiona el registro, login y tokens JWT de los usuarios. Implementa refresh tokens para sesiones seguras.

Endpoints principales:
- `POST /api/v1/auth/registro` — Crear cuenta
- `POST /api/v1/auth/login` — Iniciar sesion
- `POST /api/v1/auth/refresh` — Renovar token
- `GET /api/v1/usuarios/me` — Perfil del usuario

---

### 2. servicio_dispositivos — Gestion de Sensores :8001

Administra el inventario completo de 37 tipos de dispositivos IoT, incluyendo sensores de suelo, clima, agua, actuadores y equipos de energia. Incluye modulo de mantenimiento con historial correctivo/preventivo y hoja de vida por sensor.

Taxonomia de dispositivos (37 tipos):
- Suelo: Humedad tensiometrico, Sonda dual, NPK, Multiparametrica, pH, EC, Temperatura
- Clima: Termo-higrometro, Luxometro, Anemometro, Pluviometro
- Agua: Caudalimetro, Nivel de tanque, Calidad pH/ORP
- Planta: Dendrometro, Humedad foliar
- Actuadores: Electrovalvulas, Bombas, Ventiladores, Calefactores, Lamparas UV
- Computacion: Microcontroladores, PLCs, Servidores, Routers, Camaras
- Energia: Paneles solares, Inversores, Baterias, UPS, Plantas electricas

Endpoints principales:
- `GET /api/v1/dispositivos/tipos` — Taxonomia completa
- `POST /api/v1/dispositivos/` — Registrar sensor
- `PUT /api/v1/dispositivos/{id}` — Actualizar configuracion y limites
- `POST /api/v1/dispositivos/{id}/mantenimiento` — Registrar mantenimiento
- `GET /api/v1/dispositivos/{id}/hoja-de-vida` — Historial completo

---

### 3. servicio_ingesta — Ingesta IoT :8002

Recibe y almacena lecturas de sensores en TimescaleDB (serie temporal). Soporta envio individual y por lotes. Expone promedios por ventana temporal y exportacion a Excel.

Endpoints principales:
- `POST /api/v1/telemetria/` — Enviar lectura
- `POST /api/v1/telemetria/lote` — Envio masivo
- `GET /api/v1/telemetria/ultimas/{id}` — Ultimas lecturas
- `GET /api/v1/telemetria/promedios/{id}` — Promedios por ventana temporal
- `GET /api/v1/telemetria/export/{id}/excel` — Exportar a Excel

---

### 4. servicio_procesamiento — Procesamiento y Alertas :8003

Motor de reglas de negocio que evalua cada lectura contra umbrales definidos para los 37 tipos de sensores. Soporta limites personalizados por sensor configurados por el usuario, los cuales tienen prioridad sobre las reglas globales.

Logica de alertas:
1. Si el sensor tiene limite_minimo o limite_maximo configurados, aplica los limites del usuario.
2. Si no tiene limites personalizados, aplica las reglas globales del catalogo.

Endpoints principales:
- `POST /api/v1/procesamiento/manual` — Procesar lectura manualmente
- `GET /api/v1/procesamiento/alertas` — Listar alertas generadas
- `GET /api/v1/procesamiento/resumen` — Estadisticas del procesamiento

---

### 5. servicio_notificaciones — Notificaciones :8004

Envia alertas por email usando Gmail SMTP cuando el procesamiento detecta condiciones criticas. Registra historial de notificaciones por usuario y dispositivo.

Endpoints principales:
- `POST /api/v1/notificaciones/enviar` — Enviar notificacion
- `GET /api/v1/notificaciones/` — Historial de notificaciones
- `PUT /api/v1/notificaciones/{id}/leer` — Marcar como leida

---

### 6. servicio_parcelas — Gestion Geoespacial :8005

Gestiona parcelas agricolas con ubicacion GPS, tipos de cultivo e historial fenologico. Permite asignar sensores a parcelas y visualizarlos en mapa Leaflet.

Endpoints principales:
- `POST /api/v1/parcelas/` — Crear parcela
- `GET /api/v1/parcelas/` — Listar parcelas
- `POST /api/v1/parcelas/{id}/sensores` — Asignar sensor a parcela
- `GET /api/v1/parcelas/{id}/sensores` — Ver sensores de una parcela
- `GET /api/v1/parcelas/{id}/historial` — Historial de cultivo

---

### 7. servicio_ml — Machine Learning :8006

Sirve modelos de prediccion para requerimientos hidricos, rendimiento de cosecha y riesgos como heladas, hongos y sequias. Los modelos consumen lecturas historicas de TimescaleDB.

Endpoints principales:
- `POST /api/v1/ml/predicciones/agua` — Prediccion de riego
- `POST /api/v1/ml/predicciones/rendimiento` — Prediccion de cosecha
- `POST /api/v1/ml/predicciones/riesgo` — Prediccion de riesgo
- `GET /api/v1/ml/modelos` — Modelos activos

---

### 8. servicio_recomendaciones — Motor de Recomendaciones :8007

Genera recomendaciones agronomicas personalizadas por parcela y sensor. Se activa automaticamente cuando el procesamiento detecta una alerta, sin intervencion del usuario. Combina datos de sensores con predicciones del ML Service.

Categorias de recomendaciones: Riego, Nutricion, Proteccion, Clima, Suelo, Cosecha, Infraestructura.

Endpoints principales:
- `POST /api/v1/recomendaciones/desde-alerta` — Generacion automatica desde alerta
- `POST /api/v1/recomendaciones/generar` — Generacion manual
- `GET /api/v1/recomendaciones/activas` — Recomendaciones vigentes
- `GET /api/v1/recomendaciones/resumen` — Estadisticas

---

## Frontend

Desarrollado con React 18 + Vite. Interfaz responsive con tema oscuro y paleta verde agricola.

### Vistas principales

| Vista | Descripcion |
|---|---|
| Dashboard | KPIs animados, grafica de actividad, mapa Leaflet, clima Open-Meteo, estado de microservicios |
| Dispositivos | Registro de sensores con taxonomia completa, tabs Info/Editar/Mantenimiento/Hoja de Vida |
| Lecturas | Monitor en tiempo real con auto-refresco cada 10 segundos, tabs Tiempo Real/Promedios/Alertas |
| Parcelas | Mapa interactivo Leaflet centrado en Monteria, creacion de parcelas haciendo clic en el mapa |
| Recomendaciones | Listado de recomendaciones activas generadas automaticamente por el sistema |
| Notificaciones | Historial de alertas enviadas por email |
| ML | Predicciones de cosecha y riesgo |
| Perfil | Configuracion de cuenta del usuario |

---

## Stack Tecnologico

### Backend

| Tecnologia | Uso |
|---|---|
| Python 3.11 | Lenguaje principal |
| FastAPI | Framework REST de alto rendimiento |
| SQLAlchemy + Alembic | ORM y migraciones de base de datos |
| PostgreSQL / TimescaleDB | Base de datos relacional y series temporales |
| httpx | Comunicacion HTTP entre microservicios |
| python-jose | Generacion y validacion de tokens JWT |
| smtplib | Envio de emails via SMTP |
| scikit-learn | Modelos de Machine Learning |

### Frontend

| Tecnologia | Uso |
|---|---|
| React 18 | Framework de interfaz de usuario |
| Vite | Bundler y servidor de desarrollo |
| Axios | Cliente HTTP para llamadas a la API |
| react-leaflet 4.2.1 | Mapas interactivos con coordenadas GPS |
| Open-Meteo API | Datos climaticos en tiempo real |

### Infraestructura

| Servicio | Uso |
|---|---|
| Render | Despliegue de los 8 microservicios y el gateway |
| Vercel | Despliegue del frontend |
| Neon PostgreSQL | 8 bases de datos independientes en la nube |
| nginx | API Gateway con enrutamiento y proxy inverso |
| Docker | Contenerizacion de todos los servicios |
| GitHub Actions | Integracion y despliegue continuo |

---

## Despliegue

### URLs de Produccion

| Servicio | URL |
|---|---|
| Frontend | https://agrisense2-v2.vercel.app |
| API Gateway | https://agrisense-gateway.onrender.com |
| Auth | https://agrisense-auth.onrender.com |
| Dispositivos | https://agrisense-dispositivos.onrender.com |
| Ingesta | https://agrisense-ingesta.onrender.com |
| Procesamiento | https://agrisense-procesamiento.onrender.com |
| Notificaciones | https://agrisense-notificaciones.onrender.com |
| Parcelas | https://agrisense-parcelas.onrender.com |
| ML | https://agrisense-ml.onrender.com |
| Recomendaciones | https://agrisense-recomendaciones.onrender.com |

### Estructura del repositorio

```
Agrisense2_V2/
├── nginx/                    -- API Gateway
│   ├── Dockerfile
│   └── nginx.conf
├── servicio_auth/            -- Autenticacion
├── servicio_dispositivos/    -- Gestion de sensores
├── servicio_ingesta/         -- Ingesta IoT (TimescaleDB)
├── servicio_procesamiento/   -- Motor de alertas
├── servicio_notificaciones/  -- Notificaciones por email
├── servicio_parcelas/        -- Gestion geoespacial
├── servicio_ml/              -- Machine Learning
├── servicio_recomendaciones/ -- Motor de recomendaciones
├── frontend/                 -- React 18 + Vite
│   ├── src/
│   │   ├── components/       -- Vistas principales
│   │   ├── api/client.js     -- Cliente HTTP centralizado
│   │   └── App.jsx
│   └── vercel.json           -- Rewrites al gateway
├── simulador_iot.py          -- Simulador de sensores IoT
├── keepalive.py              -- Mantiene servicios Render activos
├── render.yaml               -- Blueprint de despliegue en Render
└── docker-compose.yml        -- Entorno local completo
```

---

## Desarrollo Local

### Requisitos

- Docker Desktop
- Python 3.11 o superior
- Node.js 20 o superior

### Levantar el sistema completo

```bash
git clone https://github.com/shadowmaker-cell/Agrisense2_V2.git
cd Agrisense2_V2

docker compose up --build
```

El frontend queda disponible en http://localhost:5173 y el API Gateway en http://localhost:8000.

### Simular lecturas IoT

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows
source .venv/bin/activate       # Linux/Mac

pip install requests

python simulador_iot.py
```

El simulador hace login con las credenciales del usuario, detecta automaticamente todos los sensores activos registrados, genera lecturas realistas respetando los limites personalizados de cada sensor, envia cada lectura a ingesta y procesamiento, y si hay alertas envia email y genera una recomendacion automatica.

---

## Flujo Completo del Sistema

```
1. Usuario registra sensores con limites personalizados desde el frontend.
2. El simulador IoT detecta los sensores activos y envia lecturas cada N segundos.
3. servicio_ingesta almacena cada lectura en TimescaleDB.
4. servicio_procesamiento evalua la lectura:
   - Si el sensor tiene limites personalizados, los aplica.
   - Si no, aplica las reglas globales por tipo de sensor.
5. Si se detecta una alerta:
   - servicio_notificaciones envia un email al usuario.
   - servicio_recomendaciones genera una recomendacion automatica.
6. El frontend muestra todo en tiempo real con auto-refresco cada 10 segundos.
```

---

## Modulo de Mantenimiento

Cada sensor tiene una hoja de vida completa que incluye historial de cambios de estado, historial de despliegues con ubicacion y fechas, y registros de mantenimiento con los siguientes campos: tipo (correctivo, preventivo, calibracion, inspeccion), causa del mantenimiento, acciones realizadas, resultado, tecnico responsable, costo, fecha de inicio, fecha de fin y proxima revision programada. El mantenimiento de tipo correctivo cambia el estado del sensor automaticamente a mantenimiento. La hoja de vida completa se puede exportar como PDF listo para imprimir.

---

## Seguridad

- Autenticacion JWT con refresh tokens
- Multi-tenancy: cada usuario solo ve sus propios datos
- Variables de entorno para secretos, nunca en el codigo fuente
- HTTPS obligatorio en todos los endpoints de produccion
- CORS configurado solo para dominios autorizados
- Rate limiting en el API Gateway

---

## Observabilidad

- Health check en /health de cada microservicio
- Dashboard de estado de servicios en el frontend
- Logs estructurados en cada servicio
- keepalive.py hace ping cada 10 minutos para mantener los servicios activos en el plan gratuito de Render

---

## Por que Microservicios

| Aspecto | Beneficio en AgriSense2 |
|---|---|
| Escalabilidad selectiva | Ingesta y procesamiento pueden escalar independientemente del resto |
| Independencia de despliegue | Cada servicio se actualiza sin afectar a los demas |
| Tecnologia especializada | TimescaleDB para series temporales, scikit-learn para ML |
| Tolerancia a fallos | Un servicio caido no tumba el sistema completo |
| Base de datos por servicio | Sin acoplamiento de datos entre dominios funcionales |

---

AgriSense2 — Plataforma de Agricultura de Precision · Ingenieria de Sistemas 2026
