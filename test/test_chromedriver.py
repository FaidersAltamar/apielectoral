"""
Script de prueba para verificar que ChromeDriver funciona correctamente
"""
import sys
import os

def test_police_scraper():
    """Prueba el scraper de policía con webdriver-manager"""
    print("\n" + "="*60)
    print("🧪 PRUEBA 1: Police Scraper (webdriver-manager)")
    print("="*60)
    try:
        from scrapper.police_scraper import PoliciaScraperAuto
        
        print("📦 Inicializando scraper de policía...")
        scraper = PoliciaScraperAuto(headless=True)
        print("✅ Scraper de policía inicializado correctamente")
        print(f"📍 Versión de Chrome: {scraper.driver.capabilities.get('browserVersion', 'Unknown')}")
        scraper.close()
        return True
    except Exception as e:
        print(f"❌ Error en scraper de policía: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_registraduria_scraper():
    """Prueba el scraper de registraduría con webdriver-manager"""
    print("\n" + "="*60)
    print("🧪 PRUEBA 2: Registraduria Scraper (webdriver-manager)")
    print("="*60)
    try:
        # Necesitamos una API key para este scraper
        api_key = os.getenv('APIKEY_2CAPTCHA')
        if not api_key:
            print("⚠️ Saltando prueba de Registraduría (no hay API key)")
            return None
            
        from scrapper.registraduria_scraper import RegistraduriaScraperAuto
        
        print("📦 Inicializando scraper de registraduría...")
        scraper = RegistraduriaScraperAuto(api_key, headless=True)
        print("✅ Scraper de registraduría inicializado correctamente")
        print(f"📍 Versión de Chrome: {scraper.driver.capabilities.get('browserVersion', 'Unknown')}")
        scraper.close()
        return True
    except Exception as e:
        print(f"❌ Error en scraper de registraduría: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_procuraduria_scraper():
    """Prueba el scraper de procuraduría con undetected-chromedriver"""
    print("\n" + "="*60)
    print("🧪 PRUEBA 3: Procuraduria Scraper (undetected-chromedriver)")
    print("="*60)
    try:
        from scrapper.procuraduria_scraper import ProcuraduriaScraperAuto
        
        print("📦 Inicializando scraper de procuraduría...")
        scraper = ProcuraduriaScraperAuto(headless=True)
        print("✅ Scraper de procuraduría inicializado correctamente")
        print(f"📍 Versión de Chrome: {scraper.driver.capabilities.get('browserVersion', 'Unknown')}")
        scraper.close()
        return True
    except Exception as e:
        print(f"❌ Error en scraper de procuraduría: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sisben_scraper():
    """Prueba el scraper de sisben con undetected-chromedriver"""
    print("\n" + "="*60)
    print("🧪 PRUEBA 4: Sisben Scraper (undetected-chromedriver)")
    print("="*60)
    try:
        from scrapper.sisben_scraper import SisbenScraperAuto
        
        print("📦 Inicializando scraper de sisben...")
        scraper = SisbenScraperAuto(headless=True)
        print("✅ Scraper de sisben inicializado correctamente")
        print(f"📍 Versión de Chrome: {scraper.driver.capabilities.get('browserVersion', 'Unknown')}")
        scraper.close()
        return True
    except Exception as e:
        print(f"❌ Error en scraper de sisben: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "🚀 "*20)
    print("VERIFICACIÓN DE CHROMEDRIVER - API ELECTORAL")
    print("🚀 "*20)
    
    # Cargar variables de entorno
    from dotenv import load_dotenv
    load_dotenv()
    
    results = {
        "Police": test_police_scraper(),
        "Registraduria": test_registraduria_scraper(),
        "Procuraduria": test_procuraduria_scraper(),
        "Sisben": test_sisben_scraper()
    }
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for name, result in results.items():
        if result is True:
            print(f"✅ {name}: PASÓ")
        elif result is False:
            print(f"❌ {name}: FALLÓ")
        else:
            print(f"⚠️ {name}: SALTADO")
    
    print(f"\n📈 Total: {passed} pasaron, {failed} fallaron, {skipped} saltados")
    
    if failed == 0:
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("✅ ChromeDriver está configurado correctamente")
        return 0
    else:
        print(f"\n⚠️ {failed} prueba(s) fallaron. Revisa los errores arriba.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
