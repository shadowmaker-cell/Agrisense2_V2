from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.prediccion import (
    ModeloRegistro, SolicitudPrediccion, ResultadoPrediccion, HistorialMetrica
)
from app.ml.modelos import predecir_agua, predecir_rendimiento, predecir_riesgo

MODELOS_DEFAULT = [
    {
        "nombre":          "AgriSense Water Predictor",
        "version":         "1.0.0",
        "tipo":            "agua",
        "descripcion":     "Predice los litros de agua necesarios por parcela",
        "variable_target": "litros_recomendados",
        "features":        ["humedad_suelo","temperatura_aire","lluvia","area_hectareas","tipo_cultivo"],
        "metricas":        {"mae": 12.3, "rmse": 18.7, "r2": 0.87},
        "estado":          "activo",
    },
    {
        "nombre":          "AgriSense Yield Predictor",
        "version":         "1.0.0",
        "tipo":            "rendimiento",
        "descripcion":     "Predice el rendimiento esperado en kg/ha",
        "variable_target": "rendimiento_kg_ha",
        "features":        ["area_hectareas","humedad_suelo","temperatura_aire","ph_suelo","lluvia_acumulada"],
        "metricas":        {"mae": 320.5, "rmse": 480.2, "r2": 0.82},
        "estado":          "activo",
    },
    {
        "nombre":          "AgriSense Risk Classifier",
        "version":         "1.0.0",
        "tipo":            "riesgo",
        "descripcion":     "Clasifica el nivel de riesgo agronomico",
        "variable_target": "nivel_riesgo",
        "features":        ["temperatura_aire","humedad_aire","humedad_suelo","velocidad_viento","lluvia"],
        "metricas":        {"accuracy": 0.89, "f1_score": 0.86},
        "estado":          "activo",
    },
]


def inicializar_modelos(db: Session):
    if db.query(ModeloRegistro).count() > 0:
        return
    for m in MODELOS_DEFAULT:
        db.add(ModeloRegistro(**m))
    db.commit()


def listar_modelos(db: Session) -> list:
    return db.query(ModeloRegistro).filter(ModeloRegistro.estado == "activo").all()


def obtener_modelo(db: Session, modelo_id: int) -> ModeloRegistro:
    return db.query(ModeloRegistro).filter(ModeloRegistro.id == modelo_id).first()


def _crear_solicitud(db: Session, modelo_id: int, tipo: str, datos: dict,
                     parcela_id=None, id_logico=None, usuario_id=None) -> SolicitudPrediccion:
    solicitud = SolicitudPrediccion(
        usuario_id=usuario_id,
        modelo_id=modelo_id,
        parcela_id=parcela_id,
        id_logico=id_logico,
        tipo_prediccion=tipo,
        datos_entrada=datos,
        estado="procesando",
    )
    db.add(solicitud)
    db.flush()
    return solicitud


def _guardar_resultado(db: Session, solicitud_id: int, valor: float, confianza: float,
                       unidad: str, explicacion: str, datos_salida: dict) -> ResultadoPrediccion:
    resultado = ResultadoPrediccion(
        solicitud_id=solicitud_id,
        valor_predicho=valor,
        confianza=confianza,
        unidad=unidad,
        explicacion=explicacion,
        datos_salida=datos_salida,
    )
    db.add(resultado)
    return resultado


def ejecutar_prediccion_agua(db: Session, data: dict, usuario_id: int = None) -> dict:
    modelo = db.query(ModeloRegistro).filter(
        ModeloRegistro.tipo == "agua", ModeloRegistro.estado == "activo"
    ).first()
    if not modelo:
        raise ValueError("Modelo de agua no disponible")

    solicitud = _crear_solicitud(
        db, modelo.id, "agua", data,
        parcela_id=data.get("parcela_id"),
        id_logico=data.get("id_logico"),
        usuario_id=usuario_id,
    )
    resultado_ml = predecir_agua(data)
    _guardar_resultado(
        db, solicitud.id,
        valor=resultado_ml["litros_recomendados"],
        confianza=resultado_ml["confianza"],
        unidad="litros",
        explicacion=resultado_ml["explicacion"],
        datos_salida=resultado_ml,
    )
    solicitud.estado = "completado"
    db.commit()
    return {**resultado_ml, "solicitud_id": solicitud.id}


def ejecutar_prediccion_rendimiento(db: Session, data: dict, usuario_id: int = None) -> dict:
    modelo = db.query(ModeloRegistro).filter(
        ModeloRegistro.tipo == "rendimiento", ModeloRegistro.estado == "activo"
    ).first()
    if not modelo:
        raise ValueError("Modelo de rendimiento no disponible")

    solicitud = _crear_solicitud(
        db, modelo.id, "rendimiento", data,
        parcela_id=data.get("parcela_id"),
        id_logico=data.get("id_logico"),
        usuario_id=usuario_id,
    )
    resultado_ml = predecir_rendimiento(data)
    _guardar_resultado(
        db, solicitud.id,
        valor=resultado_ml["rendimiento_kg_ha"],
        confianza=resultado_ml["confianza"],
        unidad="kg/ha",
        explicacion=f"Calificacion: {resultado_ml['calificacion']}",
        datos_salida=resultado_ml,
    )
    solicitud.estado = "completado"
    db.commit()
    return {**resultado_ml, "solicitud_id": solicitud.id}


def ejecutar_prediccion_riesgo(db: Session, data: dict, usuario_id: int = None) -> dict:
    modelo = db.query(ModeloRegistro).filter(
        ModeloRegistro.tipo == "riesgo", ModeloRegistro.estado == "activo"
    ).first()
    if not modelo:
        raise ValueError("Modelo de riesgo no disponible")

    solicitud = _crear_solicitud(
        db, modelo.id, "riesgo", data,
        parcela_id=data.get("parcela_id"),
        id_logico=data.get("id_logico"),
        usuario_id=usuario_id,
    )
    resultado_ml = predecir_riesgo(data)
    _guardar_resultado(
        db, solicitud.id,
        valor=resultado_ml["probabilidad"],
        confianza=resultado_ml["confianza"],
        unidad="probabilidad",
        explicacion=f"Riesgo {resultado_ml['tipo_riesgo']}: nivel {resultado_ml['nivel']}",
        datos_salida=resultado_ml,
    )
    solicitud.estado = "completado"
    db.commit()
    return {**resultado_ml, "solicitud_id": solicitud.id}


def listar_predicciones(db: Session, tipo: str = None, limite: int = 50,
                        usuario_id: int = None) -> list:
    query = db.query(SolicitudPrediccion)
    if usuario_id:
        query = query.filter(SolicitudPrediccion.usuario_id == usuario_id)
    if tipo:
        query = query.filter(SolicitudPrediccion.tipo_prediccion == tipo)
    return query.order_by(SolicitudPrediccion.solicitado_en.desc()).limit(limite).all()


def obtener_resultado(db: Session, solicitud_id: int) -> ResultadoPrediccion:
    return db.query(ResultadoPrediccion).filter(
        ResultadoPrediccion.solicitud_id == solicitud_id
    ).first()


def resumen_ml(db: Session, usuario_id: int = None) -> dict:
    q = db.query(SolicitudPrediccion)
    if usuario_id:
        q = q.filter(SolicitudPrediccion.usuario_id == usuario_id)
    ultima = q.order_by(SolicitudPrediccion.solicitado_en.desc()).first()
    return {
        "total_predicciones":        q.count(),
        "predicciones_agua":         q.filter(SolicitudPrediccion.tipo_prediccion == "agua").count(),
        "predicciones_riesgo":       q.filter(SolicitudPrediccion.tipo_prediccion == "riesgo").count(),
        "predicciones_rendimiento":  q.filter(SolicitudPrediccion.tipo_prediccion == "rendimiento").count(),
        "modelos_activos":           db.query(ModeloRegistro).filter(ModeloRegistro.estado == "activo").count(),
        "ultima_prediccion":         ultima.solicitado_en if ultima else None,
    }