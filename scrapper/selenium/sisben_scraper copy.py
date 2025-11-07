import time
import json
import os
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

class SisbenScraperAuto:
    """Scraper automatizado para consultas de nombres en el sistema de la Policía Nacional"""
    
    def __init__(self, headless=False, extension_path=None):
        """
        Inicializa el scraper de Sisben
        
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
        """Configura el driver de Chrome con soporte para extensiones"""
        chrome_options = uc.ChromeOptions()
        
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
        
        # Configuraciones críticas para producción/Linux
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-setuid-sandbox")
        # REMOVIDO: --remote-debugging-port=9222 (causa conflictos con múltiples instancias)
        
        # Configuración de directorios para headless (Fix DevToolsActivePort error)
        chrome_options.add_argument(f"--user-data-dir=/tmp/chrome-user-data-{os.getpid()}")
        chrome_options.add_argument("--crash-dumps-dir=/tmp")
        
        # Argumentos adicionales para estabilidad en producción
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        # REMOVIDO: --single-process (incompatible con --no-sandbox en Linux)
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        chrome_options.add_argument("--ignore-certificate-errors")
        
        # Configuraciones para evitar detección
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        # NOTA: undetected-chromedriver maneja automáticamente la evasión de detección
        
        # Optimizaciones de rendimiento
        chrome_options.add_argument("--disable-extensions")
        # REMOVIDO: --disable-software-rasterizer (duplicado arriba)
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
            # Usar undetected_chromedriver para mejor compatibilidad en Linux
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
        
        # Ejecutar script para ocultar webdriver
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Configurar wait
        self.wait = WebDriverWait(self.driver, 15)
        
        # Si hay extensión cargada, esperar un momento para que se inicialice
        if self.extension_path:
            print("⏳ Esperando que la extensión se inicialice...")
            time.sleep(3)
    
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