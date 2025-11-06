# ⚡ EJECUTAR AHORA - Solución en 3 Pasos

## 🎯 Problema Actual

El deployment de GitHub Actions está fallando por:
- ❌ Permisos incorrectos en `/var/www/html/apielectoral`
- ❌ Git ownership error
- ❌ Virtual environment no puede crearse

## ✅ Solución (3 minutos)

### Opción A: Script Automático (Recomendado)

```bash
# 1. Conectarse al servidor
ssh ubuntu@158.69.113.159

# 2. Ir al directorio
cd /var/www/html/apielectoral

# 3. Ejecutar script de configuración
bash setup_server.sh
```

El script configurará todo automáticamente.

---

### Opción B: Comandos Manuales

Si prefieres hacerlo manualmente:

```bash
# 1. Conectarse al servidor
ssh ubuntu@158.69.113.159

# 2. Corregir permisos
sudo chown -R ubuntu:ubuntu /var/www/html/apielectoral

# 3. Configurar git
cd /var/www/html/apielectoral
git config --global --add safe.directory /var/www/html/apielectoral

# 4. Instalar python3-venv y recrear virtual environment
sudo apt update
sudo apt install -y python3-venv python3-full python3-pip

rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configurar permisos sudo
sudo bash -c 'cat > /etc/sudoers.d/api-electoral-deploy << EOF
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
EOF'

sudo chmod 0440 /etc/sudoers.d/api-electoral-deploy

# 6. Crear .env si no existe
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Edita .env con: nano .env"
fi
```

---

## 🚀 Después de Configurar el Servidor

### En tu máquina local:

```bash
# 1. Hacer commit de los cambios del workflow
git add .github/workflows/deploy.yml
git commit -m "Fix: Update deployment workflow with permissions fix"

# 2. Push a GitHub
git push origin main
```

### Verificar en GitHub:

1. Ve a: https://github.com/TU-USUARIO/api_electroral/actions
2. Observa el workflow ejecutándose
3. Todos los pasos deben estar en verde ✅

---

## 🔍 Verificar que Funciona

### En el servidor:

```bash
ssh ubuntu@158.69.113.159

# Ver si la aplicación está corriendo
ps aux | grep python

# Probar la API
curl http://localhost:8000/balance
```

### Desde internet:

```bash
curl http://158.69.113.159:8000/balance
```

Deberías ver una respuesta JSON.

---

## 📊 Checklist Rápido

Antes de hacer push, verifica en el servidor:

```bash
ssh ubuntu@158.69.113.159
cd /var/www/html/apielectoral

# ✅ Verificar permisos
ls -la | grep ubuntu

# ✅ Verificar git
git status

# ✅ Verificar venv
ls -la venv/bin/activate

# ✅ Verificar .env
ls -la .env

# ✅ Verificar sudo
sudo -n chown ubuntu:ubuntu /tmp/test 2>/dev/null && echo "✅ OK" || echo "❌ Falta configurar"
```

Si todos muestran ✅, estás listo para hacer push.

---

## 🆘 Si Algo Falla

### El script falla

```bash
# Ver el error específico y ejecuta los comandos manualmente (Opción B)
```

### Git sigue dando error

```bash
sudo chown -R ubuntu:ubuntu /var/www/html/apielectoral
git config --global --add safe.directory /var/www/html/apielectoral
```

### Venv no se crea

```bash
sudo apt install python3-venv python3-full -y
rm -rf venv
python3 -m venv venv
```

### Permisos sudo no funcionan

```bash
sudo visudo -f /etc/sudoers.d/api-electoral-deploy
# Verifica que el contenido sea correcto
```

---

## 📞 Información del Servidor

- **IP:** 158.69.113.159
- **Usuario:** ubuntu
- **Puerto:** 22
- **Directorio:** /var/www/html/apielectoral

---

## 📚 Documentación Completa

Para más detalles, consulta:

- **[PASOS_INMEDIATOS.md](PASOS_INMEDIATOS.md)** - Guía paso a paso detallada
- **[README.md](README.md)** - Documentación completa del proyecto
- **[SOLUCION_ERRORES_GITHUB_ACTIONS.md](SOLUCION_ERRORES_GITHUB_ACTIONS.md)** - Troubleshooting completo

---

**⏱️ Tiempo total:** 3-5 minutos  
**🎯 Dificultad:** ⭐☆☆☆☆  
**📅 Última actualización:** 2025-11-06
