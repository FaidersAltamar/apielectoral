# 🚀 Solución Rápida - Errores de GitHub Actions

## ⚡ Pasos Inmediatos (5 minutos)

### 1️⃣ Configurar Secret en GitHub (CRÍTICO)

El error principal es que falta el secret `VPS_PROJECT_PATH`.

1. Ve a: https://github.com/TU-USUARIO/api_electroral/settings/secrets/actions
2. Click en **"New repository secret"**
3. Agrega:
   - **Name:** `VPS_PROJECT_PATH`
   - **Value:** La ruta donde está tu proyecto en el servidor (ejemplo: `/home/api_electroral` o `/root/api_electroral`)

### 2️⃣ Verificar otros Secrets

Asegúrate de tener estos secrets configurados:

- ✅ `VPS_HOST` - IP del servidor (ej: `123.45.67.89`)
- ✅ `VPS_USERNAME` - Usuario SSH (ej: `root` o `apiuser`)
- ✅ `VPS_SSH_KEY` - Clave privada SSH completa
- ✅ `VPS_PROJECT_PATH` - Ruta del proyecto (ej: `/home/api_electroral`)

### 3️⃣ Preparar el Servidor (una sola vez)

Conéctate a tu servidor por SSH y ejecuta:

```bash
# Definir la ruta (usa la misma que pusiste en VPS_PROJECT_PATH)
PROJECT_DIR="/home/api_electroral"

# Crear directorio
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# Clonar repositorio
cd $PROJECT_DIR
git clone https://github.com/TU-USUARIO/api_electroral.git .

# Crear .env
cp .env.example .env
nano .env  # Editar con tus valores reales

# Crear virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Probar que funciona
python api.py
```

### 4️⃣ Verificar Configuración (Opcional)

Descarga y ejecuta el script de verificación:

```bash
cd $PROJECT_DIR
bash check_server_setup.sh
```

### 5️⃣ Hacer Push y Probar

```bash
# En tu máquina local
git add .
git commit -m "Fix: Update deployment workflow"
git push origin main
```

Ve a GitHub Actions y observa el deployment.

---

## 🔍 ¿Qué se Arregló?

El workflow ahora:

1. ✅ Valida que `VPS_PROJECT_PATH` esté configurado
2. ✅ Verifica que el directorio existe
3. ✅ Crea el virtual environment automáticamente si no existe
4. ✅ Maneja el error de Python 3.13 (externally-managed-environment)
5. ✅ Funciona sin servicio systemd (inicia la app manualmente)
6. ✅ No falla si .env no existe (solo muestra warning)

---

## 🆘 Si Aún Falla

### Error: "VPS_PROJECT_PATH secret is not set"
→ Agrega el secret en GitHub (paso 1)

### Error: "Directory does not exist"
→ Crea el directorio en el servidor (paso 3)

### Error: "Permission denied (publickey)"
→ Verifica que `VPS_SSH_KEY` tenga la clave privada completa

### Error: "Not a git repository"
→ Clona el repositorio en el servidor (paso 3)

---

## 📚 Documentación Completa

Para configuración detallada, consulta:

- **SOLUCION_ERRORES_GITHUB_ACTIONS.md** - Guía completa paso a paso
- **VPS_SETUP.md** - Configuración completa del servidor
- **PRODUCTION_DEPLOYMENT.md** - Deployment en producción

---

**Tiempo estimado:** 5-10 minutos
**Dificultad:** ⭐⭐☆☆☆
