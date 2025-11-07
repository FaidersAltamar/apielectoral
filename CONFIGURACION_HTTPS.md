# 🔒 Configuración HTTPS con Let's Encrypt

Guía completa para agregar HTTPS (SSL/TLS) a tu API Electoral usando Let's Encrypt y Certbot.

---

## 📋 Prerequisitos

Antes de comenzar, asegúrate de tener:

- ✅ Un **dominio** propio (ejemplo: `miapi.com`)
- ✅ El dominio debe **apuntar a tu servidor** (registro DNS tipo A)
- ✅ **Puerto 80 y 443** abiertos en el firewall
- ✅ **Nginx** instalado y funcionando
- ✅ **API corriendo** en puerto 8000

---

## 🚀 Opción 1: Script Automático (Recomendado)

### Paso 1: Configurar DNS

Antes de ejecutar el script, configura tu dominio:

1. Ve a tu proveedor de dominio (GoDaddy, Namecheap, Cloudflare, etc.)
2. Crea un registro **A** que apunte a la IP de tu servidor:

```
Tipo: A
Nombre: @ (o tu dominio)
Valor: TU_IP_DEL_SERVIDOR
TTL: 3600 (o automático)
```

3. Si quieres incluir `www`, crea otro registro A:

```
Tipo: A
Nombre: www
Valor: TU_IP_DEL_SERVIDOR
TTL: 3600
```

4. Espera 5-10 minutos para que se propague el DNS

### Paso 2: Verificar DNS

```bash
# Verificar que el dominio apunta a tu servidor
dig +short tudominio.com

# Debe mostrar la IP de tu servidor
```

### Paso 3: Ejecutar Script

```bash
cd /var/www/html/apielectoral
chmod +x setup_https.sh
sudo ./setup_https.sh
```

El script te pedirá:
- Tu dominio (ejemplo: `miapi.com`)
- Si quieres incluir `www`
- Tu email (para notificaciones de Let's Encrypt)

**¡Listo!** En 2-3 minutos tendrás HTTPS configurado.

---

## 🔧 Opción 2: Configuración Manual

### Paso 1: Instalar Certbot

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx -y
```

### Paso 2: Actualizar Nginx

Edita tu configuración de nginx para incluir tu dominio:

```bash
sudo nano /etc/nginx/sites-available/api-electoral
```

Cambia la línea `server_name`:

```nginx
server {
    listen 80;
    server_name tudominio.com www.tudominio.com;  # ← Cambia esto
    
    # ... resto de la configuración
}
```

Verifica y recarga:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Paso 3: Obtener Certificado SSL

```bash
# Para un solo dominio
sudo certbot --nginx -d tudominio.com

# Para dominio con www
sudo certbot --nginx -d tudominio.com -d www.tudominio.com
```

Certbot te preguntará:
1. **Email:** Para notificaciones importantes
2. **Términos:** Acepta los términos de servicio (A)
3. **Redirección:** Elige opción 2 (redirigir HTTP a HTTPS)

### Paso 4: Verificar

```bash
# Ver certificados instalados
sudo certbot certificates

# Probar renovación
sudo certbot renew --dry-run
```

---

## 🔍 Verificación

### 1. Verificar que HTTPS funciona

```bash
# Desde el servidor
curl https://tudominio.com/health

# Verificar redirección HTTP -> HTTPS
curl -I http://tudominio.com
# Debe retornar: HTTP/1.1 301 Moved Permanently
```

### 2. Desde el navegador

Visita:
- `https://tudominio.com/docs` - Documentación
- `https://tudominio.com/health` - Health check
- `https://tudominio.com/balance` - Balance

Verifica que:
- ✅ El candado 🔒 aparece en la barra de direcciones
- ✅ El certificado es válido
- ✅ HTTP redirige automáticamente a HTTPS

### 3. Verificar configuración SSL

Usa herramientas online:
- **SSL Labs:** https://www.ssllabs.com/ssltest/
- **SSL Checker:** https://www.sslshopper.com/ssl-checker.html

---

## 🔄 Renovación Automática

Let's Encrypt emite certificados válidos por **90 días**. Certbot configura renovación automática.

### Verificar renovación automática

```bash
# Ver timer de systemd
sudo systemctl list-timers | grep certbot

# O verificar cron
sudo cat /etc/cron.d/certbot
```

### Probar renovación

```bash
# Dry run (no renueva realmente)
sudo certbot renew --dry-run

# Renovar manualmente (solo si faltan <30 días)
sudo certbot renew
```

### Forzar renovación

```bash
# Solo si necesitas renovar antes de tiempo
sudo certbot renew --force-renewal
```

---

## 📁 Archivos Importantes

### Certificados

```
/etc/letsencrypt/
├── live/
│   └── tudominio.com/
│       ├── fullchain.pem    # Certificado completo
│       ├── privkey.pem      # Clave privada
│       ├── cert.pem         # Certificado del dominio
│       └── chain.pem        # Cadena de certificados
├── renewal/
│   └── tudominio.com.conf   # Configuración de renovación
└── archive/                 # Versiones anteriores
```

### Configuración de Nginx

```bash
# Ver configuración actual
sudo cat /etc/nginx/sites-available/api-electoral

# Nginx usa estos archivos automáticamente después de certbot
```

---

## 🔥 Configuración de Firewall

### UFW (Ubuntu Firewall)

```bash
# Permitir HTTPS
sudo ufw allow 443/tcp comment 'HTTPS'

# Permitir HTTP (para renovación y redirección)
sudo ufw allow 80/tcp comment 'HTTP'

# Verificar reglas
sudo ufw status
```

### Firewalld (CentOS/RHEL)

```bash
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

### iptables

```bash
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables-save
```

---

## 🛠️ Configuración Avanzada de Nginx

### Mejorar seguridad SSL

Edita `/etc/nginx/sites-available/api-electoral`:

```nginx
server {
    listen 443 ssl http2;
    server_name tudominio.com www.tudominio.com;

    # Certificados (Certbot los configura automáticamente)
    ssl_certificate /etc/letsencrypt/live/tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tudominio.com/privkey.pem;
    
    # Configuración SSL moderna (A+ en SSL Labs)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    
    # HSTS (HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Otros headers de seguridad
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/tudominio.com/chain.pem;
    
    # Resto de la configuración...
    location / {
        proxy_pass http://127.0.0.1:8000;
        # ...
    }
}

# Redirección HTTP -> HTTPS
server {
    listen 80;
    server_name tudominio.com www.tudominio.com;
    return 301 https://$server_name$request_uri;
}
```

Aplicar cambios:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🆘 Troubleshooting

### Error: "too many certificates already issued"

Let's Encrypt tiene límite de **50 certificados por dominio por semana**.

**Solución:**
- Espera una semana
- Usa el staging server para pruebas:
  ```bash
  sudo certbot --nginx --staging -d tudominio.com
  ```

### Error: "DNS problem: NXDOMAIN"

El dominio no resuelve o no apunta al servidor.

**Solución:**
```bash
# Verificar DNS
dig +short tudominio.com

# Debe mostrar la IP de tu servidor
# Si no, actualiza tu DNS y espera 5-10 minutos
```

### Error: "Connection refused" o "Timeout"

Puerto 80 no es accesible desde internet.

**Solución:**
```bash
# Verificar que nginx escucha en puerto 80
sudo ss -tulpn | grep :80

# Verificar firewall
sudo ufw status

# Permitir puerto 80
sudo ufw allow 80/tcp
```

### Error: "Cert is about to expire"

El certificado está por vencer y la renovación automática falló.

**Solución:**
```bash
# Renovar manualmente
sudo certbot renew --force-renewal

# Ver logs
sudo journalctl -u certbot.timer
sudo cat /var/log/letsencrypt/letsencrypt.log
```

### Certificado no se renueva automáticamente

**Solución:**
```bash
# Verificar timer de systemd
sudo systemctl status certbot.timer
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# O agregar cron job manualmente
echo "0 0,12 * * * root certbot renew --quiet" | sudo tee -a /etc/crontab
```

### Error 502 después de configurar HTTPS

FastAPI no está corriendo.

**Solución:**
```bash
sudo systemctl status api-electoral
sudo systemctl restart api-electoral
```

---

## 📊 Monitoreo del Certificado

### Ver información del certificado

```bash
# Usando certbot
sudo certbot certificates

# Usando openssl
echo | openssl s_client -servername tudominio.com -connect tudominio.com:443 2>/dev/null | openssl x509 -noout -dates

# Ver días restantes
echo | openssl s_client -servername tudominio.com -connect tudominio.com:443 2>/dev/null | openssl x509 -noout -enddate
```

### Script de monitoreo

Crea `/usr/local/bin/check-ssl-expiry.sh`:

```bash
#!/bin/bash
DOMAIN="tudominio.com"
DAYS_WARN=30

EXPIRY_DATE=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

if [ $DAYS_LEFT -lt $DAYS_WARN ]; then
    echo "⚠️  Certificado SSL expira en $DAYS_LEFT días!"
    # Aquí puedes agregar notificación por email o Slack
else
    echo "✅ Certificado SSL válido por $DAYS_LEFT días"
fi
```

---

## 🔐 Mejores Prácticas

### 1. Usa HSTS

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### 2. Redirige todo a HTTPS

```nginx
server {
    listen 80;
    server_name tudominio.com www.tudominio.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. Usa HTTP/2

```nginx
listen 443 ssl http2;
```

### 4. Configura OCSP Stapling

```nginx
ssl_stapling on;
ssl_stapling_verify on;
```

### 5. Monitorea la expiración

- Configura alertas 30 días antes
- Verifica logs de renovación regularmente
- Usa servicios como UptimeRobot o StatusCake

---

## 📚 Recursos Adicionales

- **Let's Encrypt:** https://letsencrypt.org/
- **Certbot:** https://certbot.eff.org/
- **SSL Labs Test:** https://www.ssllabs.com/ssltest/
- **Mozilla SSL Config:** https://ssl-config.mozilla.org/

---

## ✅ Checklist Post-HTTPS

- [ ] Certificado SSL instalado
- [ ] HTTPS funciona en el navegador
- [ ] HTTP redirige a HTTPS
- [ ] Renovación automática configurada
- [ ] Test de renovación exitoso (`certbot renew --dry-run`)
- [ ] Firewall permite puerto 443
- [ ] Headers de seguridad configurados
- [ ] Calificación A o A+ en SSL Labs
- [ ] Monitoreo de expiración configurado
- [ ] Documentación actualizada con nueva URL

---

## 🎯 Próximos Pasos

1. **Actualizar URLs en tu aplicación**
   - Cambiar `http://` por `https://` en configuraciones
   - Actualizar documentación

2. **Configurar CDN (Opcional)**
   - Cloudflare
   - AWS CloudFront

3. **Implementar rate limiting**
   - Proteger contra ataques DDoS

4. **Backup de certificados**
   - Respaldar `/etc/letsencrypt/`

---

**Última actualización:** 2024  
**Versión:** 1.0
