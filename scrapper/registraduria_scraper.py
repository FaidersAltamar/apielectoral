import requests
import time
import json
import os
import sys
import re
from bs4 import BeautifulSoup
from datetime import datetime
from threading import Thread, Lock
from collections import deque

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Importar el solver de captcha desde utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.captcha_solver import TwoCaptchaSolver

class RegistraduriaScraperAuto:
    # Pool compartido de tokens entre todas las instancias
    _token_pool = deque(maxlen=5)  # Máximo 5 tokens en pool
    _pool_lock = Lock()
    _background_thread = None
    _keep_filling = False
    
    def __init__(self, captcha_api_key, check_balance=True, token_ttl=90, enable_token_pool=True):
        self.captcha_solver = TwoCaptchaSolver(captcha_api_key)
        self.session = requests.Session()
        self.base_url = "https://eleccionescolombia.registraduria.gov.co/identificacion"
        self.api_url = "https://apiweb-eleccionescolombia.infovotantes.com/api/v1/citizen/get-information"
        self.cached_site_key = "6Lc9DmgrAAAAAJAjWVhjDy1KSgqzqJikY5z7I9SV"  # Sitekey conocido
        self.cached_form_data = None  # Caché de datos del formulario
        
        # Sistema de caché de tokens
        self.cached_token = None
        self.token_timestamp = None
        self.token_ttl = token_ttl  # Tiempo de vida del token en segundos (default 90s)
        self.enable_token_pool = enable_token_pool
        self.api_key = captcha_api_key
        
        # Configurar headers para simular un navegador real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Origin': 'https://eleccionescolombia.registraduria.gov.co',
            'Referer': 'https://eleccionescolombia.registraduria.gov.co/'
        })
        
        # Iniciar pool de tokens en background si está habilitado
        if self.enable_token_pool and not RegistraduriaScraperAuto._background_thread:
            self._start_token_pool_filler()
        
        # Verificar balance solo si se solicita (para ahorrar tiempo)
        if check_balance:
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
        """Extrae datos necesarios del formulario y los cachea"""
        try:
            # Si ya tenemos los datos en caché, usarlos
            if self.cached_form_data:
                print("🔄 Usando datos del formulario en caché")
                return self.cached_form_data.copy()
            
            form_data = {}
            
            # Buscar todos los inputs hidden para incluirlos en el POST
            hidden_inputs = soup.find_all('input', type='hidden')
            for hidden in hidden_inputs:
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name:
                    form_data[name] = value
            
            # Guardar en caché
            self.cached_form_data = form_data.copy()
            print(f"💾 Datos del formulario guardados en caché ({len(form_data)} campos)")
            
            return form_data
        except Exception as e:
            print(f"❌ Error al extraer datos del formulario: {e}")
            return {}
    
    def get_recaptcha_site_key(self, soup):
        """Extrae dinámicamente el site key del reCAPTCHA desde el HTML"""
        try:
            # Buscar cualquier elemento que tenga el atributo data-sitekey
            tag_with_sitekey = soup.find(attrs={"data-sitekey": True})
            if tag_with_sitekey:
                site_key = tag_with_sitekey.get('data-sitekey')
                if site_key:
                    print(f"🔍 Site key encontrado dinámicamente: {site_key}")
                    return site_key

            # Buscar en iframes (src con k=sitekey) y en scripts por patrones comunes
            iframes = ''.join([ifr.get('src') or '' for ifr in soup.find_all('iframe')])
            scripts = ''.join([s.get('src') or s.text or '' for s in soup.find_all('script')])
            combined = iframes + scripts
            # Patrón común: k=SITEKEY en src de iframe de recaptcha
            m_iframe = re.search(r"[?&]k=([A-Za-z0-9_-]{20,100})", iframes)
            if m_iframe:
                print(f"🔍 Site key encontrado en iframe src: {m_iframe.group(1)}")
                return m_iframe.group(1)

            m = re.search(r"sitekey\s*[:=]\s*['\"]([A-Za-z0-9_-]{20,100})['\"]", combined)
            if m:
                print(f"🔍 Site key encontrado en scripts: {m.group(1)}")
                return m.group(1)

            print("⚠️ No se pudo extraer el site key dinámicamente, usando el hardcodeado")
            return "6LcthjAgAAAAFIQLxy52074zanHv47cIvmIHglH"
        
        except Exception as e:
            print(f"⚠️ Error al extraer site key: {e}, usando hardcodeado")
            return "6LcthjAgAAAAFIQLxy52074zanHv47cIvmIHglH"
    
    def solve_recaptcha(self):
        """Resuelve el reCAPTCHA automáticamente usando 2captcha"""
        try:
            # Usar el site key conocido
            site_key = self.cached_site_key
            print(f"🔄 Usando site key conocido: {site_key}")
            
            print(f"🤖 Resolviendo reCAPTCHA automáticamente con 2captcha...")
            print(f"URL: {self.base_url}")
            
            # Resolver reCAPTCHA usando la librería oficial (ahora más rápido con polling de 1s)
            captcha_response = self.captcha_solver.solve_recaptcha_v2(site_key, self.base_url, invisible=False)
            
            print("✅ reCAPTCHA resuelto correctamente")
            return captcha_response
        
        except Exception as e:
            print(f"❌ Error al resolver reCAPTCHA: {e}")
            import traceback
            print(f"🔍 Traceback completo: {traceback.format_exc()}")
            return None
    
    def submit_form(self, nuip, captcha_response):
        """Envía el formulario a la API usando POST request"""
        try:
            print("📤 Enviando consulta a la API...")
            
            # Preparar datos del formulario para la API
            post_data = {
                "identification": str(nuip),
                "identification_type": "CC",
                "election_code": "congreso",
                "module": "polling_place",
                "platform": "web"
            }
            
            # Actualizar headers para el POST JSON con el token como Bearer
            headers = self.session.headers.copy()
            headers.update({
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {captcha_response}',  # Token como Bearer
                'Sec-Ch-Ua': '"Chromium";v="120", "Not_A Brand";v="99"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'Priority': 'u=1, i'
            })
            
            print(f"🔍 Enviando a: {self.api_url}")
            print(f"🔍 Body: {json.dumps(post_data, ensure_ascii=False)}")
            
            # Enviar formulario a la API
            response = self.session.post(
                self.api_url,
                json=post_data,
                headers=headers,
                timeout=10  # Reducido de 15 a 10 segundos
            )
            
            print(f"🔍 Status Code: {response.status_code}")
            
            response.raise_for_status()
            
            json_response = response.json()
            print(f"✅ API respondió correctamente")
            print(f"🔍 Respuesta: {json.dumps(json_response, indent=2, ensure_ascii=False)[:300]}...")
            
            return json_response
        
        except requests.RequestException as e:
            print(f"❌ Error al enviar formulario: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    print(f"🔍 Respuesta de error: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                    return error_json
                except:
                    print(f"🔍 Respuesta texto: {e.response.text[:500]}")
            return None
        except Exception as e:
            print(f"❌ Error general al enviar formulario: {e}")
            return None
    
    def extract_data(self, api_response):
        """Extrae los datos de la respuesta JSON de la API"""
        try:
            print("📊 Procesando respuesta de la API...")
            
            if not api_response:
                return {
                    "status": "error",
                    "message": "Respuesta vacía de la API",
                    "timestamp": datetime.now().isoformat()
                }
            
            print(f"🔍 Respuesta API: {json.dumps(api_response, indent=2, ensure_ascii=False)[:500]}...")
            
            # Manejar caso específico: status_code 13 (NO CENSO)
            if (api_response.get('status') == False and 
                api_response.get('status_code') == 13 and 
                not api_response.get('data')):
                
                print("⚠️ Cédula no encontrada en el censo (status_code: 13)")
                
                no_censo_data = [{
                    'NUIP': 'NO CENSO',
                    'DEPARTAMENTO': 'NO CENSO',
                    'MUNICIPIO': 'NO CENSO',
                    'PUESTO': 'NO CENSO',
                    'DIRECCIÓN': 'NO CENSO',
                    'MESA': '0',
                    'ZONA': 'NO CENSO'
                }]
                
                return {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "data": no_censo_data,
                    "total_records": 1
                }
            
            # Verificar si la respuesta tiene éxito
            if api_response.get('status') and api_response.get('data'):
                data = api_response.get('data', {})
                polling_place = data.get('polling_place', {})
                place_address = polling_place.get('place_address', {})
                voter = data.get('voter', {})
                
                # Extraer campos del JSON según la estructura real
                filtered_data = [{
                    'NUIP': str(voter.get('identification', '')),
                    'DEPARTAMENTO': place_address.get('state', ''),
                    'MUNICIPIO': place_address.get('town', ''),
                    'PUESTO': polling_place.get('stand', ''),
                    'DIRECCIÓN': place_address.get('address', ''),
                    'MESA': str(polling_place.get('table', '')),
                    'ZONA': str(place_address.get('zone', ''))
                }]
                
                result = {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "data": filtered_data,
                    "total_records": 1
                }
                
                print(f"✅ Datos extraídos exitosamente")
                print(f"📋 Registro: {filtered_data[0]}")
                return result
            else:
                # Manejar errores de la API
                error_msg = api_response.get('message', api_response.get('error', 'Error desconocido'))
                print(f"⚠️ La API devolvió un error: {error_msg}")
                
                return {
                    "status": "error",
                    "message": error_msg,
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

            # Detectar estado "Cancelada por Doble Cedulación" y normalizar la respuesta
            if re.search(r"Cancelada por Doble Cedulaci[oó]n|CANCELADA POR DOBLE CEDULACI[OÓ]N", html_content, re.IGNORECASE):
                print("⚠️ Registro cancelado por doble cedulación, devolviendo valores normalizados")
                
                # Intentar extraer el NUIP del HTML
                nuip_doble = None
                nuip_match_doble = re.search(r">(\d{6,12})<\\/td>", html_content)
                if not nuip_match_doble:
                    nuip_match_doble = re.search(r"(\d{6,12})", html_content)
                if nuip_match_doble:
                    nuip_doble = nuip_match_doble.group(1)

                doble_data = [{
                    'NUIP': nuip_doble if nuip_doble else "CANCELADA",
                    'DEPARTAMENTO': 'NO HABILITA',
                    'MUNICIPIO': 'NO HABILITA',
                    'PUESTO': 'CANCELADA POR DOBLE CEDULACIÓN',
                    'DIRECCIÓN': 'NO HABILITADA',
                    'MESA': '0'
                }]

                return {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "data": doble_data,
                    "total_records": 1
                }

            # Detectar estado "Cancelada por Falsa Identidad" y normalizar la respuesta
            if re.search(r"Cancelada por Falsa Identidad|CANCELADA POR FALSA IDENTIDAD", html_content, re.IGNORECASE):
                print("⚠️ Registro cancelado por falsa identidad, devolviendo valores normalizados")
                
                # Intentar extraer el NUIP del HTML
                nuip_falsa = None
                nuip_match_falsa = re.search(r">(\d{6,12})<\\/td>", html_content)
                if not nuip_match_falsa:
                    nuip_match_falsa = re.search(r"(\d{6,12})", html_content)
                if nuip_match_falsa:
                    nuip_falsa = nuip_match_falsa.group(1)

                falsa_data = [{
                    'NUIP': nuip_falsa if nuip_falsa else "CANCELADA",
                    'DEPARTAMENTO': 'NO HABILITA',
                    'MUNICIPIO': 'NO HABILITA',
                    'PUESTO': 'CANCELADA POR FALSA IDENTIDAD',
                    'DIRECCIÓN': 'NO HABILITADA',
                    'MESA': '0'
                }]

                return {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "data": falsa_data,
                    "total_records": 1
                }

            # Detectar estado "Vigente con Perdida o Suspension de los Derechos Politicos" y normalizar la respuesta
            if re.search(r"Vigente con Perdida o Suspension de los Derechos Politicos|Vigente con P[ée]rdida o Suspensi[oó]n de los Derechos Pol[ií]ticos", html_content, re.IGNORECASE):
                print("⚠️ Cédula vigente pero con pérdida o suspensión de derechos políticos, devolviendo valores normalizados")
                
                # Intentar extraer el NUIP del HTML
                nuip_suspension = None
                nuip_match_suspension = re.search(r">(\d{6,12})<\\/td>", html_content)
                if not nuip_match_suspension:
                    nuip_match_suspension = re.search(r"(\d{6,12})", html_content)
                if nuip_match_suspension:
                    nuip_suspension = nuip_match_suspension.group(1)

                suspension_data = [{
                    'NUIP': nuip_suspension if nuip_suspension else "SUSPENDIDA",
                    'DEPARTAMENTO': 'NO HABILITA',
                    'MUNICIPIO': 'NO HABILITA',
                    'PUESTO': 'VIGENTE CON PÉRDIDA O SUSPENSIÓN DE DERECHOS POLÍTICOS',
                    'DIRECCIÓN': 'NO HABILITADA',
                    'MESA': '0'
                }]

                return {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "data": suspension_data,
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
            
            # Si el HTML coincide con el nuevo diseño (contenedor shadow-custom-card), parsearlo con BeautifulSoup
            try:
                soup_new = BeautifulSoup(html_content, 'html.parser')
                container = soup_new.find('div', class_=lambda c: c and 'shadow-custom-card' in c)
                if container:
                    print("🔎 Contenedor moderno 'shadow-custom-card' detectado, extrayendo campos...")

                    # Documento
                    h2_doc = container.find('h2', string=re.compile(r'Documento de identidad', re.I))
                    if h2_doc:
                        nuip_span = h2_doc.find_next_sibling('span')
                        if nuip_span:
                            nuip_text = nuip_span.get_text(strip=True)
                            m = re.search(r"(\d{6,12})", nuip_text)
                            if m:
                                nuip = m.group(1)

                    # Función auxiliar para obtener valor tras un label
                    def get_value_by_label(lbl):
                        lbl_span = container.find('span', string=re.compile(rf'^{re.escape(lbl)}$', re.I))
                        if lbl_span:
                            val_span = lbl_span.find_next_sibling('span')
                            if val_span:
                                return val_span.get_text(strip=True)
                        return None

                    puesto = get_value_by_label('Puesto')
                    mesa = get_value_by_label('Mesa')
                    # 'Zona' puede estar presente, lo guardamos también
                    zona = get_value_by_label('Zona')
                    departamento = get_value_by_label('Departamento')
                    municipio = get_value_by_label('Municipio')
                    direccion = get_value_by_label('Dirección')

                    # Si la mesa no viene como número dentro de un <b>, intentar extraer dígitos
                    if mesa:
                        mm = re.search(r"(\d+)", mesa)
                        if mm:
                            mesa = mm.group(1)

                    # Si puesto contiene la zona concatenada (ej. '28 - DON ALONSO'), dejar tal cual
                    if (nuip or departamento) and (puesto or municipio):
                        filtered_data = [{
                            'NUIP': nuip if nuip else '',
                            'DEPARTAMENTO': departamento if departamento else '',
                            'MUNICIPIO': municipio if municipio else '',
                            'PUESTO': puesto if puesto else (zona if zona else ''),
                            'DIRECCIÓN': direccion if direccion else '',
                            'MESA': mesa if mesa else ''
                        }]

                        result = {
                            "status": "success",
                            "timestamp": datetime.now().isoformat(),
                            "data": filtered_data,
                            "total_records": 1
                        }
                        print(f"✅ Datos extraídos del contenedor moderno: {filtered_data[0]}")
                        return result
            except Exception:
                # Si falla el parseo del nuevo diseño, continuar con la extracción previa
                pass

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
            # 1. Resolver reCAPTCHA
            captcha_response = self.solve_recaptcha()
            if not captcha_response:
                return {
                    "status": "error", 
                    "message": "Error al resolver reCAPTCHA", 
                    "nuip": nuip,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 2. Enviar consulta a la API
            api_response = self.submit_form(nuip, captcha_response)
            if not api_response:
                return {
                    "status": "error", 
                    "message": "Error al consultar la API", 
                    "nuip": nuip,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 3. Extraer datos de la respuesta JSON
            result = self.extract_data(api_response)
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
    
    def clear_cache(self):
        """Limpia la caché"""
        self.cached_form_data = None
        print("🗑️ Caché limpiada")
    
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
