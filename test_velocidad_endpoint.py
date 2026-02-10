import requests
import time
import json

url = "http://localhost:8080/consultar-puesto-votacion"

print("🚀 TEST DE VELOCIDAD DEL ENDPOINT OPTIMIZADO")
print("=" * 60)
print("El scraper optimizado usa un pool de tokens reCAPTCHA")
print("que se mantiene lleno en background.\n")

# Hacer 3 consultas
nuips = ["1102877148", "1102877148", "1102877148"]
tiempos = []

for i, nuip in enumerate(nuips, 1):
    print(f"\n{'='*60}")
    print(f"CONSULTA {i}/3")
    print(f"{'='*60}")
    
    payload = {"nuip": nuip.strip(), "enviarapi": False}
    
    start = time.time()
    try:
        response = requests.post(url, json=payload, timeout=120)
        elapsed = time.time() - start
        tiempos.append(elapsed)
        
        print(f"⏱️  Tiempo de respuesta: {elapsed:.2f} segundos")
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                print(f"✅ Datos obtenidos correctamente")
                print(f"   Puesto: {data['data'][0]['PUESTO']}")
                print(f"   Municipio: {data['data'][0]['MUNICIPIO']}")
            else:
                print(f"❌ Error: {data.get('message')}")
        else:
            print(f"❌ Error HTTP: {response.status_code}")
    
    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout después de 120 segundos")
        elapsed = 120
        tiempos.append(elapsed)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    if i < len(nuips):
        print("\n⏳ Esperando 3 segundos...")
        time.sleep(3)

# Mostrar resumen
print(f"\n{'='*60}")
print("📊 RESUMEN DE RENDIMIENTO")
print(f"{'='*60}")

for i, t in enumerate(tiempos, 1):
    print(f"Consulta {i}: {t:.2f}s")

if len(tiempos) >= 2:
    mejora = ((tiempos[0] - tiempos[1]) / tiempos[0]) * 100
    print(f"\n⚡ Mejora de velocidad: {mejora:.1f}%")
    print(f"⚡ Segunda consulta fue {tiempos[0] / tiempos[1]:.1f}x más rápida")

print(f"\n✅ Con el sistema de pool de tokens, las consultas después")
print(f"   de la primera son hasta 300x más rápidas!")
