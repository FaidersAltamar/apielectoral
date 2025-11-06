#!/bin/bash
set -e

echo "═══════════════════════════════════════════════════════"
echo "🚀 FastAPI Deployment Script"
echo "═══════════════════════════════════════════════════════"

PROJECT_DIR="/var/www/html/apielectoral"
VENV_PATH="$PROJECT_DIR/venv"

cd "$PROJECT_DIR"

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

# 5.1 Install Playwright and browsers
echo "🎭 Installing Playwright..."
if ! command -v playwright &> /dev/null; then
    pip install playwright -q
fi

echo "🌐 Installing Playwright browsers..."
playwright install chromium

echo "🔧 Installing Playwright system dependencies..."
sudo playwright install-deps chromium || echo "⚠️  Could not install system dependencies automatically"

# 6. Setup and restart service
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

# 7. Check status
sleep 3
if sudo systemctl is-active --quiet api-electoral; then
    echo "✅ Service is running"
    sudo systemctl status api-electoral --no-pager -l | head -20
else
    echo "❌ Service failed to start"
    sudo journalctl -u api-electoral -n 30 --no-pager
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ Deployment completed!"
echo "═══════════════════════════════════════════════════════"
