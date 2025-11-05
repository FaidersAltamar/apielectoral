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

class SisbenScraperAuto:
    """Scraper automatizado para consultas de nombres en el sistema de la Policía Nacional"""
    
    def __init__(self, headless=False):
        """
        Inicializa el scraper de Sisben
        
        Args:
            headless (bool): Si ejecutar el navegador en modo headless
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        self.setup_driver()
    
    def _cleanup_driver_cache(self):
        """Limpia el cache de drivers si está corrupto"""
        import shutil
        
        try:
            # Ruta del cache de undetected-chromedriver en Windows
            cache_path = os.path.join(os.getenv('APPDATA'), 'undetected_chromedriver')
            
            if os.path.exists(cache_path):
                # Verificar si hay archivos problemáticos
                driver_exe = os.path.join(cache_path, 'undetected_chromedriver.exe')
                if os.path.exists(driver_exe):
                    # Intentar eliminar el archivo si está bloqueado
                    try:
                        os.remove(driver_exe)
                        print("🧹 Cache de driver limpiado preventivamente")
                    except (PermissionError, OSError):
                        # El archivo está en uso, no hacer nada
                        pass
        except Exception as e:
            # Si falla la limpieza, continuar de todos modos
            pass
    
    def _force_cleanup_driver_cache(self):
        """Fuerza la limpieza completa del cache de drivers"""
        import shutil
        
        try:
            # Ruta del cache de undetected-chromedriver en Windows
            cache_path = os.path.join(os.getenv('APPDATA'), 'undetected_chromedriver')
            
            if os.path.exists(cache_path):
                print(f"🧹 Eliminando cache completo: {cache_path}")
                shutil.rmtree(cache_path, ignore_errors=True)
                time.sleep(1)  # Esperar un momento para que el sistema libere los archivos
                print("✅ Cache eliminado exitosamente")
        except Exception as e:
            print(f"⚠️ No se pudo limpiar el cache: {e}")
    
    def _get_chrome_binary_path(self):
        """Detecta la ruta del binario de Chrome según el sistema operativo"""
        import platform
        import shutil
        
        system = platform.system()
        
        # Posibles ubicaciones de Chrome/Chromium
        possible_paths = []
        
        if system == "Linux":
            possible_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/snap/bin/chromium",
                "/usr/local/bin/chrome",
                "/usr/local/bin/chromium"
            ]
        elif system == "Windows":
            possible_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
            ]
        elif system == "Darwin":  # macOS
            possible_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium"
            ]
        
        # Buscar el primer path que existe
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ Chrome encontrado en: {path}")
                return path
        
        # Intentar usar 'which' en Linux/Mac
        if system in ["Linux", "Darwin"]:
            for cmd in ["google-chrome", "chromium-browser", "chromium"]:
                chrome_path = shutil.which(cmd)
                if chrome_path:
                    print(f"✅ Chrome encontrado via which: {chrome_path}")
                    return chrome_path
        
        print("⚠️ No se encontró Chrome en ubicaciones conocidas")
        return None
    
    def _create_chrome_options(self):
        """Crea un nuevo objeto ChromeOptions con la configuración necesaria"""
        options = uc.ChromeOptions()
        
        # Detectar y establecer ubicación del binario de Chrome
        chrome_binary = self._get_chrome_binary_path()
        if chrome_binary:
            options.binary_location = chrome_binary
            print(f"🔧 Usando Chrome en: {chrome_binary}")
        
        # Argumentos mínimos para evitar detección
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-software-rasterizer")
        
        if self.headless:
            options.add_argument("--headless=new")
        
        return options
    
    def _get_chrome_version(self):
        """Detecta la versión de Chrome instalada"""
        import subprocess
        import re
        
        try:
            # Intentar obtener la versión de Chrome en Windows
            result = subprocess.run(
                ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                match = re.search(r'version\s+REG_SZ\s+(\d+)', result.stdout)
                if match:
                    version = int(match.group(1))
                    print(f"📍 Chrome versión detectada: {version}")
                    return version
        except Exception as e:
            print(f"⚠️ No se pudo detectar la versión de Chrome: {e}")
        
        return None
    
    def setup_driver(self):
        """Configura el driver de Chrome con undetected-chromedriver"""
        try:
            print("🔧 Configurando undetected-chromedriver...")
            
            # Detectar versión de Chrome
            chrome_version = self._get_chrome_version()
            
            # Limpiar cache corrupto si existe
            self._cleanup_driver_cache()
            
            # Crear driver con configuración optimizada para bypass
            print("🚀 Iniciando Chrome con bypass anti-detección...")
            
            # Intentar con diferentes configuraciones
            try:
                # Primer intento: configuración estándar con versión específica
                options = self._create_chrome_options()
                self.driver = uc.Chrome(
                    options=options,
                    driver_executable_path=None,
                    version_main=chrome_version,  # Usar la versión detectada
                    use_subprocess=False,
                    suppress_welcome=True,
                    headless=self.headless
                )
            except FileExistsError as fe:
                print(f"⚠️ Error de archivo existente detectado: {fe}")
                print("🧹 Limpiando cache y reintentando...")
                self._force_cleanup_driver_cache()
                
                try:
                    # Crear nuevas opciones para el reintento
                    options = self._create_chrome_options()
                    self.driver = uc.Chrome(
                        options=options,
                        driver_executable_path=None,
                        version_main=chrome_version,
                        use_subprocess=False,
                        suppress_welcome=True,
                        headless=self.headless
                    )
                except Exception as e_retry:
                    print(f"⚠️ Reintento después de limpieza falló: {e_retry}")
                    raise
                    
            except Exception as e1:
                error_msg = str(e1).lower()
                
                # Si es un error de versión de Chrome, intentar con use_subprocess=True
                if "version" in error_msg or "chromedriver" in error_msg:
                    print(f"⚠️ Error de versión detectado: {e1}")
                    print("🔄 Intentando con configuración alternativa...")
                    
                    try:
                        # Segundo intento: con use_subprocess=True
                        options = self._create_chrome_options()
                        self.driver = uc.Chrome(
                            options=options,
                            driver_executable_path=None,
                            version_main=chrome_version,
                            use_subprocess=True
                        )
                    except Exception as e2:
                        print(f"⚠️ Segundo intento falló: {e2}")
                        print("🔄 Intentando con configuración mínima...")
                        
                        # Tercer intento: configuración mínima
                        options = self._create_chrome_options()
                        self.driver = uc.Chrome(
                            options=options,
                            version_main=chrome_version
                        )
                else:
                    # Si no es un error de versión, re-lanzar
                    raise
            
            # Configurar timeouts optimizados
            self.driver.set_page_load_timeout(30)
            self.wait = WebDriverWait(self.driver, 15)
            
            # Maximizar ventana si no es headless
            if not self.headless:
                self.driver.maximize_window()
            
            print("✅ Driver de Chrome (undetected) configurado correctamente")
            print(f"📍 Versión de Chrome detectada: {self.driver.capabilities.get('browserVersion', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error al configurar el driver: {e}")
            print("\n💡 Soluciones posibles:")
            print("1. Verifica que Chrome esté instalado correctamente")
            print("2. Actualiza undetected-chromedriver: pip install --upgrade undetected-chromedriver")
            print("3. Limpia el cache de drivers: elimina la carpeta %USERPROFILE%\\.wdm")
            print("4. Intenta ejecutar con permisos de administrador")
            import traceback
            traceback.print_exc()
            raise
    
    def scrape_name_by_nuip(self, nuip, max_retries=3):
        """
        Consulta el nombre de una persona por NUIP con reintentos automáticos
        
        Args:
            nuip (str): Número único de identificación personal
            max_retries (int): Número máximo de reintentos en caso de error 404
        
        Returns:
            dict: Resultado de la consulta
        """
        start_time = time.time()
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"🔍 Consultando nombre para NUIP: {nuip} (Intento {attempt}/{max_retries})")
                
                # Navegar directamente al iframe que contiene el formulario
                url = "https://reportes.sisben.gov.co/dnp_sisbenconsulta"
                
                print("🌐 Navegando directamente al formulario del SISBEN...")
                self.driver.get(url)
                
                # Verificar si hay error 404
                page_source = self.driver.page_source.lower()
                if "404" in page_source or "not found" in page_source or "página no encontrada" in page_source:
                    print(f"⚠️ Error 404 detectado en intento {attempt}")
                    if attempt < max_retries:
                        print(f"🔄 Reintentando en 2 segundos...")
                        time.sleep(2)
                        continue
                    else:
                        raise Exception("Error 404: Página no encontrada después de múltiples intentos")
                
                # Esperar a que la página cargue completamente
                print("⏳ Esperando carga completa del formulario...")
                time.sleep(2)
                
                # 1. Seleccionar tipo de documento (value 3)
                tipo_doc_dropdown = self.wait.until(
                    EC.presence_of_element_located((By.ID, "TipoID"))
                )
                select_tipo_doc = Select(tipo_doc_dropdown)
                select_tipo_doc.select_by_value("3")
                print("✅ Tipo de documento seleccionado (value 3)")
                time.sleep(0.3)
                
                # 2. Llenar el campo NUIP
                nuip_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "documento"))
                )
                nuip_field.click()
                nuip_field.clear()
                nuip_field.send_keys(nuip)
                print(f"✅ NUIP ingresado: {nuip}")
                time.sleep(0.3)
                
                # 3. Hacer clic en el botón de consultar
                consultar_btn = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "botonenvio"))
                )
                consultar_btn.click()
                print("✅ Botón de consultar presionado")
                
                # 4. Esperar resultados con espera explícita
                try:
                    # Esperar a que aparezcan los elementos de resultado
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "p.campo1.pt-1.pl-2.font-weight-bold"))
                    )
                    time.sleep(0.5)  # Pequeña espera adicional para estabilidad
                except TimeoutException:
                    print("⚠️ Timeout esperando resultados")
                    time.sleep(1)
                
                # 5. Extraer el nombre
                nombre = self._extract_full_name()
                
                if nombre:
                    execution_time = time.time() - start_time
                    result = {
                        "status": "success",
                        "message": "Nombre encontrado exitosamente",
                        "nuip": nuip,
                        "name": nombre,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "execution_time_seconds": round(execution_time, 2)
                    }
                    print(f"✅ Nombre encontrado: {nombre}")
                    return result
                else:
                    # No se encontró nombre, reintentar si es posible
                    if attempt < max_retries:
                        print(f"⚠️ No se encontró nombre en intento {attempt}, reintentando...")
                        time.sleep(1)
                        continue
                    else:
                        execution_time = time.time() - start_time
                        return {
                            "status": "not_found",
                            "message": "No se encontró información para los datos proporcionados",
                            "nuip": nuip,
                            "name": None,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "execution_time_seconds": round(execution_time, 2)
                        }
                
            except Exception as e:
                last_error = e
                print(f"❌ Error en intento {attempt}: {e}")
                
                
                # Reintentar si no es el último intento
                if attempt < max_retries:
                    print(f"🔄 Reintentando en 2 segundos...")
                    time.sleep(2)
                    continue
        
        # Si llegamos aquí, todos los intentos fallaron
        execution_time = time.time() - start_time
        return {
            "status": "error",
            "message": f"Error después de {max_retries} intentos: {str(last_error)}",
            "nuip": nuip,
            "name": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "execution_time_seconds": round(execution_time, 2)
        }
    
    def _extract_full_name(self):
        """
        Extrae el nombre completo de las etiquetas HTML del SISBEN
        
        Returns:
            str: Nombre completo o None si no se encuentra
        """
        try:
            # Primero verificar si aparece el modal de "NO se encuentra en la base"
            try:
                # Buscar el modal de SweetAlert2
                swal_container = self.driver.find_element(By.CSS_SELECTOR, "div.swal2-container.swal2-center.swal2-backdrop-show")
                
                # Verificar si el contenido indica que NO se encuentra
                swal_content = self.driver.find_element(By.ID, "swal2-content")
                content_text = swal_content.text.strip()
                
                # Si el texto contiene "NO se encuentra", retornar None
                if "NO" in content_text and "se encuentra en la base" in content_text:
                    print(f"⚠️ Persona NO encontrada en la base del Sisbén IV")
                    return None
                    
            except NoSuchElementException:
                # No hay modal de error, continuar con la extracción normal
                pass
            
            # Buscar todos los elementos con clase 'campo1' que contienen el nombre
            name_elements = self.driver.find_elements(By.CSS_SELECTOR, "p.campo1.pt-1.pl-2.font-weight-bold")
            
            if len(name_elements) >= 2:
                # El primer elemento contiene los nombres
                first_names = name_elements[0].text.strip()
                # El segundo elemento contiene los apellidos
                last_names = name_elements[1].text.strip()
                
                # Combinar y limpiar espacios múltiples
                full_name = f"{first_names} {last_names}"
                full_name = ' '.join(full_name.split())  # Eliminar espacios múltiples
                
                return full_name if full_name else None
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error al extraer nombre: {e}")
            return None
    
    def scrape_multiple_names(self, queries, delay=2):
        """
        Consulta múltiples nombres
        
        Args:
            queries (list): Lista de diccionarios con 'nuip'
            delay (int): Delay en segundos entre consultas
        
        Returns:
            list: Lista de resultados
        """
        results = []
        total = len(queries)
        
        print(f"🚀 Iniciando consulta de {total} nombres...")
        
        for i, query in enumerate(queries):
            print(f"📋 Procesando {i+1}/{total}: NUIP {query['nuip']}")
            
            result = self.scrape_name_by_nuip(query['nuip'])
            results.append(result)
            
            # Delay entre consultas si no es la última
            if i < total - 1:
                print(f"⏳ Esperando {delay} segundos...")
                time.sleep(delay)
        
        print(f"✅ Consulta completada. {len(results)} resultados obtenidos")
        return results
    
    def close(self):
        """Cierra el driver del navegador"""
        if self.driver:
            self.driver.quit()
            print("🔒 Driver cerrado correctamente")


def save_sisben_results(result, filename=None):
    """
    Guarda los resultados de la consulta de SISBEN en un archivo JSON
    
    Args:
        result (dict or list): Resultado(s) de la consulta
        filename (str): Nombre del archivo (opcional)
    """
    try:
        # Crear directorio de resultados si no existe
        results_dir = "sisben_results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        
        # Generar nombre de archivo si no se proporciona
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sisben_query_{timestamp}.json"
        
        filepath = os.path.join(results_dir, filename)
        
        # Guardar resultados
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Resultados guardados en: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ Error al guardar resultados: {e}")
        return None


def load_queries_from_file(filepath):
    """
    Carga consultas desde un archivo JSON
    
    Args:
        filepath (str): Ruta del archivo JSON
    
    Returns:
        list: Lista de consultas
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            queries = json.load(f)
        
        print(f"📂 Cargadas {len(queries)} consultas desde {filepath}")
        return queries
        
    except Exception as e:
        print(f"❌ Error al cargar consultas: {e}")
        return []


def create_sample_queries_file():
    """Crea un archivo de ejemplo con consultas"""
    sample_queries = [
        {
            "nuip": "1102877148",
            "fecha_expedicion": "15/03/1990"
        },
        {
            "nuip": "1234567890",
            "fecha_expedicion": "01/01/1985"
        }
    ]
    
    filename = "sample_queries.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(sample_queries, f, indent=2, ensure_ascii=False)
        
        print(f"📝 Archivo de ejemplo creado: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error al crear archivo de ejemplo: {e}")
        return None


def generate_report(results):
    """
    Genera un reporte resumen de los resultados
    
    Args:
        results (list): Lista de resultados
    
    Returns:
        dict: Reporte resumen
    """
    if not results:
        return {"error": "No hay resultados para procesar"}
    
    total = len(results)
    successful = len([r for r in results if r.get("status") == "success"])
    not_found = len([r for r in results if r.get("status") == "not_found"])
    errors = len([r for r in results if r.get("status") == "error"])
    
    # Calcular tiempo promedio de ejecución
    execution_times = [r.get("execution_time_seconds", 0) for r in results]
    avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
    
    report = {
        "summary": {
            "total_queries": total,
            "successful": successful,
            "not_found": not_found,
            "errors": errors,
            "success_rate": round((successful / total) * 100, 2) if total > 0 else 0,
            "average_execution_time": round(avg_time, 2)
        },
        "successful_results": [r for r in results if r.get("status") == "success"],
        "failed_results": [r for r in results if r.get("status") != "success"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return report


def test_police_scraper():
    """Función de prueba para el scraper de policía"""
    scraper = PoliciaScraperAuto(headless=False)
    
    try:
        # Prueba con un NUIP de ejemplo
        result = scraper.scrape_name_by_nuip("1102877148", "15/03/1990")
        print("Resultado de la prueba:", json.dumps(result, indent=2, ensure_ascii=False))
        
        # Guardar resultado
        save_police_results(result)
        
    finally:
        scraper.close()


def main():
    """Función principal para ejecutar consultas masivas"""
    print("🚀 Scraper de Policía Nacional - Consulta de Nombres")
    print("=" * 50)
    
    # Crear archivo de ejemplo si no existe
    if not os.path.exists("sample_queries.json"):
        create_sample_queries_file()
    
    # Cargar consultas
    queries_file = input("Ingrese la ruta del archivo de consultas (Enter para usar sample_queries.json): ").strip()
    if not queries_file:
        queries_file = "sample_queries.json"
    
    queries = load_queries_from_file(queries_file)
    if not queries:
        print("❌ No se pudieron cargar las consultas")
        return
    
    # Configurar scraper
    headless = input("¿Ejecutar en modo headless? (y/n, default: y): ").strip().lower()
    headless = headless != 'n'
    
    delay = input("Delay entre consultas en segundos (default: 5): ").strip()
    try:
        delay = int(delay) if delay else 5
    except ValueError:
        delay = 5
    
    # Ejecutar scraping
    scraper = PoliciaScraperAuto(headless=headless)
    
    try:
        results = scraper.scrape_multiple_names(queries, delay=delay)
        
        # Guardar resultados
        save_police_results(results)
        
        # Generar y mostrar reporte
        report = generate_report(results)
        print("\n📊 REPORTE FINAL:")
        print("=" * 30)
        print(f"Total de consultas: {report['summary']['total_queries']}")
        print(f"Exitosas: {report['summary']['successful']}")
        print(f"No encontradas: {report['summary']['not_found']}")
        print(f"Errores: {report['summary']['errors']}")
        print(f"Tasa de éxito: {report['summary']['success_rate']}%")
        print(f"Tiempo promedio: {report['summary']['average_execution_time']}s")
        
        # Guardar reporte
        save_police_results(report, "police_report.json")
        
    finally:
        scraper.close()


if __name__ == "__main__":
    # Descomenta la línea que quieras usar:
    test_police_scraper()  # Para prueba individual
    # main()  # Para consultas masivas