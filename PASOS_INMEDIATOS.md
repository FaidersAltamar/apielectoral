# ⚡ Pasos Inmediatos para Solucionar Errores

## 🎯 Resumen de Errores Actuales

1. ❌ **Git ownership error** - `fatal: detected dubious ownership`
2. ❌ **Permission denied** - No puede crear venv en `/var/www/html/apielectoral`
3. ❌ **externally-managed-environment** - Python 3.13 con PEP 668

## ✅ Solución (Ejecutar en el Servidor VPS)

### Conectarse al servidor

```bash
ssh ubuntu@158.69.113.159
```

---

## 🔧 Paso 1: Corregir Permisos del Directorio

```bash
# Cambiar ownership del directorio completo
sudo chown -R ubuntu:ubuntu /var/www/html/apielectoral

# Verificar permisos
ls -la /var/www/html/apielectoral
```

**Resultado esperado:** Todos los archivos deben pertenecer a `ubuntu:ubuntu`

---

## 🔧 Paso 2: Configurar Git Safe Directory

```bash
cd /var/www/html/apielectoral

# Agregar como directorio seguro
git config --global --add safe.directory /var/www/html/apielectoral

# Verificar
git status
```

**Resultado esperado:** `git status` debe funcionar sin errores

---

## 🔧 Paso 3: Crear Virtual Environment

```bash
cd /var/www/html/apielectoral

# Eliminar venv corrupto si existe
rm -rf venv

# Crear nuevo venv
python3 -m venv venv

# Verificar que se creó correctamente
ls -la venv/bin/activate
```

**Resultado esperado:** El archivo `venv/bin/activate` debe existir

---

## 🔧 Paso 4: Instalar Dependencias

```bash
cd /var/www/html/apielectoral

# Activar venv
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

**Resultado esperado:** Todas las dependencias instaladas sin errores

---

## 🔧 Paso 5: Configurar Permisos Sudo

```bash
sudo visudo
```

Agregar al **final** del archivo:

```bash
# Permisos para GitHub Actions deployment
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/chown
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/python3
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart api-electoral
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl status api-electoral
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl stop api-electoral
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl start api-electoral
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl list-unit-files
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/pkill
```

Guardar: `Ctrl + X`, luego `Y`, luego `Enter`

**Verificar:**
```bash
sudo chown ubuntu:ubuntu /var/www/html/apielectoral
# No debe pedir contraseña
```

---

## 🔧 Paso 6: Crear archivo .env

```bash
cd /var/www/html/apielectoral

# Copiar desde ejemplo
cp .env.example .env

# Editar con tus valores
nano .env
```

Configurar:
```env
APIKEY_2CAPTCHA=tu_api_key_real
HEADLESS_MODE=True
EXTERNAL_API_NOMBRE_URL=https://tu-api.com/nombre
EXTERNAL_API_PUESTO_URL=https://tu-api.com/puesto
```

Guardar: `Ctrl + X`, luego `Y`, luego `Enter`

---

## 🔧 Paso 7: Probar la Aplicación

```bash
cd /var/www/html/apielectoral
source venv/bin/activate

# Ejecutar la aplicación
python api.py
```

En otra terminal, probar:
```bash
curl http://localhost:8000/balance
```

**Resultado esperado:** Respuesta JSON de la API

---

## 🔧 Paso 8: Configurar Servicio Systemd (Opcional)

```bash
sudo nano /etc/systemd/system/api-electoral.service
```

Contenido:
```ini
[Unit]
Description=API Electoral - FastAPI Application
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/var/www/html/apielectoral
Environment="PATH=/var/www/html/apielectoral/venv/bin"
EnvironmentFile=/var/www/html/apielectoral/.env
ExecStart=/var/www/html/apielectoral/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

# Limites
LimitNOFILE=65536

# Logs
StandardOutput=append:/var/log/api-electoral/access.log
StandardError=append:/var/log/api-electoral/error.log

[Install]
WantedBy=multi-user.target
```

Guardar y activar:
```bash
# Crear directorio de logs
sudo mkdir -p /var/log/api-electoral
sudo chown ubuntu:ubuntu /var/log/api-electoral

# Habilitar servicio
sudo systemctl daemon-reload
sudo systemctl enable api-electoral
sudo systemctl start api-electoral

# Verificar estado
sudo systemctl status api-electoral
```

---

## 🧪 Paso 9: Probar Deployment desde GitHub

Una vez completados los pasos anteriores:

1. Hacer commit y push:
   ```bash
   git add .
   git commit -m "Fix: Configure server permissions and workflow"
   git push origin main
   ```

2. Ve a GitHub → Actions y observa el workflow

3. Todos los pasos deben completarse en verde ✅

---

## 📊 Checklist de Verificación

Antes de hacer push, verifica en el servidor:

- [ ] Permisos del directorio corregidos (`ubuntu:ubuntu`)
- [ ] Git safe directory configurado
- [ ] Virtual environment creado y funcional
- [ ] Dependencias instaladas
- [ ] Archivo `.env` configurado
- [ ] Permisos sudo configurados
- [ ] Aplicación funciona manualmente
- [ ] Servicio systemd configurado (opcional)

---

## 🔍 Verificación Rápida

Ejecuta este script en el servidor para verificar todo:

```bash
cd /var/www/html/apielectoral

echo "🔍 Verificando configuración..."
echo ""

# Verificar ownership
echo "1. Ownership del directorio:"
ls -ld /var/www/html/apielectoral

# Verificar git
echo ""
echo "2. Git status:"
git status --short

# Verificar venv
echo ""
echo "3. Virtual environment:"
if [ -f venv/bin/activate ]; then
    echo "   ✅ venv existe"
    source venv/bin/activate
    echo "   Python: $(which python)"
    echo "   Pip: $(which pip)"
else
    echo "   ❌ venv no existe"
fi

# Verificar .env
echo ""
echo "4. Archivo .env:"
if [ -f .env ]; then
    echo "   ✅ .env existe"
else
    echo "   ❌ .env no existe"
fi

# Verificar permisos sudo
echo ""
echo "5. Permisos sudo:"
if sudo -n chown ubuntu:ubuntu /tmp/test 2>/dev/null; then
    echo "   ✅ Permisos sudo configurados"
else
    echo "   ❌ Permisos sudo no configurados"
fi

echo ""
echo "✅ Verificación completa"
```

---

## 🆘 Si Algo Falla

### Error: "Permission denied"
```bash
sudo chown -R ubuntu:ubuntu /var/www/html/apielectoral
```

### Error: "dubious ownership"
```bash
git config --global --add safe.directory /var/www/html/apielectoral
```

### Error: "externally-managed-environment"
```bash
# Asegúrate de estar en el venv
source venv/bin/activate
which pip  # Debe mostrar: /var/www/html/apielectoral/venv/bin/pip
```

### Error: "venv not found"
```bash
rm -rf venv
python3 -m venv venv
```

---

## 📞 Soporte

Si después de seguir todos los pasos aún hay errores:

1. Revisa los logs del workflow en GitHub Actions
2. Ejecuta el script de verificación en el servidor
3. Consulta `SOLUCION_ERRORES_GITHUB_ACTIONS.md` para más detalles

---

**Tiempo estimado:** 10-15 minutos  
**Última actualización:** 2025-11-06
