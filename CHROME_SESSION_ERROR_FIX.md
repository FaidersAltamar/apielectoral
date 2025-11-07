# 🔧 Solución para Error: Chrome Instance Exited

## Error Completo
```
Message: session not created: Chrome instance exited. 
Examine ChromeDriver verbose log to determine the cause.
For documentation on this error, please visit: 
https://www.selenium.dev/documentation/webdriver/troubleshooting/errors#sessionnotcreatedexception
```

## 🎯 Causa Raíz

Este error ocurre cuando Chrome se cierra inmediatamente después de iniciarse en modo headless. Las causas principales son:

1. **Faltan dependencias del sistema** (librerías compartidas)
2. **Configuración insuficiente** de argumentos de Chrome
3. **Problemas de permisos** o recursos del sistema

---

## ✅ Solución Rápida (Recomendada)

### Paso 1: Conectarse al servidor
```bash
ssh ubuntu@158.69.113.159
cd /var/www/html/apielectoral
```

### Paso 2: Actualizar el código
```bash
git pull origin main
```

### Paso 3: Ejecutar el script de instalación mejorado
```bash
bash install_chrome_dependencies.sh
```

### Paso 4: Reiniciar el servicio
```bash
sudo systemctl restart api-electoral
```

### Paso 5: Verificar que funciona
```bash
# Ver logs en tiempo real
sudo journalctl -u api-electoral -f

# En otra terminal, probar el endpoint
curl http://localhost:8000/balance
```

---

## 🔍 Diagnóstico Manual

Si la solución rápida no funciona, ejecuta estos comandos para diagnosticar:

### 1. Verificar que Chrome está instalado
```bash
google-chrome --version
# Debe mostrar: Google Chrome 120.x.x.x o superior
```

### 2. Probar Chrome en modo headless
```bash
google-chrome --headless --disable-gpu --no-sandbox --disable-dev-shm-usage --dump-dom https://www.google.com
```

Si este comando falla, Chrome no puede ejecutarse en modo headless.

### 3. Verificar librerías del sistema
```bash
# Verificar librerías críticas
ldd $(which google-chrome) | grep "not found"

# Si muestra librerías "not found", instalarlas:
sudo apt-get update
sudo apt-get install -y libnss3 libgbm1 libatk-bridge2.0-0 libgtk-3-0
```

### 4. Verificar logs detallados del servicio
```bash
# Ver últimos 100 logs
sudo journalctl -u api-electoral -n 100 --no-pager

# Buscar errores específicos de Chrome
sudo journalctl -u api-electoral | grep -i "chrome\|driver\|session"
```

---

## 🛠️ Cambios Realizados en el Código

### 1. Argumentos adicionales en `registraduria_scraper.py`

Se agregaron argumentos críticos para estabilidad en producción:

```python
# Argumentos adicionales para estabilidad en producción
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-features=VizDisplayCompositor")
chrome_options.add_argument("--single-process")
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
chrome_options.add_argument("--ignore-certificate-errors")
```

**Explicación de cada argumento:**
- `--disable-software-rasterizer`: Evita usar renderizado por software
- `--disable-features=VizDisplayCompositor`: Desactiva compositor visual que puede causar crashes
- `--single-process`: Ejecuta Chrome en un solo proceso (más estable en servidores)
- `--disable-web-security`: Desactiva políticas de seguridad web que pueden causar problemas
- `--disable-features=IsolateOrigins,site-per-process`: Simplifica el modelo de procesos
- `--ignore-certificate-errors`: Ignora errores de certificados SSL

### 2. Dependencias adicionales en `install_chrome_dependencies.sh`

Se agregaron librerías X11 y gráficas adicionales:

```bash
libx11-6 \
libx11-xcb1 \
libxcb1 \
libxext6 \
libxrender1 \
libxtst6 \
libxi6 \
libglib2.0-0 \
libpango-1.0-0 \
libcairo2 \
libgdk-pixbuf2.0-0
```

---

## 🚨 Solución de Problemas Avanzada

### Problema: Chrome sigue fallando después de instalar dependencias

**Solución 1: Verificar espacio en disco**
```bash
df -h
# Si /tmp está lleno, limpiar:
sudo rm -rf /tmp/*
```

**Solución 2: Verificar memoria disponible**
```bash
free -h
# Si la memoria es baja, reiniciar el servidor:
sudo reboot
```

**Solución 3: Reinstalar Chrome completamente**
```bash
# Desinstalar Chrome
sudo apt-get remove -y google-chrome-stable

# Limpiar caché
sudo rm -rf ~/.cache/google-chrome
sudo rm -rf /tmp/.org.chromium.*

# Reinstalar
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt-get install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb
```

**Solución 4: Usar Chromium en lugar de Chrome**
```bash
# Instalar Chromium
sudo apt-get install -y chromium-browser

# Verificar que funciona
chromium-browser --headless --disable-gpu --no-sandbox --dump-dom https://www.google.com
```

Si usas Chromium, debes actualizar el código para usar el binario correcto.

---

## 📊 Verificación Post-Instalación

### Test 1: Verificar el servicio
```bash
sudo systemctl status api-electoral
# Debe mostrar: active (running)
```

### Test 2: Probar endpoint de balance
```bash
curl http://localhost:8000/balance
# Debe retornar JSON con balance de 2captcha
```

### Test 3: Probar endpoint de consulta
```bash
curl -X POST http://localhost:8000/consultar-puesto-votacion \
  -H "Content-Type: application/json" \
  -d '{"nuip": "1102877148", "enviarapi": false}'
```

### Test 4: Monitorear logs en tiempo real
```bash
sudo journalctl -u api-electoral -f
# Debe mostrar logs sin errores de Chrome
```

---

## 🔄 Alternativa: Usar Docker (Opcional)

Si los problemas persisten, considera usar Docker para aislar el entorno:

```dockerfile
FROM python:3.11-slim

# Instalar dependencias de Chrome
RUN apt-get update && apt-get install -y \
    wget gnupg ca-certificates \
    fonts-liberation libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libatspi2.0-0 libcups2 libdbus-1-3 \
    libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 \
    libwayland-client0 libxcomposite1 libxdamage1 \
    libxfixes3 libxkbcommon0 libxrandr2 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Instalar Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Copiar código y dependencias
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📝 Checklist de Verificación

- [ ] Chrome está instalado (`google-chrome --version`)
- [ ] Chrome funciona en headless (`google-chrome --headless --no-sandbox --dump-dom https://www.google.com`)
- [ ] Todas las librerías están instaladas (sin "not found" en `ldd`)
- [ ] El código está actualizado (`git pull`)
- [ ] El servicio está corriendo (`systemctl status api-electoral`)
- [ ] Los endpoints responden correctamente
- [ ] No hay errores en los logs (`journalctl -u api-electoral`)

---

## 📞 Soporte Adicional

Si después de seguir todos estos pasos el error persiste:

1. **Capturar logs completos:**
   ```bash
   sudo journalctl -u api-electoral -n 500 > logs_error.txt
   ```

2. **Verificar versiones:**
   ```bash
   google-chrome --version
   python3 --version
   pip show selenium
   ```

3. **Probar script de prueba:**
   ```bash
   cd /var/www/html/apielectoral
   source venv/bin/activate
   python test/test_chromedriver.py
   ```

---

**Última actualización:** Noviembre 7, 2025  
**Versión:** 2.0
