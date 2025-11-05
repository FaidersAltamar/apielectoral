# Changelog - Fix "Binary Location Must be a String"

## Fecha: 2024-11-05

## Problema Resuelto
Error en producción (Render): **"Binary Location Must be a String"**

Este error ocurría porque Selenium y undetected-chromedriver no podían encontrar el binario de Chrome en entornos Linux sin interfaz gráfica.

## Solución Implementada

### 1. Función de Detección Automática de Chrome

Se agregó la función `_get_chrome_binary_path()` a todos los scrapers que:

- **Detecta el sistema operativo** (Linux, Windows, macOS)
- **Busca Chrome en ubicaciones estándar**:
  - Linux: `/usr/bin/google-chrome`, `/usr/bin/chromium-browser`, etc.
  - Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`, etc.
  - macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- **Usa el comando `which`** en Linux/Mac como fallback
- **Configura `binary_location`** automáticamente

### 2. Argumentos Adicionales para Producción

Se agregaron argumentos de Chrome para mejorar la estabilidad en producción:

```python
--disable-gpu
--disable-software-rasterizer
```

## Archivos Modificados

### ✅ Scrapers Actualizados

1. **`scrapper/procuraduria_scraper.py`**
   - Agregada función `_get_chrome_binary_path()`
   - Configuración automática de `binary_location`
   - Argumentos adicionales para producción

2. **`scrapper/sisben_scraper.py`**
   - Agregada función `_get_chrome_binary_path()`
   - Configuración automática de `binary_location`
   - Argumentos adicionales para producción

3. **`scrapper/registraduria_scraper.py`**
   - Agregada función `_get_chrome_binary_path()`
   - Configuración automática de `binary_location`
   - Argumentos adicionales para producción

4. **`scrapper/police_scraper.py`**
   - Agregada función `_get_chrome_binary_path()`
   - Configuración automática de `binary_location`
   - Argumentos adicionales para producción

### 📄 Documentación Creada

5. **`RENDER_DEPLOY.md`**
   - Guía completa de despliegue en Render
   - Instrucciones para instalar Chrome en Linux
   - Comandos de build y start
   - Troubleshooting común
   - Ejemplo de Dockerfile

## Código Agregado

### Ejemplo de la función agregada:

```python
def _get_chrome_binary_path(self):
    """Detecta la ruta del binario de Chrome según el sistema operativo"""
    import platform
    import shutil
    
    system = platform.system()
    
    # Posibles ubicaciones de Chrome/Chromium
    possible_paths = []
    
    if system == "Linux":
        possible_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/snap/bin/chromium",
            "/usr/local/bin/chrome",
            "/usr/local/bin/chromium"
        ]
    elif system == "Windows":
        possible_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
        ]
    elif system == "Darwin":  # macOS
        possible_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium"
        ]
    
    # Buscar el primer path que existe
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Chrome encontrado en: {path}")
            return path
    
    # Intentar usar 'which' en Linux/Mac
    if system in ["Linux", "Darwin"]:
        for cmd in ["google-chrome", "chromium-browser", "chromium"]:
            chrome_path = shutil.which(cmd)
            if chrome_path:
                print(f"✅ Chrome encontrado via which: {chrome_path}")
                return chrome_path
    
    print("⚠️ No se encontró Chrome en ubicaciones conocidas")
    return None
```

### Uso en setup_driver:

```python
def setup_driver(self):
    """Configura el driver de Chrome"""
    # Detectar ubicación de Chrome
    chrome_binary = self._get_chrome_binary_path()
    
    # Configurar opciones
    options = uc.ChromeOptions()
    
    # Establecer la ubicación del binario si se encontró
    if chrome_binary:
        options.binary_location = chrome_binary
        print(f"🔧 Usando Chrome en: {chrome_binary}")
    
    # ... resto de la configuración
```

## Logs de Verificación

Los scrapers ahora muestran logs informativos:

```
✅ Chrome encontrado en: /usr/bin/google-chrome
🔧 Usando Chrome en: /usr/bin/google-chrome
🚀 Iniciando Chrome con bypass anti-detección...
✅ Driver de Chrome configurado correctamente
```

## Instrucciones de Despliegue en Render

### Build Command:
```bash
apt-get update && apt-get install -y google-chrome-stable && pip install -r requirements.txt
```

### Start Command:
```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

### Variables de Entorno:
```
APIKEY_2CAPTCHA=tu_api_key
EXTERNAL_API_NOMBRE_URL=tu_url
EXTERNAL_API_PUESTO_URL=tu_url
```

## Compatibilidad

- ✅ **Windows**: Detecta Chrome en ubicaciones estándar
- ✅ **Linux**: Detecta Chrome/Chromium en múltiples ubicaciones
- ✅ **macOS**: Detecta Chrome en Applications
- ✅ **Render**: Compatible con instalación de Chrome vía apt-get
- ✅ **Docker**: Compatible con imágenes que incluyan Chrome

## Testing

Para probar localmente:

```python
from scrapper.procuraduria_scraper import ProcuraduriaScraperAuto

# Crear scraper (detectará Chrome automáticamente)
scraper = ProcuraduriaScraperAuto(headless=True)

# Realizar consulta
resultado = scraper.scrape_nuip("1102877148")
print(resultado)

# Cerrar
scraper.close()
```

## Notas Importantes

1. **Headless Mode**: En producción SIEMPRE usar `headless=True`
2. **Memoria**: Chrome consume ~200-300MB, considera el plan de Render
3. **Timeouts**: Los timeouts están configurados para producción
4. **Logs**: Monitorea los logs para verificar que Chrome se detecte correctamente

## Próximos Pasos

- [ ] Probar en Render después del despliegue
- [ ] Monitorear logs de producción
- [ ] Ajustar timeouts si es necesario
- [ ] Considerar usar Chrome headless shell para menor consumo de memoria

## Soporte

Si el error persiste:

1. Verifica que Chrome esté instalado: `which google-chrome`
2. Verifica la versión: `google-chrome --version`
3. Revisa los logs del scraper para ver la detección
4. Consulta `RENDER_DEPLOY.md` para más detalles
