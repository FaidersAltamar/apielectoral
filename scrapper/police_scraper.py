import time
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class PoliciaScraperAuto:
    """Scraper automatizado para consultas de nombres en el sistema de la Policía Nacional usando requests y BeautifulSoup"""
    
    def __init__(self, headless=None):
        """
        Inicializa el scraper de policía con requests y BeautifulSoup
        
        Args:
            headless: Parámetro ignorado (mantenido por compatibilidad)
        """
        self.session = requests.Session()
        self.base_url = "https://srvcnpc.policia.gov.co/PSC/frm_cnp_consulta.aspx"
        
        # Configurar headers para simular un navegador real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        print("✅ Scraper inicializado con requests y BeautifulSoup")
    
    def get_page_content(self):
        """Obtiene el contenido HTML de la página inicial"""
        try:
            print(f"🌐 Obteniendo página: {self.base_url}")
            response = self.session.get(self.base_url, timeout=15)
            response.raise_for_status()
            print("✅ Página obtenida correctamente")
            return response.text
        except requests.RequestException as e:
            print(f"❌ Error al obtener la página: {e}")
            return None
    
    def parse_page(self, html_content):
        """Parsea el contenido HTML con BeautifulSoup"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup
        except Exception as e:
            print(f"❌ Error al parsear HTML: {e}")
            return None
    
    def extract_form_data(self, soup):
        """Extrae todos los campos hidden y viewstate del formulario ASP.NET"""
        try:
            form_data = {}
            
            # Buscar todos los inputs hidden (crítico para ASP.NET)
            hidden_inputs = soup.find_all('input', type='hidden')
            for hidden in hidden_inputs:
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name:
                    form_data[name] = value
            
            print(f"✅ Extraídos {len(form_data)} campos del formulario")
            return form_data
        except Exception as e:
            print(f"❌ Error al extraer datos del formulario: {e}")
            return {}
    
    def submit_form(self, nuip, fecha_expedicion, form_data):
        """Envía el formulario de consulta con POST request"""
        try:
            print("📤 Enviando formulario de consulta...")
            
            # Preparar datos del formulario
            post_data = form_data.copy()
            post_data.update({
                'ctl00$ContentPlaceHolder3$ddlTipoDoc': '55',  # Tipo de documento
                'ctl00$ContentPlaceHolder3$txtExpediente': str(nuip),
                'ctl00$ContentPlaceHolder3$txtFechaexp': str(fecha_expedicion),
                'ctl00$ContentPlaceHolder3$btnConsultar2': 'Consultar',
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': ''
            })
            
            print(f"🔍 Datos del formulario a enviar:")
            print(f"   - Tipo Doc: 55")
            print(f"   - NUIP: {nuip}")
            print(f"   - Fecha: {fecha_expedicion}")
            
            # Actualizar headers para el POST
            headers = self.session.headers.copy()
            headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://srvcnpc.policia.gov.co',
                'Referer': self.base_url
            })
            
            # Enviar formulario
            print("⏳ Enviando POST request y esperando respuesta del servidor...")
            response = self.session.post(
                self.base_url,
                data=post_data,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            print("✅ Respuesta recibida del servidor")
            
            # Esperar un momento adicional
            time.sleep(2)
            
            return response.text
            
        except requests.RequestException as e:
            print(f"❌ Error al enviar formulario: {e}")
            return None
    
    def scrape_name_by_nuip(self, nuip, fecha_expedicion, max_retries=3):
        """
        Consulta el nombre de una persona por NUIP y fecha de expedición
        
        Args:
            nuip (str): Número único de identificación personal
            fecha_expedicion (str): Fecha de expedición en formato dd/mm/yyyy
            max_retries (int): Número máximo de reintentos en caso de error
        
        Returns:
            dict: Resultado de la consulta
        """
        start_time = time.time()
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"\n{'='*50}")
                print(f"🔍 Consultando nombre para NUIP: {nuip}, Fecha: {fecha_expedicion} (Intento {attempt}/{max_retries})")
                print(f"{'='*50}")
                
                # 1. Obtener página inicial
                html_content = self.get_page_content()
                if not html_content:
                    raise Exception("Error al obtener la página inicial")
                
                # 2. Parsear página
                soup = self.parse_page(html_content)
                if not soup:
                    raise Exception("Error al parsear la página")
                
                # 3. Extraer datos del formulario (ViewState, etc.)
                form_data = self.extract_form_data(soup)
                
                # 4. Enviar formulario
                response_html = self.submit_form(nuip, fecha_expedicion, form_data)
                if not response_html:
                    raise Exception("Error al enviar formulario")
                
                # 5. Extraer el nombre del resultado
                nombre = self._extract_name(response_html)
                
                if nombre:
                    execution_time = time.time() - start_time
                    result = {
                        "status": "success",
                        "message": "Nombre encontrado exitosamente",
                        "nuip": nuip,
                        "fecha_expedicion": fecha_expedicion,
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
                        time.sleep(2)
                        continue
                    else:
                        execution_time = time.time() - start_time
                        return {
                            "status": "not_found",
                            "message": "No se encontró información para los datos proporcionados",
                            "nuip": nuip,
                            "fecha_expedicion": fecha_expedicion,
                            "name": None,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "execution_time_seconds": round(execution_time, 2)
                        }
                
            except Exception as e:
                last_error = e
                print(f"❌ Error en intento {attempt}: {e}")
                
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
            "nuip": nuip,
            "fecha_expedicion": fecha_expedicion,
            "name": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "execution_time_seconds": round(execution_time, 2)
        }
    
    def _extract_name(self, html_content):
        """
        Extrae el nombre del resultado de la consulta
        
        Args:
            html_content (str): Contenido HTML de la respuesta
        
        Returns:
            str: Nombre completo o None si no se encuentra
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Buscar el elemento que contiene el nombre
            nombre_element = soup.find('span', id='ctl00_ContentPlaceHolder3_txtNameUser')
            
            if nombre_element:
                nombre = nombre_element.get_text(strip=True)
                
                # Remover el punto final si existe
                if nombre.endswith('.'):
                    nombre = nombre[:-1]
                
                if nombre:
                    print(f"✅ Nombre extraído: {nombre}")
                    return nombre
            
            print("⚠️ No se encontró el elemento del nombre")
            return None
            
        except Exception as e:
            print(f"⚠️ Error al extraer nombre: {e}")
            return None
    
    def scrape_multiple_names(self, queries, delay=5):
        """
        Consulta múltiples nombres
        
        Args:
            queries (list): Lista de diccionarios con 'nuip' y 'fecha_expedicion'
            delay (int): Delay en segundos entre consultas
        
        Returns:
            list: Lista de resultados
        """
        results = []
        total = len(queries)
        
        print(f"🚀 Iniciando consulta de {total} nombres...")
        
        for i, query in enumerate(queries):
            print(f"📋 Procesando {i+1}/{total}: NUIP {query['nuip']}")
            
            result = self.scrape_name_by_nuip(query['nuip'], query['fecha_expedicion'])
            results.append(result)
            
            # Delay entre consultas si no es la última
            if i < total - 1:
                print(f"⏳ Esperando {delay} segundos...")
                time.sleep(delay)
        
        print(f"✅ Consulta completada. {len(results)} resultados obtenidos")
        return results
    
    def close(self):
        """Cierra la sesión"""
        if self.session:
            self.session.close()
            print("🔒 Sesión cerrada")


def save_police_results(result, filename=None):
    """
    Guarda los resultados de la consulta de policía en un archivo JSON
    
    Args:
        result (dict or list): Resultado(s) de la consulta
        filename (str): Nombre del archivo (opcional)
    """
    try:
        # Crear directorio de resultados si no existe
        results_dir = "police_results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        
        # Generar nombre de archivo si no se proporciona
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"police_query_{timestamp}.json"
        
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