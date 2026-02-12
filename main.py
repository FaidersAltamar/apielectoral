"""
Worker de consulta Registraduría - Lugar de votación
Usa API directa de infovotantes (sin Playwright).

Variables de entorno (o archivo .env):
- TWOCAPTCHA_API_KEY: API key de 2Captcha
- CONSULTA_API_TOKEN: Token para Supabase/Lovable Cloud

Ejecutar: python main.py
"""

import os

# Cargar .env desde el directorio del script
try:
    from dotenv import load_dotenv
    _dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(_dir, '.env'))
    if not os.getenv('TWOCAPTCHA_API_KEY'):
        load_dotenv(os.path.join(_dir, '.env.example'))
except ImportError:
    pass

import sys
import time
import random
import logging
import json
import signal
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
from threading import Lock
from typing import Optional, Dict, Any, List

# Intentar usar librería oficial 2captcha
try:
    from twocaptcha import TwoCaptcha
    from twocaptcha.api import ApiException
    HAS_2CAPTCHA_LIB = True
except ImportError:
    HAS_2CAPTCHA_LIB = False

# Configuración
TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')
CONSULTA_API_TOKEN = os.getenv('CONSULTA_API_TOKEN', '')
SUPABASE_FUNCTIONS_URL = os.getenv(
    'SUPABASE_FUNCTIONS_URL',
    'https://lsdnopjulddzkkboarsp.supabase.co/functions/v1'
)

API_URL = "https://apiweb-eleccionescolombia.infovotantes.com/api/v1/citizen/get-information"
BASE_URL = "https://eleccionescolombia.registraduria.gov.co/identificacion"
SITE_KEY = "6Lc9DmgrAAAAAJAjWVhjDy1KSgqzqJikY5z7I9SV"

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

MAX_WORKERS = 1
ENABLE_TOKEN_POOL = True
TOKEN_POOL_MAX = 3
TOKEN_TTL = 90  # segundos

# Session HTTP persistente (keep-alive)
_http_session: Optional[requests.Session] = None
_session_lock = Lock()


def _get_session() -> requests.Session:
    """Obtiene la sesión HTTP persistente."""
    global _http_session
    with _session_lock:
        if _http_session is None:
            _http_session = requests.Session()
            _http_session.headers.update({
                'User-Agent': USER_AGENT,
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Origin': 'https://eleccionescolombia.registraduria.gov.co',
                'Referer': 'https://eleccionescolombia.registraduria.gov.co/',
            })
        return _http_session


class TokenCache:
    """Pool de tokens reCAPTCHA para reutilizar entre consultas."""
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
        if getattr(self, '_initialized', False):
            return
        self._token_pool: deque = deque(maxlen=TOKEN_POOL_MAX)
        self._pool_lock = Lock()
        self._initialized = True

    def get_token(self, max_age: int = TOKEN_TTL) -> Optional[str]:
        """Obtiene un token válido del pool."""
        with self._pool_lock:
            while self._token_pool:
                token_data = self._token_pool.popleft()
                age = time.time() - token_data['timestamp']
                if age < max_age:
                    logger.info(f"Token obtenido del pool (edad: {age:.1f}s)")
                    return token_data['token']
        return None

    def put_token(self, token: str) -> None:
        """Añade un token al pool."""
        with self._pool_lock:
            if len(self._token_pool) < TOKEN_POOL_MAX:
                self._token_pool.append({'token': token, 'timestamp': time.time()})
                logger.info(f"Token añadido al pool (total: {len(self._token_pool)})")

    def get_pool_size(self) -> int:
        with self._pool_lock:
            return len(self._token_pool)


# Cache: cedulas que fallaron recientemente (evitar re-gastar CAPTCHA)
FAILED_CEDULAS_CACHE: Dict[str, float] = {}
FAILED_CACHE_TTL = 20 * 60  # 20 minutos


def _cedula_fallo_reciente(cedula: str) -> bool:
    """True si la cedula fallo hace menos de FAILED_CACHE_TTL segundos."""
    now = time.time()
    if cedula in FAILED_CEDULAS_CACHE:
        if now - FAILED_CEDULAS_CACHE[cedula] < FAILED_CACHE_TTL:
            return True
        del FAILED_CEDULAS_CACHE[cedula]
    return False


def _registrar_cedula_fallo(cedula: str) -> None:
    """Registra que la cedula fallo (403/404) para bloquear reintentos."""
    FAILED_CEDULAS_CACHE[cedula] = time.time()
    logger.info(f"Cedula {cedula} registrada en cache de fallidas (TTL {FAILED_CACHE_TTL // 60}min)")


def _limpiar_cache_fallidas() -> None:
    """Elimina entradas expiradas del cache."""
    now = time.time()
    expiradas = [c for c, ts in FAILED_CEDULAS_CACHE.items() if now - ts >= FAILED_CACHE_TTL]
    for c in expiradas:
        del FAILED_CEDULAS_CACHE[c]


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _solve_recaptcha_direct(site_key: str, page_url: str) -> Optional[str]:
    """Resuelve reCAPTCHA v2 usando 2captcha (librería o requests)."""
    if not TWOCAPTCHA_API_KEY:
        logger.error("TWOCAPTCHA_API_KEY no configurado")
        return None

    if HAS_2CAPTCHA_LIB:
        try:
            solver = TwoCaptcha(TWOCAPTCHA_API_KEY, pollingInterval=1, defaultTimeout=60)
            result = solver.recaptcha(sitekey=site_key, url=page_url, invisible=0, pollingInterval=1)
            logger.info("CAPTCHA resuelto (librería 2captcha)")
            return result['code'] if isinstance(result, dict) else result
        except ApiException as e:
            msg = str(e)
            if 'ERROR_WRONG_GOOGLEKEY' in msg:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(page_url)
                    origin = f"{parsed.scheme}://{parsed.netloc}"
                    logger.warning(f"ERROR_WRONG_GOOGLEKEY, reintentando con origen: {origin}")
                    solver = TwoCaptcha(TWOCAPTCHA_API_KEY, pollingInterval=1, defaultTimeout=60)
                    result = solver.recaptcha(sitekey=site_key, url=origin, invisible=0, pollingInterval=1)
                    return result['code'] if isinstance(result, dict) else result
                except Exception:
                    pass
            logger.error(f"Error 2Captcha API: {e}")
            return None
        except Exception as e:
            logger.error(f"Error solve_recaptcha: {e}")
            return None

    # Fallback: requests directo
    try:
        session = _get_session()
        resp = session.post('http://2captcha.com/in.php', data={
            'key': TWOCAPTCHA_API_KEY,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url,
            'json': 1
        }, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"2Captcha HTTP {resp.status_code}: {resp.text[:100]}")
            return None
        try:
            r = resp.json()
        except json.JSONDecodeError:
            return None
        if r.get('status') != 1:
            logger.error(f"Error 2Captcha: {r}")
            return None
        captcha_id = r.get('request')
        logger.info(f"CAPTCHA enviado, ID: {captcha_id}")
        for attempt in range(50):
            time.sleep(1.5 if attempt < 10 else 2)
            resp = session.get('http://2captcha.com/res.php', params={
                'key': TWOCAPTCHA_API_KEY,
                'action': 'get', 'id': captcha_id, 'json': 1
            }, timeout=10)
            try:
                r = resp.json()
            except json.JSONDecodeError:
                continue
            if r.get('status') == 1:
                logger.info(f"CAPTCHA resuelto (intento {attempt + 1})")
                return r.get('request')
            if r.get('request') != 'CAPCHA_NOT_READY':
                logger.error(f"Error: {r}")
                return None
        logger.error("Timeout CAPTCHA")
        return None
    except Exception as e:
        logger.error(f"Error solve_recaptcha: {e}")
        return None


def solve_recaptcha(site_key: str, page_url: str) -> Optional[str]:
    """Obtiene token: primero del pool, si no resuelve nuevo."""
    if not TWOCAPTCHA_API_KEY:
        return None
    if ENABLE_TOKEN_POOL:
        token_cache = TokenCache()
        token = token_cache.get_token(TOKEN_TTL)
        if token:
            return token
    return _solve_recaptcha_direct(site_key, page_url)


def _warmup_token_pool(num_tokens: int = 2) -> None:
    """Pre-llena el pool de tokens al inicio (en paralelo)."""
    if not ENABLE_TOKEN_POOL or not TWOCAPTCHA_API_KEY:
        return
    token_cache = TokenCache()
    if token_cache.get_pool_size() > 0:
        return
    logger.info(f"Warmup: pre-llenando pool con {num_tokens} token(s) en paralelo...")

    def resolve_and_put(_: int) -> None:
        token = _solve_recaptcha_direct(SITE_KEY, BASE_URL)
        if token:
            token_cache.put_token(token)

    with ThreadPoolExecutor(max_workers=num_tokens) as ex:
        list(ex.map(resolve_and_put, range(num_tokens)))
    logger.info(f"Warmup completo. Pool: {token_cache.get_pool_size()} token(s)")


def query_registraduria(cedula: str) -> Optional[Dict[str, Any]]:
    """Consulta lugar de votación vía API directa"""
    try:
        if _cedula_fallo_reciente(cedula):
            logger.info(f"Cedula {cedula} bloqueada: fallo recientemente (cache 20min)")
            return {"status": "api_error", "error": "Reintento bloqueado 20min"}
        logger.info(f"Consultando Registraduria para cedula: {cedula}")

        session = _get_session()
        payload = {
            "identification": str(cedula),
            "identification_type": "CC",
            "election_code": "congreso",
            "module": "polling_place",
            "platform": "web"
        }

        token = None
        max_intentos_con_token_nuevo = 1  # 403: 1 retry con token nuevo (2 intentos total)
        for intento_token in range(max_intentos_con_token_nuevo + 1):
            token = solve_recaptcha(SITE_KEY, BASE_URL)
            if not token:
                return None

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'Sec-Ch-Ua': '"Chromium";v="120", "Not_A Brand";v="99"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
            }

            resp = None
            for intento in range(3):
                resp = session.post(API_URL, json=payload, headers=headers, timeout=15)
                if resp.status_code == 200:
                    break
                if resp.status_code == 404:
                    # La API usa 404 con JSON para "cédula no en censo" (status_code 13)
                    try:
                        data_404 = resp.json()
                        if data_404.get('status_code') == 13:
                            return {"status": "not_found"}
                    except Exception:
                        pass
                    # 404 sin JSON válido = error de API
                    logger.warning("API 404 inesperado, token consumido - sin retry")
                    _registrar_cedula_fallo(cedula)
                    return {"status": "api_error", "error": "API no disponible (404)"}
                if resp.status_code == 403:
                    logger.warning("API 403, token posiblemente usado - obteniendo token nuevo...")
                    break
                if resp.status_code == 500 and intento < 2:
                    delay = 10 + (5 * intento)
                    logger.warning(f"API 500, reintentando en {delay}s...")
                    time.sleep(delay)
                    continue
                if resp.status_code != 403:
                    resp.raise_for_status()
                    break

            if resp and resp.status_code == 200:
                break
            if resp and resp.status_code == 403:
                if intento_token < max_intentos_con_token_nuevo:
                    time.sleep(5)
                    continue
                _registrar_cedula_fallo(cedula)
                return {"status": "api_error", "error": "API no disponible (403 Forbidden)"}
            if resp and resp.status_code != 200:
                resp.raise_for_status()

        if not resp or resp.status_code != 200:
            return None

        data = resp.json()

        if data.get('status') is False and data.get('status_code') == 13:
            return {"status": "not_found"}

        if not data.get('status') or not data.get('data'):
            return None

        inner = data.get('data', {})
        voter = inner.get('voter', {}) or {}
        polling_place = inner.get('polling_place', {}) or {}
        place_address = (polling_place.get('place_address') or {}) if polling_place else {}

        # Validar: si no hay datos de votante, puesto ni novelty, la cedula no existe
        has_voter = bool(voter.get('identification'))
        has_place = bool(polling_place.get('stand') or place_address.get('address') or place_address.get('state'))
        has_novelty = bool(inner.get('novelty'))
        if not has_voter and not has_place and not has_novelty:
            return {"status": "not_found"}

        if not inner.get('is_in_census', True) and inner.get('novelty'):
            nov = inner['novelty'][0]
            return {
                "nuip": str(voter.get('identification', '')),
                "departamento": "NO HABILITADA",
                "municipio": "NO HABILITADA",
                "puesto": nov.get('name', 'NO HABILITADA'),
                "direccion": "NO HABILITADA",
                "mesa": "0",
                "zona": "",
            }

        return {
            "nuip": str(voter.get('identification', cedula)),
            "departamento": place_address.get('state') or '',
            "municipio": place_address.get('town') or '',
            "puesto": polling_place.get('stand') or '',
            "direccion": place_address.get('address') or '',
            "mesa": str(polling_place.get('table', '')),
            "zona": str(place_address.get('zone', '')),
        }
    except requests.RequestException as e:
        logger.error(f"Error API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            code = e.response.status_code
            if code in (403, 404):
                _registrar_cedula_fallo(cedula)
            if code == 404:
                return {"status": "api_error", "error": "API no disponible (404)"}
            if code == 403:
                return {"status": "api_error", "error": "API no disponible (403 Forbidden)"}
            if code == 500:
                return {"status": "api_error", "error": "API no disponible (500)"}
        return {"status": "api_error", "error": str(e)}
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return None


def obtener_consultas_pendientes(tipo: str = 'registraduria', limit: int = 50) -> List[Dict]:
    """Obtiene cedulas pendientes de consultar"""
    url = f"{SUPABASE_FUNCTIONS_URL}/consultas-pendientes"
    try:
        resp = requests.get(
            url,
            params={'tipo': tipo, 'limit': limit},
            headers={'Authorization': f'Bearer {CONSULTA_API_TOKEN}'},
            timeout=30
        )
        if resp.status_code == 401:
            logger.error("Supabase: Token invalido (401)")
            return []
        if resp.status_code != 200:
            logger.error(f"Supabase: HTTP {resp.status_code} - {resp.text[:200]}")
            resp.raise_for_status()
        data = resp.json()
        consultas = data.get('consultas', [])
        if not consultas:
            logger.info(f"Supabase OK (HTTP 200) pero 0 consultas pendientes en cola")
        return consultas
    except requests.exceptions.Timeout:
        logger.error(f"Supabase: Timeout al conectar con {url}")
        return []
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Supabase: Error de conexion - {e}")
        return []
    except Exception as e:
        logger.error(f"Supabase: Error obteniendo consultas: {e}", exc_info=True)
        return []


def enviar_resultado(cola_id: str, cedula: str, exito: bool, datos: Optional[Dict] = None, error: Optional[str] = None) -> bool:
    """Envia resultado a Lovable Cloud"""
    try:
        # Usar requests directo para Supabase (evitar headers de Registraduria)
        resp = requests.post(
            f"{SUPABASE_FUNCTIONS_URL}/recibir-datos",
            json={
                'cola_id': cola_id, 'cedula': cedula, 'tipo': 'registraduria',
                'exito': exito, 'datos': datos, 'error': error
            },
            headers={'Authorization': f'Bearer {CONSULTA_API_TOKEN}', 'Content-Type': 'application/json'},
            timeout=30
        )
        if resp.status_code in (401, 404):
            logger.error(f"Error enviando: {resp.status_code}")
            return False
        resp.raise_for_status()
        return resp.json().get('success', False)
    except Exception as e:
        logger.error(f"Error enviando resultado: {e}")
        return False


def procesar_consulta(consulta: Dict) -> tuple:
    """Worker: consulta Registraduria. Retorna (consulta, resultado)."""
    time.sleep(random.uniform(0, 3))  # espaciar peticiones
    cedula = consulta['cedula']
    resultado = query_registraduria(cedula)
    return (consulta, resultado)


def main():
    """Loop principal: obtener pendientes -> consultar -> enviar"""
    if not TWOCAPTCHA_API_KEY:
        logger.error("Configura TWOCAPTCHA_API_KEY en variables de entorno")
        sys.exit(1)

    logger.info("Worker Registraduria iniciado")
    logger.info(f"Supabase: {SUPABASE_FUNCTIONS_URL}/consultas-pendientes")
    if ENABLE_TOKEN_POOL:
        _warmup_token_pool(num_tokens=2)
    running = True

    def stop(sig, frame):
        nonlocal running
        running = False
        logger.info("Deteniendo...")

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    while running:
        try:
            _limpiar_cache_fallidas()
            consultas = obtener_consultas_pendientes(tipo='registraduria', limit=2)

            if consultas:
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = {executor.submit(procesar_consulta, c): c for c in consultas}
                    for future in as_completed(futures):
                        if not running:
                            executor.shutdown(wait=False, cancel_futures=True)
                            break
                        try:
                            consulta, resultado = future.result()
                            cola_id = consulta['id']
                            cedula = consulta['cedula']
                            if resultado and resultado.get('status') == 'api_error':
                                enviar_resultado(cola_id, cedula, False, error=resultado.get('error', 'Error API'))
                            elif resultado and resultado.get('status') == 'not_found':
                                enviar_resultado(cola_id, cedula, False, error='Cedula no encontrada')
                            elif resultado and any(v for k, v in resultado.items() if k != 'status' and v):
                                datos = {
                                    'municipio_votacion': resultado.get('municipio'),
                                    'departamento_votacion': resultado.get('departamento'),
                                    'puesto_votacion': resultado.get('puesto'),
                                    'direccion_puesto': resultado.get('direccion'),
                                    'mesa': resultado.get('mesa'),
                                    'zona_votacion': resultado.get('zona'),
                                }
                                datos = {k: v for k, v in datos.items() if v is not None}
                                enviar_resultado(cola_id, cedula, True, datos=datos)
                            else:
                                enviar_resultado(cola_id, cedula, False, error='No se encontraron datos')
                        except Exception as e:
                            logger.error(f"Error procesando consulta: {e}")
                time.sleep(5)

            if not consultas:
                logger.info("Sin consultas. Esperando 30s...")
                time.sleep(30)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            time.sleep(10)

    logger.info("Worker finalizado")


if __name__ == "__main__":
    main()
