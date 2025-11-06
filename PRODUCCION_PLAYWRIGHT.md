# Despliegue en Producción con Playwright

## Cambios Realizados para Producción

### 1. **run.py** - Script de Inicio Multiplataforma

El script ahora detecta automáticamente el sistema operativo:

- **Windows**: Usa `WindowsProactorEventLoopPolicy` (sin reload)
- **Linux**: Usa event loop por defecto (con/sin reload según entorno)

Variables de entorno soportadas:
- `ENVIRONMENT`: `production` o `development`
- `PORT`: Puerto del servidor (default: 8000)
- `WORKERS`: Número de workers (default: 2 en producción)

### 2. **Playwright en Linux**

#### Instalación Automática

El script `deploy.sh` ahora instala automáticamente:
1. Playwright Python package
2. Navegador Chromium
3. Dependencias del sistema para Chromium

#### Instalación Manual (si es necesario)

```bash
cd /var/www/html/apielectoral
source venv/bin/activate

# Instalar Playwright
pip install playwright

# Instalar Chromium
playwright install chromium

# Instalar dependencias del sistema
sudo playwright install-deps chromium
```

### 3. **Servicio Systemd Actualizado**

El archivo `api-electoral.service` ahora:
- Usa `python run.py` en lugar de `uvicorn` directamente
- Configura variables de entorno para producción
- Define ruta de navegadores de Playwright

## Despliegue Paso a Paso

### Opción 1: Despliegue Automático (GitHub Actions)

```bash
# En tu máquina local
git add .
git commit -m "Update for Playwright production"
git push origin main
```

GitHub Actions ejecutará automáticamente:
1. Pull del código
2. Instalación de dependencias
3. Instalación de Playwright
4. Reinicio del servicio

### Opción 2: Despliegue Manual

```bash
# Conectar al servidor
ssh ubuntu@158.69.113.159

# Ir al directorio del proyecto
cd /var/www/html/apielectoral

# Pull de cambios
git pull origin main

# Ejecutar script de despliegue
bash deploy.sh
```

## Verificación del Despliegue

### 1. Verificar el Servicio

```bash
# Estado del servicio
sudo systemctl status api-electoral

# Ver logs en tiempo real
sudo journalctl -u api-electoral -f

# Ver últimas 50 líneas de logs
sudo journalctl -u api-electoral -n 50
```

### 2. Verificar Playwright

```bash
# Conectar al servidor
ssh ubuntu@158.69.113.159

# Activar entorno virtual
cd /var/www/html/apielectoral
source venv/bin/activate

# Verificar instalación de Playwright
python -c "from playwright.async_api import async_playwright; print('✅ Playwright OK')"

# Verificar navegadores instalados
playwright --version
```

### 3. Probar el Endpoint

```bash
# Desde tu máquina local
curl -X POST http://158.69.113.159:8000/consultar-nombres-v1 \
  -H "Content-Type: application/json" \
  -d '{"nuip": "1102877148", "enviarapi": false}'
```

## Configuración de Headless en Producción

### Procuraduría en Producción

Por defecto, Procuraduría está configurado con `headless=False` para desarrollo.

**Para cambiar a headless en producción**, edita `api.py`:

```python
# En api.py, línea 102 y 281
scraper = ProcuraduriaScraperAuto(headless=True)  # Cambiar a True
```

O mejor aún, usa variable de entorno:

```python
# En api.py
import os
headless_mode = os.getenv('HEADLESS_MODE', 'True').lower() == 'true'
scraper = ProcuraduriaScraperAuto(headless=headless_mode)
```

Luego en `.env`:
```bash
HEADLESS_MODE=True
```

## Troubleshooting

### Error: "Chromium not found"

```bash
ssh ubuntu@158.69.113.159
cd /var/www/html/apielectoral
source venv/bin/activate
playwright install chromium
sudo playwright install-deps chromium
sudo systemctl restart api-electoral
```

### Error: "Permission denied" para Chromium

```bash
# Verificar permisos
ls -la ~/.cache/ms-playwright/

# Dar permisos si es necesario
chmod -R 755 ~/.cache/ms-playwright/
```

### El navegador no se cierra correctamente

Esto es normal en headless mode. Los procesos se limpian automáticamente.

Para verificar procesos de Chromium:
```bash
ps aux | grep chromium
```

### Logs muestran "NotImplementedError"

Esto solo debería ocurrir en Windows. En Linux, el event loop por defecto funciona correctamente.

Si ocurre en Linux, verifica:
```bash
python --version  # Debe ser 3.7+
cat /etc/os-release  # Verificar distribución
```

## Monitoreo

### Logs del Servicio

```bash
# Ver logs en tiempo real
sudo journalctl -u api-electoral -f

# Filtrar por errores
sudo journalctl -u api-electoral -p err

# Ver logs de hoy
sudo journalctl -u api-electoral --since today
```

### Recursos del Sistema

```bash
# Uso de CPU y memoria
top -p $(pgrep -f "python run.py")

# Procesos de Chromium
ps aux | grep chromium | wc -l
```

## Optimizaciones para Producción

### 1. Limitar Workers de Uvicorn

En `run.py`, el número de workers se configura según el entorno:
- Desarrollo: 1 worker (con reload)
- Producción: 2 workers (sin reload)

Para cambiar:
```bash
# En el servidor
export WORKERS=4
sudo systemctl restart api-electoral
```

### 2. Configurar Timeout

Si las consultas de Procuraduría toman mucho tiempo, aumenta el timeout en `procuraduria_scraper.py`:

```python
# Línea 89
self.page.set_default_timeout(30000)  # 30 segundos
```

### 3. Limpiar Cache de Playwright

```bash
# Limpiar navegadores antiguos
playwright uninstall --all
playwright install chromium
```

## Rollback

Si algo sale mal:

```bash
ssh ubuntu@158.69.113.159
cd /var/www/html/apielectoral

# Volver a commit anterior
git log --oneline -5
git reset --hard <commit-hash>

# Reinstalar dependencias
source venv/bin/activate
pip install -r requirements.txt

# Reiniciar servicio
sudo systemctl restart api-electoral
```

## Checklist de Despliegue

- [ ] Código pusheado a GitHub
- [ ] GitHub Actions ejecutado exitosamente
- [ ] Servicio corriendo: `sudo systemctl status api-electoral`
- [ ] Playwright instalado: `playwright --version`
- [ ] Endpoint responde: `curl http://158.69.113.159:8000/balance`
- [ ] Logs sin errores: `sudo journalctl -u api-electoral -n 50`
- [ ] Procuraduría funciona: Probar endpoint `/consultar-nombres-v1`

## Contacto y Soporte

- **Servidor**: 158.69.113.159
- **Usuario**: ubuntu
- **Directorio**: /var/www/html/apielectoral
- **Puerto**: 8000
- **Logs**: `sudo journalctl -u api-electoral`
