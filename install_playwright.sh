#!/bin/bash
# Script para instalar Playwright y sus dependencias en Linux

set -e

echo "🎭 Instalando Playwright y dependencias..."

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "✅ Activando entorno virtual..."
    source venv/bin/activate
fi

# Instalar Playwright
echo "📦 Instalando Playwright..."
pip install playwright

# Instalar navegadores de Playwright
echo "🌐 Instalando navegadores de Playwright..."
playwright install chromium

# Instalar dependencias del sistema para Chromium (Ubuntu/Debian)
echo "🔧 Instalando dependencias del sistema..."
if command -v apt-get &> /dev/null; then
    echo "Detectado sistema basado en Debian/Ubuntu"
    sudo playwright install-deps chromium || {
        echo "⚠️  No se pudieron instalar las dependencias automáticamente"
        echo "Ejecuta manualmente: sudo playwright install-deps chromium"
    }
elif command -v yum &> /dev/null; then
    echo "Detectado sistema basado en RedHat/CentOS"
    echo "⚠️  Instala manualmente las dependencias de Chromium"
fi

echo ""
echo "✅ Playwright instalado correctamente"
echo ""
echo "Para verificar la instalación:"
echo "  python -c 'from playwright.sync_api import sync_playwright; print(\"OK\")'"
