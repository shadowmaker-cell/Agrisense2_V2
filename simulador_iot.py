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
    1:  ("humedad_suelo",          "%",     5,    95   ),
    2:  ("ph_suelo",               "pH",    4,    9    ),
    3:  ("conductividad_electrica","mS/cm", 0,    5    ),
    4:  ("temperatura_suelo",      "C",     5,    40   ),
    5:  ("temperatura_suelo",      "C",     5,    40   ),
    6:  ("ph_suelo",               "pH",    4,    9    ),
    7:  ("humedad_suelo",          "%",     5,    95   ),
    8:  ("temperatura_aire",       "C",     5,    45   ),
    9:  ("humedad_aire",           "%",     0,    100  ),
    10: ("luminosidad",            "Lux",   0,    60000),
    11: ("velocidad_viento",       "km/h",  0,    80   ),
    12: ("precipitacion",          "mm",    0,    50   ),
    13: ("caudal",                 "L/min", 0,    30   ),
    14: ("nivel_agua",             "cm",    0,    500  ),
    15: ("ph_agua",                "pH",    5,    9    ),
    16: ("diametro_tallo",         "mm",    0,    500  ),
    17: ("humedad_hoja",           "%",     0,    100  ),
    18: ("estado_valvula",         "min",   0,    60   ),
    19: ("tiempo_apertura",        "min",   0,    120  ),
    20: ("consumo_amperaje",       "A",     0,    25   ),
    21: ("voltaje",                "V",     0,    220  ),
    22: ("consumo_amperaje",       "A",     0,    25   ),
    23: ("temperatura_motor",      "C",     0,    100  ),
    24: ("velocidad_ventilador",   "RPM",   0,    3000 ),
    25: ("consumo_watts",          "W",     0,    1000 ),
    26: ("consumo_watts",          "W",     0,    500  ),
    27: ("horas_uso",              "h",     0,    12000),
    28: ("uptime",                 "s",     0,    86400),
    29: ("temperatura_cpu",        "C",     0,    100  ),
    30: ("uso_cpu",                "%",     0,    100  ),
    31: ("uso_ram",                "%",     0,    100  ),
    32: ("uso_cpu",                "%",     0,    100  ),
    33: ("latencia",               "ms",    0,    2000 ),
    34: ("perdida_paquetes",       "%",     0,    100  ),
    35: ("estado_conexion",        "min",   0,    60   ),
    36: ("voltaje_panel",          "V",     0,    48   ),
    37: ("potencia_solar",         "W",     0,    500  ),
    38: ("eficiencia",             "%",     60,   100  ),
    39: ("voltaje_bateria",        "V",     3,    5    ),
    40: ("capacidad_restante",     "%",     0,    100  ),
    41: ("ciclos_carga",           "ciclos",0,    1000 ),
    42: ("voltaje_bateria",        "V",     3,    5    ),
    43: ("capacidad_restante",     "%",     0,    100  ),
    44: ("temperatura_bateria",    "C",     0,    60   ),
    45: ("carga_bateria",          "%",     0,    100  ),
    46: ("autonomia_restante",     "min",   0,    120  ),
    47: ("nivel_combustible",      "%",     0,    100  ),
    48: ("voltaje_salida",         "V",     0,    240  ),
    49: ("frecuencia",             "Hz",    55,   65   ),
    50: ("voltaje_salida",         "V",     0,    240  ),
    51: ("corriente_salida",       "A",     0,    30   ),
    52: ("temperatura",            "C",     0,    100  ),
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
    if sensor.get("limite_minimo") is not None:
        payload["limite_minimo"] = sensor["limite_minimo"]
    if sensor.get("limite_maximo") is not None:
        payload["limite_maximo"] = sensor["limite_maximo"]

    res = requests.post(
        f"{API_BASE}/api/procesamiento/api/v1/procesamiento/manual",
        json=payload, headers=headers(token)
    )
    return res.json() if res.status_code == 201 else {}


def enviar_notificacion(token, usuario_email, sensor, valor, tipos_alerta, severidad):
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


def generar_recomendacion_automatica(token, sensor, valor, tipos_alerta, severidad):
    """Genera recomendaciones automáticas basadas en la alerta detectada."""
    payload = {
        "tipo_alerta":  tipos_alerta[0],
        "tipo_metrica": sensor["tipo_metrica"],
        "valor":        valor,
        "id_logico":    sensor["id_logico"],
        "severidad":    severidad,
        "condicion":    f"Valor {valor} {sensor['unidad']} — {', '.join(tipos_alerta)}",
    }
    res = requests.post(
        f"{API_BASE}/api/recomendaciones/api/v1/recomendaciones/desde-alerta",
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
    print(f"📧 Notificaciones se enviarán a: {usuario_email}")

    dispositivos = obtener_dispositivos(token)
    if not dispositivos:
        print("❌ No hay sensores registrados.")
        return

    sensores = []
    for d in dispositivos:
        if d.get("estado") != "activo":
            continue
        tipo_id = d.get("tipo_dispositivo_id", 1)
        metrica, unidad, vmin, vmax = TIPO_METRICA_MAP.get(
            tipo_id, ("humedad_suelo", "%", 0, 100)
        )
        config = d.get("configuracion") or {}
        sensores.append({
            "db_id":         d["id"],
            "id_logico":     d["id_logico"],
            "tipo_metrica":  metrica,
            "unidad":        unidad,
            "min":           vmin,
            "max":           vmax,
            "limite_minimo": config.get("limite_minimo"),
            "limite_maximo": config.get("limite_maximo"),
        })

    if not sensores:
        print("❌ No hay sensores activos.")
        return

    intervalo = 10
    try:
        val = input(f"Intervalo entre lecturas en segundos [{intervalo}]: ").strip()
        if val:
            intervalo = int(val)
    except ValueError:
        pass

    print(f"\n✅ {len(sensores)} sensores activos:")
    for s in sensores:
        lim = ""
        if s["limite_minimo"] is not None or s["limite_maximo"] is not None:
            lim = f" [límites: {s['limite_minimo']} — {s['limite_maximo']}]"
        print(f"   • {s['id_logico']} — {s['tipo_metrica']} ({s['unidad']}){lim}")

    print(f"\n⏱  Enviando lecturas cada {intervalo}s — Ctrl+C para detener\n")

    ciclo          = 0
    total_lecturas = 0
    total_alertas  = 0
    total_notif    = 0
    total_rec      = 0

    try:
        while True:
            ciclo += 1
            print(f"── Ciclo {ciclo} — {datetime.now().strftime('%H:%M:%S')} ──────")

            for sensor in sensores:
                valor = simular_valor(sensor)

                ok_ingesta = enviar_lectura(token, sensor, valor)
                if not ok_ingesta:
                    print(f"  ✗  {sensor['id_logico']}: error en ingesta")
                    continue

                total_lecturas += 1

                resultado = procesar_lectura(token, sensor, valor)
                n_alertas = resultado.get("alertas_generadas", 0)
                tipos     = resultado.get("tipos_alerta", [])

                if n_alertas > 0:
                    total_alertas += n_alertas
                    severidad = "critica" if n_alertas > 1 else "alta"

                    ok_notif = enviar_notificacion(
                        token, usuario_email, sensor, valor, tipos, severidad
                    )
                    if ok_notif:
                        total_notif += 1

                    ok_rec = generar_recomendacion_automatica(
                        token, sensor, valor, tipos, severidad
                    )
                    if ok_rec:
                        total_rec += 1

                    print(
                        f"  ⚠️  {sensor['id_logico']}: {valor} {sensor['unidad']} "
                        f"→ {n_alertas} alerta(s): {', '.join(tipos)} "
                        f"{'📧' if ok_notif else ''} {'🤖' if ok_rec else ''}"
                    )
                else:
                    print(f"  ✓  {sensor['id_logico']}: {valor} {sensor['unidad']}")

            print(
                f"     Total: {total_lecturas} lecturas · "
                f"{total_alertas} alertas · {total_notif} notif · {total_rec} rec\n"
            )
            time.sleep(intervalo)

    except KeyboardInterrupt:
        print(f"\n🛑 Simulador detenido.")
        print(
            f"   Ciclos: {ciclo} · Lecturas: {total_lecturas} · "
            f"Alertas: {total_alertas} · Notif: {total_notif} · Rec: {total_rec}"
        )


if __name__ == "__main__":
    main()