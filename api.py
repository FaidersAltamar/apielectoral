from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import asyncio
import os
import sys
import time
import requests
from datetime import datetime

# Importar utilidades
from models.request import PeticionRequest, BulkSisbenRequest, BulkNameRequest, ConsultaNombreRequest
from utils.time_utils import format_execution_time, calculate_response_time, get_current_timestamp
from utils.captcha_solver import TwoCaptchaSolver

# Importar gestor de tareas
from task_manager import (
    create_task,
    get_task,
    delete_task,
    list_tasks,
    process_bulk_sisben_task,
    process_bulk_name_task,
    get_tasks_directory,
    get_task_count
)


# Importar clases existentes
from config import settings
from scrapper.registraduria_scraper import RegistraduriaScraperAuto, save_registraduria_results
from scrapper.police_scraper import PoliciaScraperAuto, save_police_results 
from scrapper.procuraduria_scraper import ProcuraduriaScraperAuto, save_procuraduria_results
from scrapper.sisben_scraper import SisbenScraperAuto, save_sisben_results

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Configuración global
API_KEY = os.getenv('APIKEY_2CAPTCHA')
if not API_KEY:
    print("❌ Error: No se encontró la API key de 2captcha")
    sys.exit(1)

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    print("🚀 API Electoral")
    print(f"🔑 API Key configurada: {API_KEY[:10]}...")
    print(f"📁 Directorio de tareas: {get_tasks_directory().absolute()}")
    print(f"📊 Tareas guardadas: {get_task_count()}")
    print(f"\n🌐 URLs de API Externa:")
    print(f"   📝 Nombre: {settings.EXTERNAL_API_NOMBRE_URL}")
    print(f"   🗳️  Puesto: {settings.EXTERNAL_API_PUESTO_URL}")

@app.get("/balance")
async def get_balance():
    """
    Obtener balance de la cuenta de 2captcha y estimado de peticiones
    
    Returns:
        dict: Balance en USD, costo por captcha y estimado de peticiones disponibles
    """
    try:
        solver = TwoCaptchaSolver(API_KEY)
        balance_info = solver.get_balance()
        return balance_info
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error al consultar balance: {e}"
        }


@app.post("/consultar-nombres-v1")
async def get_procuraduria_data(request: PeticionRequest):
    """
    Consulta nombre en Procuraduría
    
    Args:
        request.nuip: Número de identificación
        request.enviarapi: Si es True, envía el nombre al API externo
    """
    start_time = time.time()
    scraper = None
    try:
        scraper = ProcuraduriaScraperAuto(headless=True)
        result = scraper.scrape_nuip(request.nuip)
        
        # Si enviarapi es True y se encontró el nombre, enviar al API externo
        if request.enviarapi and result.get("status") == "success":
            nombre = result.get("name", "")
            if nombre and nombre.strip():
                print(f"📤 Enviando nombre al API externo (v1)...")
                api_response = send_name_to_external_api(request.nuip, nombre.strip())
                result["api_externa"] = api_response
        
        return result
    except Exception as e:
        response_time_seconds, execution_time = calculate_response_time(start_time)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Error al procesar la consulta: {str(e)}",
                "response_time_seconds": response_time_seconds,
                "execution_time": execution_time
            }
        )
    finally:
        if scraper:
            scraper.close()
    
@app.post("/consultar-nombres-v2")
async def get_police_data(request: PeticionRequest):
    """
    Consulta nombre en Policía
    
    Args:
        request.nuip: Número de identificación
        request.fecha_expedicion: Fecha de expedición (opcional)
        request.enviarapi: Si es True, envía el nombre al API externo
    """
    start_time = time.time()
    try:
        scraper = PoliciaScraperAuto(headless=True)
        result = scraper.scrape_name_by_nuip(request.nuip, request.fecha_expedicion)
        
        # Si enviarapi es True y se encontró el nombre, enviar al API externo
        if request.enviarapi and result.get("status") == "success":
            nombre = result.get("name", "")
            if nombre and nombre.strip():
                print(f"📤 Enviando nombre al API externo (v2)...")
                api_response = send_name_to_external_api(request.nuip, nombre.strip())
                result["api_externa"] = api_response
        
        return result    
    except Exception as e:
        response_time_seconds, execution_time = calculate_response_time(start_time)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Error al procesar la consulta: {str(e)}",
                "response_time_seconds": response_time_seconds,
                "execution_time": execution_time
            }
        )
    finally:
        scraper.close()

@app.post("/consultar-nombres-v3")
async def get_sisben_data(request: PeticionRequest):
    start_time = time.time()
    scraper = None
    try:
        scraper = SisbenScraperAuto(headless=True)
        result = scraper.scrape_name_by_nuip(request.nuip)
        return result    
    except Exception as e:
        response_time_seconds, execution_time = calculate_response_time(start_time)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Error al procesar la consulta: {str(e)}",
                "response_time_seconds": response_time_seconds,
                "execution_time": execution_time
            }
        )
    finally:
        if scraper:
            scraper.close()

@app.post("/consultar-puesto-votacion")
async def get_registraduria_data(request: PeticionRequest):
    """
    Consulta puesto de votación en Registraduría
    
    Args:
        request.nuip: Número de identificación
        request.enviarapi: Si es True, envía el puesto al API externo
    """
    start_time = time.time() 
    
    try:
        scraper = RegistraduriaScraperAuto(API_KEY, headless=True)
        
        try:
            result = scraper.scrape_nuip(request.nuip)
            
            # Si enviarapi es True y se encontró el puesto, enviar al API externo
            if request.enviarapi and result.get("status") == "success":
                data_records = result.get("data", [])
                if data_records and len(data_records) > 0:
                    voting_data = data_records[0]
                    print(f"📤 Enviando puesto de votación al API externo...")
                    api_response = send_voting_place_to_external_api(request.nuip, voting_data)
                    result["api_externa"] = api_response
            
            return result
            
        finally:
            scraper.close()
            
    except Exception as e:
        response_time_seconds, execution_time = calculate_response_time(start_time)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Error al procesar la consulta: {str(e)}",
                "response_time_seconds": response_time_seconds,
                "execution_time": execution_time
            }
        )

@app.post("/consultar-combinado")
async def get_combined_data(request: PeticionRequest):
    """
    Endpoint combinado optimizado que ejecuta consultas en paralelo:
    - Puesto de votación (Registraduría)
    - Nombres en orden de prioridad:
      1. Sisben (siempre)
      2. Procuraduría (siempre)
      3. Policía (solo si hay fecha_expedicion)
    """
    start_time = time.time()
    
    # Determinar si incluir consulta de Policía según fecha_expedicion
    use_police = request.fecha_expedicion is not None and request.fecha_expedicion.strip() != ""
    
    async def fetch_registraduria():
        scraper = None
        try:
            scraper = RegistraduriaScraperAuto(API_KEY, headless=True)
            result = await asyncio.to_thread(scraper.scrape_nuip, request.nuip)
            return {"success": True, "data": result, "source": "registraduria"}
        except Exception as e:
            return {"success": False, "error": str(e), "source": "registraduria"}
        finally:
            if scraper:
                try:
                    scraper.close()
                except:
                    pass
    
    async def fetch_police():
        scraper = None
        try:
            scraper = PoliciaScraperAuto(headless=True)
            result = await asyncio.to_thread(scraper.scrape_name_by_nuip, request.nuip, request.fecha_expedicion)
            return {"success": True, "data": result, "source": "policia"}
        except Exception as e:
            return {"success": False, "error": str(e), "source": "policia"}
        finally:
            if scraper:
                try:
                    scraper.close()
                except:
                    pass
    
    async def fetch_procuraduria():
        scraper = None
        try:
            scraper = ProcuraduriaScraperAuto(headless=True)
            result = await asyncio.to_thread(scraper.scrape_nuip, request.nuip)
            return {"success": True, "data": result, "source": "procuraduria"}
        except Exception as e:
            return {"success": False, "error": str(e), "source": "procuraduria"}
        finally:
            if scraper:
                try:
                    scraper.close()
                except:
                    pass
    
    async def fetch_sisben():
        scraper = None
        try:
            scraper = SisbenScraperAuto(headless=True)
            result = await asyncio.to_thread(scraper.scrape_name_by_nuip, request.nuip)
            return {"success": True, "data": result, "source": "sisben"}
        except Exception as e:
            return {"success": False, "error": str(e), "source": "sisben"}
        finally:
            if scraper:
                try:
                    scraper.close()
                except:
                    pass
    
    try:
        # Ejecutar Registraduría y Sisben en paralelo primero
        registraduria_result, sisben_result = await asyncio.gather(
            fetch_registraduria(),
            fetch_sisben(),
            return_exceptions=True
        )
        
        # Verificar si Sisben encontró el nombre
        def has_valid_name(result):
            """Verifica si el resultado tiene un nombre válido"""
            if isinstance(result, Exception):
                return False
            if not result.get("success"):
                return False
            data = result.get("data", {})
            name = data.get("name") or data.get("nombre") or data.get("nombre_completo")
            return name is not None and name.strip() != ""
        
        sisben_has_name = has_valid_name(sisben_result)
        
        # Si Sisben no encontró el nombre, consultar Procuraduría
        if not sisben_has_name:
            procuraduria_result = await fetch_procuraduria()
            procuraduria_has_name = has_valid_name(procuraduria_result)
            
            # Si Procuraduría tampoco encontró y hay fecha_expedicion, consultar Policía
            if not procuraduria_has_name and use_police:
                police_result = await fetch_police()
            else:
                police_result = None
        else:
            # Sisben encontró el nombre, no consultar otros
            procuraduria_result = {"success": False, "skipped": True, "reason": "Nombre encontrado en Sisben"}
            police_result = None
        
        response_time_seconds, execution_time = calculate_response_time(start_time)
        
        # Procesar resultados y extraer información
        def extract_name(result):
            """Extrae el nombre del resultado de cualquier scraper"""
            if isinstance(result, Exception):
                return None
            if not result.get("success"):
                return None
            
            data = result.get("data", {})
            # Intentar obtener el nombre de diferentes estructuras
            return data.get("name") or data.get("nombre") or data.get("nombre_completo")
        
        def extract_voting_place(result):
            """Extrae información del puesto de votación"""
            if isinstance(result, Exception):
                return None
            if not result.get("success"):
                return None
            
            data = result.get("data", {})
            records = data.get("data", [])
            if records and len(records) > 0:
                return records[0]  # Retornar el primer registro
            return None
        
        # Extraer nombres de las diferentes fuentes con orden de prioridad
        name_from_sisben = extract_name(sisben_result)
        name_from_procuraduria = extract_name(procuraduria_result)
        name_from_police = extract_name(police_result) if police_result else None
        
        # Determinar el nombre final (prioridad: Sisben > Procuraduría > Policía)
        final_name = name_from_sisben or name_from_procuraduria or name_from_police
        
        # Extraer información del puesto de votación
        voting_info = extract_voting_place(registraduria_result)
        
        # Determinar el estado general
        has_name = final_name is not None
        has_voting_info = voting_info is not None
        
        # Construir mensaje
        messages = []
        if has_name:
            messages.append("Nombre encontrado")
        if has_voting_info:
            messages.append("Puesto de votación encontrado")
        
        if not messages:
            messages.append("No se encontró información")
        
        overall_status = "success" if (has_name or has_voting_info) else "error"
        
        # Construir respuesta unificada
        response = {
            "status": overall_status,
            "message": " - ".join(messages),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nuip": request.nuip,
            "name": final_name,
            "voting_place": voting_info,
            "response_time_seconds": response_time_seconds,
            "execution_time": execution_time,
            "sources": {
                "sisben": {
                    "success": sisben_result.get("success", False) if not isinstance(sisben_result, Exception) else False,
                    "name": name_from_sisben,
                    "priority": 1,
                    "consulted": True
                },
                "procuraduria": {
                    "success": procuraduria_result.get("success", False) if not isinstance(procuraduria_result, Exception) else False,
                    "name": name_from_procuraduria,
                    "priority": 2,
                    "consulted": not procuraduria_result.get("skipped", False) if not isinstance(procuraduria_result, Exception) else True,
                    "skipped_reason": procuraduria_result.get("reason") if procuraduria_result.get("skipped") else None
                },
                "policia": {
                    "success": police_result.get("success", False) if police_result and not isinstance(police_result, Exception) else False,
                    "name": name_from_police,
                    "priority": 3,
                    "consulted": police_result is not None and not isinstance(police_result, Exception)
                },
                "registraduria": {
                    "success": registraduria_result.get("success", False) if not isinstance(registraduria_result, Exception) else False,
                    "has_data": has_voting_info
                }
            }
        }
        
        return response
        
    except Exception as e:
        response_time_seconds, execution_time = calculate_response_time(start_time)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Error al procesar la consulta combinada: {str(e)}",
                "response_time_seconds": response_time_seconds,
                "execution_time": execution_time
            }
        )

def send_name_to_external_api(numero_documento: str, nombre_completo: str) -> dict:
    """
    Envía el nombre encontrado al endpoint externo
    
    Args:
        numero_documento: Número de documento
        nombre_completo: Nombre completo encontrado
    
    Returns:
        dict: Respuesta del endpoint externo con status y message
    """
    try:
        url = settings.EXTERNAL_API_NOMBRE_URL
        print(f"🔍 DEBUG - URL cargada: {url}")
        print(f"🔍 DEBUG - Tipo de URL: {type(url)}")
        
        payload = {
            "numerodocumento": numero_documento,
            "nombrecompleto": nombre_completo
        }
        
        print(f"📤 Enviando NOMBRE al endpoint externo: {url}")
        print(f"   Documento: {numero_documento}, Nombre: {nombre_completo}")
        
        response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Respuesta del endpoint de nombre: {result}")
        
        return {
            "nombre_api_called": True,
            "nombre_api_status": result.get("status"),
            "nombre_api_message": result.get("message")
        }
        
    except requests.exceptions.Timeout:
        print(f"⚠️ Timeout al llamar al endpoint de nombre")
        return {
            "nombre_api_called": False,
            "nombre_api_error": "Timeout al conectar con el endpoint de nombre"
        }
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error al llamar al endpoint de nombre: {e}")
        return {
            "nombre_api_called": False,
            "nombre_api_error": str(e)
        }
    except Exception as e:
        print(f"⚠️ Error inesperado al llamar al endpoint de nombre: {e}")
        return {
            "nombre_api_called": False,
            "nombre_api_error": str(e)
        }

def send_voting_place_to_external_api(numero_documento: str, voting_data: dict) -> dict:
    """
    Envía los datos del puesto de votación al endpoint externo
    
    Args:
        numero_documento: Número de documento
        voting_data: Datos del puesto de votación (departamento, municipio, puesto, dirección, mesa)
    
    Returns:
        dict: Respuesta del endpoint externo con status y message
    """
    try:
        url = settings.EXTERNAL_API_PUESTO_URL
        print(f"🔍 DEBUG - URL cargada: {url}")
        print(f"🔍 DEBUG - Tipo de URL: {type(url)}")
        
        payload = {
            "numerodocumento": numero_documento,
            "departamento": voting_data.get("DEPARTAMENTO", ""),
            "municipio": voting_data.get("MUNICIPIO", ""),
            "puesto": voting_data.get("PUESTO", ""),
            "direccion": voting_data.get("DIRECCIÓN", ""),
            "mesa": voting_data.get("MESA", "")
        }
        
        print(f"📤 Enviando PUESTO DE VOTACIÓN al endpoint externo: {url}")
        print(f"   Documento: {numero_documento}, Puesto: {voting_data.get('PUESTO', 'N/A')}")
        
        response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Respuesta del endpoint de puesto: {result}")
        
        return {
            "puesto_api_called": True,
            "puesto_api_status": result.get("status"),
            "puesto_api_message": result.get("message")
        }
        
    except requests.exceptions.Timeout:
        print(f"⚠️ Timeout al llamar al endpoint de puesto")
        return {
            "puesto_api_called": False,
            "puesto_api_error": "Timeout al conectar con el endpoint de puesto"
        }
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error al llamar al endpoint de puesto: {e}")
        return {
            "puesto_api_called": False,
            "puesto_api_error": str(e)
        }
    except Exception as e:
        print(f"⚠️ Error inesperado al llamar al endpoint de puesto: {e}")
        return {
            "puesto_api_called": False,
            "puesto_api_error": str(e)
        }

async def process_single_nuip(nuip: str, enviarapi: bool = False) -> dict:
    """
    Procesa un solo NUIP buscando el nombre en Sisben y consultando Registraduría
    
    Args:
        nuip: Número de identificación a consultar
        enviarapi: Si es True, envía los datos al API externo
    
    Returns:
        dict: Resultado de la consulta con nombre, source y respuesta del API externo
    """
    start_time = time.time()
    name = ""
    source = None
    
    try:
        # 1. Buscar en Sisben (con 1 intento y timeout)
        max_intentos_sisben = 1
        for intento_sisben in range(1, max_intentos_sisben + 1):
            scraper_sisben = None
            try:
                print(f"🔍 Sisben - Intento {intento_sisben}/{max_intentos_sisben}")
                scraper_sisben = SisbenScraperAuto(headless=True)
                
                # Usar timeout de 60 segundos para Sisben
                result_sisben = await asyncio.wait_for(
                    asyncio.to_thread(scraper_sisben.scrape_name_by_nuip, nuip),
                    timeout=60.0
                )
                
                # Verificar si se encontró el nombre
                if result_sisben.get("status") == "success":
                    extracted_name = result_sisben.get("name")
                    if extracted_name and extracted_name.strip():
                        name = extracted_name.strip()
                        source = "sisben"
                        print(f"✅ Nombre encontrado en Sisben: {name}")
                        break  # Salir del loop si se encontró
            except asyncio.TimeoutError:
                print(f"⏱️ Timeout en Sisben intento {intento_sisben} (60s excedidos)")
            except Exception as e:
                print(f"⚠️ Error en Sisben intento {intento_sisben}: {e}")
            finally:
                if scraper_sisben:
                    try:
                        scraper_sisben.close()
                    except Exception as close_error:
                        print(f"⚠️ Error al cerrar Sisben: {close_error}")
            
            # Esperar un poco antes del siguiente intento (solo si no es el último)
            if intento_sisben < max_intentos_sisben and not name:
                await asyncio.sleep(2)
        
        # Si ya encontró el nombre en Sisben, enviar al API y luego consultar puesto
        if name:
            # 1. PRIMERO: Enviar nombre al endpoint externo (solo si enviarapi=True)
            nombre_response = {}
            if enviarapi:
                print(f"📤 Enviando nombre al API externo...")
                nombre_response = send_name_to_external_api(nuip, name)
            
            # 2. SEGUNDO: Consultar puesto de votación
            voting_data = None
            scraper_registraduria = None
            try:
                print(f"🗳️ Consultando puesto de votación para {nuip}...")
                scraper_registraduria = RegistraduriaScraperAuto(API_KEY, headless=True)
                
                # Usar asyncio.wait_for para timeout de 120 segundos
                voting_result = await asyncio.wait_for(
                    asyncio.to_thread(scraper_registraduria.scrape_nuip, nuip),
                    timeout=120.0
                )
                
                if voting_result.get("status") == "success":
                    data_records = voting_result.get("data", [])
                    if data_records and len(data_records) > 0:
                        voting_data = data_records[0]
                        print(f"✅ Puesto de votación encontrado: {voting_data.get('PUESTO', 'N/A')}")
                    else:
                        print(f"⚠️ No se encontró puesto de votación")
                else:
                    print(f"⚠️ Error al consultar puesto de votación: {voting_result.get('message', 'Unknown')}")
            except asyncio.TimeoutError:
                print(f"⏱️ Timeout al consultar puesto de votación (120s excedidos)")
                voting_data = None
            except Exception as e:
                print(f"⚠️ Error al consultar puesto de votación: {e}")
            finally:
                if scraper_registraduria:
                    try:
                        scraper_registraduria.close()
                    except Exception as close_error:
                        print(f"⚠️ Error al cerrar scraper de registraduría: {close_error}")
            
            # 3. TERCERO: Enviar puesto de votación al endpoint externo (solo si enviarapi=True y se encontró)
            puesto_response = {}
            if enviarapi and voting_data:
                print(f"📤 Enviando puesto de votación al API externo...")
                puesto_response = send_voting_place_to_external_api(nuip, voting_data)
            
            response_time_seconds, execution_time = calculate_response_time(start_time)
            
            return {
                "nuip": nuip,
                "status": "success",
                "name": name,
                "voting_place": voting_data,
                "execution_time": execution_time,
                "source": source,
                **nombre_response,
                **puesto_response
            }
        
        # Si llegamos aquí, no se encontró en ninguna fuente
        response_time_seconds, execution_time = calculate_response_time(start_time)
        
        return {
            "nuip": nuip,
            "status": "not_found",
            "name": "",
            "execution_time": execution_time
        }
        
    except Exception as e:
        response_time_seconds, execution_time = calculate_response_time(start_time)
        
        return {
            "nuip": nuip,
            "status": "error",
            "name": "",
            "execution_time": execution_time,
            "error": str(e)
        }

@app.post("/consultar-nombres")
async def get_name_sequential(request: ConsultaNombreRequest):
    """
    Endpoint que busca nombres para múltiples NUIPs secuencialmente en:
    1. Sisben
    2. Registraduría (para puesto de votación)
    
    Si encuentra el nombre, lo envía automáticamente al endpoint externo.
    
    Args:
        request: Lista de NUIPs a consultar
    
    Returns:
        dict: Lista de resultados con status, name, execution_time, source para cada NUIP
    """
    start_time = time.time()
    results = []
    
    # Imprimir el request recibido
    print(f"\n{'='*60}")
    print(f"📥 REQUEST RECIBIDO:")
    print(f"{'='*60}")
    print(f"NUIPs: {request.nuips}")
    print(f"Total NUIPs: {len(request.nuips)}")
    print(f"{'='*60}\n")
    
    print(f"\n📋 Procesando {len(request.nuips)} NUIPs...")
    
    for idx, nuip in enumerate(request.nuips, 1):
        print(f"\n{'='*60}")
        print(f"📌 Procesando NUIP {idx}/{len(request.nuips)}: {nuip}")
        print(f"{'='*60}")
        
        try:
            # Agregar timeout global por NUIP (6 minutos máximo)
            result = await asyncio.wait_for(
                process_single_nuip(nuip, enviarapi=request.enviarapi),
                timeout=360.0
            )
            results.append(result)
        except asyncio.TimeoutError:
            print(f"⏱️ TIMEOUT GLOBAL: NUIP {nuip} excedió 6 minutos")
            results.append({
                "nuip": nuip,
                "status": "error",
                "name": "",
                "execution_time": "360+ seconds",
                "error": "Timeout global: procesamiento excedió 6 minutos"
            })
        except Exception as e:
            print(f"❌ ERROR CRÍTICO procesando NUIP {nuip}: {e}")
            results.append({
                "nuip": nuip,
                "status": "error",
                "name": "",
                "execution_time": "unknown",
                "error": f"Error crítico: {str(e)}"
            })
        
        # Pequeña pausa entre consultas para no sobrecargar
        if idx < len(request.nuips):
            await asyncio.sleep(1)
    
    total_time_seconds, total_execution_time = calculate_response_time(start_time)
    
    # Estadísticas
    successful = sum(1 for r in results if r["status"] == "success")
    not_found = sum(1 for r in results if r["status"] == "not_found")
    errors = sum(1 for r in results if r["status"] == "error")
    
    return {
        "status": "completed",
        "total_nuips": len(request.nuips),
        "successful": successful,
        "not_found": not_found,
        "errors": errors,
        "total_execution_time": total_execution_time,
        "results": results
    }


@app.post("/bulk/name")
async def create_bulk_name_task(request: BulkNameRequest, background_tasks: BackgroundTasks):
    """
    Crea una tarea asíncrona para consultar múltiples NUIPs usando búsqueda secuencial (máximo 50)
    Busca en orden: Sisben -> Procuraduría -> Policía (si hay fecha_expedicion)
    
    Args:
        request: Lista de NUIPs a consultar y fecha de expedición opcional
        
    Returns:
        dict: ID de la tarea creada y estado inicial
    """
    try:
        # Crear tarea usando el task_manager
        result = create_task(request.nuips, task_type="name")
        task_id = result["task_id"]
        
        # Agregar tarea en segundo plano
        background_tasks.add_task(process_bulk_name_task, task_id, request.nuips)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Error al crear la tarea: {str(e)}"
            }
        )

@app.get("/bulk/tasks/{task_id}")
async def get_bulk_task(task_id: str):
    """
    Consulta el estado y resultados de una tarea de consulta masiva (cualquier tipo)
    
    Args:
        task_id: ID de la tarea a consultar
        
    Returns:
        dict: Estado actual de la tarea y resultados si está completada
    """
    # Obtener tarea usando task_manager
    task = get_task(task_id)
    
    if task is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Tarea no encontrada",
                "task_id": task_id
            }
        )
    
    response = {
        "task_id": task_id,
        "task_type": task.get("task_type", "sisben"),
        "status": task["status"],
        "created_at": task["created_at"],
        "started_at": task.get("started_at"),
        "completed_at": task.get("completed_at"),
        "total_nuips": task["total_nuips"],
        "progress": task["progress"]
    }
    
    # Si la tarea está completada, incluir los datos
    if task["status"] == "completed":
        response["data"] = task["data"]
    
    # Si la tarea falló, incluir el error
    if task["status"] == "failed":
        response["error"] = task.get("error")
    
    return response

@app.delete("/bulk/tasks/{task_id}")
async def delete_bulk_task(task_id: str):
    """
    Elimina una tarea de consulta masiva del almacenamiento (memoria y archivo)
    
    Args:
        task_id: ID de la tarea a eliminar
        
    Returns:
        dict: Confirmación de eliminación
    """
    # Obtener tarea antes de eliminar
    task = get_task(task_id)
    
    if task is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Tarea no encontrada",
                "task_id": task_id
            }
        )
    
    task_status = task["status"]
    task_type = task.get("task_type", "sisben")
    
    # Eliminar tarea usando task_manager
    delete_task(task_id)
    
    return {
        "success": True,
        "message": "Tarea eliminada exitosamente",
        "task_id": task_id,
        "task_type": task_type,
        "previous_status": task_status
    }

@app.get("/bulk/tasks")
async def list_bulk_tasks(task_type: Optional[str] = None):
    """
    Lista todas las tareas de consulta masiva guardadas
    
    Args:
        task_type: Filtro opcional por tipo de tarea ("sisben", "name", o None para todas)
    
    Returns:
        dict: Lista de tareas con información resumida
    """
    # Obtener lista de tareas usando task_manager
    tasks_summary = list_tasks(task_type=task_type)
    
    return {
        "success": True,
        "total_tasks": len(tasks_summary),
        "filter": task_type if task_type else "all",
        "tasks": tasks_summary
    }
