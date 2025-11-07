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
    xvfb \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0

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
if google-chrome --headless --disable-gpu --no-sandbox --disable-dev-shm-usage --dump-dom https://www.google.com > /dev/null 2>&1; then
    echo "✅ Chrome headless funciona correctamente"
else
    echo "⚠️ Advertencia: Chrome headless puede tener problemas"
    echo "   Intentando diagnóstico..."
    google-chrome --headless --disable-gpu --no-sandbox --disable-dev-shm-usage --dump-dom https://www.google.com 2>&1 | head -20
fi

# Verificar librerías críticas
echo ""
echo "🔍 Verificando librerías críticas..."
MISSING_LIBS=0
for lib in libnss3.so libgbm.so.1 libatk-1.0.so.0 libcups.so.2; do
    if ! ldconfig -p | grep -q "$lib"; then
        echo "❌ Falta: $lib"
        MISSING_LIBS=$((MISSING_LIBS + 1))
    else
        echo "✅ Encontrada: $lib"
    fi
done

if [ $MISSING_LIBS -gt 0 ]; then
    echo "⚠️ Faltan $MISSING_LIBS librerías. Chrome puede no funcionar correctamente."
else
    echo "✅ Todas las librerías críticas están instaladas"
fi

echo ""
echo "✅ ¡Instalación completada!"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Reiniciar el servicio de la API:"
echo "      sudo systemctl restart api-electoral"
echo "   2. Verificar logs:"
echo "      sudo journalctl -u api-electoral -f"
echo "   3. Probar un endpoint:"
echo "      curl http://localhost:8000/balance"
