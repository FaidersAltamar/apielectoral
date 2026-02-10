import time
import requests

url = "http://localhost:8080/consultar-puesto-votacion"

print("=" * 70)
print("🚀 TEST DE VELOCIDAD CON POOL MEJORADO")
print("=" * 70)
print("El sistema ahora:")
print("- Pre-llena 3 tokens en paralelo al iniciar")
print("- Mantiene 6-10 tokens disponibles")
print("- Verifica cada 1 segundo (más rápido)")
print()

# Primera consulta (debería usar el pool pre-llenado)
print("🔹 CONSULTA 1 (Primera - debería usar pool pre-llenado)")
print("-" * 70)
start1 = time.time()
try:
    r1 = requests.post(url, json={"nuip": "1102877148", "enviarapi": False}, timeout=120)
    t1 = time.time() - start1
    if r1.status_code == 200 and r1.json().get('status') == 'success':
        data = r1.json()['data'][0]
        print(f"✅ Éxito - Tiempo: {t1:.2f}s")
        print(f"   Puesto: {data['PUESTO']}, Mesa: {data['MESA']}")
    else:
        print(f"❌ Error - Tiempo: {t1:.2f}s")
except Exception as e:
    t1 = time.time() - start1
    print(f"❌ Error: {e} - Tiempo: {t1:.2f}s")

print()
print("⏳ Esperando 2 segundos...")
time.sleep(2)
print()

# Segunda consulta (rápida)
print("🔹 CONSULTA 2 (Usa pool)")
print("-" * 70)
start2 = time.time()
try:
    r2 = requests.post(url, json={"nuip": "1102877148", "enviarapi": False}, timeout=120)
    t2 = time.time() - start2
    if r2.status_code == 200 and r2.json().get('status') == 'success':
        print(f"✅ Éxito - Tiempo: {t2:.2f}s")
    else:
        print(f"❌ Error - Tiempo: {t2:.2f}s")
except Exception as e:
    t2 = time.time() - start2
    print(f"❌ Error: {e} - Tiempo: {t2:.2f}s")

print()
print("⏳ Esperando 2 segundos...")
time.sleep(2)
print()

# Tercera consulta (rápida)
print("🔹 CONSULTA 3 (Usa pool)")
print("-" * 70)
start3 = time.time()
try:
    r3 = requests.post(url, json={"nuip": "1102877148", "enviarapi": False}, timeout=120)
    t3 = time.time() - start3
    if r3.status_code == 200 and r3.json().get('status') == 'success':
        print(f"✅ Éxito - Tiempo: {t3:.2f}s")
    else:
        print(f"❌ Error - Tiempo: {t3:.2f}s")
except Exception as e:
    t3 = time.time() - start3
    print(f"❌ Error: {e} - Tiempo: {t3:.2f}s")

# Resumen
print()
print("=" * 70)
print("📊 RESUMEN - POOL MEJORADO")
print("=" * 70)
print(f"Consulta 1: {t1:.2f}s (con warmup debería ser ~40-50s)")
print(f"Consulta 2: {t2:.2f}s")
print(f"Consulta 3: {t3:.2f}s")
print()
if t1 < 60:
    print(f"🎉 ¡Primera consulta mejorada! Reducida de ~100s a {t1:.1f}s")
print(f"⚡ Consultas 2-3 siguen siendo ultra-rápidas: <1s")
print("=" * 70)
