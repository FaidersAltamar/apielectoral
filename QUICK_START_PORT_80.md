# 🚀 Quick Start - Puerto 80

## ⚡ Configuración Rápida (5 minutos)

### Opción 1: Script Automático (Recomendado)

```bash
# En tu VPS, ejecuta:
cd /var/www/html/apielectoral
chmod +x setup_port_80.sh
sudo ./setup_port_80.sh
```

✅ **Listo!** Tu API estará corriendo en el puerto 80.

---

### Opción 2: Comandos Manuales

```bash
# 1. Instalar Nginx
sudo apt update && sudo apt install nginx -y

# 2. Copiar configuración de Nginx
sudo cp /var/www/html/apielectoral/nginx.conf /etc/nginx/sites-available/api-electoral
sudo ln -sf /etc/nginx/sites-available/api-electoral /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 3. Verificar configuración
sudo nginx -t

# 4. Configurar servicio de FastAPI
sudo cp /var/www/html/apielectoral/api-electoral.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable api-electoral

# 5. Iniciar servicios
sudo systemctl start api-electoral
sudo systemctl restart nginx
```

---

## 🔍 Verificar que todo funciona

```bash
# Ver estado de servicios
sudo systemctl status api-electoral nginx

# Verificar puertos
sudo ss -tulpn | grep -E ':80|:8000'

# Probar la API
curl http://localhost/health
curl http://localhost/balance
```

---

## 📡 Acceder a tu API

Abre tu navegador y visita:

- **Documentación:** `http://TU-IP-DEL-VPS/docs`
- **Health Check:** `http://TU-IP-DEL-VPS/health`
- **Balance 2Captcha:** `http://TU-IP-DEL-VPS/balance`

---

## 🏗️ Arquitectura

```
┌─────────────┐
│   Internet  │
└──────┬──────┘
       │ Puerto 80
       ▼
┌─────────────┐
│    Nginx    │ (Proxy Reverso)
└──────┬──────┘
       │ Puerto 8000
       ▼
┌─────────────┐
│   FastAPI   │ (Tu aplicación)
└─────────────┘
```

---

## 🔧 Comandos Útiles

### Reiniciar servicios
```bash
sudo systemctl restart api-electoral  # Reiniciar FastAPI
sudo systemctl reload nginx           # Recargar Nginx (sin downtime)
```

### Ver logs
```bash
sudo journalctl -u api-electoral -f                    # Logs de FastAPI
sudo tail -f /var/log/nginx/api-electoral-access.log  # Logs de Nginx
```

### Detener servicios
```bash
sudo systemctl stop api-electoral
sudo systemctl stop nginx
```

---

## 🆘 Problemas Comunes

### Error: Puerto 80 en uso
```bash
# Ver qué está usando el puerto
sudo ss -tulpn | grep :80

# Si es Apache, detenerlo
sudo systemctl stop apache2
sudo systemctl disable apache2
```

### Error 502 Bad Gateway
```bash
# Verificar que FastAPI está corriendo
sudo systemctl status api-electoral

# Reiniciar ambos servicios
sudo systemctl restart api-electoral
sudo systemctl reload nginx
```

### Cambios no se reflejan
```bash
# Hacer pull del código
cd /var/www/html/apielectoral
git pull

# Reiniciar servicios
sudo systemctl restart api-electoral
sudo systemctl reload nginx
```

---

## 🔒 Agregar HTTPS (Opcional)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtener certificado SSL (reemplaza con tu dominio)
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Certbot configurará automáticamente HTTPS
```

---

## 📚 Más Información

- **Guía completa:** [DEPLOY_PORT_80.md](DEPLOY_PORT_80.md)
- **Troubleshooting:** Ver sección de problemas en DEPLOY_PORT_80.md
- **Arquitectura:** [ARCHITECTURE.md](ARCHITECTURE.md)

---

## ✅ Checklist de Despliegue

- [ ] Nginx instalado y corriendo
- [ ] FastAPI corriendo en puerto 8000
- [ ] Nginx configurado como proxy en puerto 80
- [ ] Servicios habilitados para inicio automático
- [ ] API accesible desde el navegador
- [ ] Logs funcionando correctamente
- [ ] (Opcional) HTTPS configurado con Let's Encrypt
