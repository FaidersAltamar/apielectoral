# 🔒 Resumen: Configuración HTTPS Completa

## ✅ Lo que se ha configurado

### 📁 Archivos Creados

1. **`setup_https.sh`** - Script automático de configuración HTTPS
   - Instala Certbot
   - Configura certificado SSL
   - Actualiza Nginx automáticamente
   - Configura renovación automática

2. **`CONFIGURACION_HTTPS.md`** - Guía completa de HTTPS
   - Configuración manual paso a paso
   - Troubleshooting extensivo
   - Mejores prácticas de seguridad
   - Monitoreo y mantenimiento

3. **`HTTPS_QUICK_START.md`** - Guía rápida de 5 minutos
   - Setup express
   - Comandos esenciales
   - Verificación rápida

---

## 🏗️ Arquitectura Final con HTTPS

```
┌──────────────────────────────────────────────────────────┐
│                      Internet                            │
└────────────────────────┬─────────────────────────────────┘
                         │
                         │ HTTPS (Puerto 443) 🔒
                         │ HTTP  (Puerto 80)  → Redirige a HTTPS
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                 Nginx + SSL/TLS                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Let's Encrypt Certificate                         │  │
│  │  • Válido por 90 días                              │  │
│  │  • Renovación automática cada 60 días             │  │
│  │  • TLS 1.2 y 1.3                                   │  │
│  │  • HSTS habilitado                                 │  │
│  │  • Headers de seguridad                            │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Proxy Reverso:                                          │
│  • Timeouts: 600s                                        │
│  • Max body: 10M                                         │
│  • HTTP/2 enabled                                        │
│  • Logs: /var/log/nginx/                                │
└────────────────────────┬─────────────────────────────────┘
                         │
                         │ HTTP (Puerto 8000)
                         │ localhost only
                         ▼
┌──────────────────────────────────────────────────────────┐
│              FastAPI (Uvicorn)                           │
│  • Workers: 2                                            │
│  • Host: 0.0.0.0:8000                                    │
│  • User: ubuntu                                          │
│  • Auto-restart: enabled                                 │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│           Scrapers (Selenium/Chrome)                     │
│  • Registraduría • Procuraduría • Policía • Sisben       │
└──────────────────────────────────────────────────────────┘
```

---

## 🚀 Cómo Implementar HTTPS

### Opción 1: Script Automático (Recomendado) ⚡

```bash
# 1. Configurar DNS (en tu proveedor de dominio)
#    Crear registro A: tudominio.com → IP_DEL_SERVIDOR
#    Esperar 5-10 minutos

# 2. Verificar DNS
dig +short tudominio.com

# 3. Ejecutar script
cd /var/www/html/apielectoral
chmod +x setup_https.sh
sudo ./setup_https.sh

# El script te pedirá:
# - Dominio: miapi.com
# - ¿Incluir www? y/n
# - Email: tu@email.com

# 4. ¡Listo! Tu API ahora está en HTTPS
```

### Opción 2: Manual

Ver guía completa en [CONFIGURACION_HTTPS.md](CONFIGURACION_HTTPS.md)

---

## 🔐 Características de Seguridad

### ✅ Implementadas Automáticamente

- **SSL/TLS:** Certificado válido de Let's Encrypt
- **Protocolos:** TLS 1.2 y TLS 1.3 únicamente
- **HSTS:** HTTP Strict Transport Security habilitado
- **Redirección:** HTTP → HTTPS automática
- **Headers de Seguridad:**
  - `X-Frame-Options: SAMEORIGIN`
  - `X-Content-Type-Options: nosniff`
  - `X-XSS-Protection: 1; mode=block`
- **HTTP/2:** Habilitado para mejor rendimiento
- **Renovación Automática:** Cada 60 días

### 🎯 Calificación SSL Labs

**Objetivo:** Grado **A** o **A+**

Verifica en: https://www.ssllabs.com/ssltest/

---

## 📊 Puertos y Servicios

| Puerto | Servicio | Acceso | Protocolo | Estado |
|--------|----------|--------|-----------|--------|
| **443** | Nginx | Público | HTTPS | ✅ Activo |
| **80** | Nginx | Público | HTTP → HTTPS | ✅ Redirige |
| **8000** | FastAPI | Localhost | HTTP | ✅ Interno |

---

## 🔄 Renovación de Certificados

### Automática ✅

- **Frecuencia:** Cada 60 días (certificado válido 90 días)
- **Método:** Systemd timer o cron job
- **Sin intervención manual requerida**

### Verificar Renovación

```bash
# Ver timer de systemd
sudo systemctl list-timers | grep certbot

# Test de renovación (no renueva realmente)
sudo certbot renew --dry-run

# Ver certificados instalados
sudo certbot certificates

# Renovar manualmente (si es necesario)
sudo certbot renew
```

---

## 📁 Ubicación de Archivos

### Certificados SSL

```
/etc/letsencrypt/
├── live/tudominio.com/
│   ├── fullchain.pem      # Certificado completo
│   ├── privkey.pem        # Clave privada
│   ├── cert.pem           # Certificado del dominio
│   └── chain.pem          # Cadena de certificados
├── renewal/
│   └── tudominio.com.conf # Config de renovación
└── archive/               # Versiones anteriores
```

### Configuración Nginx

```
/etc/nginx/
├── sites-available/
│   └── api-electoral      # Configuración principal
└── sites-enabled/
    └── api-electoral      # Symlink (activo)
```

### Logs

```
/var/log/nginx/
├── api-electoral-access.log  # Logs de acceso
└── api-electoral-error.log   # Logs de errores

/var/log/letsencrypt/
└── letsencrypt.log           # Logs de Certbot
```

---

## ✅ Checklist Post-HTTPS

### Configuración
- [ ] DNS configurado (registro A)
- [ ] Certificado SSL instalado
- [ ] HTTPS funciona en navegador
- [ ] HTTP redirige a HTTPS
- [ ] Sin advertencias de seguridad en navegador

### Seguridad
- [ ] Test SSL Labs: Grado A o A+
- [ ] HSTS habilitado
- [ ] Headers de seguridad configurados
- [ ] Solo TLS 1.2+ habilitado

### Automatización
- [ ] Renovación automática configurada
- [ ] Test de renovación exitoso
- [ ] Firewall permite puertos 80 y 443

### Documentación
- [ ] URLs actualizadas en código
- [ ] README actualizado
- [ ] Usuarios/clientes notificados
- [ ] Postman/Swagger actualizado

---

## 🌐 URLs de Acceso

### Antes (HTTP)
```
http://tu-servidor-ip/docs
http://tu-servidor-ip/health
http://tu-servidor-ip/balance
```

### Después (HTTPS)
```
https://tudominio.com/docs       🔒
https://tudominio.com/health     🔒
https://tudominio.com/balance    🔒
```

---

## 🆘 Troubleshooting Rápido

### Problema: Dominio no resuelve
```bash
# Verificar DNS
dig +short tudominio.com

# Solución: Esperar propagación DNS (5-15 min)
```

### Problema: Error "too many certificates"
```bash
# Límite de Let's Encrypt alcanzado
# Solución: Esperar 1 semana o usar staging
sudo certbot --nginx --staging -d tudominio.com
```

### Problema: Puerto 443 bloqueado
```bash
# Abrir en firewall
sudo ufw allow 443/tcp
sudo ufw reload
```

### Problema: Certificado no se renueva
```bash
# Verificar timer
sudo systemctl status certbot.timer

# Renovar manualmente
sudo certbot renew --force-renewal
```

---

## 📊 Monitoreo

### Comandos Útiles

```bash
# Ver estado de certificados
sudo certbot certificates

# Ver días restantes
echo | openssl s_client -servername tudominio.com \
  -connect tudominio.com:443 2>/dev/null | \
  openssl x509 -noout -enddate

# Ver logs de renovación
sudo journalctl -u certbot.timer

# Test de conectividad HTTPS
curl -I https://tudominio.com/health
```

### Alertas Recomendadas

- **30 días antes:** Primera alerta de expiración
- **15 días antes:** Segunda alerta
- **7 días antes:** Alerta crítica

---

## 🎯 Mejores Prácticas

1. **Monitorea la expiración** del certificado mensualmente
2. **Verifica logs** de renovación automática
3. **Backup** de `/etc/letsencrypt/` regularmente
4. **Test SSL** cada 3 meses en SSL Labs
5. **Actualiza Nginx** cuando haya parches de seguridad
6. **Documenta cambios** en configuración
7. **Notifica usuarios** de migración a HTTPS

---

## 📚 Documentación Relacionada

- **[HTTPS_QUICK_START.md](HTTPS_QUICK_START.md)** - Inicio rápido (5 min)
- **[CONFIGURACION_HTTPS.md](CONFIGURACION_HTTPS.md)** - Guía completa
- **[DEPLOY_PORT_80.md](DEPLOY_PORT_80.md)** - Configuración base
- **[RESUMEN_CONFIGURACION.md](RESUMEN_CONFIGURACION.md)** - Resumen técnico

---

## 🔗 Recursos Externos

- **Let's Encrypt:** https://letsencrypt.org/
- **Certbot:** https://certbot.eff.org/
- **SSL Labs Test:** https://www.ssllabs.com/ssltest/
- **Mozilla SSL Config:** https://ssl-config.mozilla.org/
- **Nginx Docs:** https://nginx.org/en/docs/

---

## 💡 Próximos Pasos Opcionales

1. **CDN:** Agregar Cloudflare para mejor rendimiento
2. **WAF:** Web Application Firewall para protección adicional
3. **Rate Limiting:** Limitar peticiones por IP
4. **Monitoring:** Prometheus + Grafana
5. **Backups:** Automatizar backups de certificados
6. **CI/CD:** Automatizar despliegues con GitHub Actions

---

**Última actualización:** 2024  
**Versión:** 1.0  
**Mantenedor:** API Electoral Team
