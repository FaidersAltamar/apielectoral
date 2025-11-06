# 🔧 Solución a Errores de GitHub Actions

## 📋 Resumen de Errores Encontrados

Los siguientes errores están ocurriendo en el deployment:

1. ❌ `cd ***: No such file or directory` - Secret `VPS_PROJECT_PATH` no configurado
2. ❌ `cp: cannot stat '.env'` - Archivo .env no existe o directorio incorrecto
3. ❌ `fatal: not a git repository` - No es un repositorio git o directorio incorrecto
4. ❌ `venv/bin/activate: No such file or directory` - Virtual environment no existe
5. ❌ `externally-managed-environment` - Python 3.13 con protección PEP 668
6. ❌ `api-electoral.service not found` - Servicio systemd no configurado

---

## ✅ Soluciones Implementadas

### 1. Workflow Mejorado

El archivo `.github/workflows/deploy.yml` ha sido actualizado con:

- ✅ Validación del secret `VPS_PROJECT_PATH`
- ✅ Verificación de que el directorio existe
- ✅ Verificación de repositorio git
- ✅ Creación automática del virtual environment si no existe
- ✅ Manejo de .env con warnings en lugar de errores
- ✅ Fallback si el servicio systemd no existe (inicia la app manualmente)
- ✅ Mensajes informativos con emojis

### 2. Pasos para Configurar el Servidor

#### Paso 1: Configurar GitHub Secrets

Ve a tu repositorio en GitHub → **Settings** → **Secrets and variables** → **Actions**

Agrega o verifica estos secrets:

| Secret | Valor de Ejemplo | Descripción |
|--------|------------------|-------------|
| `VPS_HOST` | `123.45.67.89` | IP o dominio del servidor |
| `VPS_USERNAME` | `root` o `apiuser` | Usuario SSH |
| `VPS_SSH_KEY` | `-----BEGIN OPENSSH...` | Clave privada SSH completa |
| `VPS_PORT` | `22` | Puerto SSH (opcional) |
| `VPS_PROJECT_PATH` | `/home/api_electroral` | **CRÍTICO: Ruta del proyecto** |
| `VPS_URL` | `http://123.45.67.89:8000` | URL para health check |

#### Paso 2: Preparar el Servidor VPS

Conéctate a tu VPS por SSH:

```bash
ssh usuario@tu-servidor
```

**A. Crear el directorio del proyecto:**

```bash
# Opción 1: En /home (recomendado para usuario normal)
sudo mkdir -p /home/api_electroral
sudo chown $USER:$USER /home/api_electroral

# Opción 2: En /var/www (requiere permisos especiales)
sudo mkdir -p /var/www/api_electroral
sudo chown $USER:$USER /var/www/api_electroral
```

**B. Clonar el repositorio:**

```bash
cd /home/api_electroral  # o la ruta que elegiste
git clone https://github.com/TU-USUARIO/api_electroral.git .

# Configurar git para pull sin problemas
git config pull.rebase false
```

**C. Crear archivo .env:**

```bash
cp .env.example .env
nano .env
```

Configurar las variables necesarias:
```env
APIKEY_2CAPTCHA=tu_api_key_real
HEADLESS_MODE=True
EXTERNAL_API_NOMBRE_URL=https://tu-api.com/nombre
EXTERNAL_API_PUESTO_URL=https://tu-api.com/puesto
```

**D. Instalar dependencias del sistema:**

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python y herramientas
sudo apt install -y python3 python3-venv python3-pip git

# Instalar Chrome (necesario para Selenium)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb
```

**E. Crear virtual environment:**

```bash
cd /home/api_electroral
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**F. Probar la aplicación manualmente:**

```bash
source venv/bin/activate
python api.py
# O si usas uvicorn:
uvicorn api:app --host 0.0.0.0 --port 8000
```

Verifica en otra terminal:
```bash
curl http://localhost:8000/balance
```

#### Paso 3: Configurar Servicio Systemd (Opcional pero Recomendado)

**A. Crear archivo de servicio:**

```bash
sudo nano /etc/systemd/system/api-electoral.service
```

**B. Contenido del archivo:**

```ini
[Unit]
Description=API Electoral - FastAPI Application
After=network.target

[Service]
Type=simple
User=TU_USUARIO_AQUI
WorkingDirectory=/home/api_electroral
Environment="PATH=/home/api_electroral/venv/bin"
EnvironmentFile=/home/api_electroral/.env
ExecStart=/home/api_electroral/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

# Limites de recursos
LimitNOFILE=65536

# Logs
StandardOutput=append:/var/log/api-electoral/access.log
StandardError=append:/var/log/api-electoral/error.log

[Install]
WantedBy=multi-user.target
```

**C. Crear directorio de logs:**

```bash
sudo mkdir -p /var/log/api-electoral
sudo chown $USER:$USER /var/log/api-electoral
```

**D. Habilitar y iniciar el servicio:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable api-electoral
sudo systemctl start api-electoral
sudo systemctl status api-electoral
```

**E. Configurar permisos sudo para GitHub Actions:**

```bash
sudo visudo
```

Agregar al final (reemplaza `TU_USUARIO` con tu usuario real):
```
TU_USUARIO ALL=(ALL) NOPASSWD: /bin/systemctl restart api-electoral
TU_USUARIO ALL=(ALL) NOPASSWD: /bin/systemctl status api-electoral
TU_USUARIO ALL=(ALL) NOPASSWD: /bin/systemctl stop api-electoral
TU_USUARIO ALL=(ALL) NOPASSWD: /bin/systemctl start api-electoral
TU_USUARIO ALL=(ALL) NOPASSWD: /bin/systemctl list-unit-files
```

#### Paso 4: Configurar SSH para GitHub Actions

**A. Generar clave SSH (si no tienes una):**

```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github-actions
```

**B. Agregar clave pública al servidor:**

```bash
cat ~/.ssh/github-actions.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

**C. Copiar clave privada para GitHub:**

```bash
cat ~/.ssh/github-actions
```

Copia **TODO** el contenido (incluyendo `-----BEGIN` y `-----END`) y agrégalo como secret `VPS_SSH_KEY` en GitHub.

---

## 🧪 Probar el Deployment

### Opción 1: Push a main

```bash
git add .
git commit -m "Fix: Update deployment workflow"
git push origin main
```

Ve a GitHub → Actions y observa el workflow ejecutándose.

### Opción 2: Trigger manual

1. Ve a GitHub → Actions
2. Selecciona "Deploy to VPS"
3. Click en "Run workflow"
4. Selecciona la rama `main`
5. Click en "Run workflow"

---

## 📊 Verificar el Deployment

### En GitHub Actions:

- ✅ Todos los pasos deben estar en verde
- ✅ Debes ver mensajes como "✅ Working directory: /home/api_electroral"
- ✅ "✅ Virtual environment activated"
- ✅ "✅ Application started"

### En el servidor:

```bash
# Ver logs del servicio
sudo journalctl -u api-electoral -f

# O si no usas systemd, ver procesos
ps aux | grep python

# Probar la API
curl http://localhost:8000/balance
```

### Desde internet:

```bash
curl http://TU_IP:8000/balance
```

---

## 🐛 Troubleshooting

### Error: "VPS_PROJECT_PATH secret is not set"

**Solución:** Agrega el secret en GitHub → Settings → Secrets → Actions

```
Nombre: VPS_PROJECT_PATH
Valor: /home/api_electroral
```

### Error: "Directory does not exist"

**Solución:** Crea el directorio en el servidor:

```bash
sudo mkdir -p /home/api_electroral
sudo chown $USER:$USER /home/api_electroral
cd /home/api_electroral
git clone https://github.com/TU-USUARIO/api_electroral.git .
```

### Error: "Not a git repository"

**Solución:** Inicializa o clona el repositorio:

```bash
cd /home/api_electroral
git init
git remote add origin https://github.com/TU-USUARIO/api_electroral.git
git pull origin main
```

### Error: "Permission denied (publickey)"

**Solución:** Verifica la clave SSH:

```bash
# En el servidor
cat ~/.ssh/authorized_keys
# Debe contener la clave pública

# Verifica permisos
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### Error: "externally-managed-environment"

**Solución:** El workflow ahora crea automáticamente el venv. Si persiste:

```bash
cd /home/api_electroral
python3 -m venv venv
```

### La aplicación no responde

**Solución:** Verifica que esté corriendo:

```bash
# Si usas systemd
sudo systemctl status api-electoral

# Si no
ps aux | grep python
netstat -tulpn | grep 8000
```

---

## 📝 Checklist Final

Antes de hacer push, verifica:

- [ ] Secret `VPS_PROJECT_PATH` configurado en GitHub
- [ ] Secret `VPS_SSH_KEY` configurado en GitHub
- [ ] Secret `VPS_HOST` configurado en GitHub
- [ ] Secret `VPS_USERNAME` configurado en GitHub
- [ ] Directorio del proyecto existe en el servidor
- [ ] Repositorio clonado en el servidor
- [ ] Archivo `.env` configurado en el servidor
- [ ] Virtual environment creado en el servidor
- [ ] Dependencias instaladas
- [ ] Aplicación funciona manualmente
- [ ] Servicio systemd configurado (opcional)
- [ ] Permisos sudo configurados (si usas systemd)

---

## 🎯 Próximos Pasos

Una vez que el deployment funcione:

1. ✅ Configurar Nginx como reverse proxy
2. ✅ Configurar SSL con Let's Encrypt
3. ✅ Configurar firewall (UFW)
4. ✅ Implementar monitoreo
5. ✅ Configurar backups automáticos

---

**Última actualización:** 2025-11-06
