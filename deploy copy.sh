#!/bin/bash
set -e

echo "═══════════════════════════════════════════════════════"
echo "🚀 API Electoral - Deployment Script with HTTPS"
echo "═══════════════════════════════════════════════════════"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="/var/www/html/apielectoral"
VENV_PATH="$PROJECT_DIR/venv"

cd "$PROJECT_DIR"

# Preguntar si se desea configurar HTTPS
echo ""
read -p "¿Deseas configurar HTTPS? (y/n): " SETUP_HTTPS
echo ""

# 1. Backup .env
echo "📦 Backing up environment..."
[ -f .env ] && cp .env .env.backup

# 2. Pull latest code
echo "📥 Pulling latest code..."
git pull origin main || git pull origin master

# 3. Restore .env
[ -f .env.backup ] && cp .env.backup .env

# 4. Setup virtual environment
echo "🐍 Setting up Python environment..."
if [ ! -d "$VENV_PATH" ]; then
    python3 -m venv "$VENV_PATH"
fi

# 5. Install dependencies
echo "📦 Installing dependencies..."
source "$VENV_PATH/bin/activate"
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 6. Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "⚠️  Nginx not found. Installing..."
    sudo apt update
    sudo apt install nginx -y
fi

# 7. Setup and restart service
echo "🔄 Setting up systemd service..."

# Copy service file to systemd directory
if [ -f "$PROJECT_DIR/api-electoral.service" ]; then
    sudo cp "$PROJECT_DIR/api-electoral.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    echo "✅ Service file updated"
fi

# Enable and restart service
if sudo systemctl list-unit-files | grep -q "api-electoral.service"; then
    sudo systemctl enable api-electoral 2>/dev/null || true
    sudo systemctl restart api-electoral
    echo "✅ Service restarted"
else
    echo "❌ Service file not found"
    exit 1
fi

# 8. Setup Nginx
echo "🌐 Configuring Nginx..."

# Si se va a configurar HTTPS, usar configuración temporal
if [[ $SETUP_HTTPS =~ ^[Yy]$ ]]; then
    # Solicitar información del dominio
    echo "📝 Información requerida para HTTPS:"
    echo ""
    read -p "Ingresa tu dominio (ejemplo: miapi.com): " DOMAIN
    read -p "¿Incluir www? (y/n): " INCLUDE_WWW
    read -p "Ingresa tu email para notificaciones de Let's Encrypt: " EMAIL
    
    # Crear configuración temporal para HTTP (para obtener certificado)
    cat > /tmp/nginx-api-electoral << EOF
server {
    listen 80;
    server_name $DOMAIN$([ "$INCLUDE_WWW" = "y" ] && echo " www.$DOMAIN" || echo "");

    access_log /var/log/nginx/api-electoral-access.log;
    error_log /var/log/nginx/api-electoral-error.log;

    client_max_body_size 10M;

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
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
}
EOF
    sudo cp /tmp/nginx-api-electoral /etc/nginx/sites-available/api-electoral
else
    # Usar configuración estándar sin HTTPS
    if [ -f "$PROJECT_DIR/nginx.conf" ]; then
        sudo cp "$PROJECT_DIR/nginx.conf" /etc/nginx/sites-available/api-electoral
    fi
fi

# Activar configuración
sudo ln -sf /etc/nginx/sites-available/api-electoral /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
if sudo nginx -t 2>/dev/null; then
    echo -e "${GREEN}✅ Nginx configuration valid${NC}"
    sudo systemctl enable nginx 2>/dev/null || true
    sudo systemctl reload nginx
    echo -e "${GREEN}✅ Nginx reloaded${NC}"
else
    echo -e "${RED}❌ Nginx configuration error${NC}"
    sudo nginx -t
    exit 1
fi

# 9. Configurar HTTPS si se solicitó
if [[ $SETUP_HTTPS =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔒 Configurando HTTPS con Let's Encrypt..."
    
    # Instalar Certbot
    echo "📦 Instalando Certbot..."
    sudo apt update -qq
    sudo apt install certbot python3-certbot-nginx -y -qq
    echo -e "${GREEN}✅ Certbot instalado${NC}"
    
    # Configurar dominio args
    if [[ $INCLUDE_WWW =~ ^[Yy]$ ]]; then
        DOMAIN_ARGS="-d $DOMAIN -d www.$DOMAIN"
    else
        DOMAIN_ARGS="-d $DOMAIN"
    fi
    
    # Obtener certificado SSL
    echo ""
    echo "🔐 Obteniendo certificado SSL..."
    if sudo certbot --nginx $DOMAIN_ARGS --non-interactive --agree-tos --email $EMAIL --redirect; then
        echo ""
        echo -e "${GREEN}✅ Certificado SSL obtenido exitosamente${NC}"
        
        # Configurar firewall
        if command -v ufw &> /dev/null; then
            sudo ufw allow 443/tcp comment 'HTTPS' 2>/dev/null || true
            sudo ufw allow 80/tcp comment 'HTTP' 2>/dev/null || true
            echo -e "${GREEN}✅ Firewall configurado${NC}"
        fi
    else
        echo ""
        echo -e "${RED}❌ Error al obtener certificado SSL${NC}"
        echo "Verifica que:"
        echo "  1. El dominio apunta a este servidor"
        echo "  2. El puerto 80 es accesible desde internet"
        exit 1
    fi
fi

# 10. Check status
sleep 3
echo ""
echo "🔍 Checking services status..."
echo ""

# Check FastAPI
if sudo systemctl is-active --quiet api-electoral; then
    echo -e "${GREEN}✅ FastAPI is running on port 8000${NC}"
    sudo systemctl status api-electoral --no-pager -l | head -15
else
    echo -e "${RED}❌ FastAPI failed to start${NC}"
    sudo journalctl -u api-electoral -n 30 --no-pager
    exit 1
fi

echo ""

# Check Nginx
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx is running${NC}"
    sudo systemctl status nginx --no-pager -l | head -10
else
    echo -e "${YELLOW}⚠️  Nginx is not running${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ Deployment completed!"
echo "═══════════════════════════════════════════════════════"
echo ""

# Mostrar URLs según configuración
if [[ $SETUP_HTTPS =~ ^[Yy]$ ]]; then
    echo "🌐 Tu API está disponible en:"
    echo "   🔒 https://$DOMAIN/docs"
    echo "   🔒 https://$DOMAIN/health"
    echo "   🔒 https://$DOMAIN/balance"
    if [[ $INCLUDE_WWW =~ ^[Yy]$ ]]; then
        echo "   🔒 https://www.$DOMAIN/docs"
    fi
    echo ""
    echo "📝 Notas HTTPS:"
    echo "   • HTTP redirige automáticamente a HTTPS"
    echo "   • Certificado válido por 90 días"
    echo "   • Renovación automática configurada"
    echo ""
    echo "🔧 Comandos útiles:"
    echo "   Ver certificados:    sudo certbot certificates"
    echo "   Renovar manualmente: sudo certbot renew"
else
    echo "📡 Access your API at:"
    echo "   🌐 http://your-server-ip/docs"
    echo "   🏥 http://your-server-ip/health"
    echo "   💰 http://your-server-ip/balance"
fi

echo ""
echo "📊 View logs:"
echo "   FastAPI: sudo journalctl -u api-electoral -f"
echo "   Nginx:   sudo tail -f /var/log/nginx/api-electoral-access.log"
echo ""
