#!/bin/bash

# Script para verificar la configuración del servidor antes del deployment
# Uso: bash check_server_setup.sh

echo "🔍 Verificando configuración del servidor para API Electoral..."
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contadores
ERRORS=0
WARNINGS=0
SUCCESS=0

# Función para verificar
check() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((SUCCESS++))
    else
        echo -e "${RED}❌ $2${NC}"
        ((ERRORS++))
    fi
}

check_warning() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((SUCCESS++))
    else
        echo -e "${YELLOW}⚠️  $2${NC}"
        ((WARNINGS++))
    fi
}

echo "📁 Verificando estructura de directorios..."
echo "=============================================="

# Verificar directorio del proyecto
if [ -d "/home/api_electroral" ]; then
    PROJECT_DIR="/home/api_electroral"
elif [ -d "/var/www/api_electroral" ]; then
    PROJECT_DIR="/var/www/api_electroral"
else
    echo -e "${RED}❌ Directorio del proyecto no encontrado${NC}"
    echo "   Buscar en: /home/api_electroral o /var/www/api_electroral"
    ((ERRORS++))
    PROJECT_DIR=""
fi

if [ -n "$PROJECT_DIR" ]; then
    echo -e "${GREEN}✅ Directorio del proyecto: $PROJECT_DIR${NC}"
    ((SUCCESS++))
    cd "$PROJECT_DIR" || exit 1
    
    # Verificar repositorio git
    [ -d .git ]
    check $? "Repositorio git inicializado"
    
    # Verificar archivos importantes
    [ -f api.py ]
    check $? "Archivo api.py existe"
    
    [ -f requirements.txt ]
    check $? "Archivo requirements.txt existe"
    
    [ -f .env ]
    check_warning $? "Archivo .env existe (puede crearse desde .env.example)"
    
    [ -f .env.example ]
    check $? "Archivo .env.example existe"
    
    echo ""
    echo "🐍 Verificando Python y entorno virtual..."
    echo "=============================================="
    
    # Verificar Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        echo -e "${GREEN}✅ Python instalado: $PYTHON_VERSION${NC}"
        ((SUCCESS++))
    else
        echo -e "${RED}❌ Python3 no está instalado${NC}"
        ((ERRORS++))
    fi
    
    # Verificar virtual environment
    [ -d venv ]
    check_warning $? "Virtual environment existe (se creará automáticamente si no existe)"
    
    if [ -d venv ]; then
        [ -f venv/bin/activate ]
        check $? "Script de activación del venv existe"
        
        [ -f venv/bin/python ]
        check $? "Python en venv existe"
        
        [ -f venv/bin/pip ]
        check $? "Pip en venv existe"
    fi
    
    echo ""
    echo "🌐 Verificando dependencias del sistema..."
    echo "=============================================="
    
    # Verificar Chrome
    if command -v google-chrome &> /dev/null; then
        CHROME_VERSION=$(google-chrome --version)
        echo -e "${GREEN}✅ Google Chrome instalado: $CHROME_VERSION${NC}"
        ((SUCCESS++))
    else
        echo -e "${YELLOW}⚠️  Google Chrome no está instalado (necesario para Selenium)${NC}"
        ((WARNINGS++))
    fi
    
    # Verificar git
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version)
        echo -e "${GREEN}✅ Git instalado: $GIT_VERSION${NC}"
        ((SUCCESS++))
    else
        echo -e "${RED}❌ Git no está instalado${NC}"
        ((ERRORS++))
    fi
    
    echo ""
    echo "⚙️  Verificando servicio systemd..."
    echo "=============================================="
    
    # Verificar servicio
    if systemctl list-unit-files | grep -q "api-electoral.service"; then
        echo -e "${GREEN}✅ Servicio api-electoral.service existe${NC}"
        ((SUCCESS++))
        
        # Estado del servicio
        if systemctl is-active --quiet api-electoral; then
            echo -e "${GREEN}✅ Servicio está activo${NC}"
            ((SUCCESS++))
        else
            echo -e "${YELLOW}⚠️  Servicio existe pero no está activo${NC}"
            ((WARNINGS++))
        fi
        
        if systemctl is-enabled --quiet api-electoral; then
            echo -e "${GREEN}✅ Servicio está habilitado${NC}"
            ((SUCCESS++))
        else
            echo -e "${YELLOW}⚠️  Servicio no está habilitado para inicio automático${NC}"
            ((WARNINGS++))
        fi
    else
        echo -e "${YELLOW}⚠️  Servicio api-electoral.service no configurado${NC}"
        echo "   El workflow usará inicio manual como fallback"
        ((WARNINGS++))
    fi
    
    echo ""
    echo "🔐 Verificando permisos..."
    echo "=============================================="
    
    # Verificar permisos del directorio
    if [ -w "$PROJECT_DIR" ]; then
        echo -e "${GREEN}✅ Permisos de escritura en $PROJECT_DIR${NC}"
        ((SUCCESS++))
    else
        echo -e "${RED}❌ Sin permisos de escritura en $PROJECT_DIR${NC}"
        ((ERRORS++))
    fi
    
    # Verificar SSH
    if [ -d ~/.ssh ]; then
        echo -e "${GREEN}✅ Directorio .ssh existe${NC}"
        ((SUCCESS++))
        
        if [ -f ~/.ssh/authorized_keys ]; then
            echo -e "${GREEN}✅ Archivo authorized_keys existe${NC}"
            ((SUCCESS++))
            
            # Verificar permisos
            PERMS=$(stat -c %a ~/.ssh/authorized_keys 2>/dev/null || stat -f %A ~/.ssh/authorized_keys 2>/dev/null)
            if [ "$PERMS" = "600" ]; then
                echo -e "${GREEN}✅ Permisos de authorized_keys correctos (600)${NC}"
                ((SUCCESS++))
            else
                echo -e "${YELLOW}⚠️  Permisos de authorized_keys: $PERMS (debería ser 600)${NC}"
                ((WARNINGS++))
            fi
        else
            echo -e "${RED}❌ Archivo authorized_keys no existe${NC}"
            ((ERRORS++))
        fi
    else
        echo -e "${RED}❌ Directorio .ssh no existe${NC}"
        ((ERRORS++))
    fi
    
    echo ""
    echo "🔌 Verificando puertos..."
    echo "=============================================="
    
    # Verificar puerto 8000
    if command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":8000 "; then
            echo -e "${YELLOW}⚠️  Puerto 8000 está en uso${NC}"
            echo "   Procesos usando el puerto:"
            netstat -tulpn 2>/dev/null | grep ":8000 " || echo "   (requiere sudo para ver procesos)"
            ((WARNINGS++))
        else
            echo -e "${GREEN}✅ Puerto 8000 está disponible${NC}"
            ((SUCCESS++))
        fi
    else
        echo -e "${YELLOW}⚠️  netstat no disponible, no se puede verificar puerto${NC}"
        ((WARNINGS++))
    fi
    
    echo ""
    echo "📝 Verificando configuración de git..."
    echo "=============================================="
    
    # Verificar remote
    if git remote -v | grep -q "origin"; then
        echo -e "${GREEN}✅ Remote 'origin' configurado${NC}"
        git remote -v | grep origin | head -1
        ((SUCCESS++))
    else
        echo -e "${RED}❌ Remote 'origin' no configurado${NC}"
        ((ERRORS++))
    fi
    
    # Verificar rama actual
    CURRENT_BRANCH=$(git branch --show-current)
    echo "   Rama actual: $CURRENT_BRANCH"
    
    # Verificar si hay cambios sin commit
    if git diff-index --quiet HEAD --; then
        echo -e "${GREEN}✅ No hay cambios sin commit${NC}"
        ((SUCCESS++))
    else
        echo -e "${YELLOW}⚠️  Hay cambios sin commit${NC}"
        ((WARNINGS++))
    fi
fi

echo ""
echo "=============================================="
echo "📊 RESUMEN"
echo "=============================================="
echo -e "${GREEN}✅ Exitosos: $SUCCESS${NC}"
echo -e "${YELLOW}⚠️  Advertencias: $WARNINGS${NC}"
echo -e "${RED}❌ Errores: $ERRORS${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 ¡Servidor configurado correctamente!${NC}"
    echo "   Puedes proceder con el deployment desde GitHub Actions"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Servidor configurado con advertencias${NC}"
    echo "   El deployment debería funcionar, pero revisa las advertencias"
    exit 0
else
    echo -e "${RED}❌ Se encontraron errores críticos${NC}"
    echo "   Corrige los errores antes de hacer deployment"
    echo ""
    echo "💡 Consulta SOLUCION_ERRORES_GITHUB_ACTIONS.md para más ayuda"
    exit 1
fi
