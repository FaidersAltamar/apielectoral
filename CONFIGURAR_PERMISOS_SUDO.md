# 🔐 Configurar Permisos Sudo para Deployment

## Problema

El usuario `ubuntu` necesita permisos para ejecutar ciertos comandos con `sudo` sin contraseña durante el deployment automático desde GitHub Actions.

## Solución

Conéctate al servidor VPS por SSH y ejecuta:

```bash
ssh ubuntu@158.69.113.159
```

### Paso 1: Editar configuración de sudoers

```bash
sudo visudo
```

### Paso 2: Agregar permisos al final del archivo

Agrega estas líneas al **final** del archivo:

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

### Paso 3: Guardar y salir

- Presiona `Ctrl + X`
- Presiona `Y` para confirmar
- Presiona `Enter` para guardar

### Paso 4: Verificar configuración

```bash
# Probar que funciona sin pedir contraseña
sudo chown ubuntu:ubuntu /var/www/html/apielectoral
sudo systemctl list-unit-files | grep api-electoral
```

Si no pide contraseña, está configurado correctamente ✅

## Alternativa: Configuración más específica (Recomendado)

Si prefieres ser más específico con los permisos:

```bash
sudo visudo
```

Agrega:

```bash
# Permisos específicos para deployment en /var/www/html/apielectoral
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/chown -R ubuntu\:ubuntu /var/www/html/apielectoral*
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/python3 -m venv /var/www/html/apielectoral/venv
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart api-electoral
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl status api-electoral
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl list-unit-files
ubuntu ALL=(ALL) NOPASSWD: /usr/bin/pkill -f python.*api.py
```

## Verificación Final

Ejecuta este comando para probar todos los permisos:

```bash
# Debe ejecutarse sin pedir contraseña
sudo chown -R ubuntu:ubuntu /var/www/html/apielectoral
sudo systemctl list-unit-files | grep api-electoral
sudo pkill -f "python.*api.py" || true

echo "✅ Todos los comandos se ejecutaron sin pedir contraseña"
```

## Notas de Seguridad

⚠️ **Importante:**
- Estos permisos permiten al usuario `ubuntu` ejecutar comandos específicos sin contraseña
- Solo afectan a los comandos listados
- Es seguro para un entorno de deployment automatizado
- No compromete la seguridad general del sistema

## Troubleshooting

### Error: "syntax error near unexpected token"

Verifica que no haya espacios extra o caracteres especiales en las líneas agregadas.

### Error: "ubuntu is not in the sudoers file"

El usuario `ubuntu` necesita estar en el grupo sudo:

```bash
sudo usermod -aG sudo ubuntu
```

### Los cambios no se aplican

Cierra la sesión SSH y vuelve a conectarte:

```bash
exit
ssh ubuntu@158.69.113.159
```

---

**Última actualización:** 2025-11-06
