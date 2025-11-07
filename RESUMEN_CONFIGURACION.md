# 📋 Resumen de Configuración - Puerto 80

## ✅ Archivos Configurados

### 1. `nginx.conf`
- **Puerto:** 80 (HTTP)
- **Proxy a:** http://127.0.0.1:8000
- **Características:**
  - Timeouts extendidos (600s) para scrapers
  - Health check endpoint en `/health`
  - Configuración HTTPS comentada (lista para usar)
  - Logs en `/var/log/nginx/api-electoral-*.log`

### 2. `api-electoral.service`
- **Puerto:** 8000 (interno)
- **Workers:** 2
- **Usuario:** ubuntu
- **Directorio:** `/var/www/html/apielectoral`
- **Auto-restart:** Habilitado

### 3. `deploy.sh`
- Actualiza código desde git
- Instala dependencias
- Configura nginx automáticamente
- Reinicia servicios
- Verifica estado

### 4. `setup_port_80.sh` (NUEVO)
- Script de instalación desde cero
- Instala nginx si no existe
- Configura todo automáticamente
- Verifica que todo funcione

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                       Internet                          │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ HTTP (Puerto 80)
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                      Nginx                              │
│  - Reverse Proxy                                        │
│  - Timeouts: 600s                                       │
│  - Max body: 10M                                        │
│  - Logs: /var/log/nginx/api-electoral-*.log            │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ HTTP (Puerto 8000)
                         │ localhost only
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI (Uvicorn)                     │
│  - Workers: 2                                           │
│  - Host: 0.0.0.0:8000                                   │
│  - User: ubuntu                                         │
│  - Auto-restart: enabled                                │
│  - Logs: journalctl -u api-electoral                    │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Scrapers (Selenium/Chrome)                 │
│  - Registraduría (2captcha)                             │
│  - Procuraduría                                         │
│  - Policía                                              │
│  - Sisben                                               │
└─────────────────────────────────────────────────────────┘
```

---

## 🔌 Puertos Utilizados

| Puerto | Servicio | Acceso | Descripción |
|--------|----------|--------|-------------|
| **80** | Nginx | Público | Punto de entrada HTTP |
| **8000** | FastAPI | Localhost | API interna |
| ~~443~~ | ~~HTTPS~~ | ~~Público~~ | Comentado (para futuro) |

---

## 📂 Estructura de Archivos

```
/var/www/html/apielectoral/
├── api.py                      # Aplicación FastAPI
├── config.py                   # Configuración
├── requirements.txt            # Dependencias Python
├── .env                        # Variables de entorno
│
├── api-electoral.service       # Systemd service
├── nginx.conf                  # Configuración Nginx
│
├── deploy.sh                   # Script de deploy
├── setup_port_80.sh           # Script de instalación
│
├── models/                     # Modelos de datos
├── scrapper/                   # Scrapers
├── utils/                      # Utilidades
├── tasks/                      # Tareas en background
└── test/                       # Tests

/etc/systemd/system/
└── api-electoral.service       # Servicio systemd

/etc/nginx/
├── sites-available/
│   └── api-electoral          # Config nginx
└── sites-enabled/
    └── api-electoral          # Symlink
```

---

## 🚀 Comandos de Gestión

### Despliegue Inicial
```bash
cd /var/www/html/apielectoral
sudo ./setup_port_80.sh
```

### Actualizar Código
```bash
cd /var/www/html/apielectoral
./deploy.sh
```

### Gestión de Servicios
```bash
# Reiniciar FastAPI
sudo systemctl restart api-electoral

# Recargar Nginx (sin downtime)
sudo systemctl reload nginx

# Ver estado
sudo systemctl status api-electoral nginx

# Ver logs
sudo journalctl -u api-electoral -f
sudo tail -f /var/log/nginx/api-electoral-access.log
```

### Verificación
```bash
# Verificar puertos
sudo ss -tulpn | grep -E ':80|:8000'

# Test de conectividad
curl http://localhost/health
curl http://localhost/balance

# Ver procesos
ps aux | grep -E 'nginx|uvicorn'
```

---

## 🔒 Seguridad

### Firewall (UFW)
```bash
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (futuro)
sudo ufw allow 22/tcp    # SSH
sudo ufw enable
```

### Permisos
- Nginx corre como `www-data`
- FastAPI corre como `ubuntu`
- Archivos en `/var/www/html/apielectoral` propiedad de `ubuntu`

### Variables Sensibles
- API Key de 2captcha en `.env`
- `.env` no está en git (en `.gitignore`)
- Backup automático en `.env.backup`

---

## 📊 Monitoreo

### Logs de FastAPI
```bash
# Tiempo real
sudo journalctl -u api-electoral -f

# Últimas 100 líneas
sudo journalctl -u api-electoral -n 100

# Filtrar por fecha
sudo journalctl -u api-electoral --since "2024-01-01"
```

### Logs de Nginx
```bash
# Access log
sudo tail -f /var/log/nginx/api-electoral-access.log

# Error log
sudo tail -f /var/log/nginx/api-electoral-error.log

# Analizar errores
sudo grep "error" /var/log/nginx/api-electoral-error.log
```

### Métricas del Sistema
```bash
# CPU y memoria
htop

# Espacio en disco
df -h

# Procesos de Python
ps aux | grep python

# Conexiones activas
sudo netstat -tulpn | grep -E ':80|:8000'
```

---

## 🔄 Flujo de Actualización

1. **Desarrollador hace push a GitHub**
   ```bash
   git add .
   git commit -m "Update"
   git push origin main
   ```

2. **En el servidor VPS**
   ```bash
   cd /var/www/html/apielectoral
   ./deploy.sh
   ```

3. **El script automáticamente:**
   - Hace backup de `.env`
   - Hace `git pull`
   - Restaura `.env`
   - Instala dependencias
   - Actualiza configuración de nginx
   - Reinicia servicios
   - Verifica estado

---

## 🆘 Troubleshooting Rápido

### API no responde
```bash
# 1. Verificar servicios
sudo systemctl status api-electoral nginx

# 2. Reiniciar todo
sudo systemctl restart api-electoral nginx

# 3. Ver logs
sudo journalctl -u api-electoral -n 50
```

### Error 502 Bad Gateway
```bash
# FastAPI no está corriendo
sudo systemctl start api-electoral

# Verificar conectividad
curl http://127.0.0.1:8000/docs
```

### Puerto 80 en uso
```bash
# Ver qué lo usa
sudo ss -tulpn | grep :80

# Detener Apache si existe
sudo systemctl stop apache2
sudo systemctl disable apache2
```

---

## 📚 Documentación Relacionada

- **[QUICK_START_PORT_80.md](QUICK_START_PORT_80.md)** - Inicio rápido
- **[DEPLOY_PORT_80.md](DEPLOY_PORT_80.md)** - Guía completa de despliegue
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Arquitectura del proyecto

---

## ✅ Checklist Post-Despliegue

- [ ] Nginx instalado y corriendo en puerto 80
- [ ] FastAPI corriendo en puerto 8000
- [ ] Servicios habilitados para inicio automático
- [ ] API accesible desde navegador externo
- [ ] Endpoint `/docs` funciona
- [ ] Endpoint `/health` responde
- [ ] Endpoint `/balance` muestra saldo de 2captcha
- [ ] Logs funcionando correctamente
- [ ] Firewall configurado (puertos 80, 443, 22)
- [ ] `.env` con API key configurada
- [ ] Scripts de deploy tienen permisos de ejecución

---

## 🎯 Próximos Pasos (Opcional)

1. **Configurar HTTPS con Let's Encrypt**
   ```bash
   sudo certbot --nginx -d tu-dominio.com
   ```

2. **Configurar monitoreo con Prometheus/Grafana**

3. **Implementar rate limiting en Nginx**

4. **Configurar backups automáticos**

5. **Implementar CI/CD con GitHub Actions**

---

**Última actualización:** 2024
**Versión:** 1.0
