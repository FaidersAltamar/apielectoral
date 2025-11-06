# 🚀 Guía de Configuración VPS

## 📋 Requisitos Previos

- Servidor VPS con Ubuntu 20.04/22.04 o Debian 11/12
- Acceso root o sudo
- Dominio apuntando al servidor (opcional pero recomendado)

---

## 🔧 1. Preparación del Servidor

### Actualizar sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### Instalar dependencias del sistema
```bash
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    nginx \
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
    xdg-utils
```

### Instalar Google Chrome
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

# Verificar instalación
google-chrome --version
```

---

## 📁 2. Configurar Aplicación

### Crear usuario para la aplicación
```bash
sudo useradd -m -s /bin/bash apiuser
sudo usermod -aG sudo apiuser
```

### Clonar repositorio
```bash
sudo mkdir -p /home/api_electroral
sudo chown apiuser:apiuser /home/api_electroral
cd /home/api_electroral

# Clonar tu repositorio
git clone https://github.com/tu-usuario/api_electroral.git .
```

### Crear entorno virtual
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Configurar variables de entorno
```bash
cp .env.example .env
nano .env
```

Editar `.env`:
```env
APIKEY_2CAPTCHA=tu_api_key_aqui
HEADLESS_MODE=True
EXTERNAL_API_NOMBRE_URL=https://tu-api.com/nombre
EXTERNAL_API_PUESTO_URL=https://tu-api.com/puesto
```

### Crear directorio de logs
```bash
sudo mkdir -p /var/log/api-electoral
sudo chown apiuser:apiuser /var/log/api-electoral
```

---

## ⚙️ 3. Configurar Systemd Service

### Copiar archivo de servicio
```bash
sudo cp api-electoral.service /etc/systemd/system/
```

### Editar el servicio si es necesario
```bash
sudo nano /etc/systemd/system/api-electoral.service
```

Ajustar:
- `User` y `Group` (por defecto: www-data)
- `WorkingDirectory` (ruta del proyecto)
- Variables de entorno

### Habilitar y iniciar servicio
```bash
sudo systemctl daemon-reload
sudo systemctl enable api-electoral
sudo systemctl start api-electoral
sudo systemctl status api-electoral
```

### Verificar logs
```bash
# Logs del servicio
sudo journalctl -u api-electoral -f

# Logs de la aplicación
tail -f /var/log/api-electoral/access.log
tail -f /var/log/api-electoral/error.log
```

---

## 🌐 4. Configurar Nginx

### Copiar configuración
```bash
sudo cp nginx.conf /etc/nginx/sites-available/api-electoral
```

### Editar configuración
```bash
sudo nano /etc/nginx/sites-available/api-electoral
```

Cambiar:
- `server_name` con tu dominio
- Rutas de certificados SSL (si usas HTTPS)

### Habilitar sitio
```bash
sudo ln -s /etc/nginx/sites-available/api-electoral /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔒 5. Configurar SSL con Let's Encrypt (Opcional)

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Renovación automática (ya configurada por defecto)
sudo certbot renew --dry-run
```

---

## 🔑 6. Configurar GitHub Actions

### Generar SSH Key para GitHub Actions
```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github-actions
```

### Agregar clave pública al servidor
```bash
cat ~/.ssh/github-actions.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Configurar Secrets en GitHub

Ve a tu repositorio → Settings → Secrets and variables → Actions

Agregar los siguientes secrets:

1. **VPS_HOST**: IP o dominio de tu VPS
   ```
   123.45.67.89
   ```

2. **VPS_USERNAME**: Usuario SSH
   ```
   apiuser
   ```

3. **VPS_SSH_KEY**: Contenido de la clave privada
   ```bash
   cat ~/.ssh/github-actions
   # Copiar TODO el contenido (incluyendo BEGIN y END)
   ```

4. **VPS_PORT**: Puerto SSH (opcional, default: 22)
   ```
   22
   ```

5. **VPS_PROJECT_PATH**: Ruta del proyecto
   ```
   /home/api_electroral
   ```

6. **VPS_URL**: URL de tu API para health check
   ```
   https://your-domain.com
   ```

---

## 🔐 7. Configurar Permisos Sudo

Para que GitHub Actions pueda reiniciar el servicio sin contraseña:

```bash
sudo visudo
```

Agregar al final:
```
apiuser ALL=(ALL) NOPASSWD: /bin/systemctl restart api-electoral
apiuser ALL=(ALL) NOPASSWD: /bin/systemctl status api-electoral
apiuser ALL=(ALL) NOPASSWD: /bin/systemctl stop api-electoral
apiuser ALL=(ALL) NOPASSWD: /bin/systemctl start api-electoral
```

---

## 🧪 8. Probar Deployment

### Prueba manual
```bash
cd /home/api_electroral
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart api-electoral
```

### Prueba con GitHub Actions
1. Hacer un commit y push a `main`
2. Ver el workflow en GitHub Actions
3. Verificar logs del deployment

---

## 📊 9. Monitoreo

### Ver logs en tiempo real
```bash
# Logs del servicio
sudo journalctl -u api-electoral -f

# Logs de Nginx
sudo tail -f /var/log/nginx/api-electoral-access.log
sudo tail -f /var/log/nginx/api-electoral-error.log

# Logs de la aplicación
tail -f /var/log/api-electoral/access.log
tail -f /var/log/api-electoral/error.log
```

### Verificar estado
```bash
# Estado del servicio
sudo systemctl status api-electoral

# Procesos de Python
ps aux | grep uvicorn

# Uso de recursos
htop
```

### Endpoints de verificación
```bash
# Health check
curl http://localhost:8000/balance

# Desde internet
curl https://your-domain.com/balance
```

---

## 🔧 10. Comandos Útiles

### Reiniciar servicios
```bash
sudo systemctl restart api-electoral
sudo systemctl restart nginx
```

### Ver logs
```bash
sudo journalctl -u api-electoral --since "1 hour ago"
sudo journalctl -u api-electoral -n 100
```

### Limpiar cache de Chrome
```bash
python3 clean_driver_cache.py
```

### Actualizar manualmente
```bash
cd /home/api_electroral
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart api-electoral
```

---

## 🐛 Troubleshooting

### ❌ Error: VPS_PROJECT_PATH no configurado
Si ves `cd ***: No such file or directory`:

```bash
# En GitHub → Settings → Secrets → Actions
# Agregar secret: VPS_PROJECT_PATH
# Valor: /home/api_electroral (o la ruta correcta de tu proyecto)
```

### ❌ Error: externally-managed-environment
Si ves error de Python 3.13 con PEP 668:

```bash
# Opción 1: Usar virtual environment (RECOMENDADO)
cd /home/api_electroral
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Opción 2: Usar --break-system-packages (NO RECOMENDADO)
pip install -r requirements.txt --break-system-packages
```

### ❌ Error: api-electoral.service not found
Si el servicio systemd no existe:

```bash
# Crear el archivo de servicio
sudo nano /etc/systemd/system/api-electoral.service
```

Contenido básico:
```ini
[Unit]
Description=API Electoral Service
After=network.target

[Service]
Type=simple
User=apiuser
WorkingDirectory=/home/api_electroral
Environment="PATH=/home/api_electroral/venv/bin"
ExecStart=/home/api_electroral/venv/bin/python api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Luego:
```bash
sudo systemctl daemon-reload
sudo systemctl enable api-electoral
sudo systemctl start api-electoral
```

### ❌ Error: .env not found
Si el archivo .env no existe:

```bash
cd /home/api_electroral
cp .env.example .env
nano .env
# Configurar las variables necesarias
```

### Servicio no inicia
```bash
# Ver logs detallados
sudo journalctl -u api-electoral -xe

# Verificar permisos
ls -la /home/api_electroral

# Verificar entorno virtual
source venv/bin/activate
python -c "import fastapi; print('OK')"
```

### Error de Chrome
```bash
# Verificar Chrome instalado
google-chrome --version

# Reinstalar Chrome
sudo apt install --reinstall google-chrome-stable
```

### Nginx error
```bash
# Verificar configuración
sudo nginx -t

# Ver logs
sudo tail -f /var/log/nginx/error.log
```

### Puerto 8000 ocupado
```bash
# Ver qué usa el puerto
sudo lsof -i :8000

# Matar proceso
sudo kill -9 PID
```

---

## 📝 Checklist de Deployment

- [ ] Servidor actualizado
- [ ] Chrome instalado
- [ ] Dependencias del sistema instaladas
- [ ] Repositorio clonado
- [ ] Entorno virtual creado
- [ ] Variables de entorno configuradas
- [ ] Servicio systemd configurado
- [ ] Nginx configurado
- [ ] SSL configurado (opcional)
- [ ] GitHub Secrets configurados
- [ ] Permisos sudo configurados
- [ ] Primer deployment exitoso
- [ ] Health check funcionando

---

## 🎯 Próximos Pasos

1. Configurar monitoreo (Prometheus, Grafana)
2. Configurar backups automáticos
3. Implementar rate limiting
4. Configurar firewall (UFW)
5. Implementar logging centralizado

---

**Última actualización:** 2025-11-05
