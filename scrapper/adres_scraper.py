import requests
import time
import json
import os
import sys
import re
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Importar el solver de captcha desde utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.captcha_solver import TwoCaptchaSolver


class AdresScraperAuto:
    def __init__(self, captcha_api_key):
        self.captcha_solver = TwoCaptchaSolver(captcha_api_key)
        self.session = requests.Session()
        self.base_url = "https://www.adres.gov.co/consulte-su-eps"

        # Configurar headers para simular un navegador real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        })

        # Verificar balance
        balance_info = self.captcha_solver.get_balance()
        if balance_info.get("success"):
            print(f"💰 2captcha - {balance_info['balance_formatted']} ({balance_info['estimated_requests']} captchas disponibles)")
        else:
            print(f"⚠️ 2captcha - {balance_info.get('message', 'Error al obtener balance')}")

    def get_page_content(self):
        """Obtiene el contenido HTML de la página principal"""
        try:
            print("🌐 Obteniendo página de ADRES...")
            response = self.session.get(self.base_url, timeout=15)
            response.raise_for_status()
            print("✅ Página obtenida correctamente")
            return response.text
        except requests.RequestException as e:
            print(f"❌ Error al obtener la página: {e}")
            return None

    def parse_page(self, html_content):
        """Parsea el contenido HTML con BeautifulSoup"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup
        except Exception as e:
            print(f"❌ Error al parsear HTML: {e}")
            return None

    def extract_form_data(self, soup):
        """Extrae datos necesarios del formulario (hidden inputs) y la acción"""
        try:
            form_data = {}
            form = soup.find('form')
            action = form.get('action') if form else None

            # Buscar todos los inputs hidden para incluirlos en el POST
            hidden_inputs = soup.find_all('input', type='hidden')
            for hidden in hidden_inputs:
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name:
                    form_data[name] = value

            return form_data, action
        except Exception as e:
            print(f"❌ Error al extraer datos del formulario: {e}")
            return {}, None

    def get_recaptcha_site_key(self, soup, html_text=None):
        """Extrae dinámicamente el site key del reCAPTCHA desde el HTML y scripts externos"""
        try:
            # 1) data-sitekey en elementos (div, button, etc.)
            data_site = soup.find(attrs={"data-sitekey": True})
            if data_site:
                site_key = data_site.get('data-sitekey')
                if site_key:
                    print(f"🔍 Site key encontrado en atributo data-sitekey: {site_key}")
                    return site_key

            # 2) Buscar en HTML con varias expresiones regulares comunes
            if not html_text:
                html_text = str(soup)

            patterns = [
                r"data-sitekey\s*=\s*['\"]([A-Za-z0-9_-]{20,})['\"]",
                r"sitekey\s*[:=]\s*['\"]([A-Za-z0-9_-]{20,})['\"]",
                r"grecaptcha\.execute\(\s*['\"]([A-Za-z0-9_-]{20,})['\"]",
                r"grecaptcha\.render\([^,]+,\s*\{[^}]*sitekey\s*:\s*['\"]([A-Za-z0-9_-]{20,})['\"]",
            ]

            for pat in patterns:
                m = re.search(pat, html_text)
                if m:
                    site_key = m.group(1)
                    print(f"🔍 Site key encontrado por regex: {site_key}")
                    return site_key

            # 3) Buscar en scripts inline
            scripts = soup.find_all('script')
            for script in scripts:
                script_text = ''
                try:
                    if script.string:
                        script_text = script.string
                    elif script.contents:
                        script_text = '\n'.join([str(c) for c in script.contents])
                except Exception:
                    continue

                for pat in patterns:
                    m = re.search(pat, script_text)
                    if m:
                        site_key = m.group(1)
                        print(f"🔍 Site key encontrado en script inline: {site_key}")
                        return site_key

            # 4) Buscar en scripts externos (hacer GET a cada src y buscar patrones)
            script_tags = [s for s in soup.find_all('script') if s.get('src')]
            for tag in script_tags:
                src = tag.get('src')
                try:
                    script_url = urljoin(self.base_url, src)
                    print(f"🔎 Obteniendo script externo: {script_url}")
                    r = self.session.get(script_url, timeout=8)
                    if r.ok and r.text:
                        for pat in patterns:
                            m = re.search(pat, r.text)
                            if m:
                                site_key = m.group(1)
                                print(f"🔍 Site key encontrado en script externo {script_url}: {site_key}")
                                return site_key
                except Exception as e:
                    # No detener por errores en scripts externos
                    print(f"⚠️ Error al obtener script externo {src}: {e}")
                    continue

            # Fallback: no encontrado
            print("⚠️ No se pudo extraer el site key dinámicamente")
            # Permitir override vía variable de entorno si el usuario proporciona un sitekey conocido
            env_sitekey = os.getenv('ADRES_SITEKEY')
            if env_sitekey:
                print("ℹ️ Usando sitekey proveniente de la variable de entorno ADRES_SITEKEY")
                return env_sitekey

            return None
        except Exception as e:
            print(f"⚠️ Error al extraer site key: {e}")
            return None

    def solve_recaptcha(self, soup, html_text=None):
        """Resuelve el reCAPTCHA automáticamente usando 2captcha"""
        try:
            site_key = self.get_recaptcha_site_key(soup, html_text=html_text)
            if not site_key:
                print("⚠️ No se encontró site key; no se intentará resolver reCAPTCHA automáticamente.")
                return None

            print(f"🤖 Resolviendo reCAPTCHA automáticamente con 2captcha...")
            print(f"Site key: {site_key}")
            print(f"URL: {self.base_url}")

            captcha_response = self.captcha_solver.solve_recaptcha_v2(site_key, self.base_url, invisible=False)

            print("✅ reCAPTCHA resuelto correctamente")
            return captcha_response

        except Exception as e:
            print(f"❌ Error al resolver reCAPTCHA: {e}")
            import traceback
            print(f"🔍 Traceback completo: {traceback.format_exc()}")
            return None

    def submit_form(self, nuip, captcha_response, form_data, action):
        """Envía el formulario con POST request"""
        try:
            print("📤 Enviando formulario a ADRES...")

            post_data = form_data.copy()
            post_data.update({
                'tipoDoc': 'CC',  # Seleccionamos CC
                'txtNumDoc': str(nuip),
                'btnConsultar': 'Consultar',
            })

            if captcha_response:
                # nombre del campo "g-recaptcha-response"
                post_data['g-recaptcha-response'] = captcha_response

            # Construir URL de acción completa
            if action:
                submit_url = urljoin(self.base_url, action)
            else:
                submit_url = self.base_url

            headers = self.session.headers.copy()
            headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://www.adres.gov.co',
                'Referer': self.base_url
            })

            response = self.session.post(
                submit_url,
                data=post_data,
                headers=headers,
                timeout=20,
                allow_redirects=True
            )

            response.raise_for_status()

            print("✅ Formulario enviado correctamente")
            return response

        except requests.RequestException as e:
            print(f"❌ Error al enviar formulario: {e}")
            return None
        except Exception as e:
            print(f"❌ Error general al enviar formulario: {e}")
            return None

    def extract_data(self, html_content):
        """Extrae los nombres y apellidos del HTML de respuesta"""
        try:
            print("📊 Extrayendo nombres y apellidos de la respuesta...")

            soup = BeautifulSoup(html_content, 'html.parser')
            table = soup.find('table', id='GridViewBasica')

            nombres = None
            apellidos = None

            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).upper()
                        val = cells[1].get_text(strip=True)
                        if 'NOMBRES' in key:
                            nombres = val
                        if 'APELLIDOS' in key:
                            apellidos = val

                if nombres or apellidos:
                    print(f"✅ Nombres: {nombres} | Apellidos: {apellidos}")
                    return {
                        'status': 'success',
                        'timestamp': datetime.now().isoformat(),
                        'NOMBRES': nombres or '',
                        'APELLIDOS': apellidos or ''
                    }

            # Fallback: buscar por regex en HTML
            nombres_search = re.search(r'NOMBRES\s*</td>\s*<td[^>]*>([^<]+)<', html_content, re.IGNORECASE)
            apellidos_search = re.search(r'APELLIDOS\s*</td>\s*<td[^>]*>([^<]+)<', html_content, re.IGNORECASE)
            nombres = nombres_search.group(1).strip() if nombres_search else nombres
            apellidos = apellidos_search.group(1).strip() if apellidos_search else apellidos

            if nombres or apellidos:
                print(f"✅ (fallback) Nombres: {nombres} | Apellidos: {apellidos}")
                return {
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'NOMBRES': nombres or '',
                    'APELLIDOS': apellidos or ''
                }

            print("❌ No se encontraron nombres ni apellidos en la respuesta")
            return {
                'status': 'error',
                'message': 'No se encontraron nombres/apellidos en la respuesta',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ Error al extraer datos: {e}")
            import traceback
            print(f"🔍 Traceback completo: {traceback.format_exc()}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def scrape_nuip(self, nuip):
        """Proceso completo de scraping para un NUIP"""
        print(f"\n{'='*50}")
        print(f"INICIANDO CONSULTA ADRES PARA NUIP: {nuip}")
        print(f"{'='*50}")

        try:
            html_content = self.get_page_content()
            if not html_content:
                return {"status": "error", "message": "Error al obtener la página", "nuip": nuip, "timestamp": datetime.now().isoformat()}

            soup = self.parse_page(html_content)
            if not soup:
                return {"status": "error", "message": "Error al parsear la página", "nuip": nuip, "timestamp": datetime.now().isoformat()}

            form_data, action = self.extract_form_data(soup)

            captcha_response = self.solve_recaptcha(soup, html_text=html_content)
            if not captcha_response:
                print("⚠️ No se obtuvo respuesta de reCAPTCHA; intentar envío sin token (fallback).")

            response = self.submit_form(nuip, captcha_response, form_data, action)
            if not response:
                return {"status": "error", "message": "Error al enviar formulario", "nuip": nuip, "timestamp": datetime.now().isoformat()}

            # Verificar que la URL final sea la página de RespuestaConsulta.aspx con tokenId
            response_url = response.url if hasattr(response, 'url') else None
            print(f"🔍 URL final de la respuesta: {response_url}")

            expected_prefix = 'https://aplicaciones.adres.gov.co/BDUA_Internet/Pages/RespuestaConsulta.aspx'
            if not response_url or not (response_url.startswith(expected_prefix) or ('RespuestaConsulta.aspx' in response_url and 'aplicaciones.adres.gov.co' in response_url and 'tokenId=' in response_url)):
                print(f"⚠️ La respuesta no redireccionó a la URL esperada de RespuestaConsulta.aspx: {response_url}")
                # Intentar localizar en el HTML un enlace o script que apunte a RespuestaConsulta.aspx
                resp_text = response.text if hasattr(response, 'text') else ''

                # 1. Buscar URL absoluta en el cuerpo
                m_full = re.search(r"(https?://[^'\"\s]*RespuestaConsulta\.aspx[^'\"\s]*)", resp_text)
                target_url = None
                if m_full:
                    target_url = m_full.group(1)
                    print(f"🔍 Encontrada URL absoluta hacia RespuestaConsulta.aspx en el HTML: {target_url}")
                else:
                    # 2. Buscar path relativo como 'RespuestaConsulta.aspx?tokenId=...'
                    m_rel = re.search(r"(RespuestaConsulta\.aspx\?[^'\"\s<]+)", resp_text)
                    if m_rel:
                        rel = m_rel.group(1)
                        print(f"🔍 Encontrado path relativo: {rel}")
                        # Construir URL en el host de aplicaciones
                        # Normalmente la página de resultados vive en 'https://aplicaciones.adres.gov.co/BDUA_Internet/Pages/'
                        target_url = urljoin('https://aplicaciones.adres.gov.co/BDUA_Internet/Pages/', rel)
                        print(f"🔍 Construyendo URL completa: {target_url}")

                if target_url:
                    try:
                        print(f"🌐 Solicitando página de resultado en: {target_url}")
                        r2 = self.session.get(target_url, timeout=15, allow_redirects=True)
                        r2.raise_for_status()
                        final_r2_url = r2.url
                        print(f"🔍 URL final tras solicitar target: {final_r2_url}")

                        if final_r2_url.startswith(expected_prefix) or ('RespuestaConsulta.aspx' in final_r2_url and 'aplicaciones.adres.gov.co' in final_r2_url and 'tokenId=' in final_r2_url):
                            # Extraer desde esta página
                            response_html = r2.text
                            result = self.extract_data(response_html)
                            result['nuip'] = nuip
                            print(f"✅ CONSULTA COMPLETADA PARA NUIP: {nuip} (usando target_url)")
                            return result
                        else:
                            print(f"⚠️ La URL encontrada no terminó en la página esperada: {final_r2_url}")
                            return {
                                "status": "error",
                                "message": "Se encontró URL hacia RespuestaConsulta.aspx pero su redirección final no es la esperada",
                                "found_url": target_url,
                                "final_url": final_r2_url,
                                "nuip": nuip,
                                "timestamp": datetime.now().isoformat()
                            }
                    except requests.RequestException as e:
                        print(f"❌ Error al obtener la página de resultado: {e}")
                        return {
                            "status": "error",
                            "message": "Error al obtener la página de resultado en target_url",
                            "found_url": target_url,
                            "error": str(e),
                            "nuip": nuip,
                            "timestamp": datetime.now().isoformat()
                        }

                # Si no se encontró target_url o su procesamiento falló, devolver error con snippet
                print("⚠️ No se encontró URL de RespuestaConsulta.aspx en la respuesta ni se pudo seguirla.")
                body_snippet = resp_text[:2000]
                return {
                    "status": "error",
                    "message": "Respuesta no apuntó a la URL de RespuestaConsulta.aspx y no se localizó un enlace a ella en el HTML",
                    "final_url": response_url,
                    "body_snippet": body_snippet,
                    "nuip": nuip,
                    "timestamp": datetime.now().isoformat()
                }

            # Extraer datos del HTML de la respuesta (caso normal en el que response.url apunta correctamente)
            response_html = response.text
            result = self.extract_data(response_html)

            # Si no se extrajeron datos y no tuvimos token de captcha, probablemente requiera resolver reCAPTCHA en la página
            if result.get('status') == 'error' and not captcha_response:
                print("⚠️ No se encontró información en la respuesta y no se pudo resolver reCAPTCHA automáticamente.")
                return {
                    "status": "error",
                    "message": "No se encontraron datos; es probable que la página requiera reCAPTCHA y no se pudo obtener/usar el sitekey. Intenta en un navegador o revisa manualmente.",
                    "nuip": nuip,
                    "timestamp": datetime.now().isoformat()
                }

            result['nuip'] = nuip

            print(f"✅ CONSULTA COMPLETADA PARA NUIP: {nuip}")
            return result

        except Exception as e:
            print(f"❌ Error general en consulta: {e}")
            import traceback
            print(f"🔍 Traceback completo: {traceback.format_exc()}")
            return {"status": "error", "message": f"Error general: {str(e)}", "nuip": nuip, "timestamp": datetime.now().isoformat()}

    def scrape_multiple_nuips(self, nuips_list, delay=5):
        """Consulta múltiples NUIPs con delay entre consultas"""
        results = []
        total = len(nuips_list)

        print(f"\n🚀 INICIANDO CONSULTA MASIVA DE {total} NUIPs")
        print(f"Delay entre consultas: {delay} segundos")

        for i, nuip in enumerate(nuips_list, 1):
            print(f"\n📋 Procesando {i}/{total}: {nuip}")

            result = self.scrape_nuip(nuip)
            results.append(result)

            if i < total:
                print(f"⏳ Esperando {delay} segundos antes de la siguiente consulta...")
                time.sleep(delay)

        print(f"\n🎉 CONSULTA MASIVA COMPLETADA: {total} NUIPs procesados")
        return results

    def close(self):
        """Cierra la sesión"""
        if self.session:
            self.session.close()
            print("🔒 Sesión cerrada")


# Función para guardar resultados específicos de ADRES
def save_adres_results(data, filename=None):
    """Guarda los resultados en un archivo JSON"""
    if filename is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_dir = "resultados"
        os.makedirs(results_dir, exist_ok=True)
        filename = os.path.join(results_dir, f"consulta_adres_{timestamp}.json")

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 Resultados guardados en: {filename}")
    return filename


# Ejemplo de uso
if __name__ == "__main__":
    API_KEY = os.getenv('APIKEY_2CAPTCHA')
    if not API_KEY:
        print("❌ Error: No se encontró la API key de 2captcha")
        print("Asegúrate de que el archivo .env contenga: APIKEY_2CAPTCHA=tu_api_key")
        sys.exit(1)

    print(f"🔑 API Key cargada: {API_KEY[:10]}...")

    scraper = AdresScraperAuto(API_KEY)

    try:
        nuip_ejemplo = "1102877148"
        resultado = scraper.scrape_nuip(nuip_ejemplo)

        print(f"\n📊 RESULTADO FINAL:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))

        save_adres_results(resultado)

    except KeyboardInterrupt:
        print("\n⚠️ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        print(f"🔍 Traceback completo: {traceback.format_exc()}")
    finally:
        scraper.close()
