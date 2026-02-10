import requests
import time
import json

url = "http://localhost:8080/consultar-puesto-votacion"

print("=" * 70)
print("🚀 DEMO DE OPTIMIZACIÓN - SISTEMA DE POOL DE TOKENS")
print("=" * 70)
print()

# Test 1 - Primera consulta (lenta - resuelve captcha)
print("🔹 CONSULTA 1 (Primera vez - resuelve reCAPTCHA)")
print("-" * 70)
start1 = time.time()
try:
    r1 = requests.post(url, json={"nuip": "1102877148", "enviarapi": False}, timeout=120)
    t1 = time.time() - start1
    if r1.status_code == 200 and r1.json().get('status') == 'success':
        print(f"✅ Éxito - Tiempo: {t1:.2f} segundos")
    else:
        print(f"❌ Error - Tiempo: {t1:.2f} segundos")
except Exception as e:
    t1 = time.time() - start1
    print(f"❌ Error: {e} - Tiempo: {t1:.2f} segundos")

print()
print("⏳ Esperando 3 segundos antes de la siguiente consulta...")
time.sleep(3)
print()

# Test 2 - Segunda consulta (rápida - usa pool)
print("🔹 CONSULTA 2 (Usa token del pool)")
print("-" * 70)
start2 = time.time()
try:
    r2 = requests.post(url, json={"nuip": "1102877148", "enviarapi": False}, timeout=120)
    t2 = time.time() - start2
    if r2.status_code == 200 and r2.json().get('status') == 'success':
        print(f"✅ Éxito - Tiempo: {t2:.2f} segundos")
    else:
        print(f"❌ Error - Tiempo: {t2:.2f} segundos")
except Exception as e:
    t2 = time.time() - start2
    print(f"❌ Error: {e} - Tiempo: {t2:.2f} segundos")

print()
print("⏳ Esperando 3 segundos antes de la siguiente consulta...")
time.sleep(3)
print()

# Test 3 - Tercera consulta (rápida - usa pool)
print("🔹 CONSULTA 3 (Usa token del pool)")
print("-" * 70)
start3 = time.time()
try:
    r3 = requests.post(url, json={"nuip": "1102877148", "enviarapi": False}, timeout=120)
    t3 = time.time() - start3
    if r3.status_code == 200 and r3.json().get('status') == 'success':
        print(f"✅ Éxito - Tiempo: {t3:.2f} segundos")
    else:
        print(f"❌ Error - Tiempo: {t3:.2f} segundos")
except Exception as e:
    t3 = time.time() - start3
    print(f"❌ Error: {e} - Tiempo: {t3:.2f} segundos")

# Resumen
print()
print("=" * 70)
print("📊 RESUMEN DE RENDIMIENTO")
print("=" * 70)
print(f"Consulta 1: {t1:.2f}s (resuelve reCAPTCHA)")
print(f"Consulta 2: {t2:.2f}s (usa pool) - {(t1/t2):.1f}x más rápida")
print(f"Consulta 3: {t3:.2f}s (usa pool) - {(t1/t3):.1f}x más rápida")
print()
print(f"⚡ Mejora promedio: {((t1 - (t2+t3)/2) / t1 * 100):.1f}%")
print("=" * 70)
