import requests
import time

SERVICIOS = [
    "https://agrisense-gateway.onrender.com/health",
    "https://agrisense-auth.onrender.com/health",
    "https://agrisense-dispositivos.onrender.com/health",
    "https://agrisense-ingesta.onrender.com/health",
    "https://agrisense-procesamiento.onrender.com/health",
    "https://agrisense-notificaciones.onrender.com/health",
    "https://agrisense-parcelas.onrender.com/health",
    "https://agrisense-ml.onrender.com/health",
    "https://agrisense-recomendaciones.onrender.com/health",
]

while True:
    for url in SERVICIOS:
        try:
            r = requests.get(url, timeout=10)
            print(f"✅ {url} — {r.status_code}")
        except Exception as e:
            print(f"❌ {url} — {e}")
    print(f"⏱ Esperando 10 minutos...\n")
    time.sleep(600)