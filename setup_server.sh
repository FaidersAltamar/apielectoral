#!/bin/bash

# Script de configuración automática del servidor VPS
# Ejecutar como: bash setup_server.sh

set -e  # Salir si hay algún error

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
PROJECT_DIR="/var/www/html/apielectoral"
USER="ubuntu"

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🚀 Configuración Automática del Servidor    ║${NC}"
echo -e "${BLUE}║        API Electoral - Deployment Setup       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Función para mostrar progreso
step() {
    echo ""
    echo -e "${BLUE}▶ $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar que estamos en el servidor correcto
step "Verificando servidor..."
if [ ! -d "$PROJECT_DIR" ]; then
    error "Directorio $PROJECT_DIR no existe"
    echo "Por favor, clona el repositorio primero:"
    echo "  sudo mkdir -p $PROJECT_DIR"
    echo "  sudo chown $USER:$USER $PROJECT_DIR"
    echo "  cd $PROJECT_DIR"
    echo "  git clone https://github.com/almanza023/api_electroral.git ."
    exit 1
fi
success "Directorio del proyecto encontrado"

# Paso 1: Corregir permisos
step "Paso 1/8: Corrigiendo permisos del directorio..."
sudo chown -R $USER:$USER "$PROJECT_DIR"
success "Permisos corregidos"

# Paso 2: Configurar Git
step "Paso 2/8: Configurando Git safe directory..."
cd "$PROJECT_DIR"
git config --global --add safe.directory "$PROJECT_DIR"
success "Git configurado"

# Verificar git
if git status &>/dev/null; then
    success "Git funciona correctamente"
else
    error "Git no funciona correctamente"
    exit 1
fi

# Paso 3: Limpiar y crear venv
step "Paso 3/8: Configurando virtual environment..."
if [ -d venv ]; then
    warning "Virtual environment existente encontrado"
    read -p "¿Deseas recrearlo? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm -rf venv
        success "Virtual environment anterior eliminado"
    fi
fi

if [ ! -d venv ]; then
    echo "Creando virtual environment..."
    python3 -m venv venv
    success "Virtual environment creado"
else
    success "Virtual environment ya existe"
fi

# Verificar venv
if [ ! -f venv/bin/activate ]; then
    error "Virtual environment no se creó correctamente"
    exit 1
fi

# Paso 4: Instalar dependencias
step "Paso 4/8: Instalando dependencias..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
success "Dependencias instaladas"

# Paso 5: Configurar .env
step "Paso 5/8: Configurando archivo .env..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        warning "Archivo .env creado desde .env.example"
        echo "⚠️  IMPORTANTE: Edita el archivo .env con tus valores reales:"
        echo "   nano $PROJECT_DIR/.env"
    else
        error ".env.example no encontrado"
    fi
else
    success "Archivo .env ya existe"
fi

# Paso 6: Verificar dependencias del sistema
step "Paso 6/8: Verificando dependencias del sistema..."

# Verificar Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    success "Python instalado: $PYTHON_VERSION"
else
    error "Python3 no está instalado"
    exit 1
fi

# Verificar Chrome
if command -v google-chrome &> /dev/null; then
    CHROME_VERSION=$(google-chrome --version 2>/dev/null || echo "instalado")
    success "Google Chrome: $CHROME_VERSION"
else
    warning "Google Chrome no está instalado"
    echo "Instalando Google Chrome..."
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo apt install -y ./google-chrome-stable_current_amd64.deb
    rm google-chrome-stable_current_amd64.deb
    success "Google Chrome instalado"
fi

# Paso 7: Configurar permisos sudo
step "Paso 7/8: Configurando permisos sudo..."

SUDOERS_FILE="/etc/sudoers.d/api-electoral-deploy"

if [ -f "$SUDOERS_FILE" ]; then
    success "Permisos sudo ya configurados"
else
    echo "Creando configuración de permisos sudo..."
    sudo tee "$SUDOERS_FILE" > /dev/null <<EOF
# Permisos para GitHub Actions deployment
$USER ALL=(ALL) NOPASSWD: /usr/bin/chown
$USER ALL=(ALL) NOPASSWD: /usr/bin/python3
$USER ALL=(ALL) NOPASSWD: /bin/systemctl restart api-electoral
$USER ALL=(ALL) NOPASSWD: /bin/systemctl status api-electoral
$USER ALL=(ALL) NOPASSWD: /bin/systemctl stop api-electoral
$USER ALL=(ALL) NOPASSWD: /bin/systemctl start api-electoral
$USER ALL=(ALL) NOPASSWD: /bin/systemctl list-unit-files
$USER ALL=(ALL) NOPASSWD: /usr/bin/pkill
EOF
    sudo chmod 0440 "$SUDOERS_FILE"
    success "Permisos sudo configurados"
fi

# Verificar permisos sudo
if sudo -n chown $USER:$USER /tmp/test 2>/dev/null; then
    success "Permisos sudo funcionan correctamente"
else
    warning "Permisos sudo pueden no estar funcionando"
fi

# Paso 8: Configurar servicio systemd (opcional)
step "Paso 8/8: Configurando servicio systemd..."

SERVICE_FILE="/etc/systemd/system/api-electoral.service"

if [ -f "$SERVICE_FILE" ]; then
    success "Servicio systemd ya configurado"
else
    read -p "¿Deseas configurar el servicio systemd? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo "Creando servicio systemd..."
        
        # Crear directorio de logs
        sudo mkdir -p /var/log/api-electoral
        sudo chown $USER:$USER /var/log/api-electoral
        
        # Crear archivo de servicio
        sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=API Electoral - FastAPI Application
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

# Limites
LimitNOFILE=65536

# Logs
StandardOutput=append:/var/log/api-electoral/access.log
StandardError=append:/var/log/api-electoral/error.log

[Install]
WantedBy=multi-user.target
EOF
        
        # Recargar systemd
        sudo systemctl daemon-reload
        sudo systemctl enable api-electoral
        
        success "Servicio systemd configurado"
        
        read -p "¿Deseas iniciar el servicio ahora? (s/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            sudo systemctl start api-electoral
            sleep 2
            sudo systemctl status api-electoral --no-pager
        fi
    else
        warning "Servicio systemd no configurado"
    fi
fi

# Resumen final
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            ✅ Configuración Completa           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📊 Resumen:${NC}"
echo "   • Directorio: $PROJECT_DIR"
echo "   • Usuario: $USER"
echo "   • Python: $(python3 --version)"
echo "   • Virtual env: ✅"
echo "   • Dependencias: ✅"
echo "   • Permisos: ✅"
echo ""

# Verificar .env
if [ -f .env ]; then
    if grep -q "YOUR_API_KEY_HERE" .env 2>/dev/null || grep -q "tu_api_key" .env 2>/dev/null; then
        echo -e "${YELLOW}⚠️  IMPORTANTE: Configura el archivo .env con tus valores reales:${NC}"
        echo "   nano $PROJECT_DIR/.env"
        echo ""
    fi
fi

echo -e "${GREEN}🎯 Próximos pasos:${NC}"
echo "   1. Editar .env con tus valores reales (si no lo has hecho)"
echo "   2. Hacer push desde tu repositorio local"
echo "   3. Observar el deployment en GitHub Actions"
echo ""

# Probar la aplicación
read -p "¿Deseas probar la aplicación ahora? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo "Iniciando aplicación en modo prueba..."
    echo "Presiona Ctrl+C para detener"
    echo ""
    cd "$PROJECT_DIR"
    source venv/bin/activate
    python api.py
fi

echo ""
echo -e "${GREEN}✅ ¡Configuración completada exitosamente!${NC}"
