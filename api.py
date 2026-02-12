"""
API Electoral - Solo Registraduría (puesto de votación).
Conectado a Supabase vía worker_registraduria.py
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict
import os
import sys
import time
import requests

from models.request import PeticionRequest
from utils.time_utils import calculate_response_time
from utils.captcha_solver import TwoCaptchaSolver
from config import settings
from services.registraduria_supabase import query_registraduria

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    description="API para consultar puesto de votación - Registraduría (Supabase)",
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

API_KEY = settings.API_KEY_2CAPTCHA or os.getenv('TWOCAPTCHA_API_KEY') or os.getenv('APIKEY_2CAPTCHA')
if not API_KEY:
    print("Error: No se encontro la API key de 2captcha (TWOCAPTCHA_API_KEY o APIKEY_2CAPTCHA)")
    sys.exit(1)


def _safe_print(msg: str) -> None:
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))


@app.on_event("startup")
async def startup_event():
    _safe_print("API Electoral - Registraduria")
    _safe_print(f"API Key configurada: {API_KEY[:10]}...")
    _safe_print(f"Supabase: {settings.SUPABASE_FUNCTIONS_URL}")
    _safe_print(f"Endpoint puesto externo: {settings.EXTERNAL_API_PUESTO_URL}")


@app.get("/balance")
async def get_balance():
    """Obtener balance de la cuenta de 2captcha."""
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


@app.post("/consultar-puesto-votacion")
async def get_registraduria_data(request: PeticionRequest):
    """
    Consulta puesto de votación en Registraduría (API directa infovotantes).
    
    - nuip: Número de identificación
    - enviarapi: Si es True, envía el puesto al API externo
    """
    start_time = time.time()

    try:
        resultado = query_registraduria(request.nuip)

        if resultado is None:
            raise HTTPException(status_code=500, detail="Error al consultar Registraduría")

        if resultado.get("status") == "api_error":
            raise HTTPException(
                status_code=503,
                detail={"error": resultado.get("error", "Error API"), "status": "api_error"}
            )

        if resultado.get("status") == "not_found":
            response_time, execution_time = calculate_response_time(start_time)
            return {
                "status": "not_found",
                "message": "Cédula no encontrada",
                "nuip": request.nuip,
                "execution_time": execution_time
            }

        # Mapear formato del servicio al formato esperado por el cliente
        data_records = [{
            "DEPARTAMENTO": resultado.get("departamento", ""),
            "MUNICIPIO": resultado.get("municipio", ""),
            "PUESTO": resultado.get("puesto", ""),
            "DIRECCIÓN": resultado.get("direccion", ""),
            "MESA": resultado.get("mesa", ""),
            "ZONA": resultado.get("zona", ""),
        }]

        response = {
            "status": "success",
            "data": data_records,
            "nuip": resultado.get("nuip", request.nuip),
            "message": "Puesto de votación encontrado"
        }

        # Enviar al API externo si está habilitado
        if request.enviarapi and settings.EXTERNAL_API_PUESTO_URL:
            voting_data = data_records[0]
            api_response = send_voting_place_to_external_api(request.nuip, voting_data)
            response["api_externa"] = api_response

        response_time, execution_time = calculate_response_time(start_time)
        response["execution_time"] = execution_time

        return response

    except HTTPException:
        raise
    except Exception as e:
        response_time, execution_time = calculate_response_time(start_time)
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "execution_time": execution_time
            }
        )


def send_voting_place_to_external_api(numero_documento: str, voting_data: dict) -> dict:
    """Envía los datos del puesto de votación al endpoint externo."""
    try:
        payload = {
            "numerodocumento": numero_documento,
            "departamento": voting_data.get("DEPARTAMENTO", ""),
            "municipio": voting_data.get("MUNICIPIO", ""),
            "puesto": voting_data.get("PUESTO", ""),
            "direccion": voting_data.get("DIRECCIÓN", ""),
            "mesa": voting_data.get("MESA", ""),
        }
        response = requests.post(
            settings.EXTERNAL_API_PUESTO_URL,
            json=payload,
            timeout=20
        )
        response.raise_for_status()
        result = response.json()
        return {
            "puesto_api_called": True,
            "puesto_api_status": result.get("status"),
            "puesto_api_message": result.get("message")
        }
    except requests.exceptions.Timeout:
        return {"puesto_api_called": False, "puesto_api_error": "Timeout"}
    except Exception as e:
        return {"puesto_api_called": False, "puesto_api_error": str(e)}
