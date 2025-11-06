import time
import json
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime


class ProcuraduriaScraperAuto:
    """Scraper automatizado para consultas de antecedentes en la Procuraduría"""
    
    def __init__(self, headless=False, extension_path=None):
        """
        Inicializa el scraper de Procuraduría
        
        Args:
            headless (bool): Si ejecutar el navegador en modo headless
            extension_path (str): Ruta a la extensión de Chrome (opcional)
        """
        self.headless = headless
        self.extension_path = extension_path
        self.driver = None
        self.wait = None
        self.setup_driver(headless)
    
    def setup_driver(self, headless=False):
        """Configura el driver de Chrome usando undetected_chromedriver"""
        chrome_options = uc.ChromeOptions()
        
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
        
        # Configuraciones críticas para producción/Linux
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-setuid-sandbox")
        
        # Optimizaciones de rendimiento
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--metrics-recording-only")
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--safebrowsing-disable-auto-update")
        
        # Cargar extensión si se proporciona la ruta (solo en modo no-headless)
        if self.extension_path and not headless:
            if os.path.exists(self.extension_path):
                chrome_options.add_argument(f"--load-extension={self.extension_path}")
                print(f"🔌 Cargando extensión desde: {self.extension_path}")
            else:
                print(f"⚠️ Advertencia: No se encontró la extensión en: {self.extension_path}")
        
        try:
            # Usar undetected_chromedriver en lugar de selenium estándar
            self.driver = uc.Chrome(
                options=chrome_options,
                use_subprocess=True,
                version_main=None  # Detecta automáticamente la versión de Chrome
            )
            print("✅ Chrome iniciado con undetected_chromedriver")
        except Exception as e:
            print(f"❌ Error al inicializar Chrome: {e}")
            print("💡 Asegúrate de que Chrome/Chromium esté instalado en el sistema")
            raise
        
        # Configurar wait
        self.wait = WebDriverWait(self.driver, 15)
        
        # Si hay extensión cargada, esperar un momento para que se inicialice
        if self.extension_path:
            print("⏳ Esperando que la extensión se inicialice...")
            time.sleep(3)
    
    def scrape_nuip(self, numero_id, max_retries=3):
        """
        Consulta los antecedentes en la Procuraduría con reintentos automáticos
        
        Args:           
            numero_id (str): Número de identificación
            max_retries (int): Número máximo de reintentos en caso de error
        
        Returns:
            dict: Resultado de la consulta
        """
        start_time = time.time()
        tipo_id = "1"
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"🔍 Consultando antecedentes para ID: {numero_id} (Intento {attempt}/{max_retries})")
                
                # Navegar a la página de la Procuraduría
                url = "https://www.procuraduria.gov.co/Pages/Consulta-de-Antecedentes.aspx"
                print(f"🌐 Navegando a: {url}")
                self.driver.get(url)
                # Esperar a que la página cargue completamente
                self.wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
                print("✅ Página cargada completamente")
                
                # La página usa PowerApps embebido, esperar a que cargue
                print("⏳ Esperando a que PowerApps cargue...")
                time.sleep(3)
                
                # Buscar si hay un iframe de PowerApps
                try:
                    iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                    print(f"📦 Encontrados {len(iframes)} iframes en la página")
                    
                    if len(iframes) > 0:
                        print("🔄 Cambiando al iframe de PowerApps...")
                        # Cambiar al primer iframe (generalmente es el de PowerApps)
                        self.driver.switch_to.frame(iframes[0])
                        print("✅ Cambiado al iframe de PowerApps")
                        time.sleep(2)  # Esperar a que cargue el contenido del iframe
                except Exception as e:
                    print(f"⚠️ No se pudo cambiar al iframe: {e}")
                
                # 1. Seleccionar tipo de documento
                print("🔎 Buscando dropdown de tipo de documento...")
                tipo_doc_dropdown = self.wait.until(
                    EC.presence_of_element_located((By.ID, "ddlTipoID"))
                )
                select_tipo_doc = Select(tipo_doc_dropdown)
                select_tipo_doc.select_by_value("1")
                print(f"✅ Tipo de documento seleccionado: {tipo_id}")
                time.sleep(0.5)
                
                # 2. Llenar el campo de número de identificación
                print("🔎 Buscando campo de número de identificación...")
                numero_id_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "txtNumID"))
                )
                numero_id_field.clear()
                numero_id_field.send_keys(numero_id)
                print(f"✅ Número de identificación ingresado: {numero_id}")
                time.sleep(0.5)
                
                # 3. Obtener la pregunta del captcha y cambiarla si es necesario
                print("🔎 Buscando pregunta del captcha...")
                pregunta_element = self.wait.until(
                    EC.presence_of_element_located((By.ID, "lblPregunta"))
                )
                pregunta_text = pregunta_element.text
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
                        # El elemento correcto es: <input type="image" id="ImageButton1" src="Media/Image/refresh.png">
                        refresh_selectors = [
                            (By.ID, "ImageButton1"),  # Selector correcto del botón de refrescar
                            (By.XPATH, "//input[@type='image' and @id='ImageButton1']"),
                            (By.XPATH, "//input[@type='image' and contains(@src, 'refresh')]"),
                            (By.ID, "btnRefrescarPregunta"),
                            (By.ID, "lnkRefrescarPregunta"),
                            (By.XPATH, "//img[contains(@src, 'refresh')]"),
                            (By.XPATH, "//input[@type='image' and contains(@alt, 'Pregunta')]")
                        ]
                        
                        refresh_clicked = False
                        for selector_type, selector_value in refresh_selectors:
                            try:
                                refresh_btn = self.driver.find_element(selector_type, selector_value)
                                refresh_btn.click()
                                print(f"✅ Click en botón refrescar usando: {selector_value}")
                                refresh_clicked = True
                                time.sleep(1)  # Esperar a que cambie la pregunta
                                break
                            except:
                                continue
                        
                        if not refresh_clicked:
                            print("⚠️ No se encontró el botón de refrescar pregunta")
                            break
                        
                        # Obtener la nueva pregunta
                        pregunta_element = self.wait.until(
                            EC.presence_of_element_located((By.ID, "lblPregunta"))
                        )
                        pregunta_text = pregunta_element.text
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
                respuesta_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "txtRespuestaPregunta"))
                )
                respuesta_field.clear()
                respuesta_field.send_keys(respuesta_captcha)
                print(f"✅ Respuesta del captcha ingresada: {respuesta_captcha}")
                time.sleep(0.5)
                
                # 6. Hacer clic en el botón "Consultar"
                print("🔎 Buscando botón 'Consultar'...")
                consultar_button = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "btnConsultar"))
                )
                consultar_button.click()
                print("✅ Botón 'Consultar' clickeado")
                
                # 7. Esperar a que se procese la solicitud y capturar el resultado
                # Esperar a que aparezca el resultado usando WebDriverWait
                print("⏳ Esperando resultado...")
                self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "datosConsultado"))
                )
                time.sleep(1)  # Pequeña espera adicional para asegurar que todo cargó
            
                # 8. Extraer el nombre completo del resultado
                nombre_completo = None
                try:
                    print("🔎 Buscando nombre completo en el resultado...")
                    # Buscar el div con clase 'datosConsultado'
                    datos_element = self.wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "datosConsultado"))
                    )
                    
                    # Extraer los spans que contienen el nombre
                    spans = datos_element.find_elements(By.TAG_NAME, "span")
                    if len(spans) >= 4:
                        # Los primeros 4 spans contienen: primer nombre, segundo nombre, primer apellido, segundo apellido
                        nombres = [span.text.strip() for span in spans[:4] if span.text.strip()]
                        nombre_completo = " ".join(nombres)
                        print(f"✅ Nombre completo extraído: {nombre_completo}")
                    else:
                        print(f"⚠️ Se encontraron {len(spans)} spans, esperados al menos 4")
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
                    page_source = self.driver.page_source.lower()
                    if "404" in page_source or "not found" in page_source or "access denied" in page_source:
                        print(f"⚠️ Error 404 o acceso denegado detectado en intento {attempt}")
                except:
                    pass
                
                # Reintentar si no es el último intento
                if attempt < max_retries:
                    print(f"🔄 Reintentando en 3 segundos...")
                    time.sleep(3)
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
    
    def _capturar_resultado(self):
        """
        Captura el resultado de la consulta después de hacer clic en "Generar"
        
        Returns:
            dict: Información del resultado capturado incluyendo el nombre
        """
        try:
            # Intentar capturar el div con clase "datosConsultado" que contiene el nombre
            nombre_completo = None
            try:
                # Aumentar el timeout específicamente para este elemento crítico
                wait_resultado = WebDriverWait(self.driver, 30)
                datos_element = wait_resultado.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "datosConsultado"))
                )
                
                # Extraer el texto completo
                texto_completo = datos_element.text
                print(f"📄 Texto capturado: {texto_completo}")
                
                # Extraer los spans que contienen el nombre
                try:
                    spans = datos_element.find_elements(By.TAG_NAME, "span")
                    if len(spans) >= 4:
                        # Los primeros 4 spans contienen: primer nombre, segundo nombre, primer apellido, segundo apellido
                        nombres = [span.text.strip() for span in spans[:4] if span.text.strip()]
                        nombre_completo = " ".join(nombres)
                        print(f"✅ Nombre extraído: {nombre_completo}")
                except Exception as e:
                    print(f"⚠️ Error extrayendo spans del nombre: {e}")
                
                # Buscar si tiene o no antecedentes en el texto
                texto_lower = texto_completo.lower()
                if "no registra antecedentes" in texto_lower or "no tiene antecedentes" in texto_lower:
                    estado_antecedentes = "sin_antecedentes"
                    mensaje = "La persona no registra antecedentes"
                elif "registra antecedentes" in texto_lower or "tiene antecedentes" in texto_lower:
                    estado_antecedentes = "con_antecedentes"
                    mensaje = "La persona registra antecedentes"
                else:
                    estado_antecedentes = "consultado"
                    mensaje = "Consulta realizada exitosamente"
                
                return {
                    "tipo": estado_antecedentes,
                    "mensaje": mensaje,
                    "nombre_completo": nombre_completo,
                    "texto_completo": texto_completo
                }
                    
            except TimeoutException as te:
                print(f"⚠️ No se encontró el elemento datosConsultado después de 30 segundos: {te}")
                
                # Intentar buscar elementos alternativos
                try:
                    # Buscar cualquier div con información de resultado
                    resultado_alt = self.driver.find_elements(By.CLASS_NAME, "resultado")
                    if resultado_alt:
                        print(f"✅ Encontrado elemento alternativo 'resultado': {len(resultado_alt)} elementos")
                    
                    # Imprimir el título de la página actual
                    print(f"📄 Título de la página: {self.driver.title}")
                    
                    # Buscar mensajes de error en la página
                    error_elements = self.driver.find_elements(By.CLASS_NAME, "error")
                    if error_elements:
                        print(f"❌ Encontrados {len(error_elements)} elementos de error")
                        for err in error_elements:
                            print(f"   - {err.text}")
                except Exception as e:
                    print(f"⚠️ No se encontraron elementos alternativos: {e}")

            # Capturar el HTML completo de la página de resultado
            page_source = self.driver.page_source
            
            # Buscar mensajes comunes de resultado
            if "No tiene antecedentes" in page_source or "no registra antecedentes" in page_source.lower():
                return {
                    "tipo": "sin_antecedentes",
                    "mensaje": "La persona no registra antecedentes",
                    "nombre_completo": nombre_completo
                }
            elif "tiene antecedentes" in page_source.lower():
                return {
                    "tipo": "con_antecedentes",
                    "mensaje": "La persona registra antecedentes",
                    "nombre_completo": nombre_completo
                }
            else:
                return {
                    "tipo": "desconocido",
                    "mensaje": "No se pudo determinar el resultado",
                    "page_title": self.driver.title,
                    "nombre_completo": nombre_completo
                }
                
        except Exception as e:
            print(f"⚠️ Error al capturar resultado: {e}")
            return {
                "tipo": "error",
                "mensaje": f"Error al capturar resultado: {str(e)}"
            }
    
    def scrape_multiple_antecedentes(self, queries, delay=5):
        """
        Consulta múltiples antecedentes
        
        Args:
            queries (list): Lista de diccionarios con 'tipo_id' y 'numero_id'
            delay (int): Segundos de espera entre consultas
        
        Returns:
            list: Lista de resultados
        """
        results = []
        total = len(queries)
        
        for i, query in enumerate(queries):
            print(f"\n📋 Procesando consulta {i+1}/{total}")
            result = self.scrape_antecedentes(query["tipo_id"], query["numero_id"])
            results.append(result)
            
            # Delay entre consultas si no es la última
            if i < total - 1:
                print(f"⏳ Esperando {delay} segundos antes de la siguiente consulta...")
                time.sleep(delay)
        
        return results
    
    def close(self):
        """Cierra el navegador"""
        if self.driver:
            self.driver.quit()
            print("🔒 Navegador cerrado")


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
if __name__ == "__main__":
    scraper = ProcuraduriaScraperAuto(headless=False)
    
    try:
        # Ejemplo de consulta con cédula de ciudadanía (tipo_id = 1)
        resultado = scraper.scrape_antecedentes("1", "1102877148")
        
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
        scraper.close()
