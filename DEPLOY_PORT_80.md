# Despliegue de API en Puerto 80

## 📋 Resumen

La API FastAPI ahora está configurada para correr **directamente en el puerto 80** sin nginx como proxy reverso.

## ⚙️ Cambios Realizados

### 1. `api-electoral.service`
- Puerto cambiado de `8000` a `80`
- Agregadas capacidades `CAP_NET_BIND_SERVICE` para permitir bind al puerto 80 sin root

### 2. `deploy.sh`
- Agregado paso para detener y desactivar nginx automáticamente
- Libera el puerto 80 antes de iniciar la API

## 🚀 Pasos para Desplegar

### Opción A: Usando el script de deploy (Recomendado)

```bash
cd /var/www/html/apielectoral
./deploy.sh
```

El script automáticamente:
1. Detendrá nginx
2. Actualizará el código
3. Instalará dependencias
4. Reiniciará el servicio en puerto 80

### Opción B: Manual

```bash
# 1. Detener nginx
sudo systemctl stop nginx
sudo systemctl disable nginx

# 2. Actualizar código
cd /var/www/html/apielectoral
git pull

# 3. Copiar archivo de servicio
sudo cp api-electoral.service /etc/systemd/system/

# 4. Recargar y reiniciar
sudo systemctl daemon-reload
sudo systemctl restart api-electoral

# 5. Verificar estado
sudo systemctl status api-electoral
```

## 🔍 Verificación

### Verificar que el servicio está corriendo:
```bash
sudo systemctl status api-electoral
```

### Verificar que el puerto 80 está en uso:
```bash
sudo netstat -tulpn | grep :80
# o
sudo ss -tulpn | grep :80
```

### Probar la API:
```bash
curl http://localhost/docs
# o desde tu navegador
http://tu-servidor-ip/docs
```

## ⚠️ Consideraciones Importantes

### Ventajas de Puerto 80 Directo:
- ✅ Acceso directo sin proxy
- ✅ Menos componentes = menos complejidad
- ✅ Menor latencia (sin capa intermedia)

### Desventajas:
- ❌ No hay SSL/HTTPS (puerto 443)
- ❌ No hay balanceo de carga
- ❌ No hay cache de nginx
- ❌ No puedes servir múltiples aplicaciones

## 🔒 Para Agregar HTTPS (Opcional)

Si necesitas HTTPS en el futuro, tendrás que:

1. **Reactivar nginx** y configurarlo como proxy reverso
2. **Usar Certbot** para obtener certificados SSL
3. **Cambiar la API** de vuelta al puerto 8000

O alternativamente:

1. **Usar uvicorn con SSL** directamente (no recomendado para producción)

## 🔄 Revertir a Nginx (Si es necesario)

Si quieres volver a usar nginx como proxy:

```bash
# 1. Cambiar puerto en api-electoral.service a 8000
# 2. Reactivar nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# 3. Reiniciar API
sudo systemctl restart api-electoral
```

## 📝 Logs

Ver logs del servicio:
```bash
# Últimas 50 líneas
sudo journalctl -u api-electoral -n 50

# Seguir logs en tiempo real
sudo journalctl -u api-electoral -f
```

## 🆘 Troubleshooting

### Error: "Address already in use"
```bash
# Ver qué está usando el puerto 80
sudo lsof -i :80
# o
sudo netstat -tulpn | grep :80

# Si es nginx, detenerlo
sudo systemctl stop nginx
```

### El servicio no inicia
```bash
# Ver logs detallados
sudo journalctl -u api-electoral -n 100 --no-pager

# Verificar permisos
ls -la /var/www/html/apielectoral/

# Verificar archivo de servicio
sudo systemctl cat api-electoral
```
