import requests
import time
import json
import os
import sys
import re
from bs4 import BeautifulSoup
from datetime import datetime

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Importar el solver de captcha desde utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.captcha_solver import TwoCaptchaSolver

class RegistraduriaScraperAuto:
    def __init__(self, captcha_api_key):
        self.captcha_solver = TwoCaptchaSolver(captcha_api_key)
        self.session = requests.Session()
        self.base_url = "https://wsp.registraduria.gov.co/censo/consultar/"
        
        # Configurar headers para simular un navegador real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Verificar balance
        balance_info = self.captcha_solver.get_balance()
        if balance_info.get("success"):
            print(f"💰 2captcha - {balance_info['balance_formatted']} ({balance_info['estimated_requests']} captchas disponibles)")
        else:
            print(f"⚠️ 2captcha - {balance_info.get('message', 'Error al obtener balance')}")
    
    def get_page_content(self):
        """Obtiene el contenido HTML de la página"""
        try:
            print("🌐 Obteniendo página de la Registraduría...")
            response = self.session.get(self.base_url, timeout=10)
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
        """Extrae datos necesarios del formulario"""
        try:
            form_data = {}
            
            # Buscar todos los inputs hidden para incluirlos en el POST
            hidden_inputs = soup.find_all('input', type='hidden')
            for hidden in hidden_inputs:
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name:
                    form_data[name] = value
            
            return form_data
        except Exception as e:
            print(f"❌ Error al extraer datos del formulario: {e}")
            return {}
    
    def get_recaptcha_site_key(self, soup):
        """Extrae dinámicamente el site key del reCAPTCHA desde el HTML"""
        try:
            # Buscar el site key en el elemento div del reCAPTCHA
            recaptcha_element = soup.find('div', class_='g-recaptcha')
            
            if recaptcha_element:
                site_key = recaptcha_element.get('data-sitekey')
                if site_key:
                    print(f"🔍 Site key encontrado dinámicamente: {site_key}")
                    return site_key
            
            print("⚠️ No se pudo extraer el site key dinámicamente, usando el hardcodeado")
            return "6LcthjAgAAAAFIQLxy52074zanHv47cIvmIHglH"
        
        except Exception as e:
            print(f"⚠️ Error al extraer site key: {e}, usando hardcodeado")
            return "6LcthjAgAAAAFIQLxy52074zanHv47cIvmIHglH"
    
    def solve_recaptcha(self, soup):
        """Resuelve el reCAPTCHA automáticamente usando 2captcha"""
        try:
            # Obtener site key dinámicamente
            site_key = self.get_recaptcha_site_key(soup)
            
            print(f"🤖 Resolviendo reCAPTCHA automáticamente con 2captcha...")
            print(f"Site key: {site_key}")
            print(f"URL: {self.base_url}")
            
            # Resolver reCAPTCHA usando la librería oficial
            captcha_response = self.captcha_solver.solve_recaptcha_v2(site_key, self.base_url, invisible=False)
            
            print("✅ reCAPTCHA resuelto correctamente")
            return captcha_response
        
        except Exception as e:
            print(f"❌ Error al resolver reCAPTCHA: {e}")
            import traceback
            print(f"🔍 Traceback completo: {traceback.format_exc()}")
            return None
    
    def submit_form(self, nuip, captcha_response, form_data):
        """Envía el formulario con POST request"""
        try:
            print("📤 Enviando formulario...")
            
            # Preparar datos del formulario
            post_data = form_data.copy()
            post_data.update({
                'nuip': str(nuip),
                'tipo': '-1',  # Puesto de votación actual
                'g-recaptcha-response': captcha_response
            })
            
            # Actualizar headers para el POST
            headers = self.session.headers.copy()
            headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://wsp.registraduria.gov.co',
                'Referer': self.base_url
            })
            
            # Enviar formulario
            response = self.session.post(
                self.base_url,
                data=post_data,
                headers=headers,
                timeout=15
            )
            
            response.raise_for_status()
            
            print("✅ Formulario enviado correctamente")
            return response.text
        
        except requests.RequestException as e:
            print(f"❌ Error al enviar formulario: {e}")
            return None
        except Exception as e:
            print(f"❌ Error general al enviar formulario: {e}")
            return None
    
    def extract_data(self, html_content):
        """Extrae los datos de la tabla de resultados del HTML"""
        try:
            print("📊 Extrayendo datos de la tabla...")
            print(f"🔍 Longitud del contenido: {len(html_content)} caracteres")
            print(f"🔍 Primeros 1000 caracteres del contenido:")
            print(html_content[:1000])
            print(f"🔍 Últimos 500 caracteres del contenido:")
            print(html_content[-500:])

            # Detectar estado "Cancelada por Muerte" y normalizar la respuesta
            if re.search(r"Cancelada por Muerte|CANCELADA POR MUERTE", html_content, re.IGNORECASE):
                print("⚠️ Registro cancelado por muerte, devolviendo valores normalizados")
                
                # Intentar extraer el NUIP del HTML
                nuip_muerte = None
                nuip_match_muerte = re.search(r">(\d{6,12})<\\/td>", html_content)
                if not nuip_match_muerte:
                    nuip_match_muerte = re.search(r"(\d{6,12})", html_content)
                if nuip_match_muerte:
                    nuip_muerte = nuip_match_muerte.group(1)

                muerte_data = [{
                    'NUIP': nuip_muerte if nuip_muerte else "CANCELADA",
                    'DEPARTAMENTO': 'NO HABILITA',
                    'MUNICIPIO': 'NO HABILITA',
                    'PUESTO': 'CANCELADA POR MUERTE',
                    'DIRECCIÓN': 'NO HABILITADA',
                    'MESA': '0'
                }]

                return {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "data": muerte_data,
                    "total_records": 1
                }

            # Detectar estado "no habilitado" y normalizar la respuesta
            if re.search(r"no se encuentra habilitado para votar", html_content, re.IGNORECASE):
                print("⚠️ El ciudadano no está habilitado para votar, devolviendo valores normalizados")
                blocked_value = "NO HABILITADO PARA VOTAR"

                # Intentar extraer el NUIP del HTML para devolverlo
                nuip_blocked = None
                nuip_match_blocked = re.search(r"NUIP[^0-9]{0,20}(\d{6,12})", html_content, re.IGNORECASE)
                if not nuip_match_blocked:
                    nuip_match_blocked = re.search(r">(\d{6,12})<\\/td>", html_content)
                if nuip_match_blocked:
                    nuip_blocked = nuip_match_blocked.group(1)

                blocked_data = [{
                    'NUIP': nuip_blocked if nuip_blocked else blocked_value,
                    'DEPARTAMENTO': blocked_value,
                    'MUNICIPIO': blocked_value,
                    'PUESTO': blocked_value,
                    'DIRECCIÓN': blocked_value,
                    'MESA': '0'
                }]

                return {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "data": blocked_data,
                    "total_records": 1
                }

            # Detectar estado "no censo" y normalizar la respuesta
            if re.search(r"no se encuentra en el censo", html_content, re.IGNORECASE):
                print("⚠️ El ciudadano no está en el censo, devolviendo valores normalizados")
                census_value = "NO CENSO"

                nuip_census = None
                nuip_match_census = re.search(r"(\d{6,12})", html_content)
                if nuip_match_census:
                    nuip_census = nuip_match_census.group(1)

                census_data = [{
                    'NUIP': nuip_census if nuip_census else census_value,
                    'DEPARTAMENTO': census_value,
                    'MUNICIPIO': census_value,
                    'PUESTO': census_value,
                    'DIRECCIÓN': census_value,
                    'MESA': '0'
                }]

                return {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "data": census_data,
                    "total_records": 1
                }
            
            # Función auxiliar para limpiar valores extraídos
            def clean_value(value):
                if not value:
                    return ''
                # Convertir a string si no lo es
                value = str(value)
                # Remover todo después de <\/td>, <\/b>, <\/th>, etc.
                value = re.split(r'<\\/', value)[0]
                # Remover cualquier tag HTML que pueda quedar
                value = re.sub(r'<[^>]+>', '', value)
                # Remover caracteres especiales y comillas
                value = re.sub(r'["\'}]+', '', value)
                # Remover espacios múltiples
                value = re.sub(r'\s+', ' ', value)
                return value.strip()
            
            # Inicializar variables
            nuip = None
            departamento = None
            municipio = None
            puesto = None
            direccion = None
            mesa = None
            
            # El HTML viene escapado, extraer datos con regex mejorados
            
            # Buscar NUIP (solo dígitos antes de </td>)
            nuip_match = re.search(r'>(\d{6,12})<\\/td>', html_content)
            if nuip_match:
                nuip = clean_value(nuip_match.group(1))
                print(f"✅ NUIP encontrado con regex: {nuip}")
            
            # Buscar todos los valores en secuencia: NUIP, DEPARTAMENTO, MUNICIPIO, PUESTO, DIRECCIÓN, MESA
            # Patrón: >NUIP</td>DEPARTAMENTO</td>MUNICIPIO</td>PUESTO</td>DIRECCIÓN</td>MESA</b></td>
            full_pattern = r'>(\d{6,12})<\\/td>([^<]+)<\\/td>([^<]+)<\\/td>([^<]+)<\\/td>([^<]+)<\\/td>(\d+)<\\/b><\\/td>'
            full_match = re.search(full_pattern, html_content)
            
            if full_match:
                nuip = clean_value(full_match.group(1))
                departamento = clean_value(full_match.group(2))
                municipio = clean_value(full_match.group(3))
                puesto = clean_value(full_match.group(4))
                direccion = clean_value(full_match.group(5))
                mesa = clean_value(full_match.group(6))
                
                print(f"✅ Extracción exitosa con patrón completo")
            else:
                # Fallback: extraer uno por uno
                print("⚠️ Patrón completo no encontrado, extrayendo individualmente...")
                
                # Buscar todos los valores entre </td>
                all_values = re.findall(r'>([^<]+)<\\/td>', html_content)
                print(f"🔍 Valores encontrados con findall: {all_values}")
                
                if len(all_values) >= 6:
                    nuip = clean_value(all_values[0])
                    departamento = clean_value(all_values[1])
                    municipio = clean_value(all_values[2])
                    puesto = clean_value(all_values[3])
                    direccion = clean_value(all_values[4])
                    # Mesa está en un tag <b>
                    mesa_match = re.search(r'>(\d+)<\\/b>', html_content)
                    mesa = clean_value(mesa_match.group(1)) if mesa_match else clean_value(all_values[5])
                    print(f"✅ Extracción con findall exitosa")
            
            print(f"🔍 NUIP: {nuip}")
            print(f"🔍 DEPARTAMENTO: {departamento}")
            print(f"🔍 MUNICIPIO: {municipio}")
            print(f"🔍 PUESTO: {puesto}")
            print(f"🔍 DIRECCIÓN: {direccion}")
            print(f"🔍 MESA: {mesa}")
            
            # Si no se pudo extraer, intentar método alternativo con BeautifulSoup
            if not nuip or not departamento:
                print("⚠️ Método regex falló, intentando con BeautifulSoup...")
                
                try:
                    # Decodificar unicode escapes
                    decoded = html_content.encode().decode('unicode_escape')
                    
                    # Parsear con BeautifulSoup
                    soup = BeautifulSoup(decoded, 'html.parser')
                    table = soup.find('table')
                    
                    if table:
                        tbody = table.find('tbody')
                        if tbody:
                            row = tbody.find('tr')
                            if row:
                                cells = row.find_all('td')
                                if len(cells) >= 6:
                                    # Limpiar TODOS los valores extraídos
                                    nuip = clean_value(cells[0].get_text(strip=True))
                                    departamento = clean_value(cells[1].get_text(strip=True))
                                    municipio = clean_value(cells[2].get_text(strip=True))
                                    puesto = clean_value(cells[3].get_text(strip=True))
                                    direccion = clean_value(cells[4].get_text(strip=True))
                                    # Mesa puede estar dentro de un <b>
                                    mesa_text = cells[5].get_text(strip=True)
                                    mesa = clean_value(re.search(r'\d+', mesa_text).group() if re.search(r'\d+', mesa_text) else mesa_text)
                                    
                                    print(f"✅ Datos extraídos con BeautifulSoup")
                except Exception as e:
                    print(f"⚠️ Error en método BeautifulSoup: {e}")
            
            # Construir resultado
            if nuip and departamento:
                # Aplicar limpieza final a todos los campos para garantizar que estén limpios
                filtered_data = [{
                    'NUIP': clean_value(nuip),
                    'DEPARTAMENTO': clean_value(departamento),
                    'MUNICIPIO': clean_value(municipio) if municipio else '',
                    'PUESTO': clean_value(puesto) if puesto else '',
                    'DIRECCIÓN': clean_value(direccion) if direccion else '',
                    'MESA': clean_value(mesa) if mesa else ''
                }]
                
                result = {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "data": filtered_data,
                    "total_records": 1
                }
                
                print(f"✅ Datos extraídos y limpiados exitosamente")
                print(f"📋 Registro final: {filtered_data[0]}")
                return result
            else:
                print("❌ No se pudieron extraer los datos")
                return {
                    "status": "error",
                    "message": "No se pudieron extraer los datos del HTML",
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            print(f"❌ Error al extraer datos: {e}")
            import traceback
            print(f"🔍 Traceback completo: {traceback.format_exc()}")
            return {
                "status": "error", 
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def scrape_nuip(self, nuip):
        """Proceso completo de scraping para un NUIP"""
        print(f"\n{'='*50}")
        print(f"INICIANDO CONSULTA PARA NUIP: {nuip}")
        print(f"{'='*50}")
        
        try:
            # 1. Obtener página
            html_content = self.get_page_content()
            if not html_content:
                return {
                    "status": "error", 
                    "message": "Error al obtener la página", 
                    "nuip": nuip,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 2. Parsear página
            soup = self.parse_page(html_content)
            if not soup:
                return {
                    "status": "error", 
                    "message": "Error al parsear la página", 
                    "nuip": nuip,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 3. Extraer datos del formulario
            form_data = self.extract_form_data(soup)
            
            # 4. Resolver reCAPTCHA
            captcha_response = self.solve_recaptcha(soup)
            if not captcha_response:
                return {
                    "status": "error", 
                    "message": "Error al resolver reCAPTCHA", 
                    "nuip": nuip,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 5. Enviar formulario
            response_html = self.submit_form(nuip, captcha_response, form_data)
            if not response_html:
                return {
                    "status": "error", 
                    "message": "Error al enviar formulario", 
                    "nuip": nuip,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 6. Extraer datos
            result = self.extract_data(response_html)
            result["nuip"] = nuip
            
            print(f"✅ CONSULTA COMPLETADA PARA NUIP: {nuip}")
            return result
        
        except Exception as e:
            print(f"❌ Error general en consulta: {e}")
            return {
                "status": "error", 
                "message": f"Error general: {str(e)}", 
                "nuip": nuip,
                "timestamp": datetime.now().isoformat()
            }
    
    def scrape_multiple_nuips(self, nuips_list, delay=5):
        """Consulta múltiples NUIPs con delay entre consultas"""
        results = []
        total = len(nuips_list)
        
        print(f"\n🚀 INICIANDO CONSULTA MASIVA DE {total} NUIPs")
        print(f"Delay entre consultas: {delay} segundos")
        
        for i, nuip in enumerate(nuips_list, 1):
            print(f"\n📋 Procesando {i}/{total}: {nuip}")
            
            result = self.scrape_nuip(nuip)
            results.append(result)
            
            # Delay entre consultas (excepto en la última)
            if i < total:
                print(f"⏳ Esperando {delay} segundos antes de la siguiente consulta...")
                time.sleep(delay)
        
        print(f"\n🎉 CONSULTA MASIVA COMPLETADA: {total} NUIPs procesados")
        return results
    
    def close(self):
        """Cierra la sesión"""
        if self.session:
            self.session.close()
            print("🔒 Sesión cerrada")

# Función para guardar resultados específicos de registraduría
def save_registraduria_results(data, filename=None):
    """Guarda los resultados en un archivo JSON"""
    if filename is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        # Crear carpeta de resultados si no existe
        results_dir = "resultados"
        os.makedirs(results_dir, exist_ok=True)
        filename = os.path.join(results_dir, f"consulta_registraduria_{timestamp}.json")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Resultados guardados en: {filename}")
    return filename

# Ejemplo de uso
if __name__ == "__main__":
    # Cargar API key desde variables de entorno
    API_KEY = os.getenv('APIKEY_2CAPTCHA')
    
    # Verificar que la API key esté disponible
    if not API_KEY:
        print("❌ Error: No se encontró la API key de 2captcha")
        print("Asegúrate de que el archivo .env contenga: APIKEY_2CAPTCHA=tu_api_key")
        sys.exit(1)
    
    print(f"🔑 API Key cargada: {API_KEY[:10]}...")  # Mostrar solo los primeros 10 caracteres
    
    # Crear scraper (sin necesidad de Chrome/Chromium)
    scraper = RegistraduriaScraperAuto(API_KEY)
    
    try:
        # Ejemplo 1: Consultar un solo NUIP
        nuip_ejemplo = "1102877148"
        resultado = scraper.scrape_nuip(nuip_ejemplo)
        
        print(f"\n📊 RESULTADO FINAL:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        # Guardar resultado
        save_registraduria_results(resultado)
        
        # Ejemplo 2: Consultar múltiples NUIPs (descomentar para usar)
        # nuips_lista = ["1102877148", "1234567890", "9876543210"]
        # resultados = scraper.scrape_multiple_nuips(nuips_lista, delay=5)
        # save_registraduria_results(resultados, "resultados_multiples.json")
        
    except KeyboardInterrupt:
        print("\n⚠️ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        print(f"🔍 Traceback completo: {traceback.format_exc()}")
    finally:
        scraper.close()
