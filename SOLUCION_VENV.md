# 🔧 Solución al Error de python3-venv

## ❌ Error Actual

```
The virtual environment was not created successfully because ensurepip is not
available. On Debian/Ubuntu systems, you need to install the python3-venv
package using the following command.

    apt install python3.13-venv
```

## ✅ Solución Inmediata (2 minutos)

### Conectarse al servidor y ejecutar:

```bash
ssh ubuntu@158.69.113.159

# Instalar python3-venv
sudo apt update
sudo apt install -y python3-venv python3-full python3-pip

# Ir al directorio del proyecto
cd /var/www/html/apielectoral

# Limpiar venv corrupto
rm -rf venv

# Crear nuevo venv
python3 -m venv venv

# Verificar que se creó correctamente
ls -la venv/bin/activate

# Activar y probar
source venv/bin/activate
python --version
pip --version
```

## 🔐 Configurar Permisos Sudo

Para que GitHub Actions pueda instalar paquetes automáticamente:

```bash
sudo visudo -f /etc/sudoers.d/api-electoral-deploy
```

Agregar este contenido:

```bash
# Permisos para GitHub Actions deployment
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/chown
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/python3
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/apt update
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/apt install
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart api-electoral
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl status api-electoral
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl stop api-electoral
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl start api-electoral
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl list-unit-files
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/pkill
```

Guardar y establecer permisos:

```bash
sudo chmod 0440 /etc/sudoers.d/api-electoral-deploy
```

## 🧪 Probar que Funciona

```bash
# Probar permisos sudo
sudo -n apt update && echo "✅ apt funciona" || echo "❌ apt no funciona"

# Probar venv
cd /var/www/html/apielectoral
source venv/bin/activate
python -c "print('✅ Python funciona')"
pip list | head -5
```

## 🚀 Hacer Push y Probar Deployment

Una vez configurado:

```bash
# En tu máquina local
git add .
git commit -m "Fix: Add python3-venv installation to workflow"
git push origin main
```

El workflow ahora:
1. ✅ Detectará si falta `python3-venv`
2. ✅ Lo instalará automáticamente
3. ✅ Creará el virtual environment
4. ✅ Instalará las dependencias
5. ✅ Iniciará la aplicación

## 📋 Verificación Completa

Ejecuta este script para verificar todo:

```bash
cd /var/www/html/apielectoral

echo "🔍 Verificación de configuración..."
echo ""

# 1. python3-venv instalado
if dpkg -l | grep -q python3.*-venv; then
    echo "✅ python3-venv instalado"
else
    echo "❌ python3-venv NO instalado"
fi

# 2. venv existe y funciona
if [ -f venv/bin/activate ]; then
    echo "✅ venv existe"
    source venv/bin/activate
    echo "   Python: $(python --version)"
    echo "   Pip: $(pip --version)"
else
    echo "❌ venv NO existe"
fi

# 3. Permisos sudo
if sudo -n apt update -qq 2>/dev/null; then
    echo "✅ Permisos sudo configurados"
else
    echo "❌ Permisos sudo NO configurados"
fi

# 4. Git configurado
if git status &>/dev/null; then
    echo "✅ Git funciona"
else
    echo "❌ Git NO funciona"
fi

# 5. Permisos del directorio
OWNER=$(stat -c '%U:%G' . 2>/dev/null || stat -f '%Su:%Sg' .)
if [ "$OWNER" = "ubuntu:ubuntu" ]; then
    echo "✅ Permisos del directorio correctos"
else
    echo "⚠️  Permisos: $OWNER (debería ser ubuntu:ubuntu)"
fi

echo ""
echo "✅ Verificación completa"
```

## 🎯 Resultado Esperado

Después de seguir estos pasos, el próximo deployment debería mostrar:

```
✅ Working directory: /var/www/html/apielectoral
✅ Git safe directory configured
✅ Directory ownership corrected
✅ Backed up .env file
📥 Pulling latest changes...
✅ Restored .env file
📦 Installing python3-venv...  (solo la primera vez)
📦 Creating virtual environment...
✅ Virtual environment activated
   Python: /var/www/html/apielectoral/venv/bin/python
   Pip: /var/www/html/apielectoral/venv/bin/pip
📦 Installing dependencies...
✅ Application started
```

---

**Tiempo estimado:** 2-3 minutos  
**Última actualización:** 2025-11-06
