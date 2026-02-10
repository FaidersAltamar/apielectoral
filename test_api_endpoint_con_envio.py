import requests
import json

# URL del endpoint
url = "http://localhost:8080/consultar-puesto-votacion"

# Datos de la petición con enviarapi=True
payload = {
    "nuip": "1102877148",
    "enviarapi": True
}

print("🚀 Probando endpoint /consultar-puesto-votacion con enviarapi=True")
print(f"📍 URL: {url}")
print(f"📦 Payload: {json.dumps(payload, indent=2)}")
print("\n⏳ Enviando petición...")

try:
    response = requests.post(url, json=payload, timeout=120)
    
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ ¡Éxito!")
        data = response.json()
        print(f"\n📦 Respuesta:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Error {response.status_code}")
        print(f"Respuesta: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ No se puede conectar al servidor. ¿Está corriendo uvicorn?")
except Exception as e:
    print(f"❌ Error: {e}")
