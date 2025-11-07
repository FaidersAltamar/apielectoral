#!/bin/bash

# Script de verificación rápida para API Electoral en puerto 80
# Uso: ./VERIFICACION.sh

echo "═══════════════════════════════════════════════════════"
echo "🔍 Verificación de API Electoral - Puerto 80"
echo "═══════════════════════════════════════════════════════"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        return 1
    fi
}

# 1. Verificar servicios
echo "📋 1. Estado de Servicios"
echo "─────────────────────────────────────────────────────"

sudo systemctl is-active --quiet api-electoral
check "FastAPI (api-electoral) está corriendo"

sudo systemctl is-active --quiet nginx
check "Nginx está corriendo"

echo ""

# 2. Verificar puertos
echo "🔌 2. Puertos en Uso"
echo "─────────────────────────────────────────────────────"

sudo ss -tulpn | grep -q ":8000"
check "Puerto 8000 (FastAPI) está escuchando"

sudo ss -tulpn | grep -q ":80"
check "Puerto 80 (Nginx) está escuchando"

echo ""
echo "Detalles de puertos:"
sudo ss -tulpn | grep -E ':80|:8000' | head -5

echo ""

# 3. Verificar archivos de configuración
echo "📁 3. Archivos de Configuración"
echo "─────────────────────────────────────────────────────"

[ -f /etc/systemd/system/api-electoral.service ]
check "Archivo de servicio systemd existe"

[ -f /etc/nginx/sites-enabled/api-electoral ]
check "Configuración de Nginx está habilitada"

[ -f /var/www/html/apielectoral/.env ]
check "Archivo .env existe"

[ -f /var/www/html/apielectoral/api.py ]
check "Archivo api.py existe"

echo ""

# 4. Verificar conectividad
echo "🌐 4. Conectividad"
echo "─────────────────────────────────────────────────────"

# Test FastAPI directo
curl -s http://127.0.0.1:8000/docs > /dev/null 2>&1
check "FastAPI responde en puerto 8000"

# Test Nginx
curl -s http://localhost/health > /dev/null 2>&1
check "Nginx proxy funciona (puerto 80)"

# Test balance
BALANCE=$(curl -s http://localhost/balance 2>/dev/null)
if [ ! -z "$BALANCE" ]; then
    echo -e "${GREEN}✅ Endpoint /balance responde${NC}"
    echo "   Respuesta: $(echo $BALANCE | head -c 100)..."
else
    echo -e "${RED}❌ Endpoint /balance no responde${NC}"
fi

echo ""

# 5. Verificar logs recientes
echo "📝 5. Logs Recientes"
echo "─────────────────────────────────────────────────────"

# Últimas líneas de FastAPI
echo "FastAPI (últimas 3 líneas):"
sudo journalctl -u api-electoral -n 3 --no-pager 2>/dev/null | tail -3

echo ""

# Últimas líneas de Nginx
if [ -f /var/log/nginx/api-electoral-access.log ]; then
    echo "Nginx Access (últimas 3 líneas):"
    sudo tail -3 /var/log/nginx/api-electoral-access.log 2>/dev/null
else
    echo -e "${YELLOW}⚠️  Log de Nginx no encontrado${NC}"
fi

echo ""

# 6. Verificar procesos
echo "⚙️  6. Procesos Activos"
echo "─────────────────────────────────────────────────────"

UVICORN_COUNT=$(ps aux | grep uvicorn | grep -v grep | wc -l)
if [ $UVICORN_COUNT -gt 0 ]; then
    echo -e "${GREEN}✅ $UVICORN_COUNT proceso(s) de Uvicorn corriendo${NC}"
else
    echo -e "${RED}❌ No hay procesos de Uvicorn${NC}"
fi

NGINX_COUNT=$(ps aux | grep nginx | grep -v grep | wc -l)
if [ $NGINX_COUNT -gt 0 ]; then
    echo -e "${GREEN}✅ $NGINX_COUNT proceso(s) de Nginx corriendo${NC}"
else
    echo -e "${RED}❌ No hay procesos de Nginx${NC}"
fi

echo ""

# 7. Verificar recursos
echo "💻 7. Recursos del Sistema"
echo "─────────────────────────────────────────────────────"

# Memoria
TOTAL_MEM=$(free -h | awk '/^Mem:/ {print $2}')
USED_MEM=$(free -h | awk '/^Mem:/ {print $3}')
echo "Memoria: $USED_MEM / $TOTAL_MEM usado"

# Disco
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}')
echo "Disco: $DISK_USAGE usado"

# CPU Load
LOAD=$(uptime | awk -F'load average:' '{print $2}')
echo "Load average:$LOAD"

echo ""

# 8. Información de la API
echo "📊 8. Información de la API"
echo "─────────────────────────────────────────────────────"

# Obtener IP del servidor
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "IP del servidor: $SERVER_IP"

echo ""
echo "URLs de acceso:"
echo "  📖 Documentación: http://$SERVER_IP/docs"
echo "  🏥 Health Check:  http://$SERVER_IP/health"
echo "  💰 Balance:       http://$SERVER_IP/balance"

echo ""

# 9. Resumen final
echo "═══════════════════════════════════════════════════════"
echo "📈 Resumen"
echo "═══════════════════════════════════════════════════════"

# Contar éxitos y fallos
TOTAL_CHECKS=10
PASSED=0

sudo systemctl is-active --quiet api-electoral && ((PASSED++))
sudo systemctl is-active --quiet nginx && ((PASSED++))
sudo ss -tulpn | grep -q ":8000" && ((PASSED++))
sudo ss -tulpn | grep -q ":80" && ((PASSED++))
[ -f /etc/systemd/system/api-electoral.service ] && ((PASSED++))
[ -f /etc/nginx/sites-enabled/api-electoral ] && ((PASSED++))
curl -s http://127.0.0.1:8000/docs > /dev/null 2>&1 && ((PASSED++))
curl -s http://localhost/health > /dev/null 2>&1 && ((PASSED++))
[ $UVICORN_COUNT -gt 0 ] && ((PASSED++))
[ $NGINX_COUNT -gt 0 ] && ((PASSED++))

PERCENTAGE=$((PASSED * 100 / TOTAL_CHECKS))

if [ $PERCENTAGE -eq 100 ]; then
    echo -e "${GREEN}✅ Todo funcionando correctamente ($PASSED/$TOTAL_CHECKS checks)${NC}"
    echo ""
    echo "🎉 Tu API está lista para usar!"
elif [ $PERCENTAGE -ge 70 ]; then
    echo -e "${YELLOW}⚠️  Funcionando con advertencias ($PASSED/$TOTAL_CHECKS checks)${NC}"
    echo ""
    echo "Revisa los errores arriba y consulta DEPLOY_PORT_80.md"
else
    echo -e "${RED}❌ Hay problemas críticos ($PASSED/$TOTAL_CHECKS checks)${NC}"
    echo ""
    echo "Acciones recomendadas:"
    echo "  1. Revisar logs: sudo journalctl -u api-electoral -n 50"
    echo "  2. Reiniciar servicios: sudo systemctl restart api-electoral nginx"
    echo "  3. Consultar: DEPLOY_PORT_80.md (sección Troubleshooting)"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
