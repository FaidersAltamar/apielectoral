import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # 2Captcha: preferir TWOCAPTCHA_API_KEY, fallback a APIKEY_2CAPTCHA
    API_KEY_2CAPTCHA = os.getenv('TWOCAPTCHA_API_KEY') or os.getenv('APIKEY_2CAPTCHA')
    # Token para Supabase/Lovable Cloud (consultas pendientes)
    CONSULTA_API_TOKEN = os.getenv('CONSULTA_API_TOKEN', '')
    # URL de Supabase Edge Functions (opcional)
    SUPABASE_FUNCTIONS_URL = os.getenv(
        'SUPABASE_FUNCTIONS_URL',
        'https://lsdnopjulddzkkboarsp.supabase.co/functions/v1'
    )
    # Solo congreso: status_code 13 es igual en todas las elecciones, evita 2 tokens extra
    ELECTION_CODES_TO_TRY = os.getenv('ELECTION_CODES', 'congreso').split(',')
    ENABLE_SCRAPER_FALLBACK = os.getenv('ENABLE_SCRAPER_FALLBACK', 'true').lower() in ('true', '1', 'yes')

settings = Settings()