# 🔧 Fix: DevToolsActivePort Error

## 📋 Nuevo Error Identificado

```json
{
  "error": "DevToolsActivePort file doesn't exist",
  "response_time_seconds": 60.74
}
```

## 🎯 Análisis

### ✅ Progreso
- El error anterior (`Chrome instance exited` en 1.24s) está **RESUELTO**
- Ahora Chrome intenta iniciar y tarda 60 segundos (timeout)
- Nuevo error: No puede crear el archivo DevToolsActivePort

### ❌ Problema Actual

**Error:** `DevToolsActivePort file doesn't exist`

**Causa:** Chrome en modo headless no puede crear el archivo de comunicación DevTools porque:
1. Falta el directorio de datos de usuario
2. Problemas de permisos en `/tmp`
3. Falta configuración de `--user-data-dir`

---

## 🛠️ Solución

### Agregar Argumentos Críticos para Headless

Los siguientes argumentos son **ESENCIALES** para Chrome headless en Linux:

```python
# Directorio de datos de usuario temporal
chrome_options.add_argument(f"--user-data-dir=/tmp/chrome-user-data-{os.getpid()}")

# Directorio de crash dumps
chrome_options.add_argument(f"--crash-dumps-dir=/tmp")

# Deshabilitar /dev/shm (memoria compartida)
chrome_options.add_argument("--disable-dev-shm-usage")  # Ya existe

# Logging
chrome_options.add_argument("--enable-logging")
chrome_options.add_argument("--v=1")
```

---

## 📝 Implementación

### Cambios en `registraduria_scraper.py` y `sisben_scraper.py`

**Agregar después de las configuraciones críticas:**

```python
# Configuraciones críticas para producción/Linux
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-setuid-sandbox")
# REMOVIDO: --remote-debugging-port=9222 (causa conflictos con múltiples instancias)

# NUEVO: Configuración de directorios para headless
import os
chrome_options.add_argument(f"--user-data-dir=/tmp/chrome-user-data-{os.getpid()}")
chrome_options.add_argument("--crash-dumps-dir=/tmp")
chrome_options.add_argument("--enable-logging")
chrome_options.add_argument("--v=1")
```

### Alternativa: Usar Directorio Persistente

Si los directorios temporales causan problemas:

```python
# Crear directorio base si no existe
import os
user_data_base = "/var/tmp/chrome-data"
os.makedirs(user_data_base, exist_ok=True)

# Usar PID para evitar conflictos
chrome_options.add_argument(f"--user-data-dir={user_data_base}/session-{os.getpid()}")
```

---

## 🚀 Deployment Rápido

### Opción A: Fix Mínimo (Recomendado)

```bash
# 1. Conectar al servidor
ssh ubuntu@158.69.113.159
cd /var/www/html/apielectoral

# 2. Editar registraduria_scraper.py
nano scrapper/registraduria_scraper.py

# Agregar después de la línea 54 (después de --disable-setuid-sandbox):
# import os ya existe al inicio del archivo
chrome_options.add_argument(f"--user-data-dir=/tmp/chrome-user-data-{os.getpid()}")
chrome_options.add_argument("--crash-dumps-dir=/tmp")

# 3. Editar sisben_scraper.py
nano scrapper/sisben_scraper.py

# Agregar después de la línea 45 (después de --disable-setuid-sandbox):
chrome_options.add_argument(f"--user-data-dir=/tmp/chrome-user-data-{os.getpid()}")
chrome_options.add_argument("--crash-dumps-dir=/tmp")

# 4. Reiniciar servicio
sudo systemctl restart api-electoral

# 5. Verificar
sudo journalctl -u api-electoral -f
```

### Opción B: Limpiar y Verificar Permisos

```bash
# 1. Limpiar /tmp
sudo rm -rf /tmp/chrome-*
sudo rm -rf /tmp/.org.chromium.*
sudo rm -rf /tmp/scoped_dir*

# 2. Verificar permisos de /tmp
ls -la /tmp
sudo chmod 1777 /tmp

# 3. Crear directorio base con permisos correctos
sudo mkdir -p /var/tmp/chrome-data
sudo chmod 777 /var/tmp/chrome-data

# 4. Reiniciar servicio
sudo systemctl restart api-electoral
```

---

## 🧪 Test Rápido

```python
# test_devtools.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument(f"--user-data-dir=/tmp/chrome-test-{os.getpid()}")

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.google.com")
    print(f"✅ SUCCESS - Título: {driver.title}")
    driver.quit()
except Exception as e:
    print(f"❌ ERROR: {e}")
```

---

## 📊 Argumentos Completos Recomendados

### Configuración Mínima y Estable

```python
def setup_driver(self, headless=False):
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
    
    # ESENCIALES para producción Linux
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-setuid-sandbox")
    
    # CRÍTICO: Directorios para headless
    import os
    chrome_options.add_argument(f"--user-data-dir=/tmp/chrome-user-data-{os.getpid()}")
    chrome_options.add_argument("--crash-dumps-dir=/tmp")
    
    # Optimizaciones básicas
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--no-first-run")
    
    # Anti-detección (solo si necesario)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"❌ Error al inicializar Chrome: {e}")
        raise
```

---

## 🔍 Diagnóstico Adicional

### Si el error persiste, verificar:

```bash
# 1. Espacio en /tmp
df -h /tmp

# 2. Permisos de /tmp
ls -ld /tmp
# Debe mostrar: drwxrwxrwt (sticky bit)

# 3. Procesos de Chrome zombie
ps aux | grep defunct

# 4. Archivos huérfanos en /tmp
sudo find /tmp -name "*chrome*" -type d -mtime +1
sudo find /tmp -name ".org.chromium*" -type d -mtime +1

# 5. Limpiar todo
sudo find /tmp -name "*chrome*" -delete
sudo find /tmp -name ".org.chromium*" -delete
```

---

## 💡 Explicación Técnica

### ¿Qué es DevToolsActivePort?

Chrome crea un archivo `DevToolsActivePort` en el directorio de datos de usuario para:
- Comunicación entre ChromeDriver y Chrome
- Debugging remoto
- Gestión de sesiones

### ¿Por qué falla en headless?

1. **Sin --user-data-dir:** Chrome intenta usar `~/.config/google-chrome/` que puede no existir
2. **Permisos:** El usuario del servicio puede no tener permisos en el directorio por defecto
3. **Múltiples instancias:** Sin directorios únicos, las instancias colisionan

### Solución con PID

```python
--user-data-dir=/tmp/chrome-user-data-{os.getpid()}
```

Cada proceso Python tiene un PID único, por lo tanto:
- Proceso 1234 → `/tmp/chrome-user-data-1234/`
- Proceso 5678 → `/tmp/chrome-user-data-5678/`
- Sin colisiones ✅

---

## 📋 Checklist de Implementación

- [ ] Agregar `--user-data-dir` con PID único
- [ ] Agregar `--crash-dumps-dir=/tmp`
- [ ] Limpiar /tmp de archivos antiguos
- [ ] Verificar permisos de /tmp (1777)
- [ ] Reiniciar servicio
- [ ] Test de endpoint
- [ ] Verificar logs sin errores

---

## 🎯 Resultado Esperado

**Antes:**
```json
{
  "error": "DevToolsActivePort file doesn't exist",
  "response_time_seconds": 60.74
}
```

**Después:**
```json
{
  "status": "success",
  "data": [{...}],
  "response_time_seconds": 45.23
}
```

---

**Fecha:** Noviembre 7, 2025  
**Versión:** 3.0  
**Estado:** 🔴 REQUIERE IMPLEMENTACIÓN INMEDIATA
