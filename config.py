import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    API_KEY_2CAPTCHA = os.getenv('APIKEY_2CAPTCHA')
    MAX_NUIPS_SYNC = 50
    DEFAULT_DELAY = 5
    HEADLESS_MODE = True
    
    # Configuración de la API
    API_TITLE = "API Consulta Información Electoral"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "API para consultar información de puestos de Votación Funete de datos Registraduría Nacional del Estado Civil"
    
    # Configuración de endpoints externos
    EXTERNAL_API_URL = 'http://localhost/votantes/api/v1/respuestaapi'
    EXTERNAL_API_NOMBRE_URL = 'http://localhost/votantes/api/v1/respuestanombreapi'
    EXTERNAL_API_PUESTO_URL = 'http://localhost/votantes/api/v1/respuestapuestoapi'
    
    # Configuración CORS
    CORS_ORIGINS = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5173",
        "*"  # Permite todos los orígenes (usar con precaución en producción)
    ]
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["*"]

settings = Settings()