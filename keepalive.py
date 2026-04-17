import requests
import time
from datetime import datetime

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

def ping_todos():
    print(f"\n🕐 {datetime.now().strftime('%H:%M:%S')} — Verificando servicios...")
    online = 0
    for url in SERVICIOS:
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200:
                print(f"  ✅ {url.split('/')[2]} — online")
                online += 1
            else:
                print(f"  ⚠️  {url.split('/')[2]} — status {r.status_code}")
        except requests.exceptions.Timeout:
            print(f"  ⏳ {url.split('/')[2]} — despertando (timeout)...")
        except Exception as e:
            print(f"  ❌ {url.split('/')[2]} — {e}")
    print(f"\n  {online}/{len(SERVICIOS)} servicios online\n")
    return online

print("🌿 AgriSense Keepalive iniciado")
print("   Mantiene los servicios de Render activos cada 10 minutos")
print("   Presiona Ctrl+C para detener\n")

# Primer ping inmediato — despierta todos
ping_todos()

while True:
    print(f"⏱  Próximo ping en 10 minutos...")
    time.sleep(600)
    ping_todos()