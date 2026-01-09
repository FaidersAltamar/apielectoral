import time
import json
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime


class ProcuraduriaScraperAuto:
    """Scraper automatizado para consultas de antecedentes en la Procuraduría usando BeautifulSoup"""
    
    def __init__(self, api_key=None, headless=None, extension_path=None):
        """
        Inicializa el scraper de Procuraduría con requests y BeautifulSoup
        
        Args:
            api_key: Parámetro ignorado (mantenido por compatibilidad con API)
            headless: Parámetro ignorado (mantenido por compatibilidad)
            extension_path: Parámetro ignorado (mantenido por compatibilidad)
        """
        self.session = requests.Session()
        self.base_url = "https://apps.procuraduria.gov.co/webcert/inicio.aspx"
        
        # Configurar headers para simular un navegador real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        print("✅ Scraper inicializado con requests y BeautifulSoup")
    
    def get_page_content(self):
        """Obtiene el contenido HTML de la página inicial"""
        try:
            print(f"🌐 Obteniendo página: {self.base_url}")
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
        """Extrae todos los campos hidden y viewstate del formulario ASP.NET

        Además devuelve la URL del atributo `action` del formulario (resuelta a absoluta)
        bajo la clave interna `_form_action` para usarla al enviar el POST.
        """
        try:
            form_data = {}

            # Buscar todos los inputs hidden (crítico para ASP.NET)
            hidden_inputs = soup.find_all('input', type='hidden')
            for hidden in hidden_inputs:
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name:
                    form_data[name] = value

            # Resolver el action del formulario (si existe)
            form_tag = soup.find('form')
            action_url = None
            if form_tag and form_tag.get('action'):
                try:
                    from urllib.parse import urljoin
                    action = form_tag.get('action')
                    action_url = urljoin(self.base_url, action)
                    form_data['_form_action'] = action_url
                except Exception:
                    # Si falla resolución, no es crítico; se usará base_url
                    form_data['_form_action'] = self.base_url

            print(f"✅ Extraídos {len(form_data)} campos del formulario")
            if action_url:
                print(f"🔗 URL del action del formulario: {action_url}")
            return form_data
        except Exception as e:
            print(f"❌ Error al extraer datos del formulario: {e}")
            return {}
    
    def get_captcha_question(self, soup):
        """Extrae la pregunta del captcha desde el HTML"""
        try:
            # Buscar el label con id 'lblPregunta'
            pregunta_element = soup.find('span', id='lblPregunta')
            if pregunta_element:
                pregunta_text = pregunta_element.get_text(strip=True)
                print(f"❓ Pregunta captcha: {pregunta_text}")
                return pregunta_text
            
            print("⚠️ No se encontró la pregunta del captcha")
            print(f"🔍 Buscando elementos 'span' en la página...")
            all_spans = soup.find_all('span', limit=10)
            for i, span in enumerate(all_spans):
                print(f"   Span {i}: id='{span.get('id')}', text='{span.get_text(strip=True)[:50]}'")
            return None
        except Exception as e:
            print(f"❌ Error al extraer pregunta del captcha: {e}")
            return None
    
    def refresh_captcha_question(self, form_data):
        """Refresca la pregunta del captcha haciendo clic en el botón de refresh"""
        try:
            print("🔄 Refrescando pregunta del captcha...")
            
            # Preparar datos para el postback de ASP.NET
            post_data = form_data.copy()
            
            # Simular el clic en el botón ImageButton1 (refresh)
            post_data['__EVENTTARGET'] = 'ImageButton1'
            post_data['__EVENTARGUMENT'] = ''
            
            # Actualizar headers para el POST
            headers = self.session.headers.copy()
            headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://apps.procuraduria.gov.co',
                'Referer': self.base_url
            })
            
            # Enviar request
            response = self.session.post(
                self.base_url,
                data=post_data,
                headers=headers,
                timeout=15
            )
            
            response.raise_for_status()
            print("✅ Pregunta refrescada")
            return response.text
            
        except requests.RequestException as e:
            print(f"❌ Error al refrescar pregunta: {e}")
            return None
    
    def _resolver_pregunta_captcha(self, pregunta, nuip):
        """
        Resuelve la pregunta del captcha basándose en un diccionario de respuestas conocidas
        
        Args:
            pregunta (str): Texto de la pregunta
            nuip (str): Número de identificación para preguntas que lo requieren
        
        Returns:
            str: Respuesta a la pregunta o None si no se conoce
        """
        # Diccionario de preguntas y respuestas conocidas
        respuestas_conocidas = {
            "¿ Cual es la Capital de Colombia (sin tilde)?": "Bogota",
            "¿Cual es la Capital de Colombia (sin tilde)?": "Bogota",
            "Capital de Colombia": "Bogota",
            "capital de colombia": "Bogota",
            "¿ Cual es la Capital de Antioquia (sin tilde)?": "Medellin",
            "¿ Cual es la Capital del Atlantico?": "Barranquilla",
            "¿ Cuanto es 6 + 2 ?": "8",  
            "¿ Cuanto es 2 X 3 ?": "6",
            "¿ Cuanto es 3 X 3 ?": "9",
            "¿ Cuanto es 9 - 2 ?": "7",
            "¿ Cuanto es 3 + 2 ?": "5",
            "¿ Cuanto es 9 - 6 ?": "3",
            "¿ Cuanto es 6 - 2 ?": "4",
            "¿ Cuanto es 5 + 3 ?": "8",
            "¿ Cuanto es 5 - 2 ?": "3",
            "¿ Cuanto es 4 X 2 ?": "8",
            "¿ Cuanto es 4 + 3 ?": "7",
            "¿ Cual es la Capital de Antioquia (sin tilde)? ":"Medellin",
            "¿ Cual es la Capital del Atlantico?":"Barranquilla",
            "¿ Cual es la Capital del Vallle del Cauca?":"Cali",
            "¿Escriba los tres primeros digitos del documento a consultar?": nuip[:3],
            "¿Escriba los dos ultimos digitos del documento a consultar?": nuip[-2:],
        }
        
        # Buscar la respuesta en el diccionario (case-insensitive)
        pregunta_lower = pregunta.lower().strip()
        
        for key, value in respuestas_conocidas.items():
            if key.lower() in pregunta_lower or pregunta_lower in key.lower():
                return value
        
        # Si contiene "capital" y "colombia", devolver Bogota
        if "capital" in pregunta_lower and "colombia" in pregunta_lower:
            return "Bogota"
        
        return None
    
    def submit_form(self, numero_id, respuesta_captcha, form_data):
        """Envía el formulario de consulta con POST request.

        Ahora se usa la URL del atributo `action` del formulario (si existe) para el POST
        y se preservan todos los campos hidden extraídos.
        """
        try:
            print("📤 Enviando formulario de consulta...")

            # Preparar datos del formulario
            post_data = form_data.copy()
            post_data.update({
                'ddlTipoID': '1',  # Cédula de ciudadanía
                'txtNumID': str(numero_id),
                'txtRespuestaPregunta': str(respuesta_captcha),
                'btnConsultar': 'Consultar',
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': ''
            })

            print(f"🔍 Datos del formulario a enviar:")
            print(f"   - Tipo ID: 1")
            print(f"   - Número ID: {numero_id}")
            print(f"   - Respuesta Captcha: {respuesta_captcha}")

            # Determinar la URL destino: usar el action del form si fue extraído
            target_url = post_data.get('_form_action', self.base_url)
            print(f"🔗 Enviando POST a: {target_url}")

            # Actualizar headers para el POST
            headers = self.session.headers.copy()
            headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://apps.procuraduria.gov.co',
                'Referer': target_url
            })

            # Enviar formulario
            print("⏳ Enviando POST request y esperando respuesta del servidor...")
            response = self.session.post(
                target_url,
                data=post_data,
                headers=headers,
                timeout=30  # Aumentado a 30 segundos para dar más tiempo
            )

            response.raise_for_status()
            print("✅ Respuesta recibida del servidor")

            # Esperar 5 segundos adicionales por si acaso
            print("⏳ Esperando 5 segundos adicionales...")
            time.sleep(5)
            print(f"🔍 Status Code: {response.status_code}")
            print(f"🔍 Longitud de respuesta: {len(response.text)} caracteres")
            print(f"\n{'='*80}")
            print("📄 CONTENIDO HTML RECIBIDO DESPUÉS DE PRESIONAR 'Consultar':")
            print(f"{'='*80}")
            print(f"\n🔍 Primeros 1000 caracteres:")
            print(response.text[:1000])
            print(f"\n{'='*80}")
            print(f"🔍 Últimos 1000 caracteres:")
            print(response.text[-1000:])
            print(f"{'='*80}\n")

            return response.text

        except requests.RequestException as e:
            print(f"❌ Error al enviar formulario: {e}")
            return None
    
    def extract_result_data(self, html_content):
        """Extrae los datos del resultado de la consulta (más robusto)."""
        try:
            print("📊 Extrayendo datos del resultado...")
            print(f"🔍 Longitud del HTML recibido: {len(html_content)} caracteres")

            soup = BeautifulSoup(html_content, 'html.parser')

            # Buscar el div con clase 'datosConsultado'
            datos_element = soup.find('div', class_='datosConsultado')

            if not datos_element:
                print("⚠️ No se encontró el elemento 'datosConsultado'")
                print(f"🔍 Primeros 500 caracteres del HTML:")
                print(html_content[:500])
                print(f"\n🔍 Últimos 500 caracteres del HTML:")
                print(html_content[-500:])
                print(f"\n🔍 Buscando divs con clase...")
                all_divs = soup.find_all('div', class_=True, limit=10)
                for i, div in enumerate(all_divs):
                    print(f"   Div {i}: class='{div.get('class')}', text='{div.get_text(strip=True)[:50]}'")
                return None

            # Extraer el texto completo (con separadores para facilitar separación en líneas)
            texto_completo = datos_element.get_text(separator="\n", strip=True)
            print(f"📄 Texto completo capturado ({len(texto_completo)} caracteres):")
            print(f"   {texto_completo}")
            print(f"\n🔍 HTML del elemento 'datosConsultado':")
            print(f"   {datos_element.prettify()[:500]}")

            # Intentar extraer el nombre de forma progresiva usando varias heurísticas
            nombre_completo = None

            # 1) Intento clásico: spans (primer nombre, segundo nombre, primer apellido, segundo apellido)
            try:
                spans = datos_element.find_all('span')
                print(f"🔍 Encontrados {len(spans)} spans en 'datosConsultado'")
                for i, span in enumerate(spans[:10]):
                    print(f"   Span {i}: '{span.get_text(strip=True)}'")

                if len(spans) >= 4:
                    nombres = [span.get_text(strip=True) for span in spans[:4] if span.get_text(strip=True)]
                    if nombres:
                        nombre_completo = " ".join(nombres)
                        print(f"✅ Nombre extraído (spans): {nombre_completo}")
                else:
                    print(f"⚠️ Se esperaban al menos 4 spans, se encontraron {len(spans)}")
            except Exception as e:
                print(f"⚠️ Error extrayendo nombre por spans: {e}")

            # 2) Buscar etiquetas con la palabra 'Nombre' o 'Nombres'
            if not nombre_completo:
                try:
                    label_elems = datos_element.find_all(text=re.compile(r'nombre', re.I))
                    for text_node in label_elems:
                        parent = text_node.parent
                        # Subir de nivel si el nodo está en una etiqueta pequeña (ej. <strong>) para obtener el texto contiguo
                        container = parent
                        while container and len(container.get_text(strip=True)) <= len(text_node.strip()) and container.parent:
                            container = container.parent
                        if container is None:
                            container = parent
                        parent_text = container.get_text(separator=" ", strip=True)
                        # Buscar patrón 'Nombre: ...' usando regex
                        m = re.search(r'nombre(?:s)?\s*[:\-]*\s*(.+)', parent_text, re.I)
                        if m:
                            candidate = m.group(1).strip()
                            # Limpiar si contiene palabras que indican estado
                            if candidate and not re.search(r'antecedente|registro|consulta', candidate, re.I):
                                # Rechazar casos como 'sin nombre', 'visible', 'señor(a)', etc.
                                if len(candidate.split()) >= 2 and not re.search(r"\b(sin|señor|señora|identificado|visible|no)\b", candidate, re.I):
                                    nombre_completo = candidate
                                    print(f"✅ Nombre extraído (label): {nombre_completo}")
                                    break
                                else:
                                    print(f"⚠️ Candidate descartado por heurística (label): '{candidate}'")
                                    continue
                except Exception as e:
                    print(f"⚠️ Error buscando label 'Nombre': {e}")

            # 3) Buscar en tablas (td siguiente a td que contenga 'Nombre')
            if not nombre_completo:
                try:
                    tds = datos_element.find_all('td')
                    for i in range(len(tds) - 1):
                        key = tds[i].get_text(strip=True).lower()
                        if 'nombre' in key:
                            candidate = tds[i + 1].get_text(separator=' ', strip=True)
                            if candidate:
                                nombre_completo = candidate
                                print(f"✅ Nombre extraído (tabla): {nombre_completo}")
                                break
                except Exception as e:
                    print(f"⚠️ Error buscando en tablas: {e}")

            # 4) Fallback heurístico: buscar el fragmento de texto más largo que parezca un nombre
            if not nombre_completo:
                try:
                    candidates = []
                    for part in datos_element.stripped_strings:
                        s = part.strip()
                        if len(s) > 3 and 'antecedente' not in s.lower():
                            # Must contain at least one space (first + last)
                            if len(s.split()) >= 2:
                                candidates.append(s)
                    # Filtrar frases que parezcan estados
                    candidates = [c for c in candidates if not re.search(r'no registra|registra antecedentes|tiene antecedentes|consulta', c, re.I)]
                    if candidates:
                        # Filtrar candidatos que contienen palabras que no son nombres
                        filtered = [c for c in candidates if not re.search(r"\b(sin|señor|señora|identificado|visible|no|ciudadad|ciudadanía|cédula|cedula|número|numero|documento)\b", c, re.I)]
                        if filtered:
                            nombre_completo = max(filtered, key=lambda x: len(x))
                            print(f"✅ Nombre extraído (heurística): {nombre_completo}")
                        else:
                            print("⚠️ Ningún candidato heurístico válido después del filtrado")
                except Exception as e:
                    print(f"⚠️ Error heurístico extrayendo nombre: {e}")



            # Determinar si tiene antecedentes
            texto_lower = texto_completo.lower()
            if "no registra antecedentes" in texto_lower or "no tiene antecedentes" in texto_lower:
                estado_antecedentes = "sin_antecedentes"
                mensaje = "La persona no registra antecedentes"
            elif "registra antecedentes" in texto_lower or "tiene antecedentes" in texto_lower:
                estado_antecedentes = "con_antecedentes"
                mensaje = "La persona registra antecedentes"
            else:
                estado_antecedentes = "consultado"
                mensaje = "Consulta realizada exitosamente"

            return {
                "tipo": estado_antecedentes,
                "mensaje": mensaje,
                "nombre_completo": nombre_completo,
                "texto_completo": texto_completo
            }

        except Exception as e:
            print(f"❌ Error al extraer datos del resultado: {e}")
            return None
    
    def scrape_nuip(self, numero_id, max_retries=3):
        """
        Consulta los antecedentes en la Procuraduría con reintentos automáticos
        
        Args:           
            numero_id (str): Número de identificación
            max_retries (int): Número máximo de reintentos en caso de error
        
        Returns:
            dict: Resultado de la consulta
        """
        start_time = time.time()
        tipo_id = "1"
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"\n{'='*50}")
                print(f"🔍 Consultando antecedentes para ID: {numero_id} (Intento {attempt}/{max_retries})")
                print(f"{'='*50}")
                
                # 1. Obtener página inicial
                html_content = self.get_page_content()
                if not html_content:
                    raise Exception("Error al obtener la página inicial")
                
                # 2. Parsear página
                soup = self.parse_page(html_content)
                if not soup:
                    raise Exception("Error al parsear la página")
                
                # 3. Extraer datos del formulario (ViewState, etc.)
                form_data = self.extract_form_data(soup)
                
                # 4. Obtener pregunta del captcha
                pregunta_text = self.get_captcha_question(soup)
                if not pregunta_text:
                    raise Exception("No se pudo obtener la pregunta del captcha")
                
                # 5. Intentar resolver la pregunta o cambiarla
                respuesta_captcha = self._resolver_pregunta_captcha(pregunta_text, numero_id)
                max_intentos_pregunta = 10
                intento_pregunta = 0
                
                while not respuesta_captcha and intento_pregunta < max_intentos_pregunta:
                    intento_pregunta += 1
                    print(f"🔄 Pregunta desconocida, cambiando pregunta (intento {intento_pregunta}/{max_intentos_pregunta})...")
                    
                    # Refrescar pregunta
                    new_html = self.refresh_captcha_question(form_data)
                    if not new_html:
                        print("⚠️ No se pudo refrescar la pregunta")
                        break
                    
                    # Parsear nueva página
                    soup = self.parse_page(new_html)
                    if not soup:
                        break
                    
                    # Actualizar form_data con los nuevos valores
                    form_data = self.extract_form_data(soup)
                    
                    # Obtener nueva pregunta
                    pregunta_text = self.get_captcha_question(soup)
                    if not pregunta_text:
                        break
                    
                    # Intentar resolver la nueva pregunta
                    respuesta_captcha = self._resolver_pregunta_captcha(pregunta_text, numero_id)
                
                if not respuesta_captcha:
                    execution_time = time.time() - start_time
                    return {
                        "status": "error",
                        "message": f"No se pudo resolver la pregunta del captcha: {pregunta_text}",
                        "name": "",
                        "tipo_id": tipo_id,
                        "numero_id": numero_id,
                        "pregunta_captcha": pregunta_text,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "execution_time_seconds": execution_time
                    }
                
                print(f"✅ Captcha resuelto: {respuesta_captcha}")
                
                # 6. Enviar formulario
                response_html = self.submit_form(numero_id, respuesta_captcha, form_data)
                if not response_html:
                    raise Exception("Error al enviar formulario")
                
                # 7. Extraer datos del resultado
                result_data = self.extract_result_data(response_html)
                
                if not result_data:
                    raise Exception("No se pudieron extraer los datos del resultado")
                
                execution_time = time.time() - start_time
                
                return {
                    "status": "success",
                    "message": result_data["mensaje"],
                    "tipo_id": tipo_id,
                    "numero_id": numero_id,
                    "name": result_data.get("nombre_completo"),
                    "estado_antecedentes": result_data["tipo"],
                    "pregunta_captcha": pregunta_text,
                    "respuesta_captcha": respuesta_captcha,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "execution_time_seconds": execution_time
                }
                
            except Exception as e:
                last_error = e
                print(f"❌ Error en intento {attempt}: {e}")
                
                # Reintentar si no es el último intento
                if attempt < max_retries:
                    print(f"🔄 Reintentando en 3 segundos...")
                    time.sleep(3)
                    continue
        
        # Si llegamos aquí, todos los intentos fallaron
        execution_time = time.time() - start_time
        return {
            "status": "error",
            "message": f"Error después de {max_retries} intentos: {str(last_error)}",
            "name": "",
            "tipo_id": tipo_id,
            "numero_id": numero_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "execution_time_seconds": execution_time
        }
    
    def scrape_multiple_nuips(self, nuips_list, delay=5):
        """
        Consulta múltiples NUIPs con delay entre consultas
        
        Args:
            nuips_list (list): Lista de números de identificación
            delay (int): Segundos de espera entre consultas
        
        Returns:
            list: Lista de resultados
        """
        results = []
        total = len(nuips_list)
        
        print(f"\n🚀 INICIANDO CONSULTA MASIVA DE {total} NUIPs")
        print(f"Delay entre consultas: {delay} segundos")
        
        for i, nuip in enumerate(nuips_list, 1):
            print(f"\n📋 Procesando {i}/{total}: {nuip}")
            
            result = self.scrape_nuip(nuip)
            results.append(result)
            
            # Delay entre consultas (excepto en la última)
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


def save_procuraduria_results(data, filename=None):
    """
    Guarda los resultados de la consulta en un archivo JSON
    
    Args:
        data: Datos a guardar (dict o list)
        filename: Nombre del archivo (opcional)
    
    Returns:
        str: Ruta del archivo guardado
    """
    # Crear directorio si no existe
    os.makedirs("procuraduria_results", exist_ok=True)
    
    # Generar nombre de archivo si no se proporciona
    if filename is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"procuraduria_results/procuraduria_query_{timestamp}.json"
    elif not filename.startswith("procuraduria_results/"):
        filename = f"procuraduria_results/{filename}"
    
    # Guardar datos
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Resultados guardados en: {filename}")
    return filename





# Ejemplo de uso
if __name__ == "__main__":
    scraper = ProcuraduriaScraperAuto()
    
    try:
        # Ejemplo de consulta con cédula de ciudadanía
        nuip_ejemplo = "1102877148"
        resultado = scraper.scrape_nuip(nuip_ejemplo)
        
        print(f"\n📊 RESULTADO FINAL:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        # Guardar resultado
        save_procuraduria_results(resultado)
        
        # Ejemplo 2: Consultar múltiples NUIPs (descomentar para usar)
        # nuips_lista = ["1102877148", "1234567890", "9876543210"]
        # resultados = scraper.scrape_multiple_nuips(nuips_lista, delay=5)
        # save_procuraduria_results(resultados, "resultados_multiples.json")
        
    except KeyboardInterrupt:
        print("\n⚠️ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        print(f"🔍 Traceback completo: {traceback.format_exc()}")
    finally:
        scraper.close()
