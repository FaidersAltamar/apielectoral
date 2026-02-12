# Worker Registraduría - Supabase

Worker que obtiene consultas pendientes de Supabase, consulta lugar de votación en la Registraduría Nacional de Colombia, y envía los resultados de vuelta a Supabase.

## Funcionamiento

El worker funciona en un bucle continuo:

1. **Obtener consultas**: Llama a la Edge Function `consultas-pendientes` de Supabase para obtener cédulas pendientes de procesar.
2. **Consultar Registraduría**: Para cada cédula, consulta la API directa de Infovotantes (usa reCAPTCHA resuelto por 2Captcha). Si obtiene `status_code 13` (no en censo), devuelve inmediatamente sin probar otros códigos de elección.
3. **Fallback opcional**: Si la API devuelve `not_found` sin `no_censo`, puede intentar el scraper (configurable con `ENABLE_SCRAPER_FALLBACK`).
4. **Enviar resultados**: Envía los datos a la Edge Function `recibir-datos` de Supabase.

### Flujo

```
Supabase (cola) → Worker → Registraduría (API/scraper) → Supabase (resultados)
```

### Datos que envía a Supabase

- `municipio_votacion`, `departamento_votacion`, `puesto_votacion`, `direccion_puesto`, `mesa`, `zona_votacion`

Si la cédula no está en censo: todos los campos se envían como `NO CENSO` con `exito: true`.

---

## Despliegue en Easypanel

### Opción 1: App Service (recomendado)

1. **Crear App** → Source: GitHub / Git → conectar repositorio
2. Easypanel detecta el `Dockerfile` y construye la imagen
3. En **Environment**, añadir las variables (ningún archivo `.env` en el contenedor):

| Variable | Requerida | Descripción |
|---------|-----------|-------------|
| `TWOCAPTCHA_API_KEY` | ✅ | API key de 2Captcha |
| `CONSULTA_API_TOKEN` | ✅ | Token Bearer para Edge Functions de Supabase |
| `SUPABASE_FUNCTIONS_URL` | ❌ | URL base (default: `.../functions/v1`) |
| `ELECTION_CODES` | ❌ | `congreso` (default) o `congreso,presidencial,alcaldes` |
| `ENABLE_SCRAPER_FALLBACK` | ❌ | `true` o `false` (default: `true`) |

4. **Deploy settings** → Replicas: 1 (o más para varios workers en paralelo)
5. No configurar Dominio/Proxy ni puertos (es un worker, no una web)

### Opción 2: Compose Service

Usar el `docker-compose.yml` del proyecto. Configurar las variables en Environment de Easypanel.

### Notas

- El worker no expone puertos; se ejecuta en background
- Logs visibles en la pestaña **Logs** de Easypanel
- Si faltan credenciales, el worker sale con `exit 1` al iniciar

---

## Ejecución local

```bash
pip install -r requirements.txt
cp .env.example .env
# Editar .env con TWOCAPTCHA_API_KEY, CONSULTA_API_TOKEN, SUPABASE_FUNCTIONS_URL
python worker_registraduria.py
```

---

## Estructura del proyecto y rol de cada archivo

| Archivo | Rol |
|---------|-----|
| `worker_registraduria.py` | Punto de entrada. Bucle principal: obtiene consultas, procesa en paralelo (2 workers), envía resultados. Warmup del pool de tokens al iniciar. |
| `config.py` | Carga variables de entorno y expone la configuración (`settings`). |
| `services/registraduria_supabase.py` | Lógica de consulta a Registraduría: API directa Infovotantes, pool de tokens reCAPTCHA, fallback a scraper. Funciones `obtener_consultas_pendientes` y `enviar_resultado` para Supabase. |
| `scrapper/registraduria_scraper_optimizado.py` | Scraper de respaldo cuando la API devuelve `not_found` sin `no_censo`. Usa requests + BeautifulSoup, no requiere Selenium. |
| `utils/captcha_solver.py` | Clase `TwoCaptchaSolver` para resolver reCAPTCHA con 2Captcha (usada por el scraper). |
| `requirements.txt` | Dependencias Python: python-dotenv, 2captcha-python, requests, beautifulsoup4, lxml. |
| `Dockerfile` | Imagen base para ejecutar el worker en Easypanel/Docker. |
| `.dockerignore` | Excluye archivos innecesarios al construir la imagen. |
| `.env.example` | Plantilla de variables de entorno. |
