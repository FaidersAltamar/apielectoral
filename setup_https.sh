#!/bin/bash
set -e

echo "═══════════════════════════════════════════════════════"
echo "🔒 Configuración HTTPS con Let's Encrypt"
echo "═══════════════════════════════════════════════════════"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar que se ejecuta como root o con sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Este script debe ejecutarse con sudo${NC}"
    exit 1
fi

# Solicitar información del dominio
echo "📝 Información requerida:"
echo ""
read -p "Ingresa tu dominio (ejemplo: miapi.com): " DOMAIN
read -p "¿Incluir www? (y/n): " INCLUDE_WWW
read -p "Ingresa tu email para notificaciones de Let's Encrypt: " EMAIL

echo ""
echo "Configuración:"
echo "  Dominio: $DOMAIN"
if [[ $INCLUDE_WWW =~ ^[Yy]$ ]]; then
    echo "  Con www: Sí (www.$DOMAIN)"
    DOMAIN_ARGS="-d $DOMAIN -d www.$DOMAIN"
else
    echo "  Con www: No"
    DOMAIN_ARGS="-d $DOMAIN"
fi
echo "  Email: $EMAIL"
echo ""
read -p "¿Continuar? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

PROJECT_DIR="/var/www/html/apielectoral"

# 1. Verificar que nginx está instalado y corriendo
echo ""
echo "🔍 Verificando prerequisitos..."

if ! command -v nginx &> /dev/null; then
    echo -e "${RED}❌ Nginx no está instalado${NC}"
    echo "Ejecuta primero: sudo ./setup_port_80.sh"
    exit 1
fi

if ! systemctl is-active --quiet nginx; then
    echo -e "${RED}❌ Nginx no está corriendo${NC}"
    echo "Inicia nginx: sudo systemctl start nginx"
    exit 1
fi

echo -e "${GREEN}✅ Nginx está instalado y corriendo${NC}"

# 2. Verificar que el dominio apunta al servidor
echo ""
echo "🌐 Verificando DNS..."
SERVER_IP=$(hostname -I | awk '{print $1}')
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)

echo "  IP del servidor: $SERVER_IP"
echo "  IP del dominio:  $DOMAIN_IP"

if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
    echo -e "${YELLOW}⚠️  ADVERTENCIA: El dominio no apunta a este servidor${NC}"
    echo ""
    echo "Para que HTTPS funcione, debes configurar tu DNS:"
    echo "  1. Ve a tu proveedor de dominio (GoDaddy, Namecheap, etc.)"
    echo "  2. Crea un registro A que apunte a: $SERVER_IP"
    echo "  3. Espera 5-10 minutos para que se propague"
    echo ""
    read -p "¿Continuar de todas formas? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 3. Instalar Certbot
echo ""
echo "📦 Instalando Certbot..."

apt update -qq
apt install certbot python3-certbot-nginx -y -qq

echo -e "${GREEN}✅ Certbot instalado${NC}"

# 4. Actualizar configuración de nginx para el dominio
echo ""
echo "⚙️  Actualizando configuración de Nginx..."

# Crear configuración temporal para obtener certificado
cat > /etc/nginx/sites-available/api-electoral << EOF
server {
    listen 80;
    server_name $DOMAIN$([ "$INCLUDE_WWW" = "y" ] && echo " www.$DOMAIN" || echo "");

    # Logs
    access_log /var/log/nginx/api-electoral-access.log;
    error_log /var/log/nginx/api-electoral-error.log;

    # Tamaño máximo de body
    client_max_body_size 10M;

    # Timeouts aumentados para scrapers
    proxy_connect_timeout 600;
    proxy_send_timeout 600;
    proxy_read_timeout 600;
    send_timeout 600;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Verificar configuración
if nginx -t 2>/dev/null; then
    echo -e "${GREEN}✅ Configuración de Nginx actualizada${NC}"
    systemctl reload nginx
else
    echo -e "${RED}❌ Error en configuración de Nginx${NC}"
    nginx -t
    exit 1
fi

# 5. Obtener certificado SSL
echo ""
echo "🔐 Obteniendo certificado SSL de Let's Encrypt..."
echo "   Esto puede tomar 1-2 minutos..."
echo ""

# Obtener certificado
if certbot --nginx $DOMAIN_ARGS --non-interactive --agree-tos --email $EMAIL --redirect; then
    echo ""
    echo -e "${GREEN}✅ Certificado SSL obtenido exitosamente${NC}"
else
    echo ""
    echo -e "${RED}❌ Error al obtener certificado SSL${NC}"
    echo ""
    echo "Posibles causas:"
    echo "  1. El dominio no apunta a este servidor"
    echo "  2. El puerto 80 no es accesible desde internet"
    echo "  3. Ya existe un certificado para este dominio"
    echo ""
    echo "Verifica tu configuración y vuelve a intentar"
    exit 1
fi

# 6. Verificar renovación automática
echo ""
echo "🔄 Configurando renovación automática..."

# Certbot instala automáticamente un cron/timer para renovación
if systemctl list-timers | grep -q certbot; then
    echo -e "${GREEN}✅ Renovación automática configurada (systemd timer)${NC}"
elif [ -f /etc/cron.d/certbot ]; then
    echo -e "${GREEN}✅ Renovación automática configurada (cron)${NC}"
else
    echo -e "${YELLOW}⚠️  Renovación automática no detectada${NC}"
    echo "   Configurando manualmente..."
    
    # Agregar cron job
    echo "0 0,12 * * * root python3 -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | tee -a /etc/crontab > /dev/null
    echo -e "${GREEN}✅ Cron job agregado${NC}"
fi

# Test de renovación
echo ""
echo "🧪 Probando renovación (dry-run)..."
if certbot renew --dry-run 2>&1 | grep -q "Congratulations"; then
    echo -e "${GREEN}✅ Test de renovación exitoso${NC}"
else
    echo -e "${YELLOW}⚠️  Test de renovación con advertencias (puede ser normal)${NC}"
fi

# 7. Configurar firewall
echo ""
echo "🔥 Configurando firewall..."

if command -v ufw &> /dev/null; then
    ufw allow 443/tcp comment 'HTTPS' 2>/dev/null || true
    ufw allow 80/tcp comment 'HTTP' 2>/dev/null || true
    echo -e "${GREEN}✅ Firewall configurado (UFW)${NC}"
else
    echo -e "${YELLOW}⚠️  UFW no instalado, saltando configuración de firewall${NC}"
fi

# 8. Verificación final
echo ""
echo "🔍 Verificación final..."
sleep 2

# Verificar que HTTPS funciona
if curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health | grep -q "200"; then
    echo -e "${GREEN}✅ HTTPS funcionando correctamente${NC}"
else
    echo -e "${YELLOW}⚠️  No se pudo verificar HTTPS (puede tomar unos segundos)${NC}"
fi

# Verificar redirección HTTP -> HTTPS
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -L http://$DOMAIN/health)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Redirección HTTP -> HTTPS funcionando${NC}"
fi

# 9. Información del certificado
echo ""
echo "📋 Información del certificado:"
certbot certificates 2>/dev/null | grep -A 5 "Certificate Name: $DOMAIN" || echo "  (ejecuta 'sudo certbot certificates' para ver detalles)"

echo ""
echo "═══════════════════════════════════════════════════════"
echo -e "${GREEN}✅ HTTPS configurado exitosamente!${NC}"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "🌐 Tu API ahora está disponible en:"
echo "   🔒 https://$DOMAIN/docs"
echo "   🔒 https://$DOMAIN/health"
echo "   🔒 https://$DOMAIN/balance"
echo ""
if [[ $INCLUDE_WWW =~ ^[Yy]$ ]]; then
    echo "   🔒 https://www.$DOMAIN/docs"
    echo ""
fi
echo "📝 Notas importantes:"
echo "   • HTTP redirige automáticamente a HTTPS"
echo "   • Certificado válido por 90 días"
echo "   • Renovación automática configurada"
echo "   • Próxima renovación: ~60 días"
echo ""
echo "🔧 Comandos útiles:"
echo "   Ver certificados:    sudo certbot certificates"
echo "   Renovar manualmente: sudo certbot renew"
echo "   Test renovación:     sudo certbot renew --dry-run"
echo ""
echo "📚 Más información: CONFIGURACION_HTTPS.md"
echo ""
