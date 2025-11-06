import time
import json
import os
import sys
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from datetime import datetime

# Configurar ProactorEventLoop para Windows (necesario para Playwright)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


class ProcuraduriaScraperAuto:
    """Scraper automatizado para consultas de antecedentes en la Procuraduría usando Playwright Async"""
    
    def __init__(self, headless=False, extension_path=None):
        """
        Inicializa el scraper de Procuraduría
        
        Args:
            headless (bool): Si ejecutar el navegador en modo headless
            extension_path (str): Ruta a la extensión de Chrome (opcional)
        """
        self.headless = headless
        self.extension_path = extension_path
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        # No llamar setup_driver aquí, se llamará de forma asíncrona
    
    async def setup_driver(self, headless=False):
        """Configura Playwright con Chromium de forma asíncrona"""
        try:
            self.playwright = await async_playwright().start()
            
            # Detectar ubicación de Chrome según el sistema operativo
            chrome_binary = None
            if os.name == 'nt':  # Windows
                possible_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
                ]
            else:  # Linux/Unix
                possible_paths = [
                    "/usr/bin/google-chrome",
                    "/usr/bin/google-chrome-stable",
                    "/usr/bin/chromium",
                    "/usr/bin/chromium-browser",
                    "/snap/bin/chromium",
                    "/usr/local/bin/google-chrome",
                    "/opt/google/chrome/google-chrome"
                ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    print(f"✅ Chrome encontrado en: {chrome_binary}")
                    break
            
            # Configurar argumentos de lanzamiento
            launch_args = [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled"
            ]
            
            # Configurar opciones del navegador
            browser_options = {
                "headless": headless,
                "args": launch_args
            }
            
            # Agregar executable_path si se encontró Chrome
            if chrome_binary:
                browser_options["executable_path"] = chrome_binary
            
            # Lanzar navegador de forma asíncrona
            self.browser = await self.playwright.chromium.launch(**browser_options)
            
            # Crear contexto con configuración anti-detección
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Crear página
            self.page = await self.context.new_page()
            
            # Configurar timeout por defecto
            self.page.set_default_timeout(15000)  # 15 segundos
            
            print("✅ Playwright iniciado correctamente")
            
        except Exception as e:
            print(f"❌ Error al inicializar Playwright: {e}")
            print("💡 Asegúrate de haber ejecutado: playwright install chromium")
            raise
    
    async def scrape_nuip(self, numero_id, max_retries=3):
        """
        Consulta los antecedentes en la Procuraduría con reintentos automáticos (async)
        
        Args:           
            numero_id (str): Número de identificación
            max_retries (int): Número máximo de reintentos en caso de error
        
        Returns:
            dict: Resultado de la consulta
        """
        # Inicializar el navegador si no está iniciado
        if not self.page:
            await self.setup_driver(self.headless)
        
        start_time = time.time()
        tipo_id = "1"
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"🔍 Consultando antecedentes para ID: {numero_id} (Intento {attempt}/{max_retries})")
                
                # Navegar a la página de la Procuraduría
                url = "https://www.procuraduria.gov.co/Pages/Consulta-de-Antecedentes.aspx"
                print(f"🌐 Navegando a: {url}")
                await self.page.goto(url, wait_until="domcontentloaded")
                print("✅ Página cargada completamente")
                
                # La página usa PowerApps embebido, esperar a que cargue
                print("⏳ Esperando a que PowerApps cargue...")
                await asyncio.sleep(3)
                
                # Buscar si hay un iframe de PowerApps
                try:
                    iframes = self.page.frames
                    print(f"📦 Encontrados {len(iframes)} iframes en la página")
                    
                    if len(iframes) > 1:
                        print("🔄 Cambiando al iframe de PowerApps...")
                        # Cambiar al primer iframe (generalmente es el de PowerApps)
                        frame = iframes[1]  # El índice 0 es la página principal
                        print("✅ Cambiado al iframe de PowerApps")
                        await asyncio.sleep(2)  # Esperar a que cargue el contenido del iframe
                    else:
                        frame = self.page
                except Exception as e:
                    print(f"⚠️ No se pudo cambiar al iframe: {e}")
                    frame = self.page
                
                # 1. Seleccionar tipo de documento
                print("🔎 Buscando dropdown de tipo de documento...")
                await frame.wait_for_selector("#ddlTipoID", timeout=15000)
                await frame.select_option("#ddlTipoID", value="1")
                print(f"✅ Tipo de documento seleccionado: {tipo_id}")
                await asyncio.sleep(0.5)
                
                # 2. Llenar el campo de número de identificación
                print("🔎 Buscando campo de número de identificación...")
                await frame.wait_for_selector("#txtNumID", timeout=15000)
                await frame.fill("#txtNumID", "")
                await frame.fill("#txtNumID", numero_id)
                print(f"✅ Número de identificación ingresado: {numero_id}")
                await asyncio.sleep(0.5)
                
                # 3. Obtener la pregunta del captcha y cambiarla si es necesario
                print("🔎 Buscando pregunta del captcha...")
                await frame.wait_for_selector("#lblPregunta", timeout=15000)
                pregunta_text = await frame.text_content("#lblPregunta")
                print(f"❓ Pregunta captcha inicial: {pregunta_text}")
                
                # 4. Intentar cambiar la pregunta hasta encontrar una conocida
                respuesta_captcha = self._resolver_pregunta_captcha(pregunta_text, numero_id)
                max_intentos_pregunta = 10
                intento_pregunta = 0
                
                while not respuesta_captcha and intento_pregunta < max_intentos_pregunta:
                    intento_pregunta += 1
                    print(f"🔄 Pregunta desconocida, cambiando pregunta (intento {intento_pregunta}/{max_intentos_pregunta})...")
                    
                    try:
                        # Buscar el botón de refrescar/cambiar pregunta
                        refresh_selectors = [
                            "#ImageButton1",
                            "input[type='image'][id='ImageButton1']",
                            "input[type='image'][src*='refresh']",
                            "#btnRefrescarPregunta",
                            "#lnkRefrescarPregunta",
                            "img[src*='refresh']",
                            "input[type='image'][alt*='Pregunta']"
                        ]
                        
                        refresh_clicked = False
                        for selector in refresh_selectors:
                            try:
                                if await frame.locator(selector).count() > 0:
                                    await frame.click(selector)
                                    print(f"✅ Click en botón refrescar usando: {selector}")
                                    refresh_clicked = True
                                    await asyncio.sleep(1)  # Esperar a que cambie la pregunta
                                    break
                            except:
                                continue
                        
                        if not refresh_clicked:
                            print("⚠️ No se encontró el botón de refrescar pregunta")
                            break
                        
                        # Obtener la nueva pregunta
                        await frame.wait_for_selector("#lblPregunta", timeout=15000)
                        pregunta_text = await frame.text_content("#lblPregunta")
                        print(f"❓ Nueva pregunta: {pregunta_text}")
                        
                        # Intentar resolver la nueva pregunta
                        respuesta_captcha = self._resolver_pregunta_captcha(pregunta_text, numero_id)
                        
                    except Exception as e:
                        print(f"⚠️ Error al cambiar pregunta: {e}")
                        break
                
                if not respuesta_captcha:
                    execution_time = time.time() - start_time
                    return {
                    "status": "error",
                    "message": f"No se pudo resolver la pregunta del captcha: {pregunta_text}",
                    "name": "",
                    "tipo_id": tipo_id,
                    "numero_id": numero_id,
                    "pregunta_captcha": pregunta_text,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "execution_time_seconds": time.time() - start_time
                    }
                
                # 5. Llenar la respuesta del captcha
                print("🔎 Buscando campo de respuesta del captcha...")
                await frame.wait_for_selector("#txtRespuestaPregunta", timeout=15000)
                await frame.fill("#txtRespuestaPregunta", "")
                await frame.fill("#txtRespuestaPregunta", respuesta_captcha)
                print(f"✅ Respuesta del captcha ingresada: {respuesta_captcha}")
                await asyncio.sleep(0.5)
                
                # 6. Hacer clic en el botón "Consultar"
                print("🔎 Buscando botón 'Consultar'...")
                await frame.wait_for_selector("#btnConsultar", timeout=15000)
                await frame.click("#btnConsultar")
                print("✅ Botón 'Consultar' clickeado")
                
                # 7. Esperar a que se procese la solicitud y capturar el resultado
                print("⏳ Esperando resultado...")
                await frame.wait_for_selector(".datosConsultado", timeout=15000)
                await asyncio.sleep(1)  # Pequeña espera adicional para asegurar que todo cargó
            
                # 8. Extraer el nombre completo del resultado
                nombre_completo = None
                try:
                    print("🔎 Buscando nombre completo en el resultado...")
                    # Buscar el div con clase 'datosConsultado'
                    datos_element = frame.locator(".datosConsultado")
                    
                    # Extraer los spans que contienen el nombre
                    spans = datos_element.locator("span")
                    span_count = await spans.count()
                    
                    if span_count >= 4:
                        # Los primeros 4 spans contienen: primer nombre, segundo nombre, primer apellido, segundo apellido
                        nombres = []
                        for i in range(4):
                            text = await spans.nth(i).text_content()
                            text = text.strip()
                            if text:
                                nombres.append(text)
                        nombre_completo = " ".join(nombres)
                        print(f"✅ Nombre completo extraído: {nombre_completo}")
                    else:
                        print(f"⚠️ Se encontraron {span_count} spans, esperados al menos 4")
                except Exception as e:
                    print(f"⚠️ No se pudo extraer el nombre completo: {e}")
                
                execution_time = time.time() - start_time
                
                return {
                    "status": "success",
                    "message": "Consulta realizada exitosamente",
                    "tipo_id": tipo_id,
                    "numero_id": numero_id,
                    "name": nombre_completo,
                    "pregunta_captcha": pregunta_text,
                    "respuesta_captcha": respuesta_captcha,              
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "execution_time_seconds": execution_time
                }
                
            except Exception as e:
                last_error = e
                print(f"❌ Error en intento {attempt}: {e}")
                
                
                # Verificar si hay error 404 o bloqueo
                try:
                    page_source = await self.page.content()
                    page_source = page_source.lower()
                    if "404" in page_source or "not found" in page_source or "access denied" in page_source:
                        print(f"⚠️ Error 404 o acceso denegado detectado en intento {attempt}")
                except:
                    pass
                
                # Reintentar si no es el último intento
                if attempt < max_retries:
                    print(f"🔄 Reintentando en 3 segundos...")
                    await asyncio.sleep(3)
                    continue
        
        # Si llegamos aquí, todos los intentos fallaron
        execution_time = time.time() - start_time
        return {
            "status": "error",
            "message": f"Error después de {max_retries} intentos: {str(last_error)}",
            "name": "",
            "tipo_id": tipo_id,
            "numero_id": numero_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "execution_time_seconds": execution_time
        }
    
    def _resolver_pregunta_captcha(self, pregunta, nuip):
        """
        Resuelve la pregunta del captcha basándose en un diccionario de respuestas conocidas
        
        Args:
            pregunta (str): Texto de la pregunta
        
        Returns:
            str: Respuesta a la pregunta o None si no se conoce
        """
        # Diccionario de preguntas y respuestas conocidas
        respuestas_conocidas = {
            "¿ Cual es la Capital de Colombia (sin tilde)?": "Bogota",
            "¿Cual es la Capital de Colombia (sin tilde)?": "Bogota",
            "Capital de Colombia": "Bogota",
            "capital de colombia": "Bogota",
            "¿ Cual es la Capital de Antioquia (sin tilde)?": "Medellin",
            "¿ Cual es la Capital del Atlantico?": "Barranquilla",
            "¿ Cuanto es 6 + 2 ?": "8",  
            "¿ Cuanto es 2 X 3 ?": "6",
            "¿ Cuanto es 3 X 3 ?": "9",
            "¿ Cuanto es 9 - 2 ?": "7",
            "¿ Cuanto es 3 + 2 ?": "5",
            "¿ Cuanto es 9 - 6 ?": "3",
            "¿ Cuanto es 6 - 2 ?": "4",
            "¿ Cuanto es 5 + 3 ?": "8",
            "¿ Cuanto es 5 - 2 ?": "3",
            "¿ Cuanto es 4 X 2 ?": "8",
            "¿ Cuanto es 4 + 3 ?": "7",
            "¿ Cual es la Capital de Antioquia (sin tilde)? ":"Medellin",
            "¿ Cual es la Capital del Atlantico?":"Barranquilla",
            "¿ Cual es la Capital del Vallle del Cauca?":"Cali",
            "¿Escriba los tres primeros digitos del documento a consultar?": nuip[:3]
        }
        
        # Buscar la respuesta en el diccionario (case-insensitive)
        pregunta_lower = pregunta.lower().strip()
        
        for key, value in respuestas_conocidas.items():
            if key.lower() in pregunta_lower or pregunta_lower in key.lower():
                return value
        
        # Si contiene "capital" y "colombia", devolver Bogota
        if "capital" in pregunta_lower and "colombia" in pregunta_lower:
            return "Bogota"
        
        return None
    
    async def close(self):
        """Cierra el navegador y Playwright de forma asíncrona"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("🔒 Navegador cerrado")
        except Exception as e:
            print(f"⚠️ Error al cerrar navegador: {e}")


def save_procuraduria_results(data, filename=None):
    """
    Guarda los resultados de la consulta en un archivo JSON
    
    Args:
        data: Datos a guardar (dict o list)
        filename: Nombre del archivo (opcional)
    
    Returns:
        str: Ruta del archivo guardado
    """
    # Crear directorio si no existe
    os.makedirs("procuraduria_results", exist_ok=True)
    
    # Generar nombre de archivo si no se proporciona
    if filename is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"procuraduria_results/procuraduria_query_{timestamp}.json"
    elif not filename.startswith("procuraduria_results/"):
        filename = f"procuraduria_results/{filename}"
    
    # Guardar datos
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Resultados guardados en: {filename}")
    return filename


# Ejemplo de uso
async def main():
    """Función principal asíncrona para ejemplo de uso"""
    scraper = ProcuraduriaScraperAuto(headless=False)
    
    try:
        # Ejemplo de consulta con cédula de ciudadanía
        resultado = await scraper.scrape_nuip("1102877148")
        
        print(f"\n📊 RESULTADO FINAL:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        # Guardar resultado
        save_procuraduria_results(resultado)
        
    except KeyboardInterrupt:
        print("\n⚠️ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        print(f"🔍 Traceback completo: {traceback.format_exc()}")
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
