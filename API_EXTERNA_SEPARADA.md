# API Externa Separada - Documentación

## Resumen de Cambios

Se ha dividido el envío de datos al API externo en **dos llamadas separadas**:

1. **API de Nombre** (`respuestanombreapi`) - Se envía cuando se encuentra el nombre
2. **API de Puesto de Votación** (`respuestapuestoapi`) - Se envía cuando se encuentra el puesto

---

## Configuración

### Variables de Entorno (.env)

```env
# API Externa - Nombre
EXTERNAL_API_NOMBRE_URL=http://localhost/votantes/api/v1/respuestanombreapi

# API Externa - Puesto de Votación
EXTERNAL_API_PUESTO_URL=http://localhost/votantes/api/v1/respuestapuestoapi
```

### Configuración en config.py

```python
EXTERNAL_API_NOMBRE_URL = os.getenv('EXTERNAL_API_NOMBRE_URL', 
    'http://localhost/votantes/api/v1/respuestanombreapi')
EXTERNAL_API_PUESTO_URL = os.getenv('EXTERNAL_API_PUESTO_URL', 
    'http://localhost/votantes/api/v1/respuestapuestoapi')
```

---

## Funciones Implementadas

### 1. `send_name_to_external_api()`

Envía el nombre encontrado al endpoint externo.

**Payload enviado:**
```json
{
  "numerodocumento": "1102877148",
  "nombrecompleto": "JUAN PEREZ GOMEZ"
}
```

**Respuesta incluida en el resultado:**
```json
{
  "nombre_api_called": true,
  "nombre_api_status": "success",
  "nombre_api_message": "Nombre registrado correctamente"
}
```

### 2. `send_voting_place_to_external_api()`

Envía los datos del puesto de votación al endpoint externo.

**Payload enviado:**
```json
{
  "numerodocumento": "1102877148",
  "departamento": "SUCRE",
  "municipio": "COROZAL",
  "puesto": "DON ALONSO",
  "direccion": "I.E DON ALONSO",
  "mesa": "3"
}
```

**Respuesta incluida en el resultado:**
```json
{
  "puesto_api_called": true,
  "puesto_api_status": "success",
  "puesto_api_message": "Puesto registrado correctamente"
}
```

---

## Flujo de Procesamiento

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Buscar Nombre                                            │
│    - Procuraduría (2 intentos, 45s timeout)                │
│    - Sisben (1 intento, 30s timeout)                       │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. ¿Se encontró el nombre?                                  │
└─────────────────────────────────────────────────────────────┘
         ↓ SÍ                              ↓ NO
┌─────────────────────────┐    ┌──────────────────────────────┐
│ 3. Enviar Nombre        │    │ Retornar "not_found"         │
│    ↓                    │    └──────────────────────────────┘
│ POST respuestanombreapi │
│ ✅ Nombre enviado       │
│ INMEDIATAMENTE          │
└─────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Consultar Puesto de Votación                            │
│    - Registraduría (60s timeout)                           │
│    (Se consulta DESPUÉS de enviar el nombre)               │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. ¿Se encontró el puesto?                                 │
└─────────────────────────────────────────────────────────────┘
         ↓ SÍ                              ↓ NO
┌─────────────────────────┐    ┌──────────────────────────────┐
│ 6. Enviar Puesto        │    │ Continuar sin puesto         │
│    ↓                    │    │ (solo con nombre)            │
│ POST respuestapuestoapi │    └──────────────────────────────┘
│ ✅ Puesto enviado       │
└─────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Retornar Resultado Completo                             │
└─────────────────────────────────────────────────────────────┘
```

### ⚠️ IMPORTANTE: Orden de Ejecución

**El nombre se envía al API ANTES de consultar el puesto de votación.**

Esto garantiza que:
- ✅ El nombre se registra inmediatamente cuando se encuentra
- ✅ No se pierde el nombre si falla la consulta del puesto
- ✅ El API externo recibe el nombre lo más rápido posible

---

## Respuesta del Endpoint `/consultar-nombres`

### Caso 1: Nombre y Puesto Encontrados

```json
{
  "status": "completed",
  "total_nuips": 1,
  "successful": 1,
  "not_found": 0,
  "errors": 0,
  "total_execution_time": "2m 15s",
  "results": [
    {
      "nuip": "1102877148",
      "status": "success",
      "name": "JUAN PEREZ GOMEZ",
      "voting_place": {
        "NUIP": "1102877148",
        "DEPARTAMENTO": "SUCRE",
        "MUNICIPIO": "COROZAL",
        "PUESTO": "DON ALONSO",
        "DIRECCIÓN": "I.E DON ALONSO",
        "MESA": "3"
      },
      "execution_time": "2m 10s",
      "source": "procuraduria",
      "nombre_api_called": true,
      "nombre_api_status": "success",
      "nombre_api_message": "Nombre registrado",
      "puesto_api_called": true,
      "puesto_api_status": "success",
      "puesto_api_message": "Puesto registrado"
    }
  ]
}
```

### Caso 2: Solo Nombre Encontrado (sin puesto)

```json
{
  "status": "completed",
  "total_nuips": 1,
  "successful": 1,
  "not_found": 0,
  "errors": 0,
  "total_execution_time": "1m 30s",
  "results": [
    {
      "nuip": "1102877148",
      "status": "success",
      "name": "JUAN PEREZ GOMEZ",
      "voting_place": null,
      "execution_time": "1m 25s",
      "source": "sisben",
      "nombre_api_called": true,
      "nombre_api_status": "success",
      "nombre_api_message": "Nombre registrado"
    }
  ]
}
```

### Caso 3: Nombre No Encontrado

```json
{
  "status": "completed",
  "total_nuips": 1,
  "successful": 0,
  "not_found": 1,
  "errors": 0,
  "total_execution_time": "1m 45s",
  "results": [
    {
      "nuip": "9999999999",
      "status": "not_found",
      "name": "",
      "execution_time": "1m 40s"
    }
  ]
}
```

---

## Ventajas de la Separación

✅ **Modularidad**: Cada endpoint tiene una responsabilidad específica
✅ **Flexibilidad**: Se puede enviar el nombre aunque falle el puesto
✅ **Trazabilidad**: Respuestas separadas para cada API
✅ **Escalabilidad**: Fácil agregar más endpoints en el futuro
✅ **Debugging**: Más fácil identificar qué API falló

---

## Manejo de Errores

### Error en API de Nombre

```json
{
  "nombre_api_called": false,
  "nombre_api_error": "Timeout al conectar con el endpoint de nombre"
}
```

### Error en API de Puesto

```json
{
  "puesto_api_called": false,
  "puesto_api_error": "Connection refused"
}
```

### Ambas APIs Fallan

El resultado aún incluye los datos encontrados (nombre y puesto), pero con los errores de las APIs:

```json
{
  "nuip": "1102877148",
  "status": "success",
  "name": "JUAN PEREZ GOMEZ",
  "voting_place": {...},
  "nombre_api_called": false,
  "nombre_api_error": "...",
  "puesto_api_called": false,
  "puesto_api_error": "..."
}
```

---

## Timeouts

- **API de Nombre**: 10 segundos
- **API de Puesto**: 10 segundos
- **Total máximo por NUIP**: 180 segundos (3 minutos)

---

## Testing

### Test Manual con cURL

**1. Endpoint de Nombre:**
```bash
curl -X POST http://localhost/votantes/api/v1/respuestanombreapi \
  -H "Content-Type: application/json" \
  -d '{
    "numerodocumento": "1102877148",
    "nombrecompleto": "JUAN PEREZ GOMEZ"
  }'
```

**2. Endpoint de Puesto:**
```bash
curl -X POST http://localhost/votantes/api/v1/respuestapuestoapi \
  -H "Content-Type: application/json" \
  -d '{
    "numerodocumento": "1102877148",
    "departamento": "SUCRE",
    "municipio": "COROZAL",
    "puesto": "DON ALONSO",
    "direccion": "I.E DON ALONSO",
    "mesa": "3"
  }'
```

---

## Notas Importantes

1. **Orden de Envío**: Siempre se envía primero el nombre, luego el puesto
2. **Puesto Opcional**: Si no se encuentra el puesto, solo se envía el nombre
3. **Independencia**: El fallo de una API no afecta a la otra
4. **Logs Detallados**: Cada envío se registra en los logs con emoji distintivo 📤
