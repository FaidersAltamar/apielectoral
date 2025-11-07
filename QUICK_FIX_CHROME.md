# ⚡ Solución Rápida - Chrome Instance Exited

## 🎯 Comando Único (Recomendado)

Conecta al servidor y ejecuta:

```bash
ssh ubuntu@158.69.113.159
cd /var/www/html/apielectoral
bash fix_chrome_production.sh
```

Este script hace TODO automáticamente:
- ✅ Actualiza el código
- ✅ Instala dependencias
- ✅ Reinicia el servicio
- ✅ Verifica que funciona

---

## 🔧 Solución Manual (3 comandos)

Si prefieres hacerlo manualmente:

```bash
# 1. Actualizar código
git pull origin main

# 2. Instalar dependencias
bash install_chrome_dependencies.sh

# 3. Reiniciar servicio
sudo systemctl restart api-electoral
```

---

## 📊 Verificar que Funciona

```bash
# Ver logs en tiempo real
sudo journalctl -u api-electoral -f

# Probar endpoint (en otra terminal)
curl http://localhost:8000/balance
```

---

## 🚨 Si Sigue Fallando

Consulta la guía completa: **[CHROME_SESSION_ERROR_FIX.md](./CHROME_SESSION_ERROR_FIX.md)**

---

## 📝 Cambios Realizados

### Código (`registraduria_scraper.py`)
✅ Agregados 6 argumentos críticos para estabilidad en producción

### Dependencias (`install_chrome_dependencies.sh`)
✅ Agregadas 11 librerías adicionales (X11, gráficas, etc.)

### Scripts
✅ `fix_chrome_production.sh` - Solución automatizada completa
✅ `CHROME_SESSION_ERROR_FIX.md` - Guía completa de troubleshooting

---

**Tiempo estimado:** 5-10 minutos  
**Última actualización:** Noviembre 7, 2025
