# 🗳️ API Electoral

API FastAPI para consultar información electoral de Colombia mediante web scraping de fuentes oficiales.

## 🌐 Despliegue en Puerto 80

### ⚡ Setup Rápido (5 minutos)

```bash
cd /var/www/html/apielectoral
chmod +x setup_port_80.sh
sudo ./setup_port_80.sh
```

**Arquitectura:** Internet (Puerto 80) → Nginx → FastAPI (Puerto 8000)

📖 **Guía completa:** [QUICK_START_PORT_80.md](QUICK_START_PORT_80.md)

---

## 🚀 Inicio Rápido

### Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/TU-USUARIO/api_electroral.git
cd api_electroral

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Ejecutar
python api.py
```

La API estará disponible en: http://localhost:8000

## 📚 Documentación

### 🆘 ¿Errores en GitHub Actions?

**Solución rápida (5 min):** [PASOS_INMEDIATOS.md](PASOS_INMEDIATOS.md)

### 📖 Guías de Deployment

| Documento | Descripción | Tiempo |
|-----------|-------------|--------|
| **[DEPLOY_PORT_80.md](DEPLOY_PORT_80.md)** | 🌐 **Despliegue en puerto 80 con Nginx** | 15-20 min |
| **[PASOS_INMEDIATOS.md](PASOS_INMEDIATOS.md)** | ⚡ Solución paso a paso a errores actuales | 10-15 min |
| **[QUICK_FIX.md](QUICK_FIX.md)** | 🔧 Configuración rápida de secrets | 5 min |
| **[SOLUCION_ERRORES_GITHUB_ACTIONS.md](SOLUCION_ERRORES_GITHUB_ACTIONS.md)** | 📖 Guía completa de troubleshooting | 20-30 min |
| **[CONFIGURAR_PERMISOS_SUDO.md](CONFIGURAR_PERMISOS_SUDO.md)** | 🔐 Configuración de permisos sudo | 5 min |
| **[VPS_SETUP.md](VPS_SETUP.md)** | 🖥️ Configuración completa del servidor | 30-60 min |
| **[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)** | 🚀 Deployment en producción | 60+ min |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | 🏗️ Arquitectura del proyecto | - |

### 🛠️ Scripts Útiles

| Script | Descripción | Uso |
|--------|-------------|-----|
| **[setup_server.sh](setup_server.sh)** | Configuración automática del servidor | `bash setup_server.sh` |
| **[check_server_setup.sh](check_server_setup.sh)** | Verificar configuración del servidor | `bash check_server_setup.sh` |

## 🔥 Solución Rápida a Errores Comunes

### Error: "dubious ownership in repository"

```bash
ssh ubuntu@158.69.113.159
git config --global --add safe.directory /var/www/html/apielectoral
```

### Error: "Permission denied" al crear venv

```bash
ssh ubuntu@158.69.113.159
sudo chown -R ubuntu:ubuntu /var/www/html/apielectoral
```

### Error: "externally-managed-environment"

```bash
ssh ubuntu@158.69.113.159
cd /var/www/html/apielectoral
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuración Completa Automática

```bash
# En el servidor VPS
ssh ubuntu@158.69.113.159
cd /var/www/html/apielectoral
bash setup_server.sh
```

## 📋 Endpoints de la API

### Balance de Carga
```bash
GET /balance
```

### Consultar Nombre por Cédula
```bash
POST /get_name
{
  "cedula": "1234567890"
}
```

### Consultar Puesto de Votación
```bash
POST /get_puesto
{
  "cedula": "1234567890"
}
```

### Consultar Antecedentes Procuraduría
```bash
POST /get_procuraduria
{
  "cedula": "1234567890"
}
```

### Consultar Antecedentes Policía
```bash
POST /get_police
{
  "cedula": "1234567890"
}
```

### Consultar SISBEN
```bash
POST /get_sisben
{
  "cedula": "1234567890"
}
```

## 🏗️ Arquitectura

```
api_electroral/
├── api.py                 # Aplicación FastAPI principal
├── config.py             # Configuración
├── task_manager.py       # Gestor de tareas asíncronas
├── models/
│   └── request.py        # Modelos de datos
├── scrapper/
│   ├── registraduria_scraper.py
│   ├── procuraduria_scraper.py
│   ├── police_scraper.py
│   └── sisben_scraper.py
├── utils/
│   ├── captcha_solver.py
│   └── time_utils.py
└── .github/
    └── workflows/
        └── deploy.yml    # CI/CD con GitHub Actions
```

## 🔧 Variables de Entorno

Crea un archivo `.env` basado en `.env.example`:

```env
# API Key para 2Captcha
APIKEY_2CAPTCHA=tu_api_key_aqui

# Modo headless para Selenium
HEADLESS_MODE=True

# URLs de APIs externas (opcional)
EXTERNAL_API_NOMBRE_URL=https://tu-api.com/nombre
EXTERNAL_API_PUESTO_URL=https://tu-api.com/puesto
```

## 🚀 Deployment

### Configuración de GitHub Secrets

Solo necesitas configurar un secret:

- `VPS_SSH_KEY`: Clave privada SSH para conectar al servidor

Los demás valores están hardcodeados en el workflow:
- Host: `158.69.113.159`
- Usuario: `ubuntu`
- Puerto: `22`
- Directorio: `/var/www/html/apielectoral`

### Deployment Automático

El deployment se ejecuta automáticamente al hacer push a `main`:

```bash
git add .
git commit -m "Update code"
git push origin main
```

### Deployment Manual

Ve a GitHub → Actions → "Deploy to VPS" → "Run workflow"

## 🧪 Testing

```bash
# Probar conexión a Registraduría
python test_procuraduria_connection.py

# Probar ChromeDriver
python test_chromedriver.py

# Probar SISBEN
python test_sisben_driver.py
```

## 📊 Monitoreo

### Ver logs del servicio

```bash
ssh ubuntu@158.69.113.159
sudo journalctl -u api-electoral -f
```

### Ver logs de la aplicación

```bash
ssh ubuntu@158.69.113.159
tail -f /var/log/api-electoral/access.log
tail -f /var/log/api-electoral/error.log
```

### Estado del servicio

```bash
ssh ubuntu@158.69.113.159
sudo systemctl status api-electoral
```

## 🔒 Seguridad

- ✅ Autenticación SSH con clave privada
- ✅ Variables sensibles en `.env`
- ✅ Permisos sudo limitados
- ✅ Logs separados por tipo
- ✅ Rate limiting (recomendado implementar)

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto es privado y confidencial.

## 🆘 Soporte

Si encuentras problemas:

1. **Revisa la documentación:** Empieza con [PASOS_INMEDIATOS.md](PASOS_INMEDIATOS.md)
2. **Ejecuta el script de verificación:** `bash check_server_setup.sh`
3. **Revisa los logs:** GitHub Actions o logs del servidor
4. **Consulta troubleshooting:** [SOLUCION_ERRORES_GITHUB_ACTIONS.md](SOLUCION_ERRORES_GITHUB_ACTIONS.md)

## 📞 Contacto

- **Servidor:** 158.69.113.159
- **Usuario:** ubuntu
- **Puerto SSH:** 22
- **Directorio:** /var/www/html/apielectoral

---

**Última actualización:** 2025-11-06  
**Versión:** 1.0.0
