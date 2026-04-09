from app.database import SessionLocal
from app.models.device import TipoDispositivo


def poblar_tipos_dispositivo(db):
    tipos = [

        # ── SENSORES DE SUELO ─────────────────────────────
        dict(nombre="Suelo: Solo Humedad (Tensiometrico)",
             categoria="suelo", unidad="%",
             rango_minimo=0, rango_maximo=100,
             umbral_alerta="< 20% (Marchitez)",
             tipo_pin="Analogico A0",
             metricas_permitidas=["humedad_suelo"]),

        dict(nombre="Suelo: Sonda Dual (Humedad y Temp)",
             categoria="suelo", unidad="%/C",
             rango_minimo=0, rango_maximo=100,
             umbral_alerta="< 20% o < 12C",
             tipo_pin="Digital OneWire",
             metricas_permitidas=["humedad_suelo", "temperatura_suelo"]),

        dict(nombre="Suelo: Sonda NPK (Nutrientes)",
             categoria="suelo", unidad="mg/kg",
             rango_minimo=0, rango_maximo=2000,
             umbral_alerta="< 10 mg/kg N (Deficit)",
             tipo_pin="UART/RS485",
             metricas_permitidas=["nitrogeno", "fosforo", "potasio"]),

        dict(nombre="Suelo: Multiparametrica (pH EC Temp Hum)",
             categoria="suelo", unidad="multi",
             rango_minimo=0, rango_maximo=14,
             umbral_alerta="pH < 5.5 o > 7.5",
             tipo_pin="I2C/UART",
             metricas_permitidas=["humedad_suelo", "temperatura_suelo", "conductividad_electrica", "ph_suelo"]),

        dict(nombre="Suelo: pH",
             categoria="suelo", unidad="pH",
             rango_minimo=0, rango_maximo=14,
             umbral_alerta="< 5.5 o > 7.5 (Bloqueo)",
             tipo_pin="Analogico A1",
             metricas_permitidas=["ph_suelo"]),

        dict(nombre="Suelo: Conductividad Electrica (EC)",
             categoria="suelo", unidad="mS/cm",
             rango_minimo=0, rango_maximo=5,
             umbral_alerta="> 3.0 mS/cm (Exceso Sal)",
             tipo_pin="I2C/UART",
             metricas_permitidas=["conductividad_electrica"]),

        dict(nombre="Suelo: Temperatura",
             categoria="suelo", unidad="C",
             rango_minimo=-10, rango_maximo=85,
             umbral_alerta="< 12C (Raiz latente)",
             tipo_pin="Digital OneWire",
             metricas_permitidas=["temperatura_suelo"]),

        # ── SENSORES CLIMATICOS ───────────────────────────
        dict(nombre="Clima: Termo-Higrometro",
             categoria="ambiental", unidad="C/%",
             rango_minimo=-40, rango_maximo=80,
             umbral_alerta="> 35C (Estres Termico)",
             tipo_pin="Digital D2",
             metricas_permitidas=["temperatura_aire", "humedad_aire"]),

        dict(nombre="Clima: Luxometro (Luz/PAR)",
             categoria="ambiental", unidad="Lux",
             rango_minimo=0, rango_maximo=65000,
             umbral_alerta="< 2000 (Falta de sol)",
             tipo_pin="I2C SDA/SCL",
             metricas_permitidas=["luminosidad"]),

        dict(nombre="Clima: Anemometro",
             categoria="ambiental", unidad="km/h",
             rango_minimo=0, rango_maximo=150,
             umbral_alerta="> 40 km/h (Dano estructural)",
             tipo_pin="Digital Interrupt",
             metricas_permitidas=["velocidad_viento"]),

        dict(nombre="Clima: Pluviometro",
             categoria="ambiental", unidad="mm",
             rango_minimo=0, rango_maximo=500,
             umbral_alerta="> 50 mm/h (Inundacion)",
             tipo_pin="Digital Pulse",
             metricas_permitidas=["precipitacion"]),

        # ── SENSORES DE AGUA ──────────────────────────────
        dict(nombre="Agua: Caudalimetro",
             categoria="agua", unidad="L/min",
             rango_minimo=0, rango_maximo=30,
             umbral_alerta="> 500L acumulado (Fuga)",
             tipo_pin="Digital D3",
             metricas_permitidas=["caudal"]),

        dict(nombre="Agua: Nivel de Tanque",
             categoria="agua", unidad="cm",
             rango_minimo=0, rango_maximo=500,
             umbral_alerta="< 10cm (Tanque vacio)",
             tipo_pin="Ultrasonico/Analogico",
             metricas_permitidas=["nivel_agua"]),

        dict(nombre="Agua: Calidad (pH/ORP)",
             categoria="agua", unidad="pH/mV",
             rango_minimo=0, rango_maximo=14,
             umbral_alerta="pH != 6.5 (Agua no apta)",
             tipo_pin="Analogico A3",
             metricas_permitidas=["ph_agua", "orp_agua"]),

        # ── SENSORES DE PLANTA ────────────────────────────
        dict(nombre="Planta: Dendrometro",
             categoria="planta", unidad="mm",
             rango_minimo=0, rango_maximo=500,
             umbral_alerta="Variacion > 5mm/dia",
             tipo_pin="Analogico/I2C",
             metricas_permitidas=["diametro_tallo"]),

        dict(nombre="Planta: Humedad Foliar",
             categoria="planta", unidad="%",
             rango_minimo=0, rango_maximo=100,
             umbral_alerta="> 85% (Riesgo hongos)",
             tipo_pin="Analogico A4",
             metricas_permitidas=["humedad_hoja"]),

        # ── ACTUADORES DE RIEGO ───────────────────────────
        dict(nombre="Riego: Electrovalvula Simple",
             categoria="actuador_riego", unidad="V/mA",
             rango_minimo=0, rango_maximo=24,
             umbral_alerta="Tiempo abierto > 30 min",
             tipo_pin="Digital Rele D4",
             metricas_permitidas=["estado_valvula", "tiempo_apertura"]),

        dict(nombre="Riego: Valvula Motorizada (Proporcional)",
             categoria="actuador_riego", unidad="V/seg",
             rango_minimo=0, rango_maximo=24,
             umbral_alerta="Falla apertura/cierre",
             tipo_pin="PWM/Rele",
             metricas_permitidas=["estado_valvula", "porcentaje_apertura", "tiempo_apertura"]),

        # ── ACTUADORES DE BOMBEO ──────────────────────────
        dict(nombre="Bombeo: Bomba Superficial",
             categoria="actuador_bombeo", unidad="HP/V",
             rango_minimo=0, rango_maximo=220,
             umbral_alerta="Consumo amperaje alto",
             tipo_pin="Digital Rele D5",
             metricas_permitidas=["consumo_amperaje", "voltaje", "estado_bomba"]),

        dict(nombre="Bombeo: Bomba Sumergible",
             categoria="actuador_bombeo", unidad="HP/V",
             rango_minimo=0, rango_maximo=220,
             umbral_alerta="Temperatura motor > 80C",
             tipo_pin="Digital Rele D6",
             metricas_permitidas=["consumo_amperaje", "voltaje", "temperatura_motor"]),

        # ── ACTUADORES CLIMATICOS ─────────────────────────
        dict(nombre="Clima: Extractor/Ventilador",
             categoria="actuador_clima", unidad="m3/h",
             rango_minimo=0, rango_maximo=5000,
             umbral_alerta="Falla motor",
             tipo_pin="PWM/Rele",
             metricas_permitidas=["velocidad_ventilador", "consumo_watts"]),

        dict(nombre="Clima: Calefactor",
             categoria="actuador_clima", unidad="BTU",
             rango_minimo=0, rango_maximo=50000,
             umbral_alerta="Temperatura > umbral",
             tipo_pin="Digital Rele",
             metricas_permitidas=["temperatura_salida", "consumo_watts"]),

        dict(nombre="Iluminacion: Lampara UV/Crecimiento",
             categoria="actuador_iluminacion", unidad="W",
             rango_minimo=0, rango_maximo=1000,
             umbral_alerta="Falla encendido",
             tipo_pin="PWM/Rele",
             metricas_permitidas=["consumo_watts", "horas_uso"]),

        # ── COMPUTACION / CONTROLADORES ───────────────────
        dict(nombre="Controlador: Microcontrolador (Arduino/ESP)",
             categoria="computacion", unidad="Metadato",
             rango_minimo=None, rango_maximo=None,
             umbral_alerta="Uptime < 1 min (Reinicio)",
             tipo_pin="N/A",
             metricas_permitidas=["uptime", "temperatura_cpu", "memoria_libre"]),

        dict(nombre="Controlador: PLC Industrial",
             categoria="computacion", unidad="Metadato",
             rango_minimo=None, rango_maximo=None,
             umbral_alerta="Falla comunicacion Modbus",
             tipo_pin="RS485/Ethernet",
             metricas_permitidas=["estado_entradas", "estado_salidas", "ciclo_scan"]),

        dict(nombre="Computacion: Servidor (Rack/Torre)",
             categoria="computacion", unidad="Metadato",
             rango_minimo=None, rango_maximo=None,
             umbral_alerta="CPU > 90% o RAM > 90%",
             tipo_pin="Ethernet",
             metricas_permitidas=["uso_cpu", "uso_ram", "temperatura_cpu", "uptime"]),

        dict(nombre="Computacion: Laptop/Desktop",
             categoria="computacion", unidad="Metadato",
             rango_minimo=None, rango_maximo=None,
             umbral_alerta="Disco > 90%",
             tipo_pin="WiFi/Ethernet",
             metricas_permitidas=["uso_cpu", "uso_ram", "espacio_disco"]),

        dict(nombre="Red: Router/Gateway IoT",
             categoria="infraestructura", unidad="ms",
             rango_minimo=0, rango_maximo=2000,
             umbral_alerta="Latencia > 2000ms",
             tipo_pin="Ethernet/WiFi",
             metricas_permitidas=["latencia", "perdida_paquetes", "dispositivos_conectados"]),

        dict(nombre="Red: Switch",
             categoria="infraestructura", unidad="Gbps",
             rango_minimo=0, rango_maximo=100,
             umbral_alerta="Puerto saturado > 90%",
             tipo_pin="Ethernet",
             metricas_permitidas=["trafico_entrada", "trafico_salida", "errores_puerto"]),

        dict(nombre="Periferico: Camara CCTV/IP",
             categoria="infraestructura", unidad="Metadato",
             rango_minimo=None, rango_maximo=None,
             umbral_alerta="Perdida de senal",
             tipo_pin="Ethernet/WiFi",
             metricas_permitidas=["estado_conexion", "almacenamiento_usado"]),

        # ── ENERGIA Y RESPALDO ────────────────────────────
        dict(nombre="Generacion: Panel Solar",
             categoria="energia", unidad="W/V",
             rango_minimo=0, rango_maximo=500,
             umbral_alerta="< 12V en horas de sol",
             tipo_pin="N/A",
             metricas_permitidas=["potencia_solar", "voltaje_panel", "corriente_panel"]),

        dict(nombre="Generacion: Inversor Solar",
             categoria="energia", unidad="W",
             rango_minimo=0, rango_maximo=10000,
             umbral_alerta="Temperatura > 70C",
             tipo_pin="N/A",
             metricas_permitidas=["potencia_salida", "eficiencia", "temperatura_inversor"]),

        dict(nombre="Almacenamiento: Bateria Ciclo Profundo",
             categoria="energia", unidad="V/Ah",
             rango_minimo=0, rango_maximo=10000,
             umbral_alerta="< 3.3V (Apagado inminente)",
             tipo_pin="N/A",
             metricas_permitidas=["voltaje_bateria", "capacidad_restante", "ciclos_carga"]),

        dict(nombre="Almacenamiento: Bateria Litio",
             categoria="energia", unidad="V/Ah",
             rango_minimo=0, rango_maximo=10000,
             umbral_alerta="< 3.0V o > 4.2V",
             tipo_pin="N/A",
             metricas_permitidas=["voltaje_bateria", "capacidad_restante", "temperatura_bateria"]),

        dict(nombre="Respaldo: UPS",
             categoria="energia", unidad="VA",
             rango_minimo=0, rango_maximo=10000,
             umbral_alerta="Bateria < 20%",
             tipo_pin="USB/RS232",
             metricas_permitidas=["carga_bateria", "autonomia_restante", "voltaje_entrada"]),

        dict(nombre="Respaldo: Planta Electrica",
             categoria="energia", unidad="kVA",
             rango_minimo=0, rango_maximo=100,
             umbral_alerta="Combustible < 20%",
             tipo_pin="N/A",
             metricas_permitidas=["voltaje_salida", "frecuencia", "nivel_combustible"]),

        dict(nombre="Fuente: Transformador/Adaptador",
             categoria="energia", unidad="V/A",
             rango_minimo=0, rango_maximo=220,
             umbral_alerta="Temperatura > 70C",
             tipo_pin="N/A",
             metricas_permitidas=["voltaje_salida", "corriente_salida", "temperatura"]),
    ]

    for t in tipos:
        existe = db.query(TipoDispositivo).filter(
            TipoDispositivo.nombre == t["nombre"]
        ).first()
        if not existe:
            db.add(TipoDispositivo(**t))
    db.commit()
    print(f"✓ {len(tipos)} tipos de dispositivo verificados")


def ejecutar_seed():
    db = SessionLocal()
    try:
        poblar_tipos_dispositivo(db)
        print("✓ Seed completado — tipos de dispositivo listos")
    finally:
        db.close()


if __name__ == "__main__":
    ejecutar_seed()