import requests
import time
import json
import os
import sys
import re
from bs4 import BeautifulSoup
from datetime import datetime
import webbrowser

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Importar el solver de captcha desde utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.captcha_solver import TwoCaptchaSolver


class PoliciaJudicialScraper:
    """Scraper para https://antecedentes.policia.gov.co:7005/WebJudicial/

    Flujo general:
    1. GET base_url
    2. "aceptar" (si es necesario) y navegar a /antecedentes.xhtml
    3. Completar formulario con cedulaTipo='cc' y cedulaInput=NUIP
    4. Resolver reCAPTCHA con 2captcha
    5. Enviar formulario y extraer resultados de /formAntecedentes.xhtml
    """

    def __init__(self, captcha_api_key):
        self.captcha_solver = TwoCaptchaSolver(captcha_api_key)
        self.session = requests.Session()
        self.base_url = "https://antecedentes.policia.gov.co:7005/WebJudicial/"
        self.antecedentes_path = "antecedentes.xhtml"
        self.result_path = "formAntecedentes.xhtml"

        # Cabeceras para simular un navegador
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        })

        # Verificar balance de 2captcha
        balance_info = self.captcha_solver.get_balance()
        if balance_info.get("success"):
            print(f"💰 2captcha - {balance_info['balance_formatted']} ({balance_info['estimated_requests']} captchas disponibles)")
        else:
            print(f"⚠️ 2captcha - {balance_info.get('message', 'Error al obtener balance')}")

    def get_page(self, path=""):
        """GET a una URL relativa dentro del sitio"""
        url = self.base_url + path
        try:
            print(f"🌐 GET {url}...")
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            print(f"✅ Página obtenida: status={r.status_code}, length={len(r.text)}")
            try:
                preview = r.text[:200].replace('\n', ' ')
                print(f"🔍 Preview (first 200 chars): {preview}")
            except Exception:
                pass

            # Guardar HTML para debug
            try:
                label = f"get_{path.replace('/', '_') or 'root'}"
                self.save_debug_html(r.text, label)
            except Exception:
                print("⚠️ No se pudo guardar HTML de GET para debug")

            return r.text
        except requests.RequestException as e:
            print(f"❌ Error en GET {url}: {e}")
            return None

    def save_debug_html(self, html, label):
        """Guarda HTML en la carpeta debug_pages con un timestamp y devuelve el filename."""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            debug_dir = "debug_pages"
            os.makedirs(debug_dir, exist_ok=True)
            filename = os.path.join(debug_dir, f"{label}_{timestamp}.html")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"💾 HTML guardado para debug: {filename}")
            return filename
        except Exception as e:
            print(f"⚠️ Error guardando HTML de debug: {e}")
            return None

    def open_url_in_browser(self, path=""):
        """Abre la URL construida con base_url + path en el navegador por defecto."""
        url = self.base_url + path
        try:
            print(f"🌐 Abriendo en navegador: {url}")
            webbrowser.open(url)
            return url
        except Exception as e:
            print(f"⚠️ Error abriendo navegador: {e}")
            return None

    def open_latest_debug_html(self, label=None):
        """Abre el último archivo HTML en debug_pages coincidente con label (o el último si label=None)."""
        debug_dir = "debug_pages"
        if not os.path.isdir(debug_dir):
            print("⚠️ No existe la carpeta 'debug_pages' con archivos guardados")
            return None

        import glob
        pattern = f"{label}_*.html" if label else "*.html"
        files = glob.glob(os.path.join(debug_dir, pattern))
        if not files:
            print(f"⚠️ No se encontraron archivos debug con patrón {pattern}")
            return None

        latest = max(files, key=os.path.getmtime)
        try:
            print(f"🌐 Abriendo HTML de debug en navegador: {latest}")
            webbrowser.open("file://" + os.path.abspath(latest))
            return latest
        except Exception as e:
            print(f"⚠️ Error abriendo archivo debug: {e}")
            return None

    def parse(self, html):
        try:
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            print(f"❌ Error al parsear HTML: {e}")
            return None

    def extract_hidden_inputs(self, soup):
        """Extrae inputs hidden; usa `id` como key si `name` no existe."""
        data = {}
        try:
            hidden = soup.find_all('input', type='hidden')
            for h in hidden:
                name = h.get('name')
                value = h.get('value', '')
                if name:
                    data[name] = value
                else:
                    # Si no hay name, usar el id como key (útil para campos como 'recaptcha-token')
                    _id = h.get('id')
                    if _id:
                        data[_id] = value
        except Exception as e:
            print(f"⚠️ Error extrayendo hidden inputs: {e}")

        # Mostrar los hidden inputs (con masking de valores largos como tokens)
        try:
            masked = {}
            for k, v in data.items():
                sv = str(v)
                if len(sv) > 80:
                    masked[k] = sv[:40] + '...' + sv[-10:]
                else:
                    masked[k] = sv
            print(f"🔍 Hidden inputs extraídos (masked): {json.dumps(masked, ensure_ascii=False)}")
        except Exception:
            print("🔍 Hidden inputs extraídos (no se pudo serializar)")

        return data

    def get_recaptcha_site_key(self, soup, html_text=''):
        """Busca el site key del reCAPTCHA en el DOM, scripts (src y inline) o en el HTML completo.
        Si no encuentra nada, intenta volver a solicitar la página un par de veces (por posibles inyecciones dinámicas).
        """
        try:
            # 1) Buscar atributo data-sitekey en cualquier elemento
            recaptcha = soup.find(attrs={'data-sitekey': True})
            if recaptcha and recaptcha.get('data-sitekey'):
                site_key = recaptcha.get('data-sitekey')
                print(f"🔍 Site key encontrado (atributo data-sitekey): {site_key}")
                return site_key

            # 2) Buscar en scripts con src (ej: recaptcha/api.js?render=SITE_KEY)
            scripts = soup.find_all('script')
            for s in scripts:
                src = s.get('src', '')
                if src and 'recaptcha' in src:
                    m = re.search(r"[?&]render=([A-Za-z0-9_-]{20,})", src)
                    if m:
                        print(f"🔍 Site key encontrado en script src: {m.group(1)} (src: {src})")
                        return m.group(1)

            # 3) Buscar en scripts inline (grecaptcha.render, sitekey: '...', etc.)
            for s in scripts:
                script_text = s.get_text() or ''
                # grecaptcha.render(..., { 'sitekey': 'KEY' })
                m = re.search(r"sitekey\s*[:=]\s*['\"]([A-Za-z0-9_-]{20,})['\"]", script_text)
                if m:
                    print(f"🔍 Site key encontrado en script inline (sitekey): {m.group(1)}")
                    return m.group(1)
                m2 = re.search(r"grecaptcha\.render\([\s\S]*?['\"]([A-Za-z0-9_-]{20,})['\"]", script_text)
                if m2:
                    print(f"🔍 Site key encontrado en grecaptcha.render: {m2.group(1)}")
                    return m2.group(1)
                m3 = re.search(r"recaptcha/api\.js\?render=([A-Za-z0-9_-]{20,})", script_text)
                if m3:
                    print(f"🔍 Site key encontrado en inline (recaptcha/api.js render): {m3.group(1)}")
                    return m3.group(1)

            # 4) Buscar en el HTML completo por patrones genéricos
            m = re.search(r"[?&]render=([A-Za-z0-9_-]{20,})", html_text)
            if m:
                print(f"🔍 Site key encontrado en HTML (render param): {m.group(1)}")
                return m.group(1)
            m = re.search(r"data-sitekey\s*=\s*['\"]([A-Za-z0-9_-]{20,})['\"]", html_text)
            if m:
                print(f"🔍 Site key encontrado en HTML (data-sitekey): {m.group(1)}")
                return m.group(1)

            # 5) Reintentos rápidos solicitando la página de nuevo por si la key se inyecta dinámicamente
            for attempt in range(1, 3):
                print(f"⏱️ Intento {attempt}/2 para reintentar obtener sitekey...")
                time.sleep(1)
                new_html = self.get_page(self.antecedentes_path)
                if not new_html:
                    continue
                new_soup = self.parse(new_html)
                if not new_soup:
                    continue

                # Repetir las búsquedas en el nuevo HTML
                recaptcha = new_soup.find(attrs={'data-sitekey': True})
                if recaptcha and recaptcha.get('data-sitekey'):
                    print(f"🔍 Site key encontrado tras reintento: {recaptcha.get('data-sitekey')}")
                    return recaptcha.get('data-sitekey')

                scripts = new_soup.find_all('script')
                for s in scripts:
                    src = s.get('src', '')
                    if src and 'recaptcha' in src:
                        m = re.search(r"[?&]render=([A-Za-z0-9_-]{20,})", src)
                        if m:
                            print(f"🔍 Site key encontrado tras reintento (script src): {m.group(1)}")
                            return m.group(1)
                    script_text = s.get_text() or ''
                    m = re.search(r"sitekey\s*[:=]\s*['\"]([A-Za-z0-9_-]{20,})['\"]", script_text)
                    if m:
                        print(f"🔍 Site key encontrado tras reintento (inline): {m.group(1)}")
                        return m.group(1)

            print("⚠️ No se encontró sitekey dinámico después de reintentos, devolviendo None")
            return None
        except Exception as e:
            print(f"⚠️ Error al obtener sitekey: {e}")
            return None

    def solve_recaptcha(self, site_key, page_url):
        try:
            if not site_key:
                print("⚠️ No hay site_key para resolver reCAPTCHA")
                return None
            print("🤖 Resolviendo reCAPTCHA con 2captcha...")
            token = self.captcha_solver.solve_recaptcha_v2(site_key, page_url, invisible=False)
            if token:
                t_preview = token[:60] + '...' if len(token) > 60 else token
                print(f"✅ reCAPTCHA resuelto, token (truncated): {t_preview}")
            else:
                print("⚠️ 2captcha devolvió token vacío")
            return token
        except Exception as e:
            print(f"❌ Error al resolver reCAPTCHA: {e}")
            return None

    def go_to_antecedentes(self):
        """Navega desde la página principal hasta /antecedentes.xhtml (si es necesario intenta POST 'Acepto')"""
        html = self.get_page("")
        if not html:
            print("⚠️ GET a la URL base falló, intentando acceder directamente a antecedentes.xhtml...")
            antecedentes_html = self.get_page(self.antecedentes_path)
            if antecedentes_html:
                return antecedentes_html
            return None

        soup = self.parse(html)
        if not soup:
            print("⚠️ Error al parsear HTML de la URL base, intentando acceder directamente a antecedentes.xhtml...")
            antecedentes_html = self.get_page(self.antecedentes_path)
            if antecedentes_html:
                return antecedentes_html
            return None

        # Si ya existe enlace o el formulario está accesible, intentar GET directo a antecedentes.xhtml
        antecedentes_html = self.get_page(self.antecedentes_path)
        if antecedentes_html:
            return antecedentes_html

        # Si no, intentar enviar un formulario de aceptación (si el site lo requiere)
        try:
            form_data = self.extract_hidden_inputs(soup)

            # Encontrar input radio 'Acepto' por label
            # Buscar input cuyo id o name contenga 'acepta' y valor '0' o similar
            for inp in soup.find_all('input'):
                _id = inp.get('id', '').lower()
                _name = inp.get('name', '').lower()
                _value = inp.get('value', '')
                if 'acepta' in _id or 'acepta' in _name:
                    # usar el name y darle el valor del primer input asociado
                    if inp.get('name'):
                        form_data[inp.get('name')] = _value or '0'
                        print(f"ℹ️ Estableciendo campo de aceptación: {inp.get('name')}={form_data[inp.get('name')]}")
                        break

            post_url = self.base_url + self.antecedentes_path
            headers = self.session.headers.copy()
            headers.update({'Referer': self.base_url})

            # Mostrar payload de aceptación (mask de tokens largos)
            try:
                masked = {k: (v if len(str(v))<=80 else str(v)[:40] + '...' + str(v)[-10:]) for k, v in form_data.items()}
                print(f"📤 Enviando aceptación hacia {post_url} con payload (masked): {json.dumps(masked, ensure_ascii=False)}")
            except Exception:
                print("📤 Enviando aceptación (payload no serializable)")

            print(f"📤 Enviando aceptación hacia {post_url}...")
            r = self.session.post(post_url, data=form_data, headers=headers, timeout=15)
            r.raise_for_status()
            print(f"✅ Navegación a antecedentes completada: status={r.status_code}, length={len(r.text)}")
            try:
                print(f"🔍 Preview respuesta (first 300 chars): {r.text[:300].replace('\n', ' ')}")
            except Exception:
                pass

            # Guardar HTML de la respuesta de aceptación
            try:
                self.save_debug_html(r.text, 'antecedentes_accept_response')
            except Exception:
                print("⚠️ No se pudo guardar HTML de la respuesta de aceptación")

            return r.text
        except Exception as e:
            print(f"⚠️ No se pudo enviar aceptación automáticamente: {e}")
            return None

    def submit_consulta(self, antecedentes_html, nuip):
        """Rellena el formulario en antecedentes.xhtml y envía la consulta"""
        soup = self.parse(antecedentes_html)
        if not soup:
            return None

        # Esperar unos segundos para que el sitio tenga tiempo de inyectar/actualizar tokens (recaptcha)
        print("⏳ Esperando 2 segundos para permitir detectar reCAPTCHA...")
        time.sleep(2)

        form_data = self.extract_hidden_inputs(soup)

        # Detectar dinámicamente los nombres de campo para 'cedulaTipo' y 'cedulaInput'
        cedula_tipo_elem = soup.find('select', id=re.compile(r'.*cedulaTipo.*', re.I)) or soup.find('select', attrs={'name': re.compile(r'cedulaTipo', re.I)})
        if cedula_tipo_elem:
            cedula_tipo_name = cedula_tipo_elem.get('name') or cedula_tipo_elem.get('id')
        else:
            cedula_tipo_name = 'cedulaTipo'
        form_data[cedula_tipo_name] = 'cc'

        cedula_input_elem = soup.find('input', id=re.compile(r'.*cedulaInput.*', re.I)) or soup.find('input', attrs={'name': re.compile(r'cedulaInput', re.I)})
        if cedula_input_elem:
            cedula_input_name = cedula_input_elem.get('name') or cedula_input_elem.get('id')
        else:
            cedula_input_name = 'cedulaInput'
        form_data[cedula_input_name] = str(nuip)

        print(f"ℹ️ Campos asignados: {cedula_tipo_name}='cc', {cedula_input_name}='{nuip}'")

        # Intentar obtener sitekey para el recaptcha
        site_key = self.get_recaptcha_site_key(soup, antecedentes_html)

        captcha_token = None
        if site_key:
            captcha_token = self.solve_recaptcha(site_key, self.base_url + self.antecedentes_path)
        else:
            # Revisar si la página incluye un token ya resuelto en un input hidden (id='recaptcha-token')
            token_hidden = form_data.get('recaptcha-token') or (soup.find('input', id='recaptcha-token') and soup.find('input', id='recaptcha-token').get('value'))
            if token_hidden:
                print("🔍 Token de captcha encontrado en input hidden 'recaptcha-token'")
                # Asegurar que esté presente en form_data con su key original
                form_data['recaptcha-token'] = token_hidden
                # Muchos sitios esperan 'g-recaptcha-response' como campo, incluir como fallback
                if 'g-recaptcha-response' not in form_data:
                    form_data['g-recaptcha-response'] = token_hidden
            else:
                print("⚠️ No se detectó sitekey ni token hidden; intentando resolver si existe otro widget")

        if captcha_token:
            # Nombre del campo de respuesta suele ser 'g-recaptcha-response'
            form_data['g-recaptcha-response'] = captcha_token

        # Algunos formularios JSF usan parámetros específicos para invocar el botón (ajax)
        # Buscamos botón por texto o por id conocido (j_idt17), y añadimos su name al payload si existe
        try:
            consult_button = (soup.find('button', text=re.compile(r'Consultar', re.I))
                              or soup.find('button', id=re.compile(r'j_idt17', re.I))
                              or soup.find('button', attrs={'name': re.compile(r'j_idt17', re.I)}))
            if consult_button:
                btn_name = consult_button.get('name') or consult_button.get('id')
                btn_value = consult_button.get('value', '')
                if btn_name:
                    form_data[btn_name] = btn_value
                    print(f"ℹ️ Agregado parámetro del botón: {btn_name} (value: '{btn_value}')")
        except Exception:
            pass

        post_url = self.base_url + self.antecedentes_path
        headers = self.session.headers.copy()
        headers.update({'Referer': self.base_url + self.antecedentes_path, 'Content-Type': 'application/x-www-form-urlencoded'})

        try:
            # Mostrar site_key / token info
            print(f"🔍 site_key detectado: {site_key}")
            if captcha_token:
                print("🔑 Usando token resuelto por 2captcha (se añadirá a 'g-recaptcha-response')")
            elif form_data.get('recaptcha-token'):
                print("🔑 Usando token presente en 'recaptcha-token' (hidden input)")

            # Mostrar payload (mask tokens largos)
            try:
                safe = {}
                for k, v in form_data.items():
                    sv = str(v)
                    if k in ('g-recaptcha-response', 'recaptcha-token') and len(sv) > 80:
                        safe[k] = sv[:40] + '...' + sv[-10:]
                    else:
                        safe[k] = sv
                print(f"📤 Payload a enviar (masked): {json.dumps(safe, ensure_ascii=False)}")
            except Exception:
                print("📤 Payload a enviar (no serializable)")

            # Mostrar headers resumidos
            try:
                hsummary = {k: headers.get(k) for k in ['Referer', 'Content-Type', 'User-Agent']}
                print(f"📤 Headers: {json.dumps(hsummary, ensure_ascii=False)}")
            except Exception:
                pass

            print(f"📤 Enviando consulta para NUIP {nuip}...")
            r = self.session.post(post_url, data=form_data, headers=headers, timeout=20)
            r.raise_for_status()
            print(f"✅ Consulta enviada, status={r.status_code}, length={len(r.text)}")
            try:
                print(f"🔍 Preview respuesta (first 500 chars): {r.text[:500].replace('\n', ' ')}")
            except Exception:
                pass

            # Guardar HTML de la respuesta de la consulta
            try:
                self.save_debug_html(r.text, f"consulta_response_{nuip}")
            except Exception:
                print("⚠️ No se pudo guardar HTML de la respuesta de la consulta")

            # Si la respuesta fue redirección o incluye el HTML final, devolverlo
            return r.text
        except requests.RequestException as e:
            print(f"❌ Error al enviar la consulta: {e}")
            return None

    def extract_result(self, html):
        """Extrae nombres/apellidos del HTML resultante"""
        try:
            # Intentar parsear la sección 'form:mensajeCiudadano'
            soup = self.parse(html)
            if not soup:
                return {'status': 'error', 'message': 'Error al parsear HTML de resultado'}

            mensaje = soup.find(id=re.compile(r'.*mensajeCiudadano.*'))
            if mensaje:
                try:
                    preview = mensaje.get_text(separator=' ', strip=True)[:300].replace('\n', ' ')
                    print(f"🔍 mensajeCiudadano (preview): {preview}")
                except Exception:
                    pass
                text = mensaje.get_text(separator=' ', strip=True)
                # Buscar 'Cédula de Ciudadanía Nº <b>1102877148</b>' y 'Apellidos y Nombres: <b>NAME</b>'
                cedula_match = re.search(r'C[eé]dula.*?N[ºo]\s*([0-9]+)', text)
                nombre_match = re.search(r'Apellidos y Nombres:?\s*(.*?)(?:NO TIENE|$)', text, re.I)

                nuip = cedula_match.group(1) if cedula_match else None
                nombres_raw = None
                if nombre_match:
                    # nombre_match puede contener todo hasta la frase siguiente; limpiar con tags <b>
                    # Intentar extraer contenido en <b> dentro del nodo
                    bolds = mensaje.find_all('b')
                    # El segundo <b> suele ser el nombre según ejemplo
                    if len(bolds) >= 2:
                        nombres_raw = bolds[1].get_text(strip=True)
                    else:
                        nombres_raw = nombre_match.group(1).strip()

                nombres = nombres_raw if nombres_raw else ''

                result = {
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'NUIP': nuip,
                    'NOMBRES': nombres
                }
                print(f"✅ Resultado extraído: {result}")
                return result

            # Fallback: buscar por texto fuerte dentro del body
            text_all = soup.get_text(separator=' ', strip=True)
            m = re.search(r'Apellidos y Nombres[:\s]*([A-Z\s]+)', text_all)
            if m:
                return {'status': 'success', 'NOMBRES': m.group(1).strip(), 'timestamp': datetime.now().isoformat()}

            print("❌ No se encontró la sección de resultado en el HTML")
            return {'status': 'error', 'message': 'No se encontró resultado', 'timestamp': datetime.now().isoformat()}

        except Exception as e:
            print(f"❌ Error extrayendo resultado: {e}")
            import traceback
            print(traceback.format_exc())
            return {'status': 'error', 'message': str(e), 'timestamp': datetime.now().isoformat()}

    def scrape_nuip(self, nuip):
        """Flujo completo para un NUIP"""
        print(f"\n{'='*50}")
        print(f"INICIANDO CONSULTA POLICÍA - NUIP: {nuip}")
        print(f"{'='*50}\n")

        try:
            antecedentes_html = self.go_to_antecedentes()
            if not antecedentes_html:
                return {'status': 'error', 'message': 'No se pudo acceder a antecedentes.xhtml', 'nuip': nuip}

            # Enviar consulta
            response_html = self.submit_consulta(antecedentes_html, nuip)
            if not response_html:
                return {'status': 'error', 'message': 'Error al enviar la consulta', 'nuip': nuip}

            # Extraer resultado
            result = self.extract_result(response_html)
            result['nuip'] = nuip

            print(f"✅ CONSULTA COMPLETADA para {nuip}")
            return result
        except Exception as e:
            print(f"❌ Error general en consulta: {e}")
            return {'status': 'error', 'message': str(e), 'nuip': nuip}

    def scrape_multiple(self, nuips, delay=5):
        results = []
        total = len(nuips)
        print(f"\n🚀 INICIANDO CONSULTA MASIVA DE {total} NUIPs")
        for i, n in enumerate(nuips, 1):
            print(f"\n📋 Procesando {i}/{total}: {n}")
            res = self.scrape_nuip(n)
            results.append(res)
            if i < total:
                print(f"⏳ Esperando {delay}s...")
                time.sleep(delay)
        print(f"\n🎉 CONSULTA MASIVA COMPLETADA")
        return results

    def close(self):
        if self.session:
            self.session.close()
            print("🔒 Sesión cerrada")


# Guardar resultados
def save_policia_results(data, filename=None):
    if filename is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_dir = "resultados"
        os.makedirs(results_dir, exist_ok=True)
        filename = os.path.join(results_dir, f"consulta_policia_{timestamp}.json")

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"💾 Resultados guardados en: {filename}")
    return filename


# Ejemplo de uso
if __name__ == '__main__':
    API_KEY = os.getenv('APIKEY_2CAPTCHA')
    if not API_KEY:
        print("❌ No se encontró APIKEY_2CAPTCHA en variables de entorno")
        sys.exit(1)

    scraper = PoliciaJudicialScraper(API_KEY)
    try:
        nuip = '1102877148'
        res = scraper.scrape_nuip(nuip)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        save_policia_results(res)
    except KeyboardInterrupt:
        print("⚠️ Interrumpido por usuario")
    finally:
        scraper.close()
