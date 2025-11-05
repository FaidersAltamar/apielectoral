# Parámetro `enviarapi` - Documentación

## Resumen

Se ha agregado el parámetro opcional `enviarapi` (por defecto `false`) a los endpoints para controlar si se envían o no los datos a las APIs externas.

---

## Endpoints Actualizados

### 1. `/consultar-nombres-v1` (Procuraduría)

**Request:**
```json
{
  "nuip": "1102877148",
  "enviarapi": true
}
```

**Comportamiento:**
- `enviarapi=false` (default): Solo consulta y retorna el nombre
- `enviarapi=true`: Consulta el nombre Y lo envía a `respuestanombreapi`

**Response con `enviarapi=true`:**
```json
{
  "status": "success",
  "name": "JUAN PEREZ GOMEZ",
  "api_externa": {
    "nombre_api_called": true,
    "nombre_api_status": "success",
    "nombre_api_message": "Nombre registrado"
  }
}
```

---

### 2. `/consultar-nombres-v2` (Policía)

**Request:**
```json
{
  "nuip": "1102877148",
  "fecha_expedicion": "15/03/2020",
  "enviarapi": true
}
```

**Comportamiento:**
- `enviarapi=false` (default): Solo consulta y retorna el nombre
- `enviarapi=true`: Consulta el nombre Y lo envía a `respuestanombreapi`

**Response con `enviarapi=true`:**
```json
{
  "status": "success",
  "name": "JUAN PEREZ GOMEZ",
  "api_externa": {
    "nombre_api_called": true,
    "nombre_api_status": "success",
    "nombre_api_message": "Nombre registrado"
  }
}
```

---

### 3. `/consultar-puesto-votacion` (Registraduría)

**Request:**
```json
{
  "nuip": "1102877148",
  "enviarapi": true
}
```

**Comportamiento:**
- `enviarapi=false` (default): Solo consulta y retorna el puesto
- `enviarapi=true`: Consulta el puesto Y lo envía a `respuestapuestoapi`

**Response con `enviarapi=true`:**
```json
{
  "status": "success",
  "data": [
    {
      "NUIP": "1102877148",
      "DEPARTAMENTO": "SUCRE",
      "MUNICIPIO": "COROZAL",
      "PUESTO": "DON ALONSO",
      "DIRECCIÓN": "I.E DON ALONSO",
      "MESA": "3"
    }
  ],
  "api_externa": {
    "puesto_api_called": true,
    "puesto_api_status": "success",
    "puesto_api_message": "Puesto registrado"
  }
}
```

---

### 4. `/consultar-nombres` (Secuencial)

**Request:**
```json
{
  "nuips": ["1102877148", "9876543210"],
  "enviarapi": true
}
```

**Comportamiento:**
- `enviarapi=false` (default): Solo consulta nombres y puestos, NO envía a APIs externas
- `enviarapi=true`: Consulta Y envía tanto nombres como puestos a las APIs externas

**Response con `enviarapi=true`:**
```json
{
  "status": "completed",
  "total_nuips": 2,
  "successful": 1,
  "not_found": 1,
  "errors": 0,
  "total_execution_time": "3m 45s",
  "results": [
    {
      "nuip": "1102877148",
      "status": "success",
      "name": "JUAN PEREZ GOMEZ",
      "voting_place": {
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
      "nombre_api_message": "...",
      "puesto_api_called": true,
      "puesto_api_status": "success",
      "puesto_api_message": "..."
    },
    {
      "nuip": "9876543210",
      "status": "not_found",
      "name": "",
      "execution_time": "1m 35s"
    }
  ]
}
```

---

## Flujo de Procesamiento

### Con `enviarapi=false` (Default)

```
┌─────────────────────────────────────┐
│ 1. Consultar datos                  │
│    (Procuraduría/Sisben/Policía)   │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 2. Retornar resultado               │
│    ❌ NO enviar a API externa       │
└─────────────────────────────────────┘
```

### Con `enviarapi=true`

```
┌─────────────────────────────────────┐
│ 1. Consultar nombre                 │
│    (Procuraduría/Sisben/Policía)   │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 2. ¿Nombre encontrado?              │
└─────────────────────────────────────┘
         ↓ SÍ
┌─────────────────────────────────────┐
│ 3. 📤 Enviar a respuestanombreapi   │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 4. Consultar puesto (si aplica)     │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 5. ¿Puesto encontrado?              │
└─────────────────────────────────────┘
         ↓ SÍ
┌─────────────────────────────────────┐
│ 6. 📤 Enviar a respuestapuestoapi   │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 7. Retornar resultado completo      │
└─────────────────────────────────────┘
```

---

## Casos de Uso

### Caso 1: Solo Consulta (Testing/Desarrollo)

```bash
curl -X POST http://localhost:8000/consultar-nombres-v1 \
  -H "Content-Type: application/json" \
  -d '{
    "nuip": "1102877148"
  }'
```

✅ Consulta el nombre
❌ NO envía a API externa

---

### Caso 2: Consulta + Envío a API (Producción)

```bash
curl -X POST http://localhost:8000/consultar-nombres-v1 \
  -H "Content-Type: application/json" \
  -d '{
    "nuip": "1102877148",
    "enviarapi": true
  }'
```

✅ Consulta el nombre
✅ Envía a `respuestanombreapi`

---

### Caso 3: Lote sin Envío

```bash
curl -X POST http://localhost:8000/consultar-nombres \
  -H "Content-Type: application/json" \
  -d '{
    "nuips": ["1102877148", "9876543210"]
  }'
```

✅ Consulta todos los nombres y puestos
❌ NO envía a APIs externas

---

### Caso 4: Lote con Envío

```bash
curl -X POST http://localhost:8000/consultar-nombres \
  -H "Content-Type: application/json" \
  -d '{
    "nuips": ["1102877148", "9876543210"],
    "enviarapi": true
  }'
```

✅ Consulta todos los nombres y puestos
✅ Envía cada nombre a `respuestanombreapi`
✅ Envía cada puesto a `respuestapuestoapi`

---

## Ventajas

✅ **Control total**: Decide cuándo enviar a APIs externas
✅ **Testing seguro**: Prueba sin afectar base de datos externa
✅ **Desarrollo local**: Trabaja sin necesidad de API externa activa
✅ **Producción flexible**: Activa envío solo cuando sea necesario
✅ **Retrocompatible**: Por defecto `false`, no rompe código existente
✅ **Granular**: Control por endpoint individual

---

## Modelos Actualizados

### `PeticionRequest`

```python
class PeticionRequest(BaseModel):
    nuip: str
    fecha_expedicion: Optional[str] = None
    enviarapi: bool = False  # ← NUEVO
```

### `ConsultaNombreRequest`

```python
class ConsultaNombreRequest(BaseModel):
    nuips: List[str]
    enviarapi: bool = False  # ← NUEVO
```

---

## Notas Importantes

1. **Valor por defecto**: `enviarapi=false` para mantener retrocompatibilidad
2. **Solo envía si encuentra datos**: No envía a API externa si no hay resultados
3. **Independiente por endpoint**: Cada endpoint controla su propio envío
4. **Respuesta incluida**: La respuesta de la API externa se incluye en el resultado
5. **No bloquea**: Si falla el envío a API externa, el resultado principal se retorna igual
