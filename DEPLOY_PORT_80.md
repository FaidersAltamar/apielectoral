# Despliegue de API en Puerto 80 con Nginx

## 📋 Resumen

La API FastAPI corre en el **puerto 8000** internamente, y **nginx** actúa como proxy reverso en el **puerto 80**.

## ⚙️ Arquitectura

```
Internet (Puerto 80) → Nginx → FastAPI (Puerto 8000)
```

### Ventajas de usar Nginx como Proxy Reverso:
- ✅ Mejor rendimiento y manejo de conexiones
- ✅ Fácil agregar SSL/HTTPS en el futuro
- ✅ Protección contra ataques DDoS
- ✅ Compresión gzip automática
- ✅ Balanceo de carga (si escalas)
- ✅ Servir múltiples aplicaciones en el mismo servidor

## 🚀 Pasos para Desplegar

### Paso 1: Copiar configuración de Nginx

```bash
# Copiar archivo de configuración
sudo cp /var/www/html/apielectoral/nginx.conf /etc/nginx/sites-available/api-electoral

# Crear enlace simbólico
sudo ln -sf /etc/nginx/sites-available/api-electoral /etc/nginx/sites-enabled/

# Eliminar configuración default si existe
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t
```

### Paso 2: Configurar el servicio de FastAPI

```bash
# Copiar archivo de servicio
sudo cp /var/www/html/apielectoral/api-electoral.service /etc/systemd/system/

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicio para que inicie automáticamente
sudo systemctl enable api-electoral
```

### Paso 3: Iniciar servicios

```bash
# Iniciar FastAPI
sudo systemctl start api-electoral

# Reiniciar Nginx
sudo systemctl restart nginx
```

### Paso 4: Verificar estado

```bash
# Verificar FastAPI
sudo systemctl status api-electoral

# Verificar Nginx
sudo systemctl status nginx
```

## 🔍 Verificación

### 1. Verificar que FastAPI está corriendo en puerto 8000:
```bash
sudo systemctl status api-electoral
sudo ss -tulpn | grep :8000
```

### 2. Verificar que Nginx está en puerto 80:
```bash
sudo systemctl status nginx
sudo ss -tulpn | grep :80
```

### 3. Probar la API desde el navegador:
```bash
# Documentación interactiva
http://tu-servidor-ip/docs

# Health check
curl http://localhost/health

# Balance de 2captcha
curl http://localhost/balance
```

### 4. Ver logs en tiempo real:
```bash
# Logs de FastAPI
sudo journalctl -u api-electoral -f

# Logs de Nginx
sudo tail -f /var/log/nginx/api-electoral-access.log
sudo tail -f /var/log/nginx/api-electoral-error.log
```

## 🔒 Agregar HTTPS con Let's Encrypt (Recomendado para Producción)

### Paso 1: Instalar Certbot

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx -y
```

### Paso 2: Obtener certificado SSL

```bash
# Reemplaza tu-dominio.com con tu dominio real
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

### Paso 3: Actualizar nginx.conf

Descomentar la sección HTTPS en `nginx.conf` y actualizar con tu dominio:

```bash
# Editar nginx.conf
sudo nano /etc/nginx/sites-available/api-electoral

# Descomentar las líneas de HTTPS (líneas 40-77)
# Reemplazar "your-domain.com" con tu dominio real
```

### Paso 4: Reiniciar Nginx

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Paso 5: Verificar renovación automática

```bash
# Certbot configura renovación automática
sudo certbot renew --dry-run
```

## 📝 Logs

Ver logs del servicio:
```bash
# Últimas 50 líneas
sudo journalctl -u api-electoral -n 50

# Seguir logs en tiempo real
sudo journalctl -u api-electoral -f
```

## 🆘 Troubleshooting

### Error: "Address already in use" en puerto 80
```bash
# Ver qué está usando el puerto 80
sudo ss -tulpn | grep :80
sudo lsof -i :80

# Si hay otro servicio, detenerlo
sudo systemctl stop apache2  # Si tienes Apache
sudo systemctl stop nginx    # Para reiniciar nginx
sudo systemctl start nginx
```

### Error: "Address already in use" en puerto 8000
```bash
# Ver qué está usando el puerto 8000
sudo ss -tulpn | grep :8000

# Detener el servicio de FastAPI
sudo systemctl stop api-electoral
sudo systemctl start api-electoral
```

### El servicio FastAPI no inicia
```bash
# Ver logs detallados
sudo journalctl -u api-electoral -n 100 --no-pager

# Verificar permisos
ls -la /var/www/html/apielectoral/

# Verificar archivo de servicio
sudo systemctl cat api-electoral

# Verificar que el entorno virtual existe
ls -la /var/www/html/apielectoral/venv/

# Verificar que uvicorn está instalado
/var/www/html/apielectoral/venv/bin/uvicorn --version
```

### Nginx retorna 502 Bad Gateway
```bash
# Verificar que FastAPI está corriendo
sudo systemctl status api-electoral

# Verificar conectividad local
curl http://127.0.0.1:8000/docs

# Ver logs de nginx
sudo tail -f /var/log/nginx/api-electoral-error.log
```

### Nginx no inicia
```bash
# Verificar sintaxis de configuración
sudo nginx -t

# Ver logs de nginx
sudo journalctl -u nginx -n 50

# Verificar que el archivo de configuración existe
ls -la /etc/nginx/sites-enabled/api-electoral
```

### Cambios no se reflejan
```bash
# Reiniciar ambos servicios
sudo systemctl restart api-electoral
sudo systemctl reload nginx

# Limpiar cache del navegador o usar modo incógnito
```

## 🔄 Comandos Útiles

### Reiniciar servicios
```bash
# Reiniciar solo FastAPI
sudo systemctl restart api-electoral

# Reiniciar solo Nginx (sin downtime)
sudo systemctl reload nginx

# Reiniciar Nginx (con downtime)
sudo systemctl restart nginx

# Reiniciar ambos
sudo systemctl restart api-electoral nginx
```

### Ver estado de servicios
```bash
# Estado de FastAPI
sudo systemctl status api-electoral

# Estado de Nginx
sudo systemctl status nginx

# Ver todos los servicios activos
sudo systemctl list-units --type=service --state=running
```

### Habilitar/Deshabilitar inicio automático
```bash
# Habilitar inicio automático
sudo systemctl enable api-electoral
sudo systemctl enable nginx

# Deshabilitar inicio automático
sudo systemctl disable api-electoral
sudo systemctl disable nginx
```
