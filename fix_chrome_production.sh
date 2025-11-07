#!/bin/bash

# Script de solución rápida para error "Chrome instance exited" en producción
# Ejecutar en el servidor: bash fix_chrome_production.sh

set -e

echo "🔧 Iniciando solución para error de Chrome en producción..."
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "api.py" ]; then
    echo "❌ Error: Este script debe ejecutarse desde el directorio del proyecto"
    echo "   Ejecuta: cd /var/www/html/apielectoral && bash fix_chrome_production.sh"
    exit 1
fi

# Paso 1: Detener el servicio
echo "1️⃣ Deteniendo servicio api-electoral..."
sudo systemctl stop api-electoral
echo "✅ Servicio detenido"
echo ""

# Paso 2: Actualizar código
echo "2️⃣ Actualizando código desde repositorio..."
git pull origin main
echo "✅ Código actualizado"
echo ""

# Paso 3: Instalar dependencias de Chrome
echo "3️⃣ Instalando dependencias de Chrome..."
bash install_chrome_dependencies.sh
echo "✅ Dependencias instaladas"
echo ""

# Paso 4: Verificar que Chrome funciona
echo "4️⃣ Verificando Chrome en modo headless..."
if google-chrome --headless --disable-gpu --no-sandbox --disable-dev-shm-usage --dump-dom https://www.google.com > /dev/null 2>&1; then
    echo "✅ Chrome headless funciona correctamente"
else
    echo "❌ Error: Chrome headless no funciona"
    echo "   Ejecutando diagnóstico..."
    google-chrome --headless --disable-gpu --no-sandbox --disable-dev-shm-usage --dump-dom https://www.google.com 2>&1 | head -20
    echo ""
    echo "⚠️ Puede que necesites instalar dependencias adicionales manualmente"
    echo "   Consulta: CHROME_SESSION_ERROR_FIX.md"
fi
echo ""

# Paso 5: Reiniciar el servicio
echo "5️⃣ Reiniciando servicio api-electoral..."
sudo systemctl start api-electoral
sleep 3
echo "✅ Servicio reiniciado"
echo ""

# Paso 6: Verificar estado del servicio
echo "6️⃣ Verificando estado del servicio..."
if sudo systemctl is-active --quiet api-electoral; then
    echo "✅ Servicio está corriendo"
    sudo systemctl status api-electoral --no-pager | head -15
else
    echo "❌ Error: El servicio no está corriendo"
    echo "   Ver logs con: sudo journalctl -u api-electoral -n 50"
    exit 1
fi
echo ""

# Paso 7: Probar endpoint
echo "7️⃣ Probando endpoint de balance..."
sleep 2
RESPONSE=$(curl -s http://localhost:8000/balance)
if [ $? -eq 0 ]; then
    echo "✅ Endpoint responde correctamente"
    echo "   Respuesta: $RESPONSE"
else
    echo "❌ Error: El endpoint no responde"
    echo "   Ver logs con: sudo journalctl -u api-electoral -f"
fi
echo ""

# Resumen final
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Proceso completado"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Comandos útiles:"
echo "   • Ver logs en tiempo real:"
echo "     sudo journalctl -u api-electoral -f"
echo ""
echo "   • Verificar estado del servicio:"
echo "     sudo systemctl status api-electoral"
echo ""
echo "   • Probar endpoint de consulta:"
echo "     curl -X POST http://localhost:8000/consultar-puesto-votacion \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"nuip\": \"1102877148\", \"enviarapi\": false}'"
echo ""
echo "📚 Documentación completa: CHROME_SESSION_ERROR_FIX.md"
echo ""
