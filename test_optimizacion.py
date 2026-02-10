import os
import sys
import time
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scrapper.registraduria_scraper_optimizado import RegistraduriaScraperAuto

API_KEY = os.getenv('APIKEY_2CAPTCHA')

print("🚀 TEST DE OPTIMIZACIÓN - Múltiples consultas")
print("=" * 60)

# Crear scraper con pool habilitado
scraper = RegistraduriaScraperAuto(API_KEY, check_balance=False, enable_token_pool=True)

# Esperar un poco a que el pool se llene
print("⏳ Esperando 10 segundos para que el pool se llene...")
time.sleep(10)

# Hacer 3 consultas y medir el tiempo
nuips = ["1102877148", "1102877148", "1102877148 "]

for i, nuip in enumerate(nuips, 1):
    print(f"\n{'='*60}")
    print(f"CONSULTA {i}/3")
    print(f"{'='*60}")
    
    start = time.time()
    resultado = scraper.scrape_nuip(nuip)
    elapsed = time.time() - start
    
    print(f"\n⏱️  TIEMPO DE RESPUESTA: {elapsed:.2f} segundos")
    
    if resultado['status'] == 'success':
        print(f"✅ Datos: {resultado['data'][0]}")
    else:
        print(f"❌ Error: {resultado.get('message')}")
    
    if i < len(nuips):
        print("\n⏳ Esperando 2 segundos...")
        time.sleep(2)

print(f"\n{'='*60}")
print("✅ TEST COMPLETADO")
print(f"{'='*60}")

scraper.close()
