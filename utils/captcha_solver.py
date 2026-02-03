# Import the official 2captcha library
from twocaptcha import TwoCaptcha


class TwoCaptchaSolver:
    """Clase para resolver captchas usando el servicio 2captcha"""
    
    def __init__(self, api_key):
        """
        Inicializa el solver de 2captcha
        
        Args:
            api_key (str): API key de 2captcha
        """
        self.api_key = api_key
        # Configurar solver con polling muy agresivo para respuestas ultra rápidas
        self.solver = TwoCaptcha(
            api_key,
            pollingInterval=2,  # Verificar cada 2 segundos para respuestas más rápidas
            defaultTimeout=60   # Timeout de 60 segundos optimizado
        )
    
    def get_balance(self):
        """
        Obtiene el balance de la cuenta
        
        Returns:
            dict: Balance y estimado de peticiones, o mensaje de error
        """
        try:
            balance = self.solver.balance()
            balance_float = float(balance)
            
            # Costo aproximado por reCAPTCHA v2: $0.002 - $0.003 USD
            # Usamos $0.0025 como promedio
            cost_per_captcha = 0.0025
            estimated_requests = int(balance_float / cost_per_captcha)
            
            # Tasa de cambio aproximada USD a COP (actualizar según necesidad)
            usd_to_cop = 4100  # 1 USD = 4100 COP (aproximado)
            balance_cop = balance_float * usd_to_cop
            cost_per_captcha_cop = cost_per_captcha * usd_to_cop
            
            return {
                "success": True,
                "balance_usd": balance_float,
                "balance_cop": round(balance_cop, 2),
                "balance_formatted": f"${balance_float:.4f} USD",
                "balance_formatted_cop": f"${balance_cop:,.2f} COP",
                "cost_per_captcha_usd": cost_per_captcha,
                "cost_per_captcha_cop": round(cost_per_captcha_cop, 2),
                "estimated_requests": estimated_requests,
                "message": f"Puedes resolver aproximadamente {estimated_requests} captchas"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error al obtener balance: {e}"
            }
    
    def solve_recaptcha_v2(self, site_key, page_url, invisible=False):
        """
        Resuelve reCAPTCHA v2 usando la librería oficial de 2captcha
        
        Args:
            site_key (str): Site key del reCAPTCHA
            page_url (str): URL de la página donde está el reCAPTCHA
            invisible (bool): True para invisible reCAPTCHA, False para normal
        
        Returns:
            str: Token de respuesta del reCAPTCHA
        
        Raises:
            Exception: Si hay un error al resolver el reCAPTCHA
        """
        print("Enviando reCAPTCHA a 2captcha para resolver...")
        print(f"🔍 Debugging - Site key: {site_key}")
        print(f"🔍 Debugging - URL: {page_url}")
        print(f"🔍 Debugging - Invisible: {invisible}")
        
        try:
            # Resolver reCAPTCHA usando la librería oficial con configuración ultra optimizada
            result = self.solver.recaptcha(
                sitekey=site_key,
                url=page_url,
                invisible=1 if invisible else 0,
                pollingInterval=1  # Polling cada 1 segundo para máxima velocidad
            )
            
            print("✅ reCAPTCHA resuelto exitosamente!")
            print(f"🔍 Token recibido (primeros 50 chars): {result['code'][:50]}...")
            return result['code']
        
        except Exception as e:
            print(f"🔍 Debugging - Error completo: {str(e)}")
            print(f"🔍 Debugging - Tipo de error: {type(e)}")
            raise Exception(f"Error al resolver reCAPTCHA: {e}")
