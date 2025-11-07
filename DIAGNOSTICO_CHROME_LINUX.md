# 🔍 Diagnóstico Chrome en Linux - Error Persistente

## 🚨 Estado Actual
El error **DevToolsActivePort** persiste después de aplicar los 4 fixes.

## 🔬 Diagnóstico Profundo Necesario

### Paso 1: Verificar Logs Detallados
```bash
# Ver logs completos del servicio
sudo journalctl -u api-electoral -n 500 --no-pager > /tmp/api_logs.txt

# Buscar errores específicos
grep -i "chrome\|driver\|devtools\|session" /tmp/api_logs.txt

# Ver últimas 50 líneas con contexto
sudo journalctl -u api-electoral -n 50 --no-pager
```

### Paso 2: Verificar Instalación de Chrome
```bash
# Versión de Chrome
google-chrome --version
google-chrome-stable --version
chromium --version

# Ubicación del binario
which google-chrome
which google-chrome-stable
which chromium

# Test básico de Chrome
google-chrome --headless=new --no-sandbox --disable-dev-shm-usage \
  --disable-gpu --user-data-dir=/tmp/test-chrome-$(date +%s) \
  --dump-dom https://www.google.com 2>&1 | head -20
```

### Paso 3: Verificar ChromeDriver
```bash
# Ubicación de ChromeDriver instalado por webdriver-manager
ls -la ~/.wdm/drivers/chromedriver/

# Si existe, verificar versión
find ~/.wdm/drivers/chromedriver/ -name "chromedriver" -type f -exec {} --version \;

# Verificar compatibilidad
echo "Chrome version:"
google-chrome --version
echo "ChromeDriver version:"
find ~/.wdm/drivers/chromedriver/ -name "chromedriver" -type f -exec {} --version \;
```

### Paso 4: Verificar Permisos y Espacio
```bash
# Permisos de /tmp
ls -ld /tmp
# Debe ser: drwxrwxrwt (1777)

# Espacio disponible
df -h /tmp
df -h /var/tmp

# Archivos de Chrome en /tmp
ls -la /tmp/ | grep -i chrome

# Limpiar archivos antiguos
sudo find /tmp -name "*chrome*" -mtime +1 -ls
sudo find /tmp -name ".org.chromium*" -mtime +1 -ls
```

### Paso 5: Test Python Detallado
```bash
cd /var/www/html/apielectoral
source venv/bin/activate

python3 << 'EOF'
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

print("=" * 60)
print("DIAGNÓSTICO CHROME EN LINUX")
print("=" * 60)

# Verificar imports
try:
    from webdriver_manager.chrome import ChromeDriverManager
    print("✅ webdriver-manager importado correctamente")
except ImportError as e:
    print(f"❌ Error importando webdriver-manager: {e}")
    sys.exit(1)

# Configurar opciones
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-setuid-sandbox")

# Directorio único
pid = os.getpid()
user_data_dir = f"/tmp/chrome-test-{pid}"
options.add_argument(f"--user-data-dir={user_data_dir}")
options.add_argument("--crash-dumps-dir=/tmp")

# Logging detallado
options.add_argument("--enable-logging")
options.add_argument("--v=1")

print(f"\n📁 Directorio de datos: {user_data_dir}")
print(f"🔢 PID del proceso: {pid}")

# Intentar iniciar Chrome
try:
    print("\n🔄 Instalando/verificando ChromeDriver...")
    service = Service(ChromeDriverManager().install())
    print(f"✅ ChromeDriver path: {service.path}")
    
    print("\n🔄 Iniciando Chrome...")
    driver = webdriver.Chrome(service=service, options=options)
    print("✅ Chrome iniciado correctamente")
    
    print("\n🔄 Navegando a Google...")
    driver.get("https://www.google.com")
    print(f"✅ Título: {driver.title}")
    
    print("\n🔄 Cerrando Chrome...")
    driver.quit()
    print("✅ Chrome cerrado correctamente")
    
    print("\n" + "=" * 60)
    print("✅ DIAGNÓSTICO EXITOSO - Chrome funciona correctamente")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\n📋 Traceback completo:")
    import traceback
    traceback.print_exc()
    
    print("\n🔍 Información adicional:")
    print(f"- Python version: {sys.version}")
    print(f"- Working directory: {os.getcwd()}")
    print(f"- User: {os.getenv('USER', 'unknown')}")
    print(f"- HOME: {os.getenv('HOME', 'unknown')}")
    
    sys.exit(1)
EOF
```

---

## 🛠️ Soluciones Alternativas

### Solución A: Usar Chromium en lugar de Chrome
```python
# En setup_driver, agregar:
chrome_options.binary_location = "/usr/bin/chromium-browser"
# o
chrome_options.binary_location = "/usr/bin/chromium"
```

### Solución B: Deshabilitar Sandbox Completamente
```python
# Agregar más argumentos de sandbox
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-setuid-sandbox")
chrome_options.add_argument("--disable-sandbox")  # Redundante pero a veces necesario
```

### Solución C: Usar Display Virtual (Xvfb)
```bash
# Instalar Xvfb
sudo apt-get install -y xvfb

# Iniciar Xvfb
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Modificar servicio para usar DISPLAY
sudo nano /etc/systemd/system/api-electoral.service
# Agregar: Environment="DISPLAY=:99"
```

### Solución D: Usar undetected-chromedriver para todos
```python
# Cambiar de selenium.webdriver a undetected_chromedriver
import undetected_chromedriver as uc

# En setup_driver:
self.driver = uc.Chrome(
    options=chrome_options,
    use_subprocess=True,
    version_main=None
)
```

---

## 🔧 Fix Alternativo: Configuración Mínima Extrema

Si todo lo anterior falla, usar configuración ultra-mínima:

```python
def setup_driver(self, headless=False):
    """Configuración mínima para máxima compatibilidad"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless=new")
    
    # SOLO argumentos absolutamente esenciales
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Directorio único
    import os
    chrome_options.add_argument(f"--user-data-dir=/tmp/chrome-{os.getpid()}")
    
    try:
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
```

---

## 📋 Checklist de Diagnóstico

Ejecutar en el servidor y reportar resultados:

- [ ] `google-chrome --version` → Versión: _______
- [ ] `which google-chrome` → Path: _______
- [ ] `ls -ld /tmp` → Permisos: _______
- [ ] `df -h /tmp` → Espacio libre: _______
- [ ] `pip show webdriver-manager` → Versión: _______
- [ ] Test Python básico → Resultado: _______
- [ ] `sudo journalctl -u api-electoral -n 50` → Errores: _______

---

## 🎯 Próximos Pasos

1. **Ejecutar diagnóstico completo** en el servidor
2. **Reportar resultados** de cada comando
3. **Identificar el punto exacto de falla**
4. **Aplicar solución específica** según los resultados

---

**Necesito ver los resultados del diagnóstico para determinar la causa exacta.**
