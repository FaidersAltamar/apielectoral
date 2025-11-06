#!/bin/bash

# Script para instalar Chrome y todas sus dependencias para modo headless
# Ejecutar en el servidor de producción: bash install_chrome_dependencies.sh

set -e

echo "🔧 Instalando dependencias de Chrome para modo headless..."

# Actualizar repositorios
sudo apt-get update

# Instalar dependencias del sistema necesarias para Chrome headless
echo "📦 Instalando librerías del sistema..."
sudo apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    xvfb

# Instalar Google Chrome si no está instalado
if ! command -v google-chrome &> /dev/null; then
    echo "🌐 Instalando Google Chrome..."
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo apt-get install -y ./google-chrome-stable_current_amd64.deb
    rm google-chrome-stable_current_amd64.deb
    echo "✅ Google Chrome instalado"
else
    echo "✅ Google Chrome ya está instalado"
    google-chrome --version
fi

# Verificar instalación
echo ""
echo "🔍 Verificando instalación..."
if google-chrome --version &> /dev/null; then
    echo "✅ Chrome instalado correctamente: $(google-chrome --version)"
else
    echo "❌ Error: Chrome no se instaló correctamente"
    exit 1
fi

# Probar Chrome en modo headless
echo ""
echo "🧪 Probando Chrome en modo headless..."
if google-chrome --headless --disable-gpu --dump-dom https://www.google.com > /dev/null 2>&1; then
    echo "✅ Chrome headless funciona correctamente"
else
    echo "⚠️ Advertencia: Chrome headless puede tener problemas"
fi

echo ""
echo "✅ ¡Instalación completada!"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Reiniciar el servicio de la API:"
echo "      sudo systemctl restart api-electoral"
echo "   2. Verificar logs:"
echo "      sudo journalctl -u api-electoral -f"
