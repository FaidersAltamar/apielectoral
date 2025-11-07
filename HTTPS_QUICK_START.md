# 🔒 HTTPS Quick Start - 5 Minutos

## ⚡ Configuración Rápida

### Paso 1: Configurar DNS (5 minutos)

Ve a tu proveedor de dominio y crea:

```
Tipo: A
Nombre: @
Valor: [IP_DE_TU_SERVIDOR]
```

**Espera 5-10 minutos** para que se propague.

Verifica:
```bash
dig +short tudominio.com
# Debe mostrar tu IP
```

---

### Paso 2: Ejecutar Script (2 minutos)

```bash
cd /var/www/html/apielectoral
chmod +x setup_https.sh
sudo ./setup_https.sh
```

El script te pedirá:
1. **Dominio:** `miapi.com`
2. **¿Incluir www?** `y` o `n`
3. **Email:** `tu@email.com`

---

### Paso 3: ¡Listo! 🎉

Tu API ahora está en:
- 🔒 `https://tudominio.com/docs`
- 🔒 `https://tudominio.com/health`
- 🔒 `https://tudominio.com/balance`

---

## 🏗️ Arquitectura Final

```
┌─────────────────────────────────────────┐
│            Internet                     │
└────────────┬────────────────────────────┘
             │
             │ HTTPS (Puerto 443) 🔒
             │ HTTP  (Puerto 80)  → Redirige a HTTPS
             │
             ▼
┌─────────────────────────────────────────┐
│           Nginx + SSL/TLS               │
│  • Let's Encrypt Certificate            │
│  • Auto-renewal enabled                 │
│  • HTTP → HTTPS redirect                │
└────────────┬────────────────────────────┘
             │
             │ HTTP (Puerto 8000)
             │ localhost only
             ▼
┌─────────────────────────────────────────┐
│         FastAPI (Uvicorn)               │
│  • Workers: 2                           │
│  • Internal only                        │
└─────────────────────────────────────────┘
```

---

## ✅ Verificación

```bash
# 1. Verificar certificado
sudo certbot certificates

# 2. Test desde navegador
https://tudominio.com/docs

# 3. Verificar redirección HTTP → HTTPS
curl -I http://tudominio.com
# Debe retornar: 301 Moved Permanently

# 4. Test de renovación
sudo certbot renew --dry-run
```

---

## 🔄 Renovación Automática

✅ **Ya está configurada!**

- Certificado válido por **90 días**
- Renovación automática cada **60 días**
- No requiere acción manual

Verificar:
```bash
sudo systemctl list-timers | grep certbot
```

---

## 🆘 Problemas Comunes

### El dominio no resuelve

```bash
# Verificar DNS
dig +short tudominio.com

# Si no muestra tu IP:
# 1. Revisa configuración DNS
# 2. Espera 10-15 minutos
# 3. Intenta de nuevo
```

### Error: "too many certificates"

Límite de Let's Encrypt alcanzado (50/semana).

**Solución:** Espera una semana o usa staging:
```bash
sudo certbot --nginx --staging -d tudominio.com
```

### Puerto 443 bloqueado

```bash
# Abrir puerto en firewall
sudo ufw allow 443/tcp
sudo ufw reload
```

### Error 502 Bad Gateway

```bash
# Reiniciar servicios
sudo systemctl restart api-electoral
sudo systemctl reload nginx
```

---

## 📊 Comandos Útiles

```bash
# Ver certificados
sudo certbot certificates

# Renovar manualmente
sudo certbot renew

# Test de renovación
sudo certbot renew --dry-run

# Ver logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# Revocar certificado
sudo certbot revoke --cert-path /etc/letsencrypt/live/tudominio.com/cert.pem
```

---

## 🔐 Mejoras de Seguridad (Opcional)

### 1. Headers de Seguridad

Ya incluidos en la configuración:
- ✅ HSTS (HTTP Strict Transport Security)
- ✅ X-Frame-Options
- ✅ X-Content-Type-Options
- ✅ X-XSS-Protection

### 2. Test de Seguridad

Verifica tu configuración SSL:
```
https://www.ssllabs.com/ssltest/analyze.html?d=tudominio.com
```

**Objetivo:** Calificación **A** o **A+**

---

## 📱 Actualizar Clientes

Después de configurar HTTPS, actualiza:

### 1. URLs en tu código
```python
# Antes
BASE_URL = "http://miapi.com"

# Después
BASE_URL = "https://miapi.com"
```

### 2. Documentación
- README
- Postman collections
- Swagger/OpenAPI specs

### 3. Webhooks
- Actualizar URLs en servicios externos
- Notificar a usuarios de la API

---

## 🎯 Checklist

- [ ] DNS configurado (registro A)
- [ ] Script ejecutado exitosamente
- [ ] HTTPS funciona en navegador
- [ ] HTTP redirige a HTTPS
- [ ] Certificado válido (sin advertencias)
- [ ] Test de renovación exitoso
- [ ] Firewall permite puerto 443
- [ ] URLs actualizadas en código
- [ ] Documentación actualizada
- [ ] Usuarios notificados

---

## 📚 Más Información

- **Guía completa:** [CONFIGURACION_HTTPS.md](CONFIGURACION_HTTPS.md)
- **Troubleshooting:** Ver sección de problemas en CONFIGURACION_HTTPS.md
- **Let's Encrypt:** https://letsencrypt.org/

---

## 💡 Tips

1. **Usa siempre HTTPS en producción**
2. **Monitorea la expiración** del certificado
3. **Verifica renovación** cada mes
4. **Backup** de `/etc/letsencrypt/`
5. **Test SSL** regularmente con SSL Labs

---

**¿Necesitas ayuda?** Consulta [CONFIGURACION_HTTPS.md](CONFIGURACION_HTTPS.md) para troubleshooting detallado.
