# 🚀 Configuración Completa del VPS - API Electoral

## 📋 Información del Servidor
- **IP:** 158.69.113.159
- **Usuario:** ubuntu
- **Puerto SSH:** 22
- **Directorio del proyecto:** `/var/www/html/apielectoral`

## 🛠️ Configuración Inicial del VPS

### 1. Conectar al VPS
```bash
ssh ubuntu@158.69.113.159
```

### 2. Actualizar el Sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Instalar Dependencias del Sistema
```bash
# Python y herramientas básicas
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Nginx (servidor web)
sudo apt install -y nginx

# Chrome y dependencias para Selenium
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# Dependencias adicionales para Selenium
sudo apt install -y xvfb unzip
```

### 4. Configurar Directorio del Proyecto
```bash
# Crear directorio
sudo mkdir -p /var/www/html/apielectoral

# Cambiar propietario
sudo chown -R ubuntu:ubuntu /var/www/html/apielectoral

# Navegar al directorio
cd /var/www/html/apielectoral
```

## 📥 Despliegue del Código

### 5. Clonar el Repositorio
```bash
# Si es la primera vez
git clone https://github.com/TU-USUARIO/api_electroral.git .

# Configurar git para evitar errores
git config --global --add safe.directory /var/www/html/apielectoral
```

### 6. Configurar Variables de Entorno
```bash
# Crear archivo .env
nano .env
```

**Contenido del archivo .env:**
```env
APIKEY_2CAPTCHA=107c3fbf77239cd07598e255b7fdc822
EXTERNAL_API_NOMBRE_URL=https://api.juliocesarjarava.com.co/api/v1/respuestanombreapi
EXTERNAL_API_PUESTO_URL=https://api.juliocesarjarava.com.co/api/v1/respuestapuestoapi
HEADLESS_MODE=True
```

### 7. Configurar Entorno Virtual de Python
```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

## ⚙️ Configuración de Servicios

### 8. Configurar Servicio Systemd
El archivo `api-electoral.service` ya está en tu proyecto. Copiarlo:

```bash
# Copiar archivo de servicio
sudo cp api-electoral.service /etc/systemd/system/

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar el servicio
sudo systemctl enable api-electoral
```

### 9. Configurar Nginx
El archivo `nginx.conf` ya está en tu proyecto. Configurarlo:

```bash
# Copiar configuración de Nginx
sudo cp nginx.conf /etc/nginx/sites-available/api-electoral

# Crear enlace simbólico
sudo ln -sf /etc/nginx/sites-available/api-electoral /etc/nginx/sites-enabled/

# Eliminar sitio por defecto
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Habilitar Nginx
sudo systemctl enable nginx
```

## 🚀 Iniciar Servicios

### 10. Iniciar la Aplicación
```bash
# Iniciar FastAPI
sudo systemctl start api-electoral

# Verificar estado
sudo systemctl status api-electoral

# Ver logs si hay errores
sudo journalctl -u api-electoral -f
```

### 11. Iniciar Nginx
```bash
# Iniciar Nginx
sudo systemctl start nginx

# Verificar estado
sudo systemctl status nginx

# Ver logs si hay errores
sudo tail -f /var/log/nginx/error.log
```

## 🔍 Verificación del Despliegue

### 12. Verificar Puertos
```bash
# Verificar que los servicios estén escuchando
sudo ss -tulpn | grep :8000  # FastAPI
sudo ss -tulpn | grep :80    # Nginx
```

### 13. Probar la API
```bash
# Desde el servidor
curl http://localhost/balance
curl http://localhost/health

# Desde tu computadora local
curl http://158.69.113.159/balance
curl http://158.69.113.159/health
```

## 🔧 Scripts de Automatización

### 14. Usar Script de Setup Automático
Tu proyecto incluye un script que hace todo automáticamente:

```bash
# Hacer ejecutable
chmod +x setup_port_80.sh

# Ejecutar setup completo
sudo ./setup_port_80.sh
```

### 15. Script de Despliegue
Para actualizaciones futuras:

```bash
# Hacer ejecutable
chmod +x deploy.sh

# Ejecutar despliegue
./deploy.sh
```

## 📊 Monitoreo y Logs

### Ver Logs de la Aplicación
```bash
# Logs del servicio FastAPI
sudo journalctl -u api-electoral -f

# Logs de Nginx
sudo tail -f /var/log/nginx/api-electoral-access.log
sudo tail -f /var/log/nginx/api-electoral-error.log
```

### Comandos de Estado
```bash
# Estado de servicios
sudo systemctl status api-electoral nginx

# Reiniciar servicios
sudo systemctl restart api-electoral
sudo systemctl reload nginx

# Ver procesos
ps aux | grep uvicorn
ps aux | grep nginx
```

## 🔒 Configuración de Firewall (Opcional)

### 16. Configurar UFW
```bash
# Habilitar firewall
sudo ufw enable

# Permitir SSH
sudo ufw allow 22

# Permitir HTTP
sudo ufw allow 80

# Permitir HTTPS (para futuro)
sudo ufw allow 443

# Ver estado
sudo ufw status
```

## 🔐 Configuración SSH para GitHub Actions

### 17. Configurar Clave SSH
Si necesitas generar una nueva clave SSH:

```bash
# Generar clave SSH (en tu computadora local)
ssh-keygen -t rsa -b 4096 -C "tu-email@ejemplo.com"

# Copiar clave pública al servidor
ssh-copy-id ubuntu@158.69.113.159

# En GitHub, agregar la clave privada como secret VPS_SSH_KEY
```

## 📱 URLs de Acceso

Una vez configurado, tu API estará disponible en:

- **Documentación:** http://158.69.113.159/docs
- **Health Check:** http://158.69.113.159/health  
- **Balance 2Captcha:** http://158.69.113.159/balance
- **Consultar Nombres:** http://158.69.113.159/consultar-nombres
- **Consultar Puesto:** http://158.69.113.159/consultar-puesto-votacion

## 🚨 Solución de Problemas Comunes

### Error: "Permission denied"
```bash
sudo chown -R ubuntu:ubuntu /var/www/html/apielectoral
```

### Error: "externally-managed-environment"
```bash
cd /var/www/html/apielectoral
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "dubious ownership in repository"
```bash
git config --global --add safe.directory /var/www/html/apielectoral
```

### Servicio no inicia
```bash
# Ver logs detallados
sudo journalctl -u api-electoral -n 50

# Verificar archivo .env
cat .env

# Verificar permisos
ls -la /var/www/html/apielectoral/
```

### Nginx no funciona
```bash
# Verificar configuración
sudo nginx -t

# Ver logs de error
sudo tail -f /var/log/nginx/error.log

# Reiniciar nginx
sudo systemctl restart nginx
```

## 🔄 Proceso de Actualización

### Actualización Manual
```bash
cd /var/www/html/apielectoral
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart api-electoral
sudo systemctl reload nginx
```

### Actualización Automática (GitHub Actions)
El proyecto ya tiene configurado GitHub Actions. Solo necesitas:

1. Hacer push a la rama `main`
2. O ejecutar manualmente desde GitHub → Actions → "Deploy to VPS"

## 📋 Checklist de Configuración

- [ ] VPS actualizado
- [ ] Dependencias del sistema instaladas
- [ ] Directorio del proyecto creado
- [ ] Código clonado
- [ ] Archivo .env configurado
- [ ] Entorno virtual creado
- [ ] Dependencias Python instaladas
- [ ] Servicio systemd configurado
- [ ] Nginx configurado
- [ ] Servicios iniciados
- [ ] Puertos verificados
- [ ] API funcionando
- [ ] Logs monitoreados
- [ ] GitHub Actions configurado

## 🆘 Comandos de Emergencia

### Reinicio Completo
```bash
sudo systemctl restart api-electoral nginx
```

### Ver Todo el Estado
```bash
sudo systemctl status api-electoral nginx
sudo ss -tulpn | grep -E ':80|:8000'
curl -s http://localhost/health
```

### Logs en Tiempo Real
```bash
# Terminal 1: Logs de FastAPI
sudo journalctl -u api-electoral -f

# Terminal 2: Logs de Nginx
sudo tail -f /var/log/nginx/api-electoral-access.log
```

---

**¡Tu API Electoral estará funcionando en http://158.69.113.159 una vez completados estos pasos!**
