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
from concurrent.futures import ThreadPoolExecutor, as_completed, CancelledError

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
    query_registraduria_scraper_fallback,
    NO_CENSO_DATOS,
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
    # Copia para evitar RuntimeError si otro thread modifica durante iteración
    expiradas = [c for c, ts in list(FAILED_CEDULAS_CACHE.items()) if now - ts >= FAILED_CACHE_TTL]
    for c in expiradas:
        FAILED_CEDULAS_CACHE.pop(c, None)


def procesar_consulta(consulta: dict) -> tuple:
    time.sleep(random.uniform(0, 0.5))
    cedula = consulta.get('cedula') or consulta.get('numero_documento', '')
    if not cedula:
        return (consulta, {"status": "api_error", "error": "Cedula no especificada"})
    resultado = query_registraduria(cedula)
    # Solo scraper si not_found SIN no_censo (scraper usa misma API, no aporta si ya sabemos no_censo)
    if resultado and resultado.get('status') == 'not_found' and not resultado.get('no_censo') and settings.ENABLE_SCRAPER_FALLBACK:
        logger.info(f"Intentando scraper fallback para cedula={cedula}")
        fallback = query_registraduria_scraper_fallback(cedula)
        if fallback and any(v for k, v in fallback.items() if k != 'status' and v):
            resultado = fallback
            logger.info(f"Scraper fallback obtuvo datos para cedula={cedula}")
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
    try:
        _warmup_token_pool(num_tokens=1)
    except BaseException as e:
        logger.warning(f"Warmup falló (continuando): {e}")
    running = True

    def stop(sig, frame):
        nonlocal running
        running = False
        logger.info("Deteniendo...")

    signal.signal(signal.SIGINT, stop)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, stop)
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, lambda s, f: None)  # Ignorar SIGHUP para no terminar por desconexión

    while running:
        try:
            _limpiar_cache_fallidas()
            consultas = obtener_consultas_pendientes(tipo='registraduria', limit=2)

            if consultas:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = {executor.submit(procesar_consulta, c): c for c in consultas}
                    for future in as_completed(futures):
                        if not running:
                            try:
                                executor.shutdown(wait=False, cancel_futures=True)
                            except TypeError:
                                executor.shutdown(wait=False)
                            break
                        try:
                            consulta, resultado = future.result()
                        except CancelledError:
                            logger.debug("Consulta cancelada")
                            continue
                        except Exception as e:
                            logger.error(f"Error procesando consulta: {e}", exc_info=True)
                            continue
                        try:
                            cola_id = consulta.get('id') or consulta.get('cola_id')
                            cedula = consulta.get('cedula') or consulta.get('numero_documento', '')
                            elector_id = consulta.get('elector_id') or consulta.get('electorId')
                            if cola_id is None:
                                logger.error(f"Consulta sin id/cola_id: {list(consulta.keys())}")
                                continue
                            def _send(ok_flag, err=None, d=None):
                                return enviar_resultado(cola_id, cedula, ok_flag, datos=d, error=err, elector_id=elector_id)

                            if resultado and resultado.get('status') == 'api_error':
                                err_msg = resultado.get('error', 'Error API')
                                ok = _send(False, err=err_msg)
                                logger.info(f"Enviado (api_error) cedula={cedula} cola_id={cola_id} ok={ok} error={err_msg}")
                            elif resultado and resultado.get('status') == 'not_found':
                                if resultado.get('no_censo'):
                                    ok = _send(True, d=NO_CENSO_DATOS)
                                    logger.info(f"Enviado (NO CENSO) cedula={cedula} cola_id={cola_id} ok={ok}")
                                else:
                                    ok = _send(False, err='Cedula no encontrada')
                                    logger.info(f"Enviado (not_found) cedula={cedula} cola_id={cola_id} ok={ok}")
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
                                ok = _send(True, d=datos)
                                logger.info(f"Enviado (exito) cedula={cedula} cola_id={cola_id} ok={ok} datos={datos}")
                            else:
                                ok = _send(False, err='No se encontraron datos')
                                logger.info(f"Enviado (sin datos) cedula={cedula} cola_id={cola_id} ok={ok} resultado={resultado}")
                        except Exception as e:
                            logger.error(f"Error enviando resultado: {e}", exc_info=True)
                time.sleep(5)

            if not consultas:
                logger.info("Sin consultas. Esperando 30s...")
                time.sleep(30)

        except KeyboardInterrupt:
            break
        except SystemExit:
            raise
        except BaseException as e:
            # Capturar cualquier error para mantener ejecución perpetua (solo salir con SIGINT/SIGTERM)
            logger.error(f"Error (continuando): {type(e).__name__}: {e}", exc_info=True)
            time.sleep(10)

    logger.info("Worker finalizado")


if __name__ == "__main__":
    main()
