# Sistema de Protección contra Bloqueos

## Resumen
Se ha implementado un sistema completo de timeouts y manejo de errores para garantizar que el procesamiento de múltiples NUIPs nunca se bloquee en un registro individual.

## Timeouts Implementados

### 1. Nivel de Scraper Individual
Cada scraper tiene su propio timeout:

```
┌─────────────────────────────────────────┐
│ Procuraduría: 90 segundos por intento  │
│ - Máximo 2 intentos                    │
│ - Total máximo: 180 segundos           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Sisben: 60 segundos por intento        │
│ - Máximo 1 intento                     │
│ - Total máximo: 60 segundos            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Registraduría: 120 segundos            │
│ - Consulta de puesto de votación      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ APIs Externas: 20 segundos             │
│ - Timeout para POST requests          │
└─────────────────────────────────────────┘
```

### 2. Timeout Global por NUIP
Cada NUIP tiene un timeout global de **6 minutos (360 segundos)**:

```python
result = await asyncio.wait_for(
    process_single_nuip(nuip),
    timeout=360.0
)
```

Esto garantiza que incluso si todos los timeouts individuales fallan, el procesamiento continuará después de 6 minutos.

## Flujo de Procesamiento

```
┌──────────────────────────────────────────────────────────┐
│ NUIP 1                                                   │
├──────────────────────────────────────────────────────────┤
│ ┌─ Procuraduría (90s) ──────────────────────────┐       │
│ │   Intento 1 → timeout/error                   │       │
│ │   Intento 2 → timeout/error                   │       │
│ └───────────────────────────────────────────────┘       │
│ ┌─ Sisben (60s) ────────────────────────────────┐       │
│ │   Intento 1 → timeout/error                   │       │
│ └───────────────────────────────────────────────┘       │
│ ┌─ Registraduría (120s) ────────────────────────┐       │
│ │   Si encontró nombre → consulta votación      │       │
│ │   timeout/error → continúa sin datos          │       │
│ └───────────────────────────────────────────────┘       │
│                                                          │
│ ⚠️ Si excede 360s → TIMEOUT GLOBAL                      │
│ ✅ Resultado guardado (éxito o error)                   │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ NUIP 2 (continúa automáticamente)                       │
└──────────────────────────────────────────────────────────┘
```

## Manejo de Errores

### Nivel 1: Timeout del Scraper
```python
try:
    result = await asyncio.wait_for(
        asyncio.to_thread(scraper.scrape_nuip, nuip),
        timeout=90.0
    )
except asyncio.TimeoutError:
    print(f"⏱️ Timeout en Procuraduría (90s excedidos)")
    # Continúa con el siguiente intento o scraper
```

### Nivel 2: Error del Scraper
```python
except Exception as e:
    print(f"⚠️ Error en Procuraduría: {e}")
    # Continúa con el siguiente intento o scraper
```

### Nivel 3: Cierre Garantizado
```python
finally:
    if scraper:
        try:
            scraper.close()
        except Exception as close_error:
            print(f"⚠️ Error al cerrar scraper: {close_error}")
```

### Nivel 4: Timeout Global por NUIP
```python
try:
    result = await asyncio.wait_for(
        process_single_nuip(nuip),
        timeout=360.0
    )
except asyncio.TimeoutError:
    # Registra error y continúa con siguiente NUIP
    results.append({
        "nuip": nuip,
        "status": "error",
        "error": "Timeout global: procesamiento excedió 6 minutos"
    })
```

### Nivel 5: Error Crítico
```python
except Exception as e:
    # Captura cualquier error inesperado
    results.append({
        "nuip": nuip,
        "status": "error",
        "error": f"Error crítico: {str(e)}"
    })
```

## Respuesta del Endpoint

```json
{
  "status": "completed",
  "total_nuips": 10,
  "successful": 7,
  "not_found": 2,
  "errors": 1,
  "total_execution_time": "15m 30s",
  "results": [
    {
      "nuip": "1102877148",
      "status": "success",
      "name": "JUAN PEREZ",
      "voting_place": {
        "DEPARTAMENTO": "SUCRE",
        "MUNICIPIO": "COROZAL",
        "PUESTO": "DON ALONSO",
        "DIRECCIÓN": "I.E DON ALONSO",
        "MESA": "3"
      },
      "execution_time": "1m 45s",
      "source": "procuraduria",
      "external_api_called": true,
      "external_api_status": "success"
    },
    {
      "nuip": "1234567890",
      "status": "error",
      "name": "",
      "execution_time": "360+ seconds",
      "error": "Timeout global: procesamiento excedió 6 minutos"
    }
  ]
}
```

## Ventajas del Sistema

✅ **No se bloquea nunca**: Múltiples niveles de timeout garantizan progreso
✅ **Continúa procesando**: Un error no detiene los demás registros
✅ **Recursos liberados**: Los navegadores siempre se cierran
✅ **Logging detallado**: Sabes exactamente qué pasó con cada NUIP
✅ **Resultados parciales**: Incluso con errores, obtienes los datos exitosos
✅ **Timeout configurable**: Fácil de ajustar según necesidades

## Tiempos Máximos Estimados

Para un lote de 100 NUIPs en el peor escenario (todos con timeout):

```
Tiempo máximo por NUIP: 360 segundos (6 minutos)
Pausa entre NUIPs: 1 segundo
Total máximo: (360s × 100) + (1s × 99) = 36,099 segundos ≈ 10 horas

Tiempo promedio esperado por NUIP: 120-180 segundos
Total esperado para 100 NUIPs: 200-300 minutos ≈ 3.3-5 horas
```

## Recomendaciones

1. **Lotes pequeños**: Procesar en lotes de 20-50 NUIPs para mejor control
2. **Monitoreo**: Revisar logs para identificar NUIPs problemáticos
3. **Ajuste de timeouts**: Si los scrapers son más lentos, aumentar timeouts
4. **Headless mode**: Usar `headless=True` para mejor rendimiento
5. **Recursos del servidor**: Asegurar suficiente memoria y CPU
