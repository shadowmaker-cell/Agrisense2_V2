from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone, timedelta
from typing import Optional
import httpx
import os

from app.models.recomendacion import (
    CategoriaRecomendacion, Recomendacion,
    EvidenciaRecomendacion, EjecucionRecomendacion
)
from app.schemas.recomendacion import RecomendacionEntrada

ML_SERVICE_URL         = os.getenv("ML_SERVICE_URL",         "http://localhost:8006")
PROCESAMIENTO_SERVICE_URL = os.getenv("PROCESAMIENTO_SERVICE_URL", "http://localhost:8003")
PARCELAS_SERVICE_URL   = os.getenv("PARCELAS_SERVICE_URL",   "http://localhost:8005")

CATEGORIAS_DEFAULT = [
    { "nombre": "Riego",           "descripcion": "Recomendaciones sobre manejo del agua y riego",             "icono": "💧" },
    { "nombre": "Nutricion",       "descripcion": "Fertilizacion y nutricion del cultivo",                     "icono": "🌱" },
    { "nombre": "Proteccion",      "descripcion": "Control de plagas, enfermedades y condiciones adversas",    "icono": "🛡️" },
    { "nombre": "Clima",           "descripcion": "Alertas y acciones ante condiciones climaticas extremas",   "icono": "🌤️" },
    { "nombre": "Suelo",           "descripcion": "Manejo y mejoramiento del suelo agricola",                  "icono": "🪱" },
    { "nombre": "Cosecha",         "descripcion": "Planificacion y optimizacion de la cosecha",                "icono": "🌾" },
    { "nombre": "Infraestructura", "descripcion": "Mantenimiento de sensores y equipos de campo",              "icono": "🔧" },
]


def inicializar_categorias(db: Session):
    existentes = db.query(CategoriaRecomendacion).count()
    if existentes > 0:
        return
    for c in CATEGORIAS_DEFAULT:
        db.add(CategoriaRecomendacion(**c))
    db.commit()


def listar_categorias(db: Session) -> list:
    return db.query(CategoriaRecomendacion).filter(CategoriaRecomendacion.activo == True).all()


def _consultar_alertas(id_logico: str = None) -> list:
    try:
        url = f"{PROCESAMIENTO_SERVICE_URL}/api/v1/procesamiento/alertas"
        if id_logico:
            url = f"{PROCESAMIENTO_SERVICE_URL}/api/v1/procesamiento/alertas/{id_logico}"
        res = httpx.get(url, timeout=3.0)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []


def _consultar_ml_agua(data: dict) -> dict:
    try:
        res = httpx.post(
            f"{ML_SERVICE_URL}/api/v1/ml/predicciones/agua",
            json=data, timeout=10.0
        )
        if res.status_code == 201:
            return res.json()
    except Exception:
        pass
    return {}


def _consultar_ml_riesgo(data: dict, tipo_riesgo: str) -> dict:
    try:
        payload = {**data, "tipo_riesgo": tipo_riesgo}
        res = httpx.post(
            f"{ML_SERVICE_URL}/api/v1/ml/predicciones/riesgo",
            json=payload, timeout=10.0
        )
        if res.status_code == 201:
            return res.json()
    except Exception:
        pass
    return {}


def _obtener_categoria_id(db: Session, nombre: str) -> int:
    cat = db.query(CategoriaRecomendacion).filter(
        CategoriaRecomendacion.nombre == nombre
    ).first()
    return cat.id if cat else 1


def _crear_recomendacion(
    db: Session, categoria_nombre: str, titulo: str,
    descripcion: str, accion: str, prioridad: str,
    parcela_id: int = None, id_logico: str = None,
    fuente: str = "regla", datos_contexto: dict = None,
    evidencias: list = None, horas_valida: int = 24,
) -> Recomendacion:
    cat_id = _obtener_categoria_id(db, categoria_nombre)
    rec = Recomendacion(
        categoria_id=cat_id,
        parcela_id=parcela_id,
        id_logico=id_logico,
        titulo=titulo,
        descripcion=descripcion,
        accion=accion,
        prioridad=prioridad,
        fuente=fuente,
        datos_contexto=datos_contexto,
        valida_hasta=datetime.now(timezone.utc) + timedelta(hours=horas_valida),
    )
    db.add(rec)
    db.flush()

    if evidencias:
        for ev in evidencias:
            db.add(EvidenciaRecomendacion(
                recomendacion_id=rec.id,
                **ev
            ))
    return rec


def generar_recomendaciones(db: Session, data: dict) -> dict:
    """
    Motor principal de recomendaciones.
    Consulta alertas activas, predicciones ML y genera recomendaciones.
    """
    parcela_id   = data.get("parcela_id")
    id_logico    = data.get("id_logico")
    humedad      = data.get("humedad_suelo")
    temperatura  = data.get("temperatura_aire")
    ph           = data.get("ph_suelo")
    lluvia       = data.get("lluvia", 0)
    viento       = data.get("velocidad_viento", 0)
    hum_aire     = data.get("humedad_aire", 60)
    tipo_cultivo = data.get("tipo_cultivo", "maiz")
    area         = data.get("area_hectareas", 1.0)

    recomendaciones = []
    fuentes_consultadas = []

    # ── 1. Recomendaciones por humedad del suelo ──────
    if humedad is not None:
        if humedad < 20:
            pred_agua = _consultar_ml_agua({
                "humedad_suelo": humedad,
                "temperatura_aire": temperatura or 25,
                "lluvia": lluvia,
                "area_hectareas": area,
                "tipo_cultivo": tipo_cultivo,
            })
            fuentes_consultadas.append("ml_agua")
            litros = pred_agua.get("litros_recomendados", area * 400)
            rec = _crear_recomendacion(
                db, "Riego",
                titulo=f"Riego de emergencia — humedad critica ({humedad:.1f}%)",
                descripcion=f"El suelo presenta deficit hidrico severo con {humedad:.1f}% de humedad. El umbral critico es 20%.",
                accion=f"Aplicar riego inmediato de {litros:.0f} litros. Frecuencia: cada {pred_agua.get('frecuencia_horas', 6)} horas.",
                prioridad="critica",
                parcela_id=parcela_id, id_logico=id_logico,
                fuente="ml", datos_contexto=pred_agua,
                evidencias=[{
                    "tipo_fuente": "lectura",
                    "descripcion": "Humedad del suelo bajo umbral critico",
                    "valor_observado": humedad,
                    "valor_esperado": 40.0,
                    "unidad": "%",
                }],
                horas_valida=6,
            )
            recomendaciones.append(rec)

        elif humedad < 35:
            rec = _crear_recomendacion(
                db, "Riego",
                titulo=f"Riego preventivo recomendado ({humedad:.1f}% humedad)",
                descripcion=f"La humedad del suelo ({humedad:.1f}%) esta por debajo del rango optimo (40-80%).",
                accion="Programar riego en las proximas 12 horas para evitar estres hidrico.",
                prioridad="alta",
                parcela_id=parcela_id, id_logico=id_logico,
                fuente="regla",
                evidencias=[{
                    "tipo_fuente": "lectura",
                    "descripcion": "Humedad suelo baja",
                    "valor_observado": humedad,
                    "valor_esperado": 50.0,
                    "unidad": "%",
                }],
                horas_valida=12,
            )
            recomendaciones.append(rec)

        elif humedad > 85:
            pred_hongo = _consultar_ml_riesgo({
                "temperatura_aire": temperatura or 22,
                "humedad_aire":     hum_aire,
                "humedad_suelo":    humedad,
                "velocidad_viento": viento,
                "lluvia":           lluvia,
            }, "hongo")
            fuentes_consultadas.append("ml_riesgo_hongo")
            nivel = pred_hongo.get("nivel", "medio")
            prioridad = "critica" if nivel == "critico" else "alta" if nivel == "alto" else "media"
            rec = _crear_recomendacion(
                db, "Proteccion",
                titulo=f"Riesgo de hongos — exceso de humedad ({humedad:.1f}%)",
                descripcion=f"La humedad del suelo ({humedad:.1f}%) supera el umbral maximo. Riesgo de enfermedades fungicas: {nivel}.",
                accion="Suspender riego. Mejorar drenaje. Aplicar fungicida preventivo si el nivel es alto o critico.",
                prioridad=prioridad,
                parcela_id=parcela_id, id_logico=id_logico,
                fuente="ml", datos_contexto=pred_hongo,
                evidencias=[{
                    "tipo_fuente": "prediccion_ml",
                    "descripcion": f"Riesgo hongo nivel {nivel}",
                    "valor_observado": pred_hongo.get("probabilidad", 0),
                    "valor_esperado": 0.3,
                    "unidad": "probabilidad",
                }],
                horas_valida=24,
            )
            recomendaciones.append(rec)

    # ── 2. Recomendaciones por temperatura ───────────
    if temperatura is not None:
        if temperatura < 2:
            pred_helada = _consultar_ml_riesgo({
                "temperatura_aire": temperatura,
                "humedad_aire":     hum_aire,
                "humedad_suelo":    humedad or 50,
                "velocidad_viento": viento,
                "lluvia":           lluvia,
            }, "helada")
            fuentes_consultadas.append("ml_riesgo_helada")
            acciones_helada = pred_helada.get("acciones", ["Proteger cultivos con coberturas"])
            rec = _crear_recomendacion(
                db, "Clima",
                titulo=f"Alerta de helada — temperatura {temperatura:.1f}C",
                descripcion=f"Temperatura critica de {temperatura:.1f}C detectada. Riesgo de perdida del cultivo.",
                accion=" | ".join(acciones_helada),
                prioridad="critica",
                parcela_id=parcela_id, id_logico=id_logico,
                fuente="ml", datos_contexto=pred_helada,
                evidencias=[{
                    "tipo_fuente": "lectura",
                    "descripcion": "Temperatura bajo punto de congelacion",
                    "valor_observado": temperatura,
                    "valor_esperado": 10.0,
                    "unidad": "C",
                }],
                horas_valida=8,
            )
            recomendaciones.append(rec)

        elif temperatura > 36:
            rec = _crear_recomendacion(
                db, "Clima",
                titulo=f"Estres termico alto — {temperatura:.1f}C",
                descripcion=f"La temperatura ({temperatura:.1f}C) supera el umbral de estres termico para la mayoria de cultivos.",
                accion="Aumentar frecuencia de riego. Aplicar mulch para reducir temperatura del suelo. Considerar sombreo.",
                prioridad="alta",
                parcela_id=parcela_id, id_logico=id_logico,
                fuente="regla",
                evidencias=[{
                    "tipo_fuente": "lectura",
                    "descripcion": "Temperatura sobre umbral de estres",
                    "valor_observado": temperatura,
                    "valor_esperado": 30.0,
                    "unidad": "C",
                }],
                horas_valida=12,
            )
            recomendaciones.append(rec)

    # ── 3. Recomendaciones por pH ─────────────────────
    if ph is not None:
        if ph < 5.5:
            rec = _crear_recomendacion(
                db, "Suelo",
                titulo=f"Suelo acido — pH {ph:.1f}",
                descripcion=f"El pH del suelo ({ph:.1f}) esta bajo el rango optimo (5.5-7.5). Bloquea nutrientes esenciales.",
                accion="Aplicar cal dolomitica a razon de 1-2 ton/ha segun analisis de suelo. Repetir en 30 dias.",
                prioridad="alta",
                parcela_id=parcela_id, id_logico=id_logico,
                fuente="regla",
                evidencias=[{
                    "tipo_fuente": "lectura",
                    "descripcion": "pH suelo bajo rango optimo",
                    "valor_observado": ph,
                    "valor_esperado": 6.5,
                    "unidad": "pH",
                }],
                horas_valida=72,
            )
            recomendaciones.append(rec)

        elif ph > 7.5:
            rec = _crear_recomendacion(
                db, "Suelo",
                titulo=f"Suelo alcalino — pH {ph:.1f}",
                descripcion=f"El pH del suelo ({ph:.1f}) esta sobre el rango optimo. Reduce disponibilidad de micronutrientes.",
                accion="Aplicar azufre elemental o materia organica para reducir pH. Verificar agua de riego.",
                prioridad="media",
                parcela_id=parcela_id, id_logico=id_logico,
                fuente="regla",
                evidencias=[{
                    "tipo_fuente": "lectura",
                    "descripcion": "pH suelo sobre rango optimo",
                    "valor_observado": ph,
                    "valor_esperado": 6.5,
                    "unidad": "pH",
                }],
                horas_valida=72,
            )
            recomendaciones.append(rec)

    # ── 4. Recomendaciones por viento ─────────────────
    if viento is not None and viento > 40:
        rec = _crear_recomendacion(
            db, "Proteccion",
            titulo=f"Viento fuerte — {viento:.1f} km/h",
            descripcion=f"Velocidad del viento de {viento:.1f} km/h puede causar dano estructural a los cultivos.",
            accion="Instalar barreras cortavientos. Atar y reforzar plantas altas. Revisar estructuras de invernadero.",
            prioridad="alta" if viento < 60 else "critica",
            parcela_id=parcela_id, id_logico=id_logico,
            fuente="regla",
            evidencias=[{
                "tipo_fuente": "lectura",
                "descripcion": "Velocidad viento sobre umbral",
                "valor_observado": viento,
                "valor_esperado": 20.0,
                "unidad": "km/h",
            }],
            horas_valida=6,
        )
        recomendaciones.append(rec)

    # ── 5. Recomendacion general si no hay criticas ───
    if not recomendaciones:
        rec = _crear_recomendacion(
            db, "Riego",
            titulo="Condiciones del cultivo dentro de parametros normales",
            descripcion="Los valores de los sensores estan dentro de los rangos optimos para el cultivo.",
            accion="Continuar con el plan de monitoreo regular. Proxima revision en 24 horas.",
            prioridad="baja",
            parcela_id=parcela_id, id_logico=id_logico,
            fuente="regla",
            horas_valida=24,
        )
        recomendaciones.append(rec)

    db.commit()

    # Enriquecer con nombre de categoria
    for r in recomendaciones:
        db.refresh(r)
        if r.categoria:
            r.categoria_nombre = r.categoria.nombre

    # Registrar ejecucion
    ejecucion = EjecucionRecomendacion(
        parcela_id=parcela_id,
        id_logico=id_logico,
        total_recomendaciones=len(recomendaciones),
        criticas=sum(1 for r in recomendaciones if r.prioridad == "critica"),
        altas=sum(1 for r in recomendaciones if r.prioridad == "alta"),
        medias=sum(1 for r in recomendaciones if r.prioridad == "media"),
        bajas=sum(1 for r in recomendaciones if r.prioridad == "baja"),
        fuentes_consultadas=fuentes_consultadas,
    )
    db.add(ejecucion)
    db.commit()

    return {
        "total_generadas": len(recomendaciones),
        "criticas":        sum(1 for r in recomendaciones if r.prioridad == "critica"),
        "altas":           sum(1 for r in recomendaciones if r.prioridad == "alta"),
        "medias":          sum(1 for r in recomendaciones if r.prioridad == "media"),
        "bajas":           sum(1 for r in recomendaciones if r.prioridad == "baja"),
        "recomendaciones": recomendaciones,
        "ejecucion_id":    ejecucion.id,
    }


def listar_recomendaciones(
    db: Session,
    parcela_id: int = None,
    id_logico: str = None,
    prioridad: str = None,
    estado: str = None,
    limite: int = 50,
) -> list:
    query = db.query(Recomendacion).options(
        joinedload(Recomendacion.categoria),
        joinedload(Recomendacion.evidencias),
    )
    if parcela_id:
        query = query.filter(Recomendacion.parcela_id == parcela_id)
    if id_logico:
        query = query.filter(Recomendacion.id_logico == id_logico)
    if prioridad:
        query = query.filter(Recomendacion.prioridad == prioridad)
    if estado:
        query = query.filter(Recomendacion.estado == estado)
    recs = query.order_by(Recomendacion.generada_en.desc()).limit(limite).all()
    for r in recs:
        if r.categoria:
            r.categoria_nombre = r.categoria.nombre
    return recs


def obtener_recomendacion(db: Session, rec_id: int) -> Recomendacion:
    rec = db.query(Recomendacion).options(
        joinedload(Recomendacion.categoria),
        joinedload(Recomendacion.evidencias),
    ).filter(Recomendacion.id == rec_id).first()
    if rec and rec.categoria:
        rec.categoria_nombre = rec.categoria.nombre
    return rec


def actualizar_estado(db: Session, rec_id: int, estado: str) -> Recomendacion:
    rec = db.query(Recomendacion).filter(Recomendacion.id == rec_id).first()
    if not rec:
        return None
    rec.estado = estado
    db.commit()
    db.refresh(rec)
    return rec


def crear_recomendacion_manual(db: Session, data: RecomendacionEntrada) -> Recomendacion:
    data_dict = data.model_dump(exclude={"fuente"})
    rec = Recomendacion(
        **data_dict,
        fuente=data.fuente or "manual",
        valida_hasta=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    if rec.categoria:
        rec.categoria_nombre = rec.categoria.nombre
    return rec

def resumen_recomendaciones(db: Session) -> dict:
    total   = db.query(Recomendacion).count()
    activas = db.query(Recomendacion).filter(Recomendacion.estado == "activa").count()
    aplicadas = db.query(Recomendacion).filter(Recomendacion.estado == "aplicada").count()
    criticas = db.query(Recomendacion).filter(Recomendacion.prioridad == "critica").count()
    altas    = db.query(Recomendacion).filter(Recomendacion.prioridad == "alta").count()

    categorias = db.query(CategoriaRecomendacion).all()
    por_categoria = {}
    for cat in categorias:
        count = db.query(Recomendacion).filter(Recomendacion.categoria_id == cat.id).count()
        if count > 0:
            por_categoria[cat.nombre] = count

    ultima = db.query(EjecucionRecomendacion).order_by(
        EjecucionRecomendacion.ejecutado_en.desc()
    ).first()

    return {
        "total":            total,
        "activas":          activas,
        "aplicadas":        aplicadas,
        "criticas":         criticas,
        "altas":            altas,
        "por_categoria":    por_categoria,
        "ultima_generacion": ultima.ejecutado_en if ultima else None,
    }