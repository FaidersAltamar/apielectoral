# Guía de Despliegue en Render

## Problema: "Binary Location Must be a String"

Este error ocurre cuando Selenium/undetected-chromedriver no puede encontrar el binario de Chrome en producción.

## Solución Implementada

Los scrapers ahora detectan automáticamente la ubicación de Chrome según el sistema operativo y configuran `binary_location` apropiadamente.

## Pasos para Desplegar en Render

### 1. Instalar Chrome/Chromium en Render

Render usa contenedores Linux, necesitas instalar Chrome. Agrega un archivo `render.yaml` o configura en el dashboard:

**Opción A: Usar buildpack de Chrome**

En el dashboard de Render, ve a:
- **Settings** → **Build & Deploy**
- Agrega el siguiente **Build Command**:

```bash
# Instalar dependencias de Chrome
apt-get update && apt-get install -y wget gnupg && \
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
apt-get update && apt-get install -y google-chrome-stable && \
pip install -r requirements.txt
```

**Opción B: Usar Chromium (más ligero)**

```bash
apt-get update && apt-get install -y chromium-browser chromium-chromedriver && \
pip install -r requirements.txt
```

### 2. Variables de Entorno

Asegúrate de configurar en Render:

```
APIKEY_2CAPTCHA=tu_api_key_aqui
EXTERNAL_API_NOMBRE_URL=tu_url_aqui
EXTERNAL_API_PUESTO_URL=tu_url_aqui
```

### 3. Configuración de Headless Mode

En producción, **SIEMPRE** usa `headless=True`:

```python
# En config.py ya está configurado
HEADLESS_MODE = True
```

### 4. Dockerfile (Alternativa Recomendada)

Si prefieres usar Docker, crea un `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5. Verificar Instalación

Los scrapers ahora incluyen logs que muestran:
- ✅ Chrome encontrado en: `/usr/bin/google-chrome`
- 🔧 Usando Chrome en: `/usr/bin/google-chrome`

Si ves estos mensajes, la configuración es correcta.

### 6. Troubleshooting

**Error: Chrome no encontrado**
```bash
# Verifica que Chrome esté instalado
which google-chrome
which chromium-browser

# Verifica la versión
google-chrome --version
```

**Error: Permisos**
```bash
# Asegúrate de que Chrome sea ejecutable
chmod +x /usr/bin/google-chrome
```

**Error: Dependencias faltantes**
```bash
# Instala dependencias adicionales
apt-get install -y libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1
```

## Archivos Modificados

Los siguientes scrapers fueron actualizados con detección automática de Chrome:

1. ✅ `scrapper/procuraduria_scraper.py`
2. ✅ `scrapper/sisben_scraper.py`
3. ✅ `scrapper/registraduria_scraper.py`

## Cambios Implementados

### Función `_get_chrome_binary_path()`

Detecta automáticamente Chrome en:
- **Linux**: `/usr/bin/google-chrome`, `/usr/bin/chromium-browser`, etc.
- **Windows**: `C:\Program Files\Google\Chrome\Application\chrome.exe`, etc.
- **macOS**: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`

### Configuración de `binary_location`

```python
chrome_binary = self._get_chrome_binary_path()
if chrome_binary:
    options.binary_location = chrome_binary
```

Esto resuelve el error **"Binary Location Must be a String"**.

## Comandos de Render

### Build Command
```bash
apt-get update && apt-get install -y google-chrome-stable && pip install -r requirements.txt
```

### Start Command
```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

## Notas Importantes

1. **Headless Mode**: Render no tiene display, siempre usa `headless=True`
2. **Memoria**: Chrome consume mucha memoria, considera usar el plan con más RAM
3. **Timeouts**: Aumenta timeouts en producción si es necesario
4. **Logs**: Monitorea los logs para ver si Chrome se detecta correctamente

## Recursos Adicionales

- [Render Docs - Chrome/Puppeteer](https://render.com/docs/chrome-puppeteer)
- [Selenium Docker Images](https://github.com/SeleniumHQ/docker-selenium)
- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)
