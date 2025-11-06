# Configuración de Playwright para Procuraduría

## Instalación

El scraper de Procuraduría ahora usa **Playwright Async API** en lugar de Selenium para mejor rendimiento y menor detección.

### 1. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

### 2. Instalar navegadores de Playwright

Después de instalar el paquete de Python, debes instalar los navegadores:

```bash
# Instalar solo Chromium (recomendado)
playwright install chromium

# O instalar todos los navegadores
playwright install
```

### 3. En Linux (servidor de producción)

Si estás en un servidor Linux, también necesitas instalar las dependencias del sistema:

```bash
# Ubuntu/Debian
playwright install-deps chromium

# O para todos los navegadores
playwright install-deps
```

## Ventajas de Playwright sobre Selenium

- ✅ **Más rápido**: Mejor rendimiento en operaciones de scraping
- ✅ **Menos detectable**: Mejor evasión de sistemas anti-bot
- ✅ **API moderna**: Sintaxis más limpia y simple
- ✅ **Auto-wait**: Espera automática de elementos
- ✅ **Mejor manejo de iframes**: Más robusto con contenido embebido
- ✅ **Async/Await**: Compatible con FastAPI y asyncio

## Uso

El scraper ahora usa **async/await**:

```python
import asyncio
from scrapper.procuraduria_scraper import ProcuraduriaScraperAuto

async def main():
    # Crear scraper (headless=False para ver el navegador)
    scraper = ProcuraduriaScraperAuto(headless=False)
    
    try:
        # Consultar antecedentes (ahora es async)
        resultado = await scraper.scrape_nuip("1234567890")
        print(resultado)
    finally:
        await scraper.close()

# Ejecutar
asyncio.run(main())
```

## Uso en FastAPI

En FastAPI, simplemente usa `await`:

```python
@app.post("/consultar")
async def consultar(nuip: str):
    scraper = ProcuraduriaScraperAuto(headless=False)
    try:
        resultado = await scraper.scrape_nuip(nuip)
        return resultado
    finally:
        await scraper.close()
```

## Iniciar el Servidor

### En Windows (IMPORTANTE)

**NO uses** `uvicorn api:app --reload` directamente. En su lugar, usa el script `run.py`:

```bash
python run.py
```

Este script configura correctamente el `ProactorEventLoop` antes de iniciar uvicorn.

### En Linux

Puedes usar uvicorn normalmente:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

## Solución de Problemas

### Error: NotImplementedError en Windows

Si ves este error:
```
NotImplementedError
raise NotImplementedError
```

**Causa**: Windows requiere `ProactorEventLoop` para que Playwright pueda crear subprocesos.

**Solución**: Usa el script `run.py` en lugar de uvicorn directamente:

```bash
# ❌ NO USAR en Windows
uvicorn api:app --reload

# ✅ USAR en Windows
python run.py
```

## Notas

- Los otros scrapers (Sisben, Policía, Registraduría) siguen usando Selenium
- Solo Procuraduría usa Playwright Async API
- El navegador se muestra por defecto (`headless=False`) solo en Procuraduría
- **IMPORTANTE**: Siempre usa `await` con `scrape_nuip()` y `close()`
- **Windows**: El código ya incluye la configuración necesaria para `ProactorEventLoop`
