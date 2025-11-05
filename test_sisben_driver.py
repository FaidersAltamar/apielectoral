"""
Script de prueba para verificar la configuración del driver de Sisben
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapper.sisben_scraper import SisbenScraperAuto

def test_driver_setup():
    """Prueba la configuración del driver"""
    print("=" * 60)
    print("🧪 PRUEBA DE CONFIGURACIÓN DEL DRIVER DE SISBEN")
    print("=" * 60)
    
    try:
        # Intentar crear el scraper (esto ejecuta setup_driver)
        print("\n1️⃣ Intentando inicializar el scraper...")
        scraper = SisbenScraperAuto(headless=False)
        
        print("\n2️⃣ Verificando que el driver esté funcionando...")
        # Navegar a una página simple para verificar
        scraper.driver.get("https://www.google.com")
        print(f"✅ Navegación exitosa a Google")
        print(f"✅ Título de la página: {scraper.driver.title}")
        
        print("\n3️⃣ Cerrando el driver...")
        scraper.close()
        
        print("\n" + "=" * 60)
        print("✅ PRUEBA EXITOSA - El driver está configurado correctamente")
        print("=" * 60)
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ PRUEBA FALLIDA - Error: {e}")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_driver_setup()
    sys.exit(0 if success else 1)
