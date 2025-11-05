# 🚀 Guía de Despliegue en Producción

## Error Resuelto: Chrome Session Not Created

### Problema
```
Error al procesar la consulta: Message: session not created: Chrome instance exited.
```

### Causa Raíz
Este error ocurre en entornos de producción (especialmente Linux/containers) cuando:
1. Chrome/Chromium no está instalado
2. Faltan dependencias del sistema
3. Opciones de Chrome insuficientes para modo headless
4. Permisos insuficientes

### Solución Implementada ✅

Se actualizaron **todos los scrapers** con opciones de Chrome optimizadas para producción:

#### Cambios Aplicados:
- `procuraduria_scraper.py` ✅
- `sisben_scraper.py` ✅
- `registraduria_scraper.py` ✅
- `police_scraper.py` ✅

---

## 📋 Requisitos de Producción

### 1. Instalar Chrome/Chromium en el Servidor

#### Para Ubuntu/Debian:
```bash
# Opción 1: Google Chrome (recomendado)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb

# Opción 2: Chromium
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver
```

#### Para CentOS/RHEL:
```bash
# Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo yum install -y ./google-chrome-stable_current_x86_64.rpm
```

#### Para Alpine Linux (Docker):
```bash
apk add --no-cache chromium chromium-chromedriver
```

### 2. Instalar Dependencias del Sistema

```bash
# Ubuntu/Debian
sudo apt-get install -y \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils
```

### 3. Verificar Instalación

```bash
# Verificar Chrome
google-chrome --version
# o
chromium-browser --version

# Verificar ChromeDriver
chromedriver --version
```

---

## 🐳 Despliegue con Docker

### Dockerfile Recomendado

```dockerfile
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APIKEY_2CAPTCHA=${APIKEY_2CAPTCHA}
      - HEADLESS_MODE=True
    volumes:
      - ./tasks:/app/tasks
    restart: unless-stopped
    shm_size: '2gb'  # Importante para Chrome
```

---

## ☁️ Despliegue en Render.com

### render.yaml

```yaml
services:
  - type: web
    name: api-electoral
    env: python
    region: oregon
    plan: starter
    buildCommand: |
      apt-get update
      apt-get install -y wget gnupg
      wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
      echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
      apt-get update
      apt-get install -y google-chrome-stable fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 libwayland-client0 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 xdg-utils
      pip install -r requirements.txt
    startCommand: uvicorn api:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: APIKEY_2CAPTCHA
        sync: false
      - key: HEADLESS_MODE
        value: "True"
```

### Configuración Manual en Render

1. **Build Command:**
```bash
apt-get update && apt-get install -y wget gnupg && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && apt-get update && apt-get install -y google-chrome-stable fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 libwayland-client0 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 xdg-utils && pip install -r requirements.txt
```

2. **Start Command:**
```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

3. **Environment Variables:**
   - `APIKEY_2CAPTCHA`: Tu API key de 2captcha
   - `HEADLESS_MODE`: `True`

---

## 🔧 Opciones de Chrome Implementadas

### Críticas para Producción
```python
--headless=new              # Nuevo modo headless (más estable)
--no-sandbox                # Requerido en containers
--disable-dev-shm-usage     # Evita problemas de memoria compartida
--disable-setuid-sandbox    # Requerido sin privilegios root
--remote-debugging-port=9222 # Para debugging
--disable-gpu               # No necesario en headless
--window-size=1920,1080     # Tamaño de ventana consistente
```

### Optimizaciones de Rendimiento
```python
--disable-extensions
--disable-software-rasterizer
--disable-background-networking
--disable-default-apps
--disable-sync
--metrics-recording-only
--mute-audio
--no-first-run
--safebrowsing-disable-auto-update
```

---

## 🧪 Verificación Post-Despliegue

### 1. Test de Endpoint de Salud
```bash
curl https://tu-api.com/
```

### 2. Test de Scraper
```bash
curl -X POST https://tu-api.com/consultar-nombres-v3 \
  -H "Content-Type: application/json" \
  -d '{"nuip": "1102877148"}'
```

### 3. Verificar Logs
```bash
# Render
render logs --tail

# Docker
docker logs -f api-electoral

# Heroku
heroku logs --tail
```

---

## 🐛 Troubleshooting

### Error: "Chrome binary not found"
```bash
# Verificar instalación
which google-chrome
which chromium-browser

# Reinstalar
sudo apt-get install --reinstall google-chrome-stable
```

### Error: "DevToolsActivePort file doesn't exist"
**Solución:** Ya implementada con `--remote-debugging-port=9222`

### Error: "Failed to move to new namespace"
**Solución:** Ya implementada con `--no-sandbox`

### Error: "Shared memory issue"
**Solución:** Ya implementada con `--disable-dev-shm-usage`

### Chrome se cierra inmediatamente
**Verificar:**
1. Todas las dependencias del sistema están instaladas
2. `HEADLESS_MODE=True` en variables de entorno
3. Suficiente memoria RAM (mínimo 512MB, recomendado 1GB+)

---

## 📊 Monitoreo

### Logs Importantes
```python
# Éxito
"✅ Driver de Chrome configurado correctamente"
"✅ Página cargada completamente"

# Error
"❌ Error al inicializar Chrome"
"💡 Asegúrate de que Chrome/Chromium esté instalado en el sistema"
```

### Métricas a Monitorear
- Uso de memoria (Chrome consume ~200-500MB por instancia)
- Tiempo de respuesta de endpoints
- Tasa de éxito de scrapers
- Balance de 2captcha

---

## 🔐 Seguridad en Producción

### Variables de Entorno Requeridas
```bash
APIKEY_2CAPTCHA=tu_api_key_aqui
HEADLESS_MODE=True
```

### Recomendaciones
1. No exponer puertos de debugging en producción
2. Implementar rate limiting
3. Usar HTTPS
4. Configurar CORS apropiadamente
5. Implementar autenticación/autorización

---

## 📝 Checklist de Despliegue

- [ ] Chrome/Chromium instalado
- [ ] Dependencias del sistema instaladas
- [ ] Variables de entorno configuradas
- [ ] `HEADLESS_MODE=True`
- [ ] Scrapers actualizados con nuevas opciones
- [ ] Tests de endpoints funcionando
- [ ] Logs monitoreados
- [ ] Memoria suficiente (1GB+ recomendado)
- [ ] Balance de 2captcha verificado

---

## 📞 Soporte

Si el error persiste después de aplicar estos cambios:

1. Verificar logs completos del servidor
2. Confirmar versión de Chrome instalada
3. Verificar que todas las dependencias del sistema estén instaladas
4. Revisar límites de memoria del servidor

**Última actualización:** 2025-11-05
**Versión:** 2.0.0
