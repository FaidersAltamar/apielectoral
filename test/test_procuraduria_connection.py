"""
Script de prueba para verificar la conexión y estructura de la página de Procuraduría
"""
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_procuraduria_connection():
    """Prueba la conexión y estructura de la página de Procuraduría"""
    
    print("🔧 Configurando Chrome...")
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    
    driver = uc.Chrome(options=options, version_main=None)
    wait = WebDriverWait(driver, 20)
    
    try:
        # 1. Navegar a la página
        url = "https://www.procuraduria.gov.co/Pages/Consulta-de-Antecedentes.aspx"
        print(f"\n🌐 Navegando a: {url}")
        driver.get(url)
        
        # Esperar carga completa
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        print("✅ Página cargada")
        
        # 2. Verificar título de la página
        print(f"\n📄 Título: {driver.title}")
        
        # 3. Buscar iframes
        time.sleep(3)
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"\n📦 Iframes encontrados: {len(iframes)}")
        
        for i, iframe in enumerate(iframes):
            src = iframe.get_attribute("src")
            print(f"   {i+1}. {src}")
        
        # 4. Cambiar al primer iframe si existe
        if len(iframes) > 0:
            print(f"\n🔄 Cambiando al iframe principal...")
            driver.switch_to.frame(iframes[0])
            print("✅ Dentro del iframe")
            time.sleep(2)
            
            # 5. Buscar elementos del formulario
            print("\n🔍 Buscando elementos del formulario...")
            
            # Dropdown de tipo de documento
            try:
                tipo_doc = driver.find_element(By.ID, "ddlTipoID")
                print("   ✅ Dropdown tipo documento (ddlTipoID) encontrado")
            except:
                print("   ❌ Dropdown tipo documento NO encontrado")
            
            # Campo de número de ID
            try:
                num_id = driver.find_element(By.ID, "txtNumID")
                print("   ✅ Campo número ID (txtNumID) encontrado")
            except:
                print("   ❌ Campo número ID NO encontrado")
            
            # Pregunta captcha
            try:
                pregunta = driver.find_element(By.ID, "lblPregunta")
                print(f"   ✅ Pregunta captcha encontrada: '{pregunta.text}'")
            except:
                print("   ❌ Pregunta captcha NO encontrada")
            
            # Botón de refrescar pregunta
            try:
                refresh_btn = driver.find_element(By.ID, "ImageButton1")
                print("   ✅ Botón refrescar pregunta (ImageButton1) encontrado")
            except:
                print("   ❌ Botón refrescar pregunta NO encontrado")
            
            # Campo de respuesta
            try:
                respuesta = driver.find_element(By.ID, "txtRespuestaPregunta")
                print("   ✅ Campo respuesta (txtRespuestaPregunta) encontrado")
            except:
                print("   ❌ Campo respuesta NO encontrado")
            
            # Botón consultar
            try:
                btn_consultar = driver.find_element(By.ID, "btnConsultar")
                print("   ✅ Botón consultar (btnConsultar) encontrado")
            except:
                print("   ❌ Botón consultar NO encontrado")
            
            # 6. Capturar HTML del formulario
            print("\n📋 Capturando estructura HTML del formulario...")
            try:
                form_html = driver.find_element(By.TAG_NAME, "form").get_attribute("outerHTML")
                
                # Guardar en archivo para análisis
                with open("procuraduria_form_structure.html", "w", encoding="utf-8") as f:
                    f.write(form_html)
                print("   ✅ HTML guardado en: procuraduria_form_structure.html")
            except Exception as e:
                print(f"   ⚠️ No se pudo capturar HTML: {e}")
            
            # 7. Verificar si hay cambios en la URL del iframe
            current_url = driver.current_url
            print(f"\n🔗 URL actual del iframe: {current_url}")
            
        else:
            print("\n⚠️ No se encontraron iframes. La estructura puede haber cambiado.")
            
            # Buscar formulario directamente en la página principal
            print("\n🔍 Buscando formulario en página principal...")
            try:
                form = driver.find_element(By.TAG_NAME, "form")
                print("   ✅ Formulario encontrado en página principal")
            except:
                print("   ❌ No se encontró formulario en página principal")
        
        # 8. Tomar screenshot
        print("\n📸 Tomando screenshot...")
        driver.save_screenshot("procuraduria_page_test.png")
        print("   ✅ Screenshot guardado: procuraduria_page_test.png")
        
        # 9. Esperar para inspección manual
        print("\n⏸️ Pausa de 10 segundos para inspección manual...")
        time.sleep(10)
        
        print("\n✅ Prueba completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🔒 Cerrando navegador...")
        driver.quit()

if __name__ == "__main__":
    print("=" * 60)
    print("TEST DE CONEXIÓN - PROCURADURÍA")
    print("=" * 60)
    test_procuraduria_connection()
