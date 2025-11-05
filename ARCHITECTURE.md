# 🏗️ Arquitectura del Sistema - API Electoral

## Índice
1. [Visión General](#visión-general)
2. [Arquitectura de Alto Nivel](#arquitectura-de-alto-nivel)
3. [Componentes del Sistema](#componentes-del-sistema)
4. [Scrapers](#scrapers)
5. [Sistema de Tareas Asíncronas](#sistema-de-tareas-asíncronas)
6. [Endpoints de la API](#endpoints-de-la-api)
7. [Flujos de Datos](#flujos-de-datos)
8. [Persistencia](#persistencia)
9. [Patrones de Diseño](#patrones-de-diseño)
10. [Seguridad](#seguridad)
11. [Mejoras Futuras](#mejoras-futuras)

---

## Visión General

**API Electoral** es un sistema de web scraping que permite consultar información de ciudadanos colombianos desde múltiples fuentes gubernamentales:

- **Registraduría Nacional**: Puesto de votación
- **Procuraduría General**: Antecedentes y nombres
- **Policía Nacional**: Nombres por NUIP y fecha de expedición
- **SISBEN**: Nombres por NUIP

### Características Principales
- ✅ Consultas individuales y masivas (hasta 50 NUIPs)
- ✅ Procesamiento asíncrono con seguimiento en tiempo real
- ✅ Persistencia de tareas en JSON
- ✅ Resolución automática de CAPTCHAs (2captcha)
- ✅ Bypass de detección anti-bot (undetected-chromedriver)
- ✅ Endpoint combinado con lógica de prioridad

### Stack Tecnológico
- **Framework**: FastAPI
- **Web Scraping**: Selenium, undetected-chromedriver
- **CAPTCHA**: 2captcha-python
- **Validación**: Pydantic
- **Persistencia**: JSON
- **Async**: asyncio

---

## Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTE HTTP                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI SERVER                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API ENDPOINTS                         │  │
│  │  • /balance                                              │  │
│  │  • /consultar-nombres-v1 (Procuraduría)                 │  │
│  │  • /consultar-nombres-v2 (Policía)                      │  │
│  │  • /consultar-nombres-v3 (SISBEN)                       │  │
│  │  • /consultar-puesto-votacion (Registraduría)           │  │
│  │  • /consultar-combinado (Optimizado)                    │  │
│  │  • /consultar-nombres-v3/bulk (Masivo)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  TASK MANAGER                            │  │
│  │  • Gestión de tareas asíncronas                          │  │
│  │  • Persistencia en JSON                                  │  │
│  │  • Seguimiento de progreso                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────┬────────────┬────────────┬────────────┬─────────────┘
             │            │            │            │
             ▼            ▼            ▼            ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
    │Registraduría│ │Procuraduría│ │  Policía   │ │  SISBEN    │
    │  Scraper   │ │  Scraper   │ │  Scraper   │ │  Scraper   │
    └────────────┘ └────────────┘ └────────────┘ └────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
    │ Selenium   │ │ Undetected │ │ Selenium   │ │ Undetected │
    │  Chrome    │ │  Chrome    │ │  Chrome    │ │  Chrome    │
    └────────────┘ └────────────┘ └────────────┘ └────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    ┌────────────────────────────────────────────────────────┐
    │              SITIOS WEB GUBERNAMENTALES               │
    │  • registraduria.gov.co                               │
    │  • procuraduria.gov.co                                │
    │  • policia.gov.co                                     │
    │  • sisben.gov.co                                      │
    └────────────────────────────────────────────────────────┘
```

---

## Componentes del Sistema

### 1. API Layer (`api.py`)
**Responsabilidad**: Exponer endpoints REST y coordinar operaciones

**Funciones principales**:
- Validación de requests
- Orquestación de scrapers
- Gestión de tareas asíncronas
- Manejo de errores y respuestas

**Tecnologías**:
- FastAPI
- Pydantic (validación)
- asyncio (operaciones asíncronas)

### 2. Models (`models/request.py`)
**Responsabilidad**: Definir esquemas de datos

```python
class PeticionRequest(BaseModel):
    nuip: str
    fecha_expedicion: Optional[str]  # Formato: dd/mm/yyyy

class BulkSisbenRequest(BaseModel):
    nuips: List[str]  # 1-50 NUIPs
```

### 3. Task Manager (`task_manager.py`)
**Responsabilidad**: Gestionar tareas asíncronas con persistencia

**Características**:
- Almacenamiento dual: memoria + JSON
- Estados: `pending`, `processing`, `completed`, `failed`
- Seguimiento de progreso en tiempo real
- Persistencia automática

**Estructura de directorio**:
```
tasks/
├── {task_id_1}.json
├── {task_id_2}.json
└── {task_id_3}.json
```

### 4. Scrapers (`scrapper/`)

#### a) `registraduria_scraper.py`
- **Fuente**: Registraduría Nacional
- **Datos**: Puesto de votación
- **Tecnología**: Selenium + 2captcha
- **CAPTCHA**: reCAPTCHA v2

#### b) `procuraduria_scraper.py`
- **Fuente**: Procuraduría General
- **Datos**: Nombres completos, antecedentes
- **Tecnología**: undetected-chromedriver
- **CAPTCHA**: Preguntas matemáticas/geográficas

#### c) `police_scraper.py`
- **Fuente**: Policía Nacional
- **Datos**: Nombres completos
- **Requisitos**: NUIP + fecha de expedición
- **Tecnología**: Selenium

#### d) `sisben_scraper.py`
- **Fuente**: SISBEN
- **Datos**: Nombres completos
- **Tecnología**: undetected-chromedriver
- **Reintentos**: Hasta 3 intentos automáticos

### 5. Utils (`utils/`)

#### `captcha_solver.py`
```python
class TwoCaptchaSolver:
    - solve_recaptcha_v2()
    - get_balance()
```

#### `time_utils.py`
```python
- format_execution_time()
- calculate_response_time()
- get_current_timestamp()
```

### 6. Configuration (`config.py`)
```python
class Settings:
    API_KEY_2CAPTCHA: str
    MAX_NUIPS_SYNC: int = 50
    DEFAULT_DELAY: int = 5
    HEADLESS_MODE: bool = True
```

### 7. Cleanup Tasks (`cleanup_tasks.py`)
**Responsabilidad**: Gestión y limpieza de archivos JSON de tareas

**Comandos**:
```bash
# Listar todas las tareas
python cleanup_tasks.py list

# Listar tareas completadas
python cleanup_tasks.py list --status completed

# Limpiar tareas > 7 días (dry-run)
python cleanup_tasks.py clean --days 7

# Ejecutar limpieza
python cleanup_tasks.py clean --status completed --days 30 --execute
```

---

## Scrapers

### Comparación de Scrapers

| Scraper | Fuente | CAPTCHA | Tecnología | Headless | Reintentos |
|---------|--------|---------|------------|----------|------------|
| Registraduría | registraduria.gov.co | reCAPTCHA v2 | Selenium | ✅ | ❌ |
| Procuraduría | procuraduria.gov.co | Preguntas | undetected-chrome | ✅ | ✅ (3x) |
| Policía | policia.gov.co | ❌ | Selenium | ✅ | ❌ |
| SISBEN | sisben.gov.co | ❌ | undetected-chrome | ✅ | ✅ (3x) |

### Flujo de un Scraper

```
┌─────────────────────────────────────────────────────────┐
│                    SCRAPER LIFECYCLE                    │
└─────────────────────────────────────────────────────────┘

1. Inicialización
   ├─ setup_driver()
   │  ├─ Configurar opciones de Chrome
   │  ├─ Bypass anti-detección
   │  └─ Inicializar WebDriver
   │
2. Navegación
   ├─ load_page()
   │  └─ Navegar a URL objetivo
   │
3. Interacción
   ├─ fill_form()
   │  ├─ Llenar campos
   │  └─ Seleccionar opciones
   │
4. Resolución de CAPTCHA (si aplica)
   ├─ solve_captcha()
   │  ├─ Detectar tipo de CAPTCHA
   │  ├─ Resolver (2captcha o lógica local)
   │  └─ Inyectar respuesta
   │
5. Envío
   ├─ submit_form()
   │  └─ Click en botón de consulta
   │
6. Extracción
   ├─ extract_data()
   │  ├─ Esperar resultados
   │  ├─ Parsear HTML
   │  └─ Estructurar datos
   │
7. Limpieza
   └─ close()
      └─ Cerrar navegador
```

### Técnicas Anti-Detección

#### Selenium (Registraduría, Policía)
```python
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
```

#### Undetected-chromedriver (Procuraduría, SISBEN)
```python
driver = uc.Chrome(
    options=options,
    version_main=None,
    use_subprocess=False,
    suppress_welcome=True,
    headless=headless
)
```

---

## Sistema de Tareas Asíncronas

### Arquitectura de Tareas

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │
       │ 1. POST /consultar-nombres-v3/bulk
       │    {"nuips": ["123", "456", "789"]}
       ▼
┌─────────────────────────────────────────┐
│           FastAPI Server                │
│  ┌───────────────────────────────────┐  │
│  │  create_task()                    │  │
│  │  - Genera UUID                    │  │
│  │  - Guarda en memoria + JSON       │  │
│  │  - Lanza background task          │  │
│  └───────────────────────────────────┘  │
└──────┬──────────────────────────────────┘
       │
       │ 2. Retorna task_id
       ▼
┌─────────────┐
│   Cliente   │ ◄─── {"task_id": "550e8400-...", "status": "pending"}
└──────┬──────┘
       │
       │ 3. GET /consultar-nombres-v3/bulk/{task_id}
       │    (polling cada 2-3 segundos)
       ▼
┌─────────────────────────────────────────┐
│           FastAPI Server                │
│  ┌───────────────────────────────────┐  │
│  │  get_task()                       │  │
│  │  - Lee de memoria o JSON          │  │
│  │  - Retorna estado y progreso      │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Procesamiento en Background

```
Background Task: process_bulk_sisben_task()
│
├─ 1. Actualiza status → "processing"
│     └─ Guarda en memoria + JSON
│
├─ 2. Para cada NUIP:
│   │
│   ├─ Crea SisbenScraperAuto(headless=True)
│   ├─ Ejecuta scrape_name_by_nuip(nuip)
│   ├─ Guarda resultado en array
│   ├─ Actualiza progreso
│   │   └─ Guarda en memoria + JSON
│   └─ Cierra scraper
│
├─ 3. Actualiza status → "completed"
│     └─ Guarda en memoria + JSON
│
└─ 4. Guarda todos los resultados en task["data"]
```

### Estructura de Tarea

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2025-10-13T13:45:00.123456",
  "started_at": "2025-10-13T13:45:02.456789",
  "completed_at": "2025-10-13T13:46:30.789012",
  "nuips": ["123", "456", "789"],
  "total_nuips": 3,
  "progress": {
    "total": 3,
    "processed": 3,
    "successful": 2,
    "failed": 1
  },
  "data": [
    {
      "nuip": "123",
      "success": true,
      "name": "JUAN PEREZ GOMEZ",
      "data": {...}
    }
  ],
  "error": null
}
```

---

## Endpoints de la API

### 1. Balance de 2captcha
```http
GET /balance
```

### 2. Consulta Procuraduría (v1)
```http
POST /consultar-nombres-v1
{
  "nuip": "1102877148"
}
```

### 3. Consulta Policía (v2)
```http
POST /consultar-nombres-v2
{
  "nuip": "1102877148",
  "fecha_expedicion": "15/03/1990"
}
```

### 4. Consulta SISBEN (v3)
```http
POST /consultar-nombres-v3
{
  "nuip": "1102877148"
}
```

### 5. Consulta Registraduría
```http
POST /consultar-puesto-votacion
{
  "nuip": "1102877148"
}
```

### 6. Consulta Combinada (Optimizada)
```http
POST /consultar-combinado
{
  "nuip": "1102877148",
  "fecha_expedicion": "15/03/1990"
}
```

**Lógica de prioridad**:
1. Ejecuta **Registraduría** y **SISBEN** en paralelo
2. Si SISBEN encuentra el nombre → **STOP**
3. Si SISBEN no encuentra → Consulta **Procuraduría**
4. Si Procuraduría no encuentra Y hay `fecha_expedicion` → Consulta **Policía**

### 7. Consulta Masiva SISBEN

```http
POST /consultar-nombres-v3/bulk
{
  "nuips": ["123", "456", "789"]
}

GET /consultar-nombres-v3/bulk/{task_id}
GET /consultar-nombres-v3/bulk
DELETE /consultar-nombres-v3/bulk/{task_id}
```

---

## Flujos de Datos

### Flujo de Consulta Individual

```
Cliente → API → Scraper → Sitio Web → Scraper → API → Cliente
   │       │        │          │          │       │       │
   │       │        │          │          │       │       │
   1       2        3          4          5       6       7

1. Cliente envía NUIP
2. API valida y crea scraper
3. Scraper navega y llena formulario
4. Sitio web procesa y retorna HTML
5. Scraper extrae datos
6. API estructura respuesta
7. Cliente recibe datos
```

### Flujo de Consulta Combinada

```
Cliente
  │
  ├─ POST /consultar-combinado
  │
  ▼
API
  │
  ├─ Paralelo ──┬─► Registraduría Scraper
  │             │
  │             └─► SISBEN Scraper
  │                     │
  │                     ├─ ✓ Nombre encontrado → STOP
  │                     │
  │                     └─ ✗ No encontrado
  │                             │
  ├─ Secuencial ───────────────┴─► Procuraduría Scraper
  │                                      │
  │                                      ├─ ✓ Encontrado → STOP
  │                                      │
  │                                      └─ ✗ No encontrado
  │                                              │
  └─ Condicional (si fecha_expedicion) ─────────┴─► Policía Scraper
```

### Flujo de Consulta Masiva

```
Cliente                 API                  Background Task         Scraper
  │                      │                           │                  │
  ├─ POST nuips ────────►│                           │                  │
  │                      ├─ Crea task ──────────────►│                  │
  │◄─ task_id ───────────┤                           │                  │
  │                      │                           ├─ Para cada NUIP  │
  │                      │                           ├─────────────────►│
  │                      │                           │◄─ resultado ─────┤
  │                      │                           ├─ Actualiza       │
  ├─ GET status ────────►│                           │   progreso       │
  │◄─ progress ──────────┤◄─ Lee tasks_storage ─────┤   + JSON         │
  │                      │                           │                  │
  │ (polling...)         │                           │                  │
  │                      │                           ├─ Completa        │
  ├─ GET status ────────►│                           │   todos          │
  │◄─ completed + data ──┤◄─ Lee tasks_storage ─────┤                  │
  │                      │                           │                  │
  ├─ DELETE task ───────►│                           │                  │
  │◄─ success ───────────┤                           │                  │
```

---

## Persistencia

### Almacenamiento Dual

```
┌─────────────────────────────────────────────────────────┐
│                   TASK MANAGER                          │
│                                                         │
│  ┌──────────────────┐      ┌──────────────────┐       │
│  │   MEMORIA (RAM)  │◄────►│   DISCO (JSON)   │       │
│  │                  │      │                  │       │
│  │  tasks_storage   │      │  tasks/*.json    │       │
│  │  (Dict)          │      │                  │       │
│  └──────────────────┘      └──────────────────┘       │
│           │                          │                 │
│           │                          │                 │
│           ▼                          ▼                 │
│    Lectura rápida          Persistencia entre         │
│    Escritura rápida        reinicios del servidor     │
└─────────────────────────────────────────────────────────┘
```

### Operaciones de Persistencia

```python
# Crear tarea
create_task(nuips) 
  ├─ Genera UUID
  ├─ Crea estructura en memoria
  ├─ Guarda en tasks/{task_id}.json
  └─ Retorna task_id

# Obtener tarea
get_task(task_id)
  ├─ Busca en memoria
  ├─ Si no existe → Carga desde JSON
  └─ Retorna task_data

# Actualizar tarea
save_task_to_file(task_id, task_data)
  ├─ Actualiza memoria
  └─ Guarda en JSON

# Eliminar tarea
delete_task(task_id)
  ├─ Elimina de memoria
  └─ Elimina archivo JSON
```

### Ventajas del Sistema Dual

✅ **Rendimiento**: Lectura/escritura rápida en memoria  
✅ **Persistencia**: Datos sobreviven reinicios  
✅ **Recuperación**: Tareas se cargan automáticamente  
✅ **Auditoría**: Archivos JSON legibles  

---

## Patrones de Diseño

### 1. Task Queue Pattern
```
Cliente → Encola tarea → Background worker → Polling de resultados
```

### 2. Repository Pattern
```
API ←→ Task Manager (Repository) ←→ JSON Storage
```

### 3. Factory Pattern
```python
for nuip in nuips:
    scraper = SisbenScraperAuto(headless=True)  # Factory
    result = scraper.scrape_name_by_nuip(nuip)
    scraper.close()  # Cleanup
```

### 4. Strategy Pattern
```python
# Diferentes estrategias de scraping
if source == "registraduria":
    scraper = RegistraduriaScraperAuto()
elif source == "procuraduria":
    scraper = ProcuraduriaScraperAuto()
```

### 5. Observer Pattern (Polling)
```python
# Cliente observa cambios
while task["status"] != "completed":
    task = get_task(task_id)
    time.sleep(2)
```

---

## Seguridad

### Implementado ✅

- **Validación de entrada**: Pydantic schemas
- **Límites de consulta**: Máximo 50 NUIPs
- **UUID aleatorio**: Task IDs no predecibles
- **Manejo de errores**: Try-catch en todos los scrapers
- **Headless mode**: Reduce consumo de recursos

### Recomendado 🔒

- **Autenticación**: JWT o API Keys
- **Rate limiting**: Por IP/usuario
- **CORS**: Configuración restrictiva
- **Logging**: Registro de todas las operaciones
- **Timeout**: Límite de tiempo por tarea
- **Sanitización**: Validación estricta de NUIPs
- **Encriptación**: Datos sensibles en tránsito

---

## Mejoras Futuras

### Corto Plazo
1. ✨ **WebSockets**: Notificaciones en tiempo real
2. ✨ **Rate Limiting**: Prevenir abuso
3. ✨ **Logging**: Sistema de logs estructurado
4. ✨ **Métricas**: Prometheus + Grafana

### Mediano Plazo
5. ✨ **Redis**: Cache y almacenamiento persistente
6. ✨ **PostgreSQL**: Base de datos relacional
7. ✨ **Autenticación**: Sistema de usuarios
8. ✨ **Docker**: Containerización

### Largo Plazo
9. ✨ **Celery**: Procesamiento distribuido
10. ✨ **Kubernetes**: Orquestación de contenedores
11. ✨ **ML**: Detección de patrones y anomalías
12. ✨ **API Gateway**: Kong o AWS API Gateway

---

## Métricas y Monitoreo

### Métricas Disponibles

```python
# Por tarea
- created_at
- started_at
- completed_at
- total_nuips
- processed
- successful
- failed
- execution_time

# Cálculos
total_time = completed_at - started_at
avg_time_per_nuip = total_time / total_nuips
success_rate = (successful / total) * 100
```

### Comandos de Monitoreo

```bash
# Ver estadísticas
python cleanup_tasks.py stats

# Listar tareas activas
python cleanup_tasks.py list --status processing

# Ver tareas completadas
python cleanup_tasks.py list --status completed
```

---

## Consideraciones de Diseño

### ✅ Ventajas
1. **No bloqueante**: Servidor responde inmediatamente
2. **Escalable**: Procesamiento en background
3. **Robusto**: Errores individuales no detienen el proceso
4. **Transparente**: Cliente puede monitorear progreso
5. **Persistente**: Tareas sobreviven reinicios
6. **Simple**: Sin dependencias complejas

### ⚠️ Limitaciones
1. **Memoria**: Limitado por RAM del servidor
2. **Secuencial**: Un NUIP a la vez por tarea
3. **Sin distribución**: Un solo servidor
4. **Sin autenticación**: Acceso abierto
5. **Polling**: Cliente debe consultar activamente

---

## Estructura del Proyecto

```
api_electroral/
├── api.py                      # FastAPI app y endpoints
├── config.py                   # Configuración
├── task_manager.py             # Gestión de tareas
├── cleanup_tasks.py            # Limpieza de tareas
├── requirements.txt            # Dependencias
│
├── models/
│   └── request.py              # Modelos Pydantic
│
├── scrapper/
│   ├── registraduria_scraper.py
│   ├── procuraduria_scraper.py
│   ├── police_scraper.py
│   └── sisben_scraper.py
│
├── utils/
│   ├── __init__.py
│   ├── captcha_solver.py       # 2captcha integration
│   └── time_utils.py           # Utilidades de tiempo
│
└── tasks/                      # Tareas persistidas (JSON)
    ├── {uuid-1}.json
    ├── {uuid-2}.json
    └── {uuid-3}.json
```

---

## Ejecución

### Desarrollo
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
echo "APIKEY_2CAPTCHA=tu_api_key" > .env

# Ejecutar servidor
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Producción
```bash
# Con Gunicorn
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Con Docker (futuro)
docker build -t api-electoral .
docker run -p 8000:8000 api-electoral
```

---

## Documentación Adicional

- **BULK_API_USAGE.md**: Guía de uso de consultas masivas
- **TASK_MANAGER_README.md**: Documentación del gestor de tareas
- **QUICK_REFERENCE.md**: Referencia rápida de endpoints
- **CHANGELOG.md**: Historial de cambios

---

**Última actualización**: 2025-10-13  
**Versión**: 1.0.0  
**Autor**: Eduardo
