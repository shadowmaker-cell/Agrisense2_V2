import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from app.models.notificacion import Notificacion, LogEnvio
from app.services.formateador import formatear_notificacion, formatear_para_canal
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

GMAIL_USER     = os.getenv("GMAIL_USER", "")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "")
GMAIL_FROM     = os.getenv("GMAIL_FROM", GMAIL_USER)


def enviar_email_gmail(destinatario: str, titulo: str, mensaje: str, severidad: str) -> bool:
    """Envia un email via Gmail SMTP."""
    if not GMAIL_USER or not GMAIL_PASSWORD:
        logger.warning("Gmail no configurado — EMAIL_USER o EMAIL_PASSWORD vacios")
        return False
    if not destinatario:
        logger.warning("Sin destinatario para email")
        return False

    try:
        color_severidad = {
            "critica":  "#dc2626",
            "alta":     "#d97706",
            "media":    "#2563eb",
            "baja":     "#16a34a",
        }.get(severidad, "#16a34a")

        html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f9fafb;padding:0;margin:0;">
  <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
    <div style="background:#166534;padding:24px 32px;display:flex;align-items:center;gap:12px;">
      <span style="font-size:28px;">🌿</span>
      <div>
        <div style="color:#fff;font-size:20px;font-weight:700;">AgriSense</div>
        <div style="color:#86efac;font-size:12px;">Plataforma de Agricultura de Precision</div>
      </div>
    </div>
    <div style="padding:32px;">
      <div style="background:{color_severidad};color:#fff;padding:8px 16px;border-radius:20px;display:inline-block;font-size:12px;font-weight:700;margin-bottom:16px;">
        ALERTA {severidad.upper()}
      </div>
      <h2 style="color:#111;font-size:18px;margin:0 0 12px;">{titulo}</h2>
      <p style="color:#4b5563;font-size:14px;line-height:1.6;margin:0 0 24px;">{mensaje}</p>
      <div style="background:#f0fdf4;border-radius:8px;padding:16px;border-left:4px solid #16a34a;">
        <p style="color:#166534;font-size:13px;margin:0;">
          Revisa el dashboard de AgriSense para mas detalles y tomar accion inmediata.
        </p>
      </div>
    </div>
    <div style="background:#f9fafb;padding:16px 32px;text-align:center;border-top:1px solid #e5e7eb;">
      <p style="color:#9ca3af;font-size:11px;margin:0;">
        AgriSense — Plataforma de Agricultura de Precision · {datetime.now().strftime('%d/%m/%Y %H:%M')}
      </p>
    </div>
  </div>
</body>
</html>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🌿 AgriSense — {titulo}"
        msg["From"]    = GMAIL_FROM
        msg["To"]      = destinatario
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, destinatario, msg.as_string())

        logger.info(f"Email enviado a {destinatario}: {titulo}")
        return True

    except Exception as e:
        logger.error(f"Error enviando email a {destinatario}: {e}")
        return False


def obtener_email_usuario(usuario_id: int) -> str:
    """Obtiene el email del usuario desde el servicio de auth."""
    try:
        import httpx
        AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://servicio-auth:8008")
        res = httpx.get(f"{AUTH_SERVICE_URL}/api/v1/usuarios/{usuario_id}/email", timeout=3.0)
        if res.status_code == 200:
            return res.json().get("email", "")
    except Exception:
        pass
    return ""


def crear_notificacion(
    db: Session,
    dispositivo_id: int,
    id_logico: str,
    tipo_alerta: str,
    tipo_metrica: str,
    valor: float,
    condicion: str,
    severidad: str,
    canal: str = "sistema",
    origen_evento: str = "alert.generated",
    usuario_id: int = None,
) -> Notificacion:
    contenido = formatear_notificacion(
        tipo_alerta=tipo_alerta,
        id_logico=id_logico,
        tipo_metrica=tipo_metrica,
        valor=valor,
        condicion=condicion,
        severidad=severidad
    )
    notificacion = Notificacion(
        usuario_id=usuario_id,
        dispositivo_id=dispositivo_id,
        id_logico=id_logico,
        titulo=contenido["titulo"],
        mensaje=contenido["mensaje"],
        tipo=tipo_alerta,
        severidad=severidad,
        canal=canal,
        estado="pendiente",
        origen_evento=origen_evento
    )
    db.add(notificacion)
    db.flush()
    return notificacion


def enviar_notificacion(db: Session, notificacion: Notificacion, email_destino: str = "") -> bool:
    contenido_canal = formatear_para_canal(
        titulo=notificacion.titulo,
        mensaje=notificacion.mensaje,
        canal=notificacion.canal
    )
    try:
        respuesta = "Notificacion registrada en sistema"
        enviado   = True

        if notificacion.canal in ("email", "push", "sistema") and email_destino:
            enviado   = enviar_email_gmail(email_destino, notificacion.titulo, notificacion.mensaje, notificacion.severidad)
            respuesta = "Email enviado via Gmail" if enviado else "Error enviando email"
        elif notificacion.canal == "sistema":
            logger.info(f"[SISTEMA] {contenido_canal['titulo']}")
            respuesta = "Notificacion registrada en sistema"

        log = LogEnvio(
            notificacion_id=notificacion.id,
            canal=notificacion.canal,
            estado="enviado" if enviado else "fallido",
            respuesta=respuesta
        )
        db.add(log)
        notificacion.estado     = "enviada" if enviado else "fallida"
        notificacion.enviada_en = datetime.now(timezone.utc)
        db.commit()
        return enviado

    except Exception as e:
        log = LogEnvio(
            notificacion_id=notificacion.id,
            canal=notificacion.canal,
            estado="fallido",
            respuesta=str(e)
        )
        db.add(log)
        notificacion.estado = "fallida"
        db.commit()
        logger.error(f"Error enviando notificacion {notificacion.id}: {e}")
        return False


def procesar_alerta(db: Session, datos: dict) -> dict:
    severidad  = datos.get("severidad", "media")
    usuario_id = datos.get("usuario_id")

    canal = "sistema"
    if severidad in ("critica", "alta"):
        canal = "email"

    notificacion = crear_notificacion(
        db=db,
        usuario_id=usuario_id,
        dispositivo_id=datos.get("dispositivo_id"),
        id_logico=datos.get("id_logico"),
        tipo_alerta=datos.get("tipo_alerta", datos.get("tipo_metrica")),
        tipo_metrica=datos.get("tipo_metrica"),
        valor=datos.get("valor_detectado", datos.get("valor_metrica", 0)),
        condicion=datos.get("condicion", ""),
        severidad=severidad,
        canal=canal,
        origen_evento=datos.get("event", "alert.generated")
    )

    # Obtener email del destinatario
    email_destino = datos.get("email_destino", "")
    if not email_destino and usuario_id:
        email_destino = obtener_email_usuario(usuario_id)

    enviada = enviar_notificacion(db, notificacion, email_destino)

    return {
        "notificacion_id": notificacion.id,
        "canal":           canal,
        "estado":          notificacion.estado,
        "enviada":         enviada,
    }