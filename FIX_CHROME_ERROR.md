# 🔧 Solución para Error de Chrome en Producción

## Error Actual
```
session not created: Chrome instance exited
```

## Causa
El servidor de producción no tiene las **librerías del sistema necesarias** para ejecutar Chrome en modo headless.

---

## ✅ Solución Rápida (Opción 1)

Conectarse al servidor y ejecutar el script de instalación:

```bash
# 1. Conectarse al servidor
ssh ubuntu@158.69.113.159

# 2. Ir al directorio del proyecto
cd /var/www/html/apielectoral

# 3. Hacer pull de los últimos cambios
git pull origin main

# 4. Ejecutar el script de instalación
bash install_chrome_dependencies.sh

# 5. Reiniciar el servicio
sudo systemctl restart api-electoral

# 6. Verificar logs
sudo journalctl -u api-electoral -f
```

---

## 🔧 Solución Manual (Opción 2)

Si prefieres instalar las dependencias manualmente:

```bash
# Conectarse al servidor
ssh ubuntu@158.69.113.159

# Actualizar repositorios
sudo apt-get update

# Instalar todas las dependencias necesarias
sudo apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
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
    libu2f-udev \
    libvulkan1 \
    xvfb

# Verificar que Chrome funciona
google-chrome --headless --disable-gpu --dump-dom https://www.google.com

# Reiniciar el servicio
sudo systemctl restart api-electoral

# Ver logs en tiempo real
sudo journalctl -u api-electoral -f
```

---

## 📋 Cambios Realizados en el Código

### 1. API (`api.py`)
✅ Cambiado `ProcuraduriaScraperAuto(headless=False)` → `headless=True`

**Antes:**
```python
scraper = ProcuraduriaScraperAuto(headless=False)  # ❌ No funciona en producción
```

**Después:**
```python
scraper = ProcuraduriaScraperAuto(headless=True)   # ✅ Funciona en producción
```

### 2. Configuración del Scraper (`procuraduria_scraper.py`)
El scraper ya tiene las configuraciones correctas para modo headless:
- `--headless=new`
- `--no-sandbox`
- `--disable-dev-shm-usage`
- `--disable-gpu`

---

## 🧪 Verificación

Después de instalar las dependencias, verifica que todo funciona:

```bash
# 1. Verificar que el servicio está corriendo
sudo systemctl status api-electoral

# 2. Probar el endpoint localmente
curl http://localhost:8000/balance

# 3. Probar el endpoint de Procuraduría
curl -X POST http://localhost:8000/consultar-nombres-v1 \
  -H "Content-Type: application/json" \
  -d '{"nuip": "1102877148", "enviarapi": false}'

# 4. Ver logs en tiempo real
sudo journalctl -u api-electoral -f
```

---

## 🚨 Si el Error Persiste

### Opción A: Verificar versión de Chrome
```bash
google-chrome --version
# Debe mostrar: Google Chrome 120.x.x.x o superior
```

### Opción B: Verificar ChromeDriver
```bash
# El scraper usa el ChromeDriver incluido con Selenium
# Verificar que selenium está instalado
cd /var/www/html/apielectoral
source venv/bin/activate
pip show selenium
```

### Opción C: Revisar logs detallados
```bash
# Ver logs completos del servicio
sudo journalctl -u api-electoral -n 200 --no-pager

# Buscar errores específicos de Chrome
sudo journalctl -u api-electoral | grep -i "chrome\|driver\|session"
```

### Opción D: Probar Chrome manualmente
```bash
# Probar que Chrome funciona en modo headless
google-chrome --headless --disable-gpu --no-sandbox --dump-dom https://www.google.com

# Si esto falla, hay un problema con Chrome o sus dependencias
```

---

## 📊 Todos los Scrapers Ahora Usan Headless

Verificado que todos los scrapers en `api.py` usan `headless=True`:

| Scraper | Modo Headless | Estado |
|---------|---------------|--------|
| ProcuraduriaScraperAuto | ✅ True | Corregido |
| PoliciaScraperAuto | ✅ True | OK |
| SisbenScraperAuto | ✅ True | OK |
| RegistraduriaScraperAuto | ✅ True | OK |

---

## 🎯 Resumen

1. **Problema**: Chrome no puede iniciar sin interfaz gráfica
2. **Causa**: Faltan librerías del sistema para modo headless
3. **Solución**: Instalar dependencias con el script `install_chrome_dependencies.sh`
4. **Verificación**: Reiniciar servicio y probar endpoints

---

## 📞 Soporte

Si después de seguir estos pasos el error persiste:
1. Revisar logs: `sudo journalctl -u api-electoral -f`
2. Verificar que Chrome está instalado: `google-chrome --version`
3. Probar Chrome manualmente en modo headless
4. Verificar que el código está actualizado: `git log -1`

**Última actualización**: Noviembre 6, 2025
