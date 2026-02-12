"""
Worker de Registraduría conectado a Supabase.

Obtiene consultas pendientes de Supabase, consulta lugar de votación
vía API directa infovotantes, y envía resultados a Supabase.

Variables de entorno (.env):
- TWOCAPTCHA_API_KEY: API key de 2Captcha
- CONSULTA_API_TOKEN: Token para Supabase
- SUPABASE_FUNCTIONS_URL: (opcional) URL de Edge Functions

Ejecutar: python worker_registraduria.py
"""

import os
import sys
import time
import random
import signal
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Cargar .env
try:
    from dotenv import load_dotenv
    _dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(_dir, '.env'))
except ImportError:
    pass

from config import settings
from services.registraduria_supabase import (
    TWOCAPTCHA_API_KEY,
    CONSULTA_API_TOKEN,
    SUPABASE_FUNCTIONS_URL,
    SITE_KEY,
    BASE_URL,
    query_registraduria,
    obtener_consultas_pendientes,
    enviar_resultado,
    TokenCache,
    ENABLE_TOKEN_POOL,
    FAILED_CEDULAS_CACHE,
    FAILED_CACHE_TTL,
    _solve_recaptcha_direct,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _warmup_token_pool(num_tokens: int = 2) -> None:
    if not ENABLE_TOKEN_POOL or not TWOCAPTCHA_API_KEY:
        return
    token_cache = TokenCache()
    if token_cache.get_pool_size() > 0:
        return
    logger.info(f"Warmup: pre-llenando pool con {num_tokens} token(s)...")
    for _ in range(num_tokens):
        token = _solve_recaptcha_direct(SITE_KEY, BASE_URL)
        if token:
            token_cache.put_token(token)
    logger.info(f"Warmup completo. Pool: {token_cache.get_pool_size()} token(s)")


def _limpiar_cache_fallidas() -> None:
    now = time.time()
    expiradas = [c for c, ts in FAILED_CEDULAS_CACHE.items() if now - ts >= FAILED_CACHE_TTL]
    for c in expiradas:
        del FAILED_CEDULAS_CACHE[c]


def procesar_consulta(consulta: dict) -> tuple:
    time.sleep(random.uniform(0, 3))
    cedula = consulta['cedula']
    resultado = query_registraduria(cedula)
    return (consulta, resultado)


def main():
    if not TWOCAPTCHA_API_KEY:
        logger.error("Configura TWOCAPTCHA_API_KEY en .env")
        sys.exit(1)
    if not CONSULTA_API_TOKEN or not SUPABASE_FUNCTIONS_URL:
        logger.error("Configura CONSULTA_API_TOKEN y SUPABASE_FUNCTIONS_URL en .env")
        sys.exit(1)

    logger.info("Worker Registraduria (Supabase) iniciado")
    logger.info(f"Supabase: {SUPABASE_FUNCTIONS_URL}/consultas-pendientes")
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
                with ThreadPoolExecutor(max_workers=1) as executor:
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
