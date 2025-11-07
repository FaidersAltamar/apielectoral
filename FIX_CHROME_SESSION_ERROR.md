# 🔧 Fix: Chrome Session Error en Producción

## 📋 Problema Identificado

**Error:** `session not created: Chrome instance exited`

### Causa Raíz

El argumento `--single-process` es **incompatible** con `--no-sandbox` en entornos Linux/producción. Esta combinación causa que Chrome crashee inmediatamente después de iniciarse.

```
--no-sandbox (línea 49)  +  --single-process (línea 57)  =  💥 CRASH
```

### Archivos Afectados

1. ✅ `scrapper/registraduria_scraper.py` - **CORREGIDO**
2. ✅ `scrapper/sisben_scraper.py` - **CORREGIDO**

---

## 🛠️ Cambios Realizados

### 1. Eliminado `--single-process`

**Antes:**
```python
chrome_options.add_argument("--single-process")
```

**Después:**
```python
# REMOVIDO: --single-process (incompatible con --no-sandbox en Linux)
```

### 2. Eliminado argumento duplicado

**Antes:**
```python
chrome_options.add_argument("--disable-software-rasterizer")  # línea 55
# ... otras opciones ...
chrome_options.add_argument("--disable-software-rasterizer")  # línea 70 (duplicado)
```

**Después:**
```python
chrome_options.add_argument("--disable-software-rasterizer")  # línea 55
# ... otras opciones ...
# REMOVIDO: --disable-software-rasterizer (duplicado arriba)
```

---

## 🚀 Pasos para Deployment en Producción

### Paso 1: Conectarse al servidor
```bash
ssh ubuntu@158.69.113.159
cd /var/www/html/apielectoral
```

### Paso 2: Hacer backup del código actual
```bash
cp -r scrapper scrapper_backup_$(date +%Y%m%d_%H%M%S)
```

### Paso 3: Actualizar el código desde Git
```bash
git pull origin main
```

### Paso 4: Verificar los cambios
```bash
# Verificar que --single-process fue removido
grep -n "single-process" scrapper/registraduria_scraper.py
grep -n "single-process" scrapper/sisben_scraper.py

# No debería mostrar ninguna línea activa (solo comentarios)
```

### Paso 5: Reiniciar el servicio
```bash
sudo systemctl restart api-electoral
```

### Paso 6: Verificar que el servicio está corriendo
```bash
sudo systemctl status api-electoral
```

Debe mostrar: `active (running)` en verde

### Paso 7: Monitorear logs en tiempo real
```bash
sudo journalctl -u api-electoral -f
```

Presiona `Ctrl+C` para salir cuando veas que todo funciona correctamente.

---

## ✅ Verificación Post-Deployment

### Test 1: Verificar endpoint de balance
```bash
curl http://localhost:8000/balance
```

**Resultado esperado:** JSON con balance de 2captcha

### Test 2: Probar endpoint de Registraduría
```bash
curl -X POST http://localhost:8000/consultar-puesto-votacion \
  -H "Content-Type: application/json" \
  -d '{"nuip": "1102877148", "enviarapi": false}'
```

**Resultado esperado:** JSON con datos del puesto de votación (puede tardar ~30-60 segundos por el captcha)

### Test 3: Verificar logs sin errores
```bash
sudo journalctl -u api-electoral -n 50 --no-pager | grep -i "error\|chrome\|session"
```

**Resultado esperado:** No debería mostrar errores de "Chrome instance exited"

---

## 🔍 Diagnóstico Adicional (si persiste el error)

### Verificar que Chrome funciona en headless
```bash
google-chrome --headless --disable-gpu --no-sandbox --disable-dev-shm-usage --dump-dom https://www.google.com
```

### Verificar librerías del sistema
```bash
ldd $(which google-chrome) | grep "not found"
```

Si muestra librerías faltantes, ejecutar:
```bash
bash install_chrome_dependencies.sh
```

### Verificar espacio en disco
```bash
df -h
```

Si `/tmp` está lleno:
```bash
sudo rm -rf /tmp/.org.chromium.*
sudo rm -rf /tmp/chrome_*
```

---

## 📊 Argumentos de Chrome Actuales

### Configuraciones Críticas (Producción/Linux)
```python
--no-sandbox                    # Requerido en Docker/contenedores
--disable-dev-shm-usage         # Evita problemas de memoria compartida
--disable-setuid-sandbox        # Desactiva sandbox adicional
--remote-debugging-port=9222    # Para debugging remoto
```

### Estabilidad en Producción
```python
--disable-software-rasterizer           # Evita renderizado por software
--disable-features=VizDisplayCompositor # Desactiva compositor visual
--disable-web-security                  # Simplifica políticas de seguridad
--disable-features=IsolateOrigins,site-per-process  # Simplifica procesos
--ignore-certificate-errors             # Ignora errores SSL
```

### Optimizaciones de Rendimiento
```python
--disable-extensions                # No cargar extensiones
--disable-background-networking     # Sin networking en background
--disable-default-apps              # No cargar apps por defecto
--disable-sync                      # Sin sincronización
--metrics-recording-only            # Solo métricas
--mute-audio                        # Sin audio
--no-first-run                      # Sin wizard de primera ejecución
--safebrowsing-disable-auto-update  # Sin actualizaciones de safebrowsing
```

---

## 📝 Notas Importantes

1. **`--single-process` NO debe usarse con `--no-sandbox`** en producción Linux
2. Los argumentos duplicados pueden causar comportamiento impredecible
3. El error "Chrome instance exited" típicamente indica:
   - Conflicto de argumentos (como `--single-process` + `--no-sandbox`)
   - Librerías del sistema faltantes
   - Problemas de permisos o recursos

---

## 🆘 Rollback (si algo sale mal)

```bash
# Detener el servicio
sudo systemctl stop api-electoral

# Restaurar backup
cp -r scrapper_backup_YYYYMMDD_HHMMSS/* scrapper/

# Reiniciar servicio
sudo systemctl start api-electoral
```

---

**Fecha:** Noviembre 7, 2025  
**Versión:** 1.0  
**Estado:** ✅ CORREGIDO
