import os
import requests
import json
from dotenv import load_dotenv
from utils.captcha_solver import TwoCaptchaSolver

# Cargar variables de entorno
load_dotenv()

# Configuración
API_KEY = os.getenv('APIKEY_2CAPTCHA')

# Si no hay API key, intentar obtenerla del archivo
if not API_KEY:
    print("❌ No se encontró la API key en las variables de entorno")
    print("Por favor, asegúrate de tener el archivo .env con APIKEY_2CAPTCHA")
    exit(1)

SITEKEY = '6Lc9DmgrAAAAAJAjWVhjDy1KSgqzqJikY5z7I9SV'
PAGE_URL = 'https://eleccionescolombia.registraduria.gov.co/identificacion'
API_URL = 'https://apiweb-eleccionescolombia.infovotantes.com/api/v1/citizen/get-information'

print("🔑 Iniciando prueba de API directa...")
print(f"API Key: {API_KEY[:10]}...")

# Paso 1: Resolver reCAPTCHA
print("\n🤖 Resolviendo reCAPTCHA...")
solver = TwoCaptchaSolver(API_KEY)
captcha_token = solver.solve_recaptcha_v2(SITEKEY, PAGE_URL, invisible=False)

if not captcha_token:
    print("❌ No se pudo resolver el reCAPTCHA")
    exit(1)

print(f"✅ Token obtenido: {captcha_token[:50]}...")

# Paso 2: Preparar request a la API
print("\n📤 Enviando request a la API...")

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'es-419,es;q=0.9',
    'Authorization': f'Bearer {captcha_token}',
    'Content-Type': 'application/json',
    'Origin': 'https://eleccionescolombia.registraduria.gov.co',
    'Sec-Ch-Ua': '"Chromium";v="142", "Opera";v="126", "Not_A Brand";v="99"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'Priority': 'u=1, i',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
}

payload = {
    "identification": "1102877148",
    "identification_type": "CC",
    "election_code": "congreso",
    "module": "polling_place",
    "platform": "web"
}

print(f"🔍 URL: {API_URL}")
print(f"🔍 Payload: {json.dumps(payload, indent=2)}")

# Paso 3: Hacer request
try:
    response = requests.post(API_URL, json=payload, headers=headers, timeout=15)
    
    print(f"\n📊 Status Code: {response.status_code}")
    print(f"📊 Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("✅ ¡Éxito!")
        data = response.json()
        print(f"\n📦 Datos recibidos:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Error {response.status_code}")
        print(f"Respuesta: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
