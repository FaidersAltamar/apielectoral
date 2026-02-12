import os
import sys
import time
import json
import logging
import requests
import re
from datetime import datetime
from threading import Thread, Lock
from collections import deque
from bs4 import BeautifulSoup

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(_dir), '.env'))

from utils.captcha_solver import TwoCaptchaSolver

logger = logging.getLogger(__name__)

class TokenCache:
    """Sistema de caché de tokens reCAPTCHA compartido"""
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._token_pool = deque(maxlen=10)  # Aumentado de 5 a 10 tokens
        self._pool_lock = Lock()
        self._background_thread = None
        self._keep_filling = False
        self._initialized = True
    
    def start_filler(self, api_key, sitekey, page_url):
        """Inicia el thread de background para mantener tokens disponibles"""
        if not self._keep_filling:
            self._keep_filling = True
            self._background_thread = Thread(
                target=self._fill_pool,
                args=(api_key, sitekey, page_url),
                daemon=True
            )
            self._background_thread.start()
            logger.debug("[TokenCache] Pool de tokens iniciado en background")
    
    def warmup_pool(self, api_key, sitekey, page_url, num_tokens=2):
        """Pre-llena el pool con tokens al inicio para tener disponibles rápidamente"""
        def resolve_token():
            try:
                solver = TwoCaptchaSolver(api_key)
                token = solver.solve_recaptcha_v2(site_key=sitekey, page_url=page_url, invisible=False)
                if token:
                    with self._pool_lock:
                        self._token_pool.append({
                            'token': token,
                            'timestamp': time.time()
                        })
                    logger.debug(f"[Warmup] Token agregado (total: {len(self._token_pool)})")
            except Exception as e:
                logger.warning(f"[Warmup] Error: {e}")
        
        # Iniciar threads paralelos para resolver tokens
        threads = []
        for i in range(num_tokens):
            t = Thread(target=resolve_token, daemon=True)
            t.start()
            threads.append(t)
        
        logger.debug(f"[Warmup] Iniciando pre-llenado de {num_tokens} tokens en paralelo")
        return threads
    
    def _fill_pool(self, api_key, sitekey, page_url):
        """Mantiene el pool lleno de tokens válidos"""
        solver = TwoCaptchaSolver(api_key)
        while self._keep_filling:
            with self._pool_lock:
                pool_size = len(self._token_pool)
            
            if pool_size < 6:  # Mantener al menos 6 tokens (aumentado de 3)
                try:
                    token = solver.solve_recaptcha_v2(site_key=sitekey, page_url=page_url, invisible=False)
                    if token:
                        with self._pool_lock:
                            self._token_pool.append({
                                'token': token,
                                'timestamp': time.time()
                            })
                        logger.debug(f"[TokenCache] Token agregado (total: {len(self._token_pool)})")
                except Exception as e:
                    logger.warning(f"[TokenCache] Error: {e}")
            
            time.sleep(1)  # Verificar cada 1 segundo (más agresivo)
    
    def get_token(self, max_age=90):
        """Obtiene un token válido del pool"""
        with self._pool_lock:
            while self._token_pool:
                token_data = self._token_pool.popleft()
                age = time.time() - token_data['timestamp']
                if age < max_age:
                    logger.debug(f"[TokenCache] Token obtenido del pool (edad: {age:.1f}s)")
                    return token_data['token']
        return None
    
    def get_pool_size(self):
        """Retorna el tamaño actual del pool"""
        with self._pool_lock:
            return len(self._token_pool)
    
    def stop_filler(self):
        """Detiene el thread de background"""
        self._keep_filling = False

class RegistraduriaScraperAuto:
    def __init__(self, captcha_api_key, check_balance=True, token_ttl=90, enable_token_pool=True):
        self.captcha_solver = TwoCaptchaSolver(captcha_api_key)
        self.session = requests.Session()
        self.base_url = "https://eleccionescolombia.registraduria.gov.co/identificacion"
        self.api_url = "https://apiweb-eleccionescolombia.infovotantes.com/api/v1/citizen/get-information"
        self.cached_site_key = "6Lc9DmgrAAAAAJAjWVhjDy1KSgqzqJikY5z7I9SV"
        self.cached_form_data = None
        
        # Sistema de caché de tokens
        self.cached_token = None
        self.token_timestamp = None
        self.token_ttl = token_ttl
        self.enable_token_pool = enable_token_pool
        self.api_key = captcha_api_key
        
        # Configurar headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Origin': 'https://eleccionescolombia.registraduria.gov.co',
            'Referer': 'https://eleccionescolombia.registraduria.gov.co/'
        })
        
        # Iniciar pool de tokens si está habilitado
        if self.enable_token_pool:
            self.token_cache = TokenCache()
            pool_size = self.token_cache.get_pool_size()
            if pool_size == 0:
                # Iniciar background filler
                self.token_cache.start_filler(self.api_key, self.cached_site_key, self.base_url)
                self.token_cache.warmup_pool(self.api_key, self.cached_site_key, self.base_url, num_tokens=3)
            else:
                logger.debug(f"Pool de tokens ya activo ({pool_size} tokens disponibles)")
        
        # Verificar balance solo si se solicita
        if check_balance:
            balance_info = self.captcha_solver.get_balance()
            if balance_info.get('success'):
                balance = balance_info.get('balance_usd', balance_info.get('balance_USD', 0))
                captchas = balance_info.get('estimated_requests', balance_info.get('estimated_captchas', 0))
                logger.info(f"2captcha - ${balance:.4f} USD ({captchas} captchas disponibles)")
    
    def _is_cached_token_valid(self):
        """Verifica si el token en caché sigue válido"""
        if not self.cached_token or not self.token_timestamp:
            return False
        
        age = time.time() - self.token_timestamp
        is_valid = age < self.token_ttl
        
        if is_valid:
            logger.debug(f"Token en caché válido (edad: {age:.1f}s)")
        
        return is_valid
    
    def wait_for_pool_ready(self, timeout=40):
        """Espera a que el pool tenga al menos 1 token disponible"""
        if not self.enable_token_pool:
            return True
        
        logger.debug("Esperando a que el pool tenga tokens disponibles...")
        start = time.time()
        
        while time.time() - start < timeout:
            pool_size = self.token_cache.get_pool_size()
            if pool_size > 0:
                elapsed = time.time() - start
                logger.debug(f"Pool listo con {pool_size} token(s) (esperó {elapsed:.1f}s)")
                return True
            time.sleep(0.5)
        
        logger.warning("Timeout esperando pool, continuando de todos modos")
        return False
    
    def solve_recaptcha(self):
        """Resuelve reCAPTCHA usando sistema de caché optimizado"""
        try:
            # 1. Verificar caché local
            if self._is_cached_token_valid():
                return self.cached_token
            
            # 2. Intentar obtener del pool
            if self.enable_token_pool:
                # Si el pool está vacío y nunca hemos resuelto un token, esperar un poco
                if self.token_cache.get_pool_size() == 0 and not self.cached_token:
                    self.wait_for_pool_ready(timeout=40)
                
                pool_token = self.token_cache.get_token(self.token_ttl)
                if pool_token:
                    self.cached_token = pool_token
                    self.token_timestamp = time.time()
                    return pool_token
            
            # 3. Resolver nuevo token
            logger.debug("Resolviendo nuevo reCAPTCHA...")
            captcha_response = self.captcha_solver.solve_recaptcha_v2(
                site_key=self.cached_site_key,
                page_url=self.base_url,
                invisible=False
            )
            
            if captcha_response:
                self.cached_token = captcha_response
                self.token_timestamp = time.time()
                return captcha_response
            return None
                
        except Exception as e:
            logger.warning(f"Error al resolver reCAPTCHA: {e}")
            return None
    
    def submit_form(self, nuip, captcha_response):
        """Envía el formulario a la API"""
        try:
            logger.debug("Enviando consulta a la API...")
            
            post_data = {
                "identification": str(nuip),
                "identification_type": "CC",
                "election_code": "congreso",
                "module": "polling_place",
                "platform": "web"
            }
            
            headers = self.session.headers.copy()
            headers.update({
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {captcha_response}',
                'Sec-Ch-Ua': '"Chromium";v="120", "Not_A Brand";v="99"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'Priority': 'u=1, i'
            })
            
            response = self.session.post(
                self.api_url,
                json=post_data,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            
            json_response = response.json()
            logger.debug("API respondió correctamente")
            
            return json_response
        
        except requests.RequestException as e:
            logger.warning(f"Error al enviar formulario: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    return error_json
                except Exception:
                    pass
            return None
        except Exception as e:
            logger.warning(f"Error general enviando formulario: {e}")
            return None
    
    def extract_data(self, api_response):
        """Extrae los datos de la respuesta JSON"""
        try:
            if not api_response:
                return {
                    "status": "error",
                    "message": "Respuesta vacía de la API",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Manejar caso específico: status_code 13 (NO CENSO)
            if (api_response.get('status') == False and 
                api_response.get('status_code') == 13 and 
                not api_response.get('data')):
                
                logger.info("Cédula no encontrada en el censo (status_code: 13)")
                
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
                    "total_records": 1,
                    "nuip": "NO CENSO"
                }
            
            # Verificar si la respuesta tiene éxito y data
            if api_response.get('status') and api_response.get('data'):
                data = api_response.get('data', {})
                is_in_census = data.get('is_in_census', True)
                novelty = data.get('novelty', [])
                voter = data.get('voter', {})
                
                # Manejar caso: Cédula no habilitada (is_in_census: false con novelty)
                if not is_in_census and novelty:
                    logger.info("Cédula no habilitada en el censo")
                    
                    novelty_name = novelty[0].get('name', 'NO HABILITADA').upper()
                    
                    no_habilitada_data = [{
                        'NUIP': str(voter.get('identification', '')),
                        'DEPARTAMENTO': 'NO HABILITADA',
                        'MUNICIPIO': 'NO HABILITADA',
                        'PUESTO': novelty_name,
                        'DIRECCIÓN': 'NO HABILITADA',
                        'MESA': '0',
                        'ZONA': 'NO HABILITADA'
                    }]
                    
                    return {
                        "status": "success",
                        "timestamp": datetime.now().isoformat(),
                        "data": no_habilitada_data,
                        "total_records": 1,
                        "nuip": str(voter.get('identification', ''))
                    }
                
                # Caso normal: Cédula habilitada con puesto de votación
                polling_place = data.get('polling_place', {})
                place_address = polling_place.get('place_address', {})
                
                filtered_data = [{
                    'NUIP': str(voter.get('identification', '')),
                    'DEPARTAMENTO': place_address.get('state', ''),
                    'MUNICIPIO': place_address.get('town', ''),
                    'PUESTO': polling_place.get('stand', ''),
                    'DIRECCIÓN': place_address.get('address', ''),
                    'MESA': str(polling_place.get('table', '')),
                    'ZONA': str(place_address.get('zone', ''))
                }]
                
                logger.debug("Datos extraídos correctamente")
                
                result = {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "data": filtered_data,
                    "total_records": len(filtered_data),
                    "nuip": str(voter.get('identification', ''))
                }
                
                return result
            else:
                error_msg = api_response.get('message', 'Error desconocido')
                return {
                    "status": "error",
                    "message": error_msg,
                    "timestamp": datetime.now().isoformat(),
                    "api_response": api_response
                }
        
        except Exception as e:
            logger.warning(f"Error al extraer datos: {e}")
            return {
                "status": "error",
                "message": f"Error al procesar respuesta: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def scrape_nuip(self, nuip):
        """Método principal para consultar un NUIP"""
        try:
            logger.debug(f"Iniciando consulta para NUIP: {nuip}")
            
            # Resolver reCAPTCHA (usará caché si está disponible)
            captcha_response = self.solve_recaptcha()
            if not captcha_response:
                return {
                    "status": "error",
                    "message": "No se pudo resolver el reCAPTCHA",
                    "timestamp": datetime.now().isoformat(),
                    "nuip": str(nuip)
                }
            
            # Enviar formulario
            api_response = self.submit_form(nuip, captcha_response)
            
            # Si falla con el token actual (403), intentar con nuevo token del pool
            if api_response and not api_response.get('status'):
                logger.debug("Token usado, obteniendo nuevo token del pool...")
                # Invalidar caché
                self.cached_token = None
                self.token_timestamp = None
                # Obtener nuevo token
                captcha_response = self.solve_recaptcha()
                if captcha_response:
                    api_response = self.submit_form(nuip, captcha_response)
            
            # Extraer datos
            result = self.extract_data(api_response)
            
            logger.debug(f"Consulta completada para NUIP: {nuip}")
            
            return result
            
        except Exception as e:
            logger.warning(f"Error al consultar NUIP {nuip}: {e}")
            return {
                "status": "error",
                "message": f"Error en la consulta: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "nuip": str(nuip)
            }
    
    def scrape_multiple_nuips(self, nuips, delay=2):
        """Consulta múltiples NUIPs con delay entre cada una"""
        results = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_nuips": len(nuips),
            "results": []
        }
        
        for i, nuip in enumerate(nuips, 1):
            logger.info(f"Consultando NUIP {i}/{len(nuips)}: {nuip}")
            
            result = self.scrape_nuip(nuip)
            results["results"].append(result)
            
            if i < len(nuips):
                logger.debug(f"Esperando {delay} segundos...")
                time.sleep(delay)
        
        return results
    
    def close(self):
        """Cierra la sesión"""
        if self.session:
            self.session.close()
            logger.debug("Sesión cerrada")

# Función para guardar resultados
def save_registraduria_results(data, filename=None):
    """Guarda los resultados en un archivo JSON"""
    if filename is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_dir = "resultados"
        os.makedirs(results_dir, exist_ok=True)
        filename = os.path.join(results_dir, f"consulta_registraduria_{timestamp}.json")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Resultados guardados en: {filename}")
    return filename

# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    API_KEY = os.getenv('TWOCAPTCHA_API_KEY') or os.getenv('APIKEY_2CAPTCHA')
    
    if not API_KEY:
        logger.error("No se encontró la API key de 2captcha (TWOCAPTCHA_API_KEY o APIKEY_2CAPTCHA)")
        sys.exit(1)
    
    logger.info(f"API Key cargada: {API_KEY[:10]}...")
    
    # Crear scraper con pool de tokens habilitado (sin verificar balance para ser más rápido)
    scraper = RegistraduriaScraperAuto(API_KEY, check_balance=False, enable_token_pool=True)
    
    try:
        # Ejemplo: Consultar un NUIP
        nuip_ejemplo = "1102877148"
        resultado = scraper.scrape_nuip(nuip_ejemplo)
        
        logger.info("Resultado final:")
        logger.info(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        save_registraduria_results(resultado)
        
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error crítico: {e}")
    finally:
        scraper.close()
