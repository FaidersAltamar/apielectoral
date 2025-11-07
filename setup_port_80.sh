#!/bin/bash
set -e

echo "═══════════════════════════════════════════════════════"
echo "🚀 API Electoral - Setup Script for Port 80"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "This script will:"
echo "  1. Install Nginx"
echo "  2. Configure FastAPI to run on port 8000"
echo "  3. Configure Nginx as reverse proxy on port 80"
echo "  4. Setup systemd service"
echo "  5. Start all services"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

PROJECT_DIR="/var/www/html/apielectoral"
VENV_PATH="$PROJECT_DIR/venv"

# Navigate to project directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# 1. Install Nginx
echo ""
echo "📦 Installing Nginx..."
if ! command -v nginx &> /dev/null; then
    sudo apt update
    sudo apt install nginx -y
    echo "✅ Nginx installed"
else
    echo "✅ Nginx already installed"
fi

# 2. Setup Python environment
echo ""
echo "🐍 Setting up Python environment..."
if [ ! -d "$VENV_PATH" ]; then
    python3 -m venv "$VENV_PATH"
    echo "✅ Virtual environment created"
fi

source "$VENV_PATH/bin/activate"
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencies installed"

# 3. Configure Nginx
echo ""
echo "🌐 Configuring Nginx..."

# Copy nginx config
sudo cp "$PROJECT_DIR/nginx.conf" /etc/nginx/sites-available/api-electoral

# Create symbolic link
sudo ln -sf /etc/nginx/sites-available/api-electoral /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
if sudo nginx -t; then
    echo "✅ Nginx configuration valid"
else
    echo "❌ Nginx configuration error"
    exit 1
fi

# 4. Setup systemd service
echo ""
echo "⚙️  Setting up systemd service..."

# Copy service file
sudo cp "$PROJECT_DIR/api-electoral.service" /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable api-electoral
sudo systemctl enable nginx

echo "✅ Systemd service configured"

# 5. Start services
echo ""
echo "🚀 Starting services..."

# Start FastAPI
sudo systemctl restart api-electoral
sleep 2

if sudo systemctl is-active --quiet api-electoral; then
    echo "✅ FastAPI started on port 8000"
else
    echo "❌ FastAPI failed to start"
    sudo journalctl -u api-electoral -n 20 --no-pager
    exit 1
fi

# Start Nginx
sudo systemctl restart nginx
sleep 1

if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx started on port 80"
else
    echo "❌ Nginx failed to start"
    sudo journalctl -u nginx -n 20 --no-pager
    exit 1
fi

# 6. Verify setup
echo ""
echo "🔍 Verifying setup..."
echo ""

# Check ports
echo "Port 8000 (FastAPI):"
sudo ss -tulpn | grep :8000 || echo "  ⚠️  Not listening"

echo ""
echo "Port 80 (Nginx):"
sudo ss -tulpn | grep :80 || echo "  ⚠️  Not listening"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ Setup completed successfully!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📡 Your API is now accessible at:"
echo "   🌐 http://$(hostname -I | awk '{print $1}')/docs"
echo "   🏥 http://$(hostname -I | awk '{print $1}')/health"
echo "   💰 http://$(hostname -I | awk '{print $1}')/balance"
echo ""
echo "📊 View logs:"
echo "   FastAPI: sudo journalctl -u api-electoral -f"
echo "   Nginx:   sudo tail -f /var/log/nginx/api-electoral-access.log"
echo ""
echo "🔧 Manage services:"
echo "   Restart FastAPI: sudo systemctl restart api-electoral"
echo "   Restart Nginx:   sudo systemctl reload nginx"
echo "   View status:     sudo systemctl status api-electoral nginx"
echo ""
echo "📚 For HTTPS setup, see: DEPLOY_PORT_80.md"
echo ""
