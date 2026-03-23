from app.database import SessionLocal
from app.models.device import TipoDispositivo, Dispositivo, ConfiguracionDispositivo


def poblar_tipos_dispositivo(db):
    tipos = [
        # ── Suelo ────────────────────────────────────────────
        dict(nombre="Higrómetro de Suelo",   categoria="suelo",
             unidad="%",        rango_minimo=0,    rango_maximo=100,
             umbral_alerta="< 20% (Marchitez)",
             tipo_pin="Analógico A0",
             metricas_permitidas=["humedad_suelo"]),

        dict(nombre="pH de Suelo",            categoria="suelo",
             unidad="pH",       rango_minimo=0,    rango_maximo=14,
             umbral_alerta="< 5.5 o > 7.5 (Bloqueo)",
             tipo_pin="Analógico A1",
             metricas_permitidas=["ph_suelo"]),

        dict(nombre="Sensor EC de Suelo",     categoria="suelo",
             unidad="mS/cm",    rango_minimo=0,    rango_maximo=5,
             umbral_alerta="> 3.0 mS/cm (Exceso Sal)",
             tipo_pin="I2C/UART",
             metricas_permitidas=["conductividad_electrica"]),

        dict(nombre="Temperatura de Suelo",   categoria="suelo",
             unidad="°C",       rango_minimo=-10,  rango_maximo=85,
             umbral_alerta="< 12°C (Raíz latente)",
             tipo_pin="Digital OneWire",
             metricas_permitidas=["temperatura_suelo"]),

        # ── Ambiental ────────────────────────────────────────
        dict(nombre="Termómetro Aire",        categoria="ambiental",
             unidad="°C",       rango_minimo=-40,  rango_maximo=80,
             umbral_alerta="> 35°C (Estrés Térmico)",
             tipo_pin="Digital D2",
             metricas_permitidas=["temperatura_aire"]),

        dict(nombre="Higrómetro Aire",        categoria="ambiental",
             unidad="%HR",      rango_minimo=0,    rango_maximo=100,
             umbral_alerta="> 85% (Riesgo Hongos)",
             tipo_pin="Digital D2",
             metricas_permitidas=["humedad_aire"]),

        dict(nombre="Luxómetro",              categoria="ambiental",
             unidad="Lux",      rango_minimo=0,    rango_maximo=65000,
             umbral_alerta="< 2000 (Falta de sol)",
             tipo_pin="I2C SDA/SCL",
             metricas_permitidas=["luminosidad"]),

        dict(nombre="Anemómetro",             categoria="ambiental",
             unidad="km/h",     rango_minimo=0,    rango_maximo=150,
             umbral_alerta="> 40 km/h (Daño estructural)",
             tipo_pin="Digital Interrupt",
             metricas_permitidas=["velocidad_viento"]),

        dict(nombre="Pluviómetro",            categoria="ambiental",
             unidad="mm",       rango_minimo=0,    rango_maximo=500,
             umbral_alerta="> 50 mm/h (Inundación)",
             tipo_pin="Digital Pulse",
             metricas_permitidas=["precipitacion"]),

        # ── Agua ─────────────────────────────────────────────
        dict(nombre="pH de Agua",             categoria="agua",
             unidad="pH",       rango_minimo=0,    rango_maximo=14,
             umbral_alerta="!= 6.5 (Agua no apta)",
             tipo_pin="Analógico A3",
             metricas_permitidas=["ph_agua"]),

        dict(nombre="Caudalímetro",           categoria="agua",
             unidad="L/min",    rango_minimo=1,    rango_maximo=30,
             umbral_alerta="> 500L (Fuga detectada)",
             tipo_pin="Digital D3",
             metricas_permitidas=["caudal"]),

        dict(nombre="Electroválvula",         categoria="agua",
             unidad="V/mA",     rango_minimo=0,    rango_maximo=500,
             umbral_alerta="Tiempo abierto > 30 min",
             tipo_pin="Digital Relé D4",
             metricas_permitidas=["estado_valvula", "tiempo_apertura"]),

        dict(nombre="Bomba de Agua",          categoria="agua",
             unidad="HP/V",     rango_minimo=0,    rango_maximo=220,
             umbral_alerta="Consumo amperaje alto",
             tipo_pin="Digital Relé D5",
             metricas_permitidas=["consumo_amperaje", "voltaje"]),

        # ── Infraestructura ───────────────────────────────────
        dict(nombre="Controlador MCU",        categoria="infraestructura",
             unidad="Metadato", rango_minimo=None, rango_maximo=None,
             umbral_alerta="Uptime < 1 min (Reinicio)",
             tipo_pin="N/A",
             metricas_permitidas=["uptime", "temperatura_cpu"]),

        dict(nombre="Interfaz Red",           categoria="infraestructura",
             unidad="ms",       rango_minimo=0,    rango_maximo=2000,
             umbral_alerta="Latencia > 2000ms",
             tipo_pin="N/A",
             metricas_permitidas=["latencia", "perdida_paquetes"]),

        dict(nombre="Batería",                categoria="infraestructura",
             unidad="V/mAh",    rango_minimo=0,    rango_maximo=10000,
             umbral_alerta="< 3.3V (Apagado inminente)",
             tipo_pin="N/A",
             metricas_permitidas=["voltaje_bateria", "capacidad_restante"]),

        dict(nombre="Panel Solar",            categoria="infraestructura",
             unidad="W/V",      rango_minimo=0,    rango_maximo=50,
             umbral_alerta="< 12V en horas de sol",
             tipo_pin="N/A",
             metricas_permitidas=["potencia_solar", "voltaje_panel"]),

        dict(nombre="Ciclos de Batería",      categoria="infraestructura",
             unidad="ciclos",   rango_minimo=0,    rango_maximo=1000,
             umbral_alerta="> 500 ciclos (Degradación)",
             tipo_pin="N/A",
             metricas_permitidas=["ciclos_carga"]),

        dict(nombre="Señal de Red",           categoria="infraestructura",
             unidad="Mbps",     rango_minimo=0,    rango_maximo=100,
             umbral_alerta="Packet Loss > 5%",
             tipo_pin="N/A",
             metricas_permitidas=["velocidad_red", "perdida_paquetes"]),
    ]

    for t in tipos:
        existe = db.query(TipoDispositivo).filter(
            TipoDispositivo.nombre == t["nombre"]
        ).first()
        if not existe:
            db.add(TipoDispositivo(**t))
    db.commit()
    print(f"✓ {len(tipos)} tipos de sensor insertados")


def poblar_dispositivos(db):
    def obtener_tipo_id(nombre):
        t = db.query(TipoDispositivo).filter(
            TipoDispositivo.nombre == nombre
        ).first()
        return t.id if t else None

    dispositivos = [
        dict(id_logico="SOIL_HUM_01",  numero_serial="SN-HUM-CAP-001",
             tipo_dispositivo_id=obtener_tipo_id("Higrómetro de Suelo")),
        dict(id_logico="SOIL_PH_01",   numero_serial="SN-PHS-450-001",
             tipo_dispositivo_id=obtener_tipo_id("pH de Suelo")),
        dict(id_logico="SOIL_EC_01",   numero_serial="SN-EC-DS1-001",
             tipo_dispositivo_id=obtener_tipo_id("Sensor EC de Suelo")),
        dict(id_logico="SOIL_TEMP_01", numero_serial="28-FF-64-12-3D",
             tipo_dispositivo_id=obtener_tipo_id("Temperatura de Suelo")),
        dict(id_logico="AIR_TEMP_01",  numero_serial="SN-DHT22-001",
             tipo_dispositivo_id=obtener_tipo_id("Termómetro Aire")),
        dict(id_logico="AIR_HUM_01",   numero_serial="SN-DHT22-002",
             tipo_dispositivo_id=obtener_tipo_id("Higrómetro Aire")),
        dict(id_logico="LUX_01",       numero_serial="SN-BH1750-001",
             tipo_dispositivo_id=obtener_tipo_id("Luxómetro")),
        dict(id_logico="WIND_01",      numero_serial="SN-WIND-991",
             tipo_dispositivo_id=obtener_tipo_id("Anemómetro")),
        dict(id_logico="RAIN_01",      numero_serial="SN-RAIN-442",
             tipo_dispositivo_id=obtener_tipo_id("Pluviómetro")),
        dict(id_logico="WAT_PH_01",    numero_serial="SN-PHW-BNC-001",
             tipo_dispositivo_id=obtener_tipo_id("pH de Agua")),
        dict(id_logico="WAT_FLOW_01",  numero_serial="SN-FLOW-YFS-01",
             tipo_dispositivo_id=obtener_tipo_id("Caudalímetro")),
        dict(id_logico="VALVE_01",     numero_serial="SN-SOL-12V-01",
             tipo_dispositivo_id=obtener_tipo_id("Electroválvula")),
        dict(id_logico="PUMP_01",      numero_serial="SN-PUMP-220-01",
             tipo_dispositivo_id=obtener_tipo_id("Bomba de Agua")),
        dict(id_logico="MCU_01",       numero_serial="SN-MEGA-2560",
             tipo_dispositivo_id=obtener_tipo_id("Controlador MCU")),
        dict(id_logico="ETH_01",       numero_serial="DE:AD:BE:EF:01",
             tipo_dispositivo_id=obtener_tipo_id("Interfaz Red")),
        dict(id_logico="BATT_01",      numero_serial="SN-LIPO-10AH",
             tipo_dispositivo_id=obtener_tipo_id("Batería")),
        dict(id_logico="SOLAR_01",     numero_serial="SN-POLY-50W",
             tipo_dispositivo_id=obtener_tipo_id("Panel Solar")),
    ]

    for d in dispositivos:
        existe = db.query(Dispositivo).filter(
            Dispositivo.id_logico == d["id_logico"]
        ).first()
        if not existe:
            dispositivo = Dispositivo(**d)
            db.add(dispositivo)
            db.flush()
            db.add(ConfiguracionDispositivo(dispositivo_id=dispositivo.id))
    db.commit()
    print(f"✓ {len(dispositivos)} dispositivos insertados")


def ejecutar_seed():
    db = SessionLocal()
    try:
        poblar_tipos_dispositivo(db)
        poblar_dispositivos(db)
        print("✓ Datos iniciales cargados exitosamente")
    finally:
        db.close()


if __name__ == "__main__":
    ejecutar_seed()