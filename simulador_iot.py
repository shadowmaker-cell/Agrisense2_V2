"""
Simulador IoT — AgriSense
Simula lecturas de sensores y las envia al sistema via API.
Uso: python simulador_iot.py
"""
import requests
import random
import time
from datetime import datetime

API_BASE = "https://agrisense-gateway.onrender.com"

TIPO_METRICA_MAP = {
    1: ("humedad_suelo",     "%",    5,   95  ),
    2: ("ph_suelo",          "pH",   4,   9   ),
    3: ("ec_suelo",          "mS",   0,   5   ),
    4: ("temperatura_suelo", "C",    5,   40  ),
    5: ("temperatura_aire",  "C",    5,   45  ),
    6: ("humedad_aire",      "%",    0,   100 ),
    7: ("luz",               "Lux",  0,   60000),
    8: ("velocidad_viento",  "km/h", 0,   80  ),
    9: ("lluvia",            "mm",   0,   50  ),
    10:("ph_agua",           "pH",   5,   9   ),
    11:("caudal",            "L/m",  0,   30  ),
    12:("voltaje_valvula",   "V",    0,   24  ),
    13:("consumo_bomba",     "W",    0,   220 ),
    14:("latencia_red",      "ms",   0,   500 ),
    15:("latencia_red",      "ms",   0,   500 ),
    16:("voltaje_bateria",   "V",    3,   5   ),
    17:("potencia_solar",    "W",    0,   50  ),
}


def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def login(email, password):
    res = requests.post(
        f"{API_BASE}/api/auth/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    if res.status_code == 200:
        data  = res.json()
        token = data.get("access_token")
        uid   = data.get("usuario", {}).get("id")
        print(f"✅ Login exitoso — {email} (id={uid})")
        return token, uid
    print(f"❌ Error login: {res.status_code} — {res.text}")
    return None, None


def obtener_email_propio(token):
    """Obtiene el email del usuario autenticado."""
    res = requests.get(
        f"{API_BASE}/api/auth/api/v1/usuarios/me",
        headers=headers(token)
    )
    if res.status_code == 200:
        return res.json().get("email", "")
    return ""


def obtener_dispositivos(token):
    res = requests.get(
        f"{API_BASE}/api/dispositivos/api/v1/dispositivos/",
        headers=headers(token)
    )
    return res.json() if res.status_code == 200 else []


def enviar_lectura(token, sensor, valor):
    payload = {
        "dispositivo_id": sensor["db_id"],
        "id_logico":      sensor["id_logico"],
        "tipo_metrica":   sensor["tipo_metrica"],
        "valor_metrica":  valor,
        "unidad":         sensor["unidad"],
    }
    res = requests.post(
        f"{API_BASE}/api/ingesta/api/v1/telemetria/",
        json=payload, headers=headers(token)
    )
    return res.status_code == 201


def procesar_lectura(token, sensor, valor):
    payload = {
        "dispositivo_id": sensor["db_id"],
        "id_logico":      sensor["id_logico"],
        "tipo_metrica":   sensor["tipo_metrica"],
        "valor_metrica":  valor,
        "unidad":         sensor["unidad"],
    }
    res = requests.post(
        f"{API_BASE}/api/procesamiento/api/v1/procesamiento/manual",
        json=payload, headers=headers(token)
    )
    return res.json() if res.status_code == 201 else {}


def enviar_notificacion(token, usuario_email, sensor, valor, tipos_alerta, n_alertas):
    """Envia notificacion con email del usuario incluido."""
    severidad = "critica" if n_alertas > 1 else "alta"
    payload = {
        "dispositivo_id": sensor["db_id"],
        "id_logico":      sensor["id_logico"],
        "tipo_alerta":    tipos_alerta[0],
        "tipo_metrica":   sensor["tipo_metrica"],
        "valor":          valor,
        "condicion":      f"Valor {valor} {sensor['unidad']} — {', '.join(tipos_alerta)}",
        "severidad":      severidad,
        "canal":          "email",
        "email_destino":  usuario_email,
    }
    res = requests.post(
        f"{API_BASE}/api/notificaciones/api/v1/notificaciones/enviar",
        json=payload, headers=headers(token)
    )
    return res.status_code == 201


def simular_valor(sensor):
    rango = sensor["max"] - sensor["min"]
    base  = (sensor["max"] + sensor["min"]) / 2
    if random.random() < 0.15:
        valor = sensor["min"] + random.uniform(0, rango * 0.1)
    elif random.random() < 0.15:
        valor = sensor["max"] - random.uniform(0, rango * 0.1)
    else:
        valor = base + random.gauss(0, rango * 0.1)
    return round(max(sensor["min"], min(sensor["max"], valor)), 2)


def main():
    print("=" * 55)
    print("  AgriSense — Simulador IoT")
    print("=" * 55)

    email    = input("Email: ").strip()
    password = input("Password: ").strip()

    token, usuario_id = login(email, password)
    if not token:
        return

    usuario_email = obtener_email_propio(token)
    print(f"📧 Notificaciones se enviaran a: {usuario_email}")

    dispositivos = obtener_dispositivos(token)
    if not dispositivos:
        print("❌ No hay sensores registrados.")
        print("   Registra sensores en la seccion Dispositivos.")
        return

    sensores = []
    for d in dispositivos:
        if d.get("estado") != "activo":
            continue
        tipo_id = d.get("tipo_dispositivo_id", 1)
        metrica, unidad, vmin, vmax = TIPO_METRICA_MAP.get(
            tipo_id, ("humedad_suelo", "%", 0, 100)
        )
        sensores.append({
            "db_id":        d["id"],
            "id_logico":    d["id_logico"],
            "tipo_metrica": metrica,
            "unidad":       unidad,
            "min":          vmin,
            "max":          vmax,
        })

    if not sensores:
        print("❌ No hay sensores activos.")
        return

    intervalo = 10
    try:
        intervalo = int(
            input(f"Intervalo entre lecturas en segundos [{intervalo}]: ").strip() or intervalo
        )
    except ValueError:
        pass

    print(f"\n✅ {len(sensores)} sensores activos:")
    for s in sensores:
        print(f"   • {s['id_logico']} — {s['tipo_metrica']} ({s['unidad']})")

    print(f"\n⏱  Enviando lecturas cada {intervalo}s — Ctrl+C para detener\n")

    ciclo          = 0
    total_lecturas = 0
    total_alertas  = 0
    total_notif    = 0

    try:
        while True:
            ciclo += 1
            print(f"── Ciclo {ciclo} — {datetime.now().strftime('%H:%M:%S')} ──────")

            for sensor in sensores:
                valor = simular_valor(sensor)

                # 1. Ingesta
                ok_ingesta = enviar_lectura(token, sensor, valor)
                if not ok_ingesta:
                    print(f"  ✗  {sensor['id_logico']}: error en ingesta")
                    continue

                total_lecturas += 1

                # 2. Procesamiento
                resultado = procesar_lectura(token, sensor, valor)
                n_alertas = resultado.get("alertas_generadas", 0)
                tipos     = resultado.get("tipos_alerta", [])

                if n_alertas > 0:
                    total_alertas += n_alertas
                    # 3. Notificacion con email
                    ok_notif = enviar_notificacion(
                        token, usuario_email, sensor, valor, tipos, n_alertas
                    )
                    if ok_notif:
                        total_notif += 1
                    print(
                        f"  ⚠️  {sensor['id_logico']}: {valor} {sensor['unidad']} "
                        f"→ {n_alertas} alerta(s): {', '.join(tipos)} "
                        f"{'📧' if ok_notif else '✗'}"
                    )
                else:
                    print(f"  ✓  {sensor['id_logico']}: {valor} {sensor['unidad']}")

            print(
                f"     Total: {total_lecturas} lecturas · "
                f"{total_alertas} alertas · {total_notif} notificaciones\n"
            )
            time.sleep(intervalo)

    except KeyboardInterrupt:
        print(f"\n🛑 Simulador detenido.")
        print(
            f"   Ciclos: {ciclo} · Lecturas: {total_lecturas} · "
            f"Alertas: {total_alertas} · Notificaciones: {total_notif}"
        )


if __name__ == "__main__":
    main()