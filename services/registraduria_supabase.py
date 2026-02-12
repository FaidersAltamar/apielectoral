"""
Servicio de Registraduría conectado a Supabase.
Usa API directa de infovotantes (sin Playwright).

- Obtiene consultas pendientes de Supabase
- Consulta lugar de votación vía API directa
- Envía resultados a Supabase
"""

import os
import time
import json
import logging
import requests
from collections import deque
from threading import Lock
from typing import Optional, Dict, Any, List

# Cargar config desde el proyecto
from config import settings

# Intentar librería 2captcha
try:
    from twocaptcha import TwoCaptcha
    from twocaptcha.api import ApiException
    HAS_2CAPTCHA_LIB = True
except ImportError:
    HAS_2CAPTCHA_LIB = False

# Configuración
TWOCAPTCHA_API_KEY = settings.API_KEY_2CAPTCHA or os.getenv('TWOCAPTCHA_API_KEY')
CONSULTA_API_TOKEN = settings.CONSULTA_API_TOKEN or os.getenv('CONSULTA_API_TOKEN')
SUPABASE_FUNCTIONS_URL = settings.SUPABASE_FUNCTIONS_URL

API_URL = "https://apiweb-eleccionescolombia.infovotantes.com/api/v1/citizen/get-information"
BASE_URL = "https://eleccionescolombia.registraduria.gov.co/identificacion"
SITE_KEY = "6Lc9DmgrAAAAAJAjWVhjDy1KSgqzqJikY5z7I9SV"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

ENABLE_TOKEN_POOL = True
TOKEN_POOL_MAX = 3
TOKEN_TTL = 90
FAILED_CACHE_TTL = 20 * 60  # 20 min

_http_session: Optional[requests.Session] = None
_session_lock = Lock()
FAILED_CEDULAS_CACHE: Dict[str, float] = {}

logger = logging.getLogger(__name__)


def _get_session() -> requests.Session:
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
        with self._pool_lock:
            while self._token_pool:
                token_data = self._token_pool.popleft()
                if time.time() - token_data['timestamp'] < max_age:
                    return token_data['token']
        return None

    def put_token(self, token: str) -> None:
        with self._pool_lock:
            if len(self._token_pool) < TOKEN_POOL_MAX:
                self._token_pool.append({'token': token, 'timestamp': time.time()})

    def get_pool_size(self) -> int:
        with self._pool_lock:
            return len(self._token_pool)


def _cedula_fallo_reciente(cedula: str) -> bool:
    now = time.time()
    if cedula in FAILED_CEDULAS_CACHE:
        if now - FAILED_CEDULAS_CACHE[cedula] < FAILED_CACHE_TTL:
            return True
        del FAILED_CEDULAS_CACHE[cedula]
    return False


def _registrar_cedula_fallo(cedula: str) -> None:
    FAILED_CEDULAS_CACHE[cedula] = time.time()


def _solve_recaptcha_direct(site_key: str, page_url: str) -> Optional[str]:
    if not TWOCAPTCHA_API_KEY:
        return None
    if HAS_2CAPTCHA_LIB:
        try:
            solver = TwoCaptcha(TWOCAPTCHA_API_KEY, pollingInterval=1, defaultTimeout=60)
            result = solver.recaptcha(sitekey=site_key, url=page_url, invisible=0, pollingInterval=1)
            return result['code'] if isinstance(result, dict) else result
        except ApiException as e:
            if 'ERROR_WRONG_GOOGLEKEY' in str(e):
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(page_url)
                    origin = f"{parsed.scheme}://{parsed.netloc}"
                    solver = TwoCaptcha(TWOCAPTCHA_API_KEY, pollingInterval=1, defaultTimeout=60)
                    result = solver.recaptcha(sitekey=site_key, url=origin, invisible=0, pollingInterval=1)
                    return result['code'] if isinstance(result, dict) else result
                except Exception:
                    pass
            logger.error(f"Error 2Captcha: {e}")
            return None
        except Exception as e:
            logger.error(f"Error solve_recaptcha: {e}")
            return None
    # Fallback: requests directo
    try:
        session = _get_session()
        resp = session.post('http://2captcha.com/in.php', data={
            'key': TWOCAPTCHA_API_KEY, 'method': 'userrecaptcha',
            'googlekey': site_key, 'pageurl': page_url, 'json': 1
        }, timeout=10)
        if resp.status_code != 200:
            return None
        r = resp.json()
        if r.get('status') != 1:
            return None
        captcha_id = r.get('request')
        for attempt in range(50):
            time.sleep(1.5 if attempt < 10 else 2)
            resp = session.get('http://2captcha.com/res.php', params={
                'key': TWOCAPTCHA_API_KEY, 'action': 'get', 'id': captcha_id, 'json': 1
            }, timeout=10)
            r = resp.json()
            if r.get('status') == 1:
                return r.get('request')
            if r.get('request') != 'CAPCHA_NOT_READY':
                return None
        return None
    except Exception as e:
        logger.error(f"Error solve_recaptcha: {e}")
        return None


def solve_recaptcha(site_key: str, page_url: str) -> Optional[str]:
    if not TWOCAPTCHA_API_KEY:
        return None
    if ENABLE_TOKEN_POOL:
        token_cache = TokenCache()
        token = token_cache.get_token(TOKEN_TTL)
        if token:
            return token
    return _solve_recaptcha_direct(site_key, page_url)


def _query_registraduria_with_code(cedula: str, election_code: str) -> Optional[Dict[str, Any]]:
    """Consulta API con un election_code especifico. Retorna None si status_code 13 (para reintentar)."""
    session = _get_session()
    payload = {
        "identification": str(cedula),
        "identification_type": "CC",
        "election_code": election_code.strip(),
        "module": "polling_place",
        "platform": "web"
    }
    for intento_token in range(2):
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
                try:
                    data = resp.json()
                    if data.get('status_code') == 13:
                        return {"status": "not_found", "no_censo": True}  # Respuesta definitiva, no probar otros codes
                except Exception:
                    pass
                _registrar_cedula_fallo(cedula)
                return {"status": "api_error", "error": "API no disponible (404)"}
            if resp.status_code == 403:
                break
            if resp.status_code == 500 and intento < 2:
                time.sleep(10 + 5 * intento)
                continue
            if resp.status_code != 403:
                resp.raise_for_status()
                break

        if resp and resp.status_code == 200:
            break
        if resp and resp.status_code == 403:
            if intento_token < 1:
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
        return {"status": "not_found", "no_censo": True}
    if not data.get('status') or not data.get('data'):
        return None

    inner = data.get('data', {})
    voter = inner.get('voter', {}) or {}
    polling_place = inner.get('polling_place', {}) or {}
    place_address = (polling_place.get('place_address') or {}) if polling_place else {}

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


def query_registraduria(cedula: str) -> Optional[Dict[str, Any]]:
    """Consulta lugar de votacion via API directa. Intenta multiples election_code."""
    try:
        if _cedula_fallo_reciente(cedula):
            return {"status": "api_error", "error": "Reintento bloqueado 20min"}
        logger.info(f"Consultando Registraduria para cedula: {cedula}")

        election_codes = getattr(settings, 'ELECTION_CODES_TO_TRY', ['congreso', 'presidencial', 'alcaldes'])
        for ec in election_codes:
            ec = ec.strip() if isinstance(ec, str) else str(ec)
            if not ec:
                continue
            logger.info(f"Intentando election_code={ec}")
            result = _query_registraduria_with_code(cedula, ec)
            if result is None:
                continue
            if result.get('status') == 'not_found':
                if result.get('no_censo'):
                    return result  # Respuesta definitiva, no probar otros codes
                continue
            if result.get('status') == 'api_error':
                return result
            return result

        return {"status": "not_found", "no_censo": True}
    except requests.RequestException as e:
        logger.error(f"Error API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            code = e.response.status_code
            if code == 404:
                try:
                    data = e.response.json()
                    if data.get('status_code') == 13:
                        return {"status": "not_found", "no_censo": True}
                except Exception:
                    pass
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


def query_registraduria_scraper_fallback(cedula: str) -> Optional[Dict[str, Any]]:
    """Fallback con scraper Playwright cuando la API directa devuelve not_found."""
    if not getattr(settings, 'ENABLE_SCRAPER_FALLBACK', True):
        return None
    if not TWOCAPTCHA_API_KEY:
        return None
    try:
        from scrapper.registraduria_scraper_optimizado import RegistraduriaScraperAuto
        scraper = RegistraduriaScraperAuto(TWOCAPTCHA_API_KEY, check_balance=False, enable_token_pool=False)
        try:
            result = scraper.scrape_nuip(cedula)
            if result.get('status') != 'success':
                return None
            data_records = result.get('data', [])
            if not data_records:
                return None
            rec = data_records[0]
            return {
                'nuip': rec.get('NUIP', cedula),
                'departamento': rec.get('DEPARTAMENTO', ''),
                'municipio': rec.get('MUNICIPIO', ''),
                'puesto': rec.get('PUESTO', ''),
                'direccion': rec.get('DIRECCIÓN', rec.get('DIRECCION', '')),
                'mesa': str(rec.get('MESA', '')),
                'zona': str(rec.get('ZONA', '')),
            }
        finally:
            scraper.close()
    except Exception as e:
        logger.warning(f"Scraper fallback error: {e}")
        return None


NO_CENSO_DATOS = {
    'municipio_votacion': 'NO CENSO',
    'departamento_votacion': 'NO CENSO',
    'puesto_votacion': 'NO CENSO',
    'direccion_puesto': 'NO CENSO',
    'mesa': 'NO CENSO',
    'zona_votacion': 'NO CENSO',
}


def obtener_consultas_pendientes(tipo: str = 'registraduria', limit: int = 50) -> List[Dict]:
    """Obtiene cedulas pendientes de Supabase."""
    if not CONSULTA_API_TOKEN or not SUPABASE_FUNCTIONS_URL:
        logger.error("CONSULTA_API_TOKEN o SUPABASE_FUNCTIONS_URL no configurados")
        return []
    url = f"{SUPABASE_FUNCTIONS_URL.rstrip('/')}/consultas-pendientes"
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
            logger.info("Supabase OK (HTTP 200) pero 0 consultas pendientes en cola")
        elif consultas:
            logger.info(f"Consulta keys: {list(consultas[0].keys())}")
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


def enviar_resultado(cola_id: str, cedula: str, exito: bool, datos: Optional[Dict] = None, error: Optional[str] = None, elector_id: Optional[str] = None) -> bool:
    """Envía resultado a Supabase."""
    if not CONSULTA_API_TOKEN or not SUPABASE_FUNCTIONS_URL:
        return False
    payload = {
        'cola_id': cola_id, 'cedula': cedula, 'numero_documento': cedula,
        'tipo': 'registraduria', 'exito': exito, 'datos': datos or {}, 'error': error
    }
    if elector_id is not None:
        payload['elector_id'] = elector_id
    try:
        resp = requests.post(
            f"{SUPABASE_FUNCTIONS_URL.rstrip('/')}/recibir-datos",
            json=payload,
            headers={'Authorization': f'Bearer {CONSULTA_API_TOKEN}', 'Content-Type': 'application/json'},
            timeout=30
        )
        resp_body = resp.text[:500] if resp.text else ''
        if resp.status_code in (401, 404):
            logger.error(f"Error enviando: {resp.status_code} - {resp_body}")
            return False
        resp.raise_for_status()
        try:
            resp_json = resp.json()
        except Exception:
            resp_json = {}
        ok = resp_json.get('success', False)
        msg = resp_json.get('message', resp_json.get('error', ''))
        if not ok:
            logger.warning(f"recibir-datos success=False cedula={cedula} cola_id={cola_id} resp={resp_body}")
        elif msg:
            logger.info(f"recibir-datos ok cedula={cedula} message={msg}")
        return ok
    except Exception as e:
        logger.error(f"Error enviando resultado: {e}", exc_info=True)
        return False
