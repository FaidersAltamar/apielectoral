# 🚀 Guía de Deployment - API Electoral

## Índice
1. [Resumen del Sistema](#resumen-del-sistema)
2. [Arquitectura de Deployment](#arquitectura-de-deployment)
3. [Componentes Principales](#componentes-principales)
4. [Flujo de Deployment](#flujo-de-deployment)
5. [Configuración del Servidor](#configuración-del-servidor)
6. [Troubleshooting](#troubleshooting)
7. [Comandos Útiles](#comandos-útiles)

---

## Resumen del Sistema

El sistema de deployment está diseñado para ser **automático, robusto y profesional**, utilizando:

- ✅ **GitHub Actions** para CI/CD automático
- ✅ **Systemd** para gestión del proceso
- ✅ **Script bash dedicado** para lógica de deployment
- ✅ **SSH** para conexión segura al VPS

### Datos del Servidor
- **Host**: 158.69.113.159
- **Usuario**: ubuntu
- **Puerto SSH**: 22
- **Directorio**: `/var/www/html/apielectoral`
- **Puerto API**: 8000

---

## Arquitectura de Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Repository                        │
│  (Push to main branch)                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              GitHub Actions Workflow                         │
│  (.github/workflows/deploy.yml)                              │
│  - Checkout code                                             │
│  - Connect via SSH                                           │
│  - Execute deploy.sh                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   VPS Server (Ubuntu)                        │
│  /var/www/html/apielectoral/                                 │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         deploy.sh (Deployment Script)                │   │
│  │  1. Backup .env                                      │   │
│  │  2. Git pull                                         │   │
│  │  3. Restore .env                                     │   │
│  │  4. Setup virtual environment                        │   │
│  │  5. Install dependencies                             │   │
│  │  6. Copy systemd service file                        │   │
│  │  7. Restart service                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                   │
│                           ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │    Systemd Service (api-electoral.service)           │   │
│  │  - Manages uvicorn process                           │   │
│  │  - Auto-restart on failure                           │   │
│  │  - Centralized logging                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                   │
│                           ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Uvicorn (FastAPI Server)                     │   │
│  │  - Host: 0.0.0.0                                     │   │
│  │  - Port: 8000                                        │   │
│  │  - Workers: 2                                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Componentes Principales

### 1. GitHub Actions Workflow (`.github/workflows/deploy.yml`)

**Propósito**: Automatizar el deployment en cada push a `main`

**Pasos clave**:
```yaml
- Checkout code
- Deploy via SSH:
  - Validar directorio del proyecto
  - Configurar git safe.directory
  - Ajustar permisos (ubuntu:ubuntu)
  - Ejecutar deploy.sh
- Health check del endpoint /balance
- Notificaciones de éxito/fallo
```

**Secretos requeridos**:
- `VPS_SSH_KEY`: Clave SSH privada para acceso al servidor

---

### 2. Script de Deployment (`deploy.sh`)

**Propósito**: Lógica centralizada de deployment

**Funciones**:
```bash
#!/bin/bash
set -e  # Exit on error

# Variables
PROJECT_DIR="/var/www/html/apielectoral"
VENV_PATH="$PROJECT_DIR/venv"

# 1. Backup de .env
# 2. Git pull (actualizar código)
# 3. Restore .env
# 4. Setup virtual environment
# 5. Instalar dependencias (pip install -r requirements.txt)
# 6. Copiar y recargar servicio systemd
# 7. Restart del servicio
# 8. Verificar status
```

**Ventajas**:
- ✅ Ejecuta localmente en el servidor (no depende de SSH)
- ✅ Manejo de errores con `set -e`
- ✅ Logs claros y descriptivos
- ✅ Fácil de mantener y debuggear

---

### 3. Systemd Service (`api-electoral.service`)

**Propósito**: Gestionar el proceso de la aplicación como servicio del sistema

**Configuración**:
```ini
[Unit]
Description=API Electoral - FastAPI Application
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/var/www/html/apielectoral
Environment="PATH=/var/www/html/apielectoral/venv/bin"
EnvironmentFile=/var/www/html/apielectoral/.env
ExecStart=/var/www/html/apielectoral/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5

# Limites de recursos
LimitNOFILE=65536

# Logs
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Características**:
- ✅ Auto-restart en caso de fallo
- ✅ Logs centralizados en systemd journal
- ✅ Gestión de recursos (límite de archivos abiertos)
- ✅ Inicio automático al bootear el servidor

---

## Flujo de Deployment

### Deployment Automático (Push a main)

```bash
# 1. Developer hace cambios
git add .
git commit -m "feat: nueva funcionalidad"
git push origin main

# 2. GitHub Actions se activa automáticamente
# 3. Workflow ejecuta deployment via SSH
# 4. deploy.sh actualiza el código y reinicia el servicio
# 5. Health check verifica que la API responde
# 6. Notificación de éxito/fallo
```

### Deployment Manual (workflow_dispatch)

1. Ir a GitHub → Actions
2. Seleccionar "Deploy FastAPI to VPS"
3. Click en "Run workflow"
4. Seleccionar branch (main)
5. Click "Run workflow"

---

## Configuración del Servidor

### Requisitos Previos

```bash
# 1. Instalar dependencias del sistema
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx

# 2. Crear directorio del proyecto
sudo mkdir -p /var/www/html/apielectoral
sudo chown -R ubuntu:ubuntu /var/www/html/apielectoral

# 3. Clonar repositorio
cd /var/www/html
git clone https://github.com/almanza023/apielectoral.git

# 4. Configurar archivo .env
cd apielectoral
cp .env.example .env
nano .env  # Editar con las credenciales reales
```

### Instalación del Servicio Systemd

```bash
# 1. Copiar archivo de servicio
sudo cp api-electoral.service /etc/systemd/system/

# 2. Recargar systemd
sudo systemctl daemon-reload

# 3. Habilitar servicio (inicio automático)
sudo systemctl enable api-electoral

# 4. Iniciar servicio
sudo systemctl start api-electoral

# 5. Verificar status
sudo systemctl status api-electoral
```

### Configuración de Nginx (Reverse Proxy)

```nginx
# /etc/nginx/sites-available/api-electoral
server {
    listen 80;
    server_name 158.69.113.159;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts para scrapers
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/api-electoral /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Troubleshooting

### Problema: El servicio no inicia

```bash
# Ver logs del servicio
sudo journalctl -u api-electoral -n 50 --no-pager

# Ver logs en tiempo real
sudo journalctl -u api-electoral -f

# Verificar status
sudo systemctl status api-electoral

# Reiniciar manualmente
sudo systemctl restart api-electoral
```

### Problema: Deployment falla en GitHub Actions

```bash
# 1. Verificar logs en GitHub Actions
# 2. Conectarse al servidor manualmente
ssh ubuntu@158.69.113.159

# 3. Ejecutar deploy.sh manualmente
cd /var/www/html/apielectoral
bash deploy.sh

# 4. Verificar permisos
ls -la
# Debe ser ubuntu:ubuntu
```

### Problema: API no responde

```bash
# Verificar que el servicio está corriendo
sudo systemctl status api-electoral

# Verificar que el puerto está escuchando
sudo netstat -tuln | grep 8000
# o
sudo ss -tuln | grep 8000

# Probar endpoint localmente
curl http://localhost:8000/balance

# Ver logs de errores
sudo journalctl -u api-electoral -n 100 | grep -i error
```

### Problema: Dependencias faltantes

```bash
# Activar virtual environment
cd /var/www/html/apielectoral
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt

# Verificar instalación
pip list

# Reiniciar servicio
sudo systemctl restart api-electoral
```

### Problema: Variables de entorno no cargadas

```bash
# Verificar que .env existe
ls -la /var/www/html/apielectoral/.env

# Ver contenido (sin mostrar secretos)
cat /var/www/html/apielectoral/.env | grep -v "API_KEY"

# Verificar que systemd carga el archivo
sudo systemctl show api-electoral | grep EnvironmentFile

# Reiniciar servicio después de cambios
sudo systemctl restart api-electoral
```

---

## Comandos Útiles

### Gestión del Servicio

```bash
# Iniciar servicio
sudo systemctl start api-electoral

# Detener servicio
sudo systemctl stop api-electoral

# Reiniciar servicio
sudo systemctl restart api-electoral

# Ver status
sudo systemctl status api-electoral

# Habilitar inicio automático
sudo systemctl enable api-electoral

# Deshabilitar inicio automático
sudo systemctl disable api-electoral

# Ver logs en tiempo real
sudo journalctl -u api-electoral -f

# Ver últimas 100 líneas de logs
sudo journalctl -u api-electoral -n 100

# Ver logs desde hoy
sudo journalctl -u api-electoral --since today
```

### Gestión del Código

```bash
# Ir al directorio del proyecto
cd /var/www/html/apielectoral

# Ver status de git
git status

# Ver último commit
git log -1

# Actualizar código manualmente
git pull origin main

# Ver cambios pendientes
git diff

# Ejecutar deployment manual
bash deploy.sh
```

### Monitoreo

```bash
# Ver procesos de uvicorn
ps aux | grep uvicorn

# Ver uso de recursos
top -p $(pgrep -f uvicorn)

# Ver conexiones al puerto 8000
sudo netstat -anp | grep :8000

# Probar endpoint
curl http://localhost:8000/balance

# Probar desde fuera del servidor
curl http://158.69.113.159:8000/balance
```

### Limpieza

```bash
# Limpiar caché de pip
pip cache purge

# Limpiar archivos temporales
cd /var/www/html/apielectoral
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Limpiar logs antiguos de systemd
sudo journalctl --vacuum-time=7d
```

---

## Puntos Clave para Recordar

### ✅ Ventajas del Sistema Actual

1. **Automatización completa**: Push → Deploy automático
2. **Gestión profesional**: Systemd maneja el proceso
3. **Logs centralizados**: Todo en systemd journal
4. **Auto-recovery**: Reinicio automático en caso de fallo
5. **Mantenibilidad**: Script separado, fácil de modificar
6. **Seguridad**: SSH con clave privada, no passwords

### ⚠️ Consideraciones Importantes

1. **Archivo .env**: Nunca commitear al repositorio
2. **Secretos de GitHub**: Mantener `VPS_SSH_KEY` seguro
3. **Permisos**: Todo debe ser `ubuntu:ubuntu`
4. **Backup**: `.env` se respalda automáticamente en cada deploy
5. **Logs**: Revisar regularmente con `journalctl`

### 🔒 Seguridad

```bash
# Verificar permisos de .env
ls -la /var/www/html/apielectoral/.env
# Debe ser: -rw------- (600) ubuntu ubuntu

# Si no es correcto:
chmod 600 /var/www/html/apielectoral/.env
chown ubuntu:ubuntu /var/www/html/apielectoral/.env
```

### 📊 Monitoreo Recomendado

- **Logs**: Revisar diariamente con `journalctl`
- **Uptime**: Verificar que el servicio está activo
- **Recursos**: Monitorear uso de CPU/RAM
- **Endpoints**: Health checks periódicos

---

## Contacto y Soporte

Para problemas o mejoras:
1. Revisar logs con `journalctl`
2. Ejecutar `deploy.sh` manualmente para debugging
3. Verificar GitHub Actions logs
4. Consultar esta documentación

**Última actualización**: Noviembre 6, 2025
