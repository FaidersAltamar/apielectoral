# 🚀 Guía Completa de Deployment - De Cero a Producción

Esta guía te lleva desde un servidor vacío hasta una API completamente funcional con HTTPS.

---

## 📋 Índice

1. [Prerequisitos](#prerequisitos)
2. [Fase 1: Setup Inicial del Servidor](#fase-1-setup-inicial-del-servidor)
3. [Fase 2: Despliegue en Puerto 80](#fase-2-despliegue-en-puerto-80)
4. [Fase 3: Configuración HTTPS](#fase-3-configuración-https)
5. [Fase 4: Verificación y Monitoreo](#fase-4-verificación-y-monitoreo)
6. [Mantenimiento](#mantenimiento)

---

## Prerequisitos

### Lo que necesitas:

- ✅ **VPS/Servidor** con Ubuntu 20.04+ (mínimo 2GB RAM)
- ✅ **Dominio** propio (para HTTPS)
- ✅ **Acceso SSH** al servidor
- ✅ **API Key de 2captcha** (para scrapers)
- ✅ **Conocimientos básicos** de Linux/terminal

### Costos estimados:

- VPS: $5-10/mes (DigitalOcean, Linode, Vultr)
- Dominio: $10-15/año (Namecheap, GoDaddy)
- 2captcha: Variable según uso
- **Total:** ~$7-12/mes

---

## Fase 1: Setup Inicial del Servidor

### Tiempo estimado: 15-20 minutos

### 1.1 Conectar al Servidor

```bash
# Desde tu computadora local
ssh root@TU_IP_DEL_SERVIDOR

# O si tienes usuario específico
ssh ubuntu@TU_IP_DEL_SERVIDOR
```

### 1.2 Actualizar Sistema

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.3 Instalar Dependencias Base

```bash
# Python y herramientas
sudo apt install -y python3 python3-pip python3-venv git

# Nginx
sudo apt install -y nginx

# Herramientas útiles
sudo apt install -y curl wget htop
```

### 1.4 Configurar Firewall

```bash
# Instalar UFW si no está
sudo apt install -y ufw

# Configurar reglas
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# Habilitar firewall
sudo ufw enable

# Verificar
sudo ufw status
```

### 1.5 Clonar Repositorio

```bash
# Crear directorio
sudo mkdir -p /var/www/html
cd /var/www/html

# Clonar (reemplaza con tu repo)
sudo git clone https://github.com/TU_USUARIO/api_electroral.git apielectoral

# Cambiar permisos
sudo chown -R $USER:$USER /var/www/html/apielectoral
cd apielectoral
```

### 1.6 Configurar Variables de Entorno

```bash
# Crear archivo .env
nano .env
```

Contenido del `.env`:
```bash
APIKEY_2CAPTCHA=tu_api_key_aqui
EXTERNAL_API_NOMBRE_URL=https://tu-api-externa.com/nombre
EXTERNAL_API_PUESTO_URL=https://tu-api-externa.com/puesto
```

Guardar: `Ctrl+O`, `Enter`, `Ctrl+X`

### 1.7 Instalar Dependencias de Chrome

```bash
# Ejecutar script de instalación
chmod +x install_chrome_dependencies.sh
sudo ./install_chrome_dependencies.sh
```

✅ **Fase 1 Completada!**

---

## Fase 2: Despliegue en Puerto 80

### Tiempo estimado: 5-10 minutos

### 2.1 Ejecutar Script de Setup

```bash
cd /var/www/html/apielectoral
chmod +x setup_port_80.sh
sudo ./setup_port_80.sh
```

El script automáticamente:
- ✅ Instala Nginx
- ✅ Crea entorno virtual Python
- ✅ Instala dependencias
- ✅ Configura servicio systemd
- ✅ Inicia servicios

### 2.2 Verificar Instalación

```bash
# Verificar servicios
sudo systemctl status api-electoral
sudo systemctl status nginx

# Verificar puertos
sudo ss -tulpn | grep -E ':80|:8000'

# Test de conectividad
curl http://localhost/health
```

### 2.3 Acceder desde Navegador

Abre tu navegador y visita:
```
http://TU_IP_DEL_SERVIDOR/docs
```

Deberías ver la documentación interactiva de FastAPI.

✅ **Fase 2 Completada!** Tu API está funcionando en HTTP.

---

## Fase 3: Configuración HTTPS

### Tiempo estimado: 10-15 minutos

### 3.1 Configurar DNS

**En tu proveedor de dominio** (GoDaddy, Namecheap, etc.):

1. Ve a la sección de DNS
2. Crea un registro A:
   ```
   Tipo: A
   Nombre: @ (o tu dominio)
   Valor: TU_IP_DEL_SERVIDOR
   TTL: 3600
   ```
3. (Opcional) Para www:
   ```
   Tipo: A
   Nombre: www
   Valor: TU_IP_DEL_SERVIDOR
   TTL: 3600
   ```

### 3.2 Esperar Propagación DNS

```bash
# Verificar cada 2-3 minutos
dig +short tudominio.com

# Debe mostrar tu IP del servidor
# Si no, espera 5-10 minutos más
```

### 3.3 Ejecutar Script de HTTPS

```bash
cd /var/www/html/apielectoral
chmod +x setup_https.sh
sudo ./setup_https.sh
```

El script te pedirá:
- **Dominio:** `miapi.com`
- **¿Incluir www?** `y` o `n`
- **Email:** `tu@email.com`

El script automáticamente:
- ✅ Instala Certbot
- ✅ Obtiene certificado SSL
- ✅ Configura Nginx para HTTPS
- ✅ Configura renovación automática
- ✅ Configura redirección HTTP → HTTPS

### 3.4 Verificar HTTPS

```bash
# Test desde servidor
curl https://tudominio.com/health

# Ver certificado
sudo certbot certificates

# Test de renovación
sudo certbot renew --dry-run
```

### 3.5 Acceder desde Navegador

Abre tu navegador:
```
https://tudominio.com/docs
```

Verifica:
- ✅ Candado 🔒 en la barra de direcciones
- ✅ Certificado válido
- ✅ HTTP redirige a HTTPS

✅ **Fase 3 Completada!** Tu API ahora tiene HTTPS.

---

## Fase 4: Verificación y Monitoreo

### Tiempo estimado: 5 minutos

### 4.1 Ejecutar Script de Verificación

```bash
cd /var/www/html/apielectoral
chmod +x VERIFICACION.sh
./VERIFICACION.sh
```

Este script verifica:
- ✅ Servicios corriendo
- ✅ Puertos abiertos
- ✅ Configuración correcta
- ✅ Conectividad
- ✅ Logs funcionando

### 4.2 Test de Endpoints

```bash
# Health check
curl https://tudominio.com/health

# Balance de 2captcha
curl https://tudominio.com/balance

# Documentación
curl -I https://tudominio.com/docs
```

### 4.3 Test SSL

Visita: https://www.ssllabs.com/ssltest/

Ingresa tu dominio y espera el análisis.

**Objetivo:** Grado **A** o **A+**

### 4.4 Configurar Monitoreo (Opcional)

```bash
# Ver logs en tiempo real
sudo journalctl -u api-electoral -f

# En otra terminal
sudo tail -f /var/log/nginx/api-electoral-access.log
```

✅ **Fase 4 Completada!** Todo verificado y funcionando.

---

## Mantenimiento

### Actualizar Código

```bash
cd /var/www/html/apielectoral
./deploy.sh
```

### Ver Logs

```bash
# FastAPI
sudo journalctl -u api-electoral -n 100

# Nginx
sudo tail -100 /var/log/nginx/api-electoral-error.log
```

### Reiniciar Servicios

```bash
# FastAPI
sudo systemctl restart api-electoral

# Nginx
sudo systemctl reload nginx

# Ambos
sudo systemctl restart api-electoral nginx
```

### Verificar Certificado SSL

```bash
# Ver certificados
sudo certbot certificates

# Test de renovación
sudo certbot renew --dry-run

# Renovar manualmente (si es necesario)
sudo certbot renew
```

### Backup

```bash
# Backup de .env
cp .env .env.backup

# Backup de certificados
sudo tar -czf letsencrypt-backup.tar.gz /etc/letsencrypt/

# Backup de código
git add .
git commit -m "Backup"
git push
```

---

## 📊 Resumen de Comandos Importantes

### Gestión de Servicios
```bash
sudo systemctl status api-electoral nginx    # Ver estado
sudo systemctl restart api-electoral         # Reiniciar FastAPI
sudo systemctl reload nginx                  # Recargar Nginx
sudo systemctl stop api-electoral            # Detener FastAPI
sudo systemctl start api-electoral           # Iniciar FastAPI
```

### Logs
```bash
sudo journalctl -u api-electoral -f          # Logs FastAPI (tiempo real)
sudo tail -f /var/log/nginx/api-electoral-access.log  # Logs Nginx
sudo journalctl -u certbot.timer             # Logs renovación SSL
```

### Verificación
```bash
./VERIFICACION.sh                            # Script de verificación completo
sudo ss -tulpn | grep -E ':80|:443|:8000'   # Ver puertos
curl https://tudominio.com/health            # Test endpoint
sudo certbot certificates                    # Ver certificados SSL
```

### Deployment
```bash
./deploy.sh                                  # Actualizar aplicación
git pull                                     # Actualizar código
sudo systemctl restart api-electoral nginx   # Reiniciar servicios
```

---

## 🆘 Troubleshooting Rápido

### API no responde
```bash
sudo systemctl status api-electoral
sudo journalctl -u api-electoral -n 50
sudo systemctl restart api-electoral
```

### Error 502 Bad Gateway
```bash
# FastAPI no está corriendo
sudo systemctl start api-electoral
curl http://127.0.0.1:8000/docs
```

### HTTPS no funciona
```bash
# Verificar certificado
sudo certbot certificates

# Verificar Nginx
sudo nginx -t
sudo systemctl status nginx

# Ver logs
sudo tail -50 /var/log/nginx/api-electoral-error.log
```

### Certificado expirado
```bash
# Renovar manualmente
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```

---

## 📚 Documentación Completa

| Documento | Descripción |
|-----------|-------------|
| [HTTPS_QUICK_START.md](HTTPS_QUICK_START.md) | Setup HTTPS rápido |
| [CONFIGURACION_HTTPS.md](CONFIGURACION_HTTPS.md) | Guía completa HTTPS |
| [DEPLOY_PORT_80.md](DEPLOY_PORT_80.md) | Despliegue puerto 80 |
| [RESUMEN_CONFIGURACION.md](RESUMEN_CONFIGURACION.md) | Resumen técnico |
| [RESUMEN_HTTPS.md](RESUMEN_HTTPS.md) | Resumen HTTPS |

---

## ✅ Checklist Final

### Setup Inicial
- [ ] Servidor actualizado
- [ ] Firewall configurado
- [ ] Repositorio clonado
- [ ] Variables de entorno configuradas
- [ ] Dependencias de Chrome instaladas

### Puerto 80
- [ ] Nginx instalado
- [ ] FastAPI corriendo en puerto 8000
- [ ] Nginx proxy en puerto 80
- [ ] API accesible desde navegador

### HTTPS
- [ ] Dominio configurado (DNS)
- [ ] Certificado SSL instalado
- [ ] HTTPS funcionando
- [ ] HTTP redirige a HTTPS
- [ ] Renovación automática configurada

### Verificación
- [ ] Todos los servicios activos
- [ ] Endpoints funcionando
- [ ] SSL Labs: Grado A o A+
- [ ] Logs funcionando
- [ ] Monitoreo configurado

### Documentación
- [ ] URLs actualizadas
- [ ] README actualizado
- [ ] Usuarios notificados
- [ ] Backup configurado

---

## 🎉 ¡Felicidades!

Tu API Electoral está completamente desplegada y funcionando en producción con HTTPS.

### URLs Finales:
- 📖 **Documentación:** `https://tudominio.com/docs`
- 🏥 **Health Check:** `https://tudominio.com/health`
- 💰 **Balance:** `https://tudominio.com/balance`

### Próximos Pasos Opcionales:
1. Configurar CDN (Cloudflare)
2. Implementar rate limiting
3. Configurar monitoreo avanzado
4. Automatizar backups
5. Implementar CI/CD

---

**¿Necesitas ayuda?** Consulta la documentación específica o abre un issue en GitHub.

**Última actualización:** 2024  
**Versión:** 1.0
