## Confirmación de implementación
- Existe un importador dedicado en `src/importar_historico.py` que descarga un ZIP, lee los `.csv` y carga por lotes a `historico_licitaciones`.
- La conexión y el esquema están en `src/database_extended.py`, compatible con PostgreSQL y SQLite.

## Verificación de ejecución
- Ejecutar en entorno controlado con SQLite: `python src/importar_historico.py --url "https://.../COT_2025-01.zip"`.
- Ejecutar con PostgreSQL: `python src/importar_historico.py --db-url "postgresql://user:pass@host/db" --url "https://.../COT_2025-01.zip"`.
- Validar: inserciones por lotes, tiempos de proceso, tamaño de memoria, y deduplicación por mes (`verificar_existencia`).

## Calidad y normalización de datos
- Asegurar parseo robusto de tipos: `cantidad`/`monto_total` con valores vacíos y separadores.
- Normalizar `fecha_cierre` a `DATE` consistente; añadir parseo y validación de formato.
- Mejorar manejo de encoding CSV: detección y fallback (`latin-1` si falla `utf-8`).

## Idempotencia y deduplicación
- Añadir restricción única compuesta (por ejemplo `codigo_cotizacion`, `rut_proveedor`, `producto_cotizado`) en `historico_licitaciones`.
- Cambiar inserción masiva a upsert:
  - PostgreSQL: `ON CONFLICT DO NOTHING`/`DO UPDATE`.
  - SQLite: `INSERT OR IGNORE`.
- Mantener verificación por mes como guardarraíl, pero evitar duplicados a nivel de fila.

## Observabilidad y resiliencia
- Sustituir `print` por `logging` con niveles y contexto (archivo, CSV, lote, tiempo).
- Registrar métricas: registros totales, descartados, tiempo por archivo, errores.
- Manejo de errores granular: continuar procesamiento de otros CSV si uno falla; reintentos en descarga.

## Configuración y documentación
- Documentar variables: `DATABASE_URL` (.env), ejemplos de URLs ZIP.
- Añadir guía rápida en `README` para ejecutar con ambos motores.

## Pruebas
- Unitarias: `verificar_existencia`, parseo de filas con valores edge.
- Integración: ZIP pequeño de prueba con inserción en DB temporal; validar upsert y índices.

## Optimización opcional
- Evitar archivo temporal con streaming en memoria (`io.BytesIO`) y `zipfile.ZipFile` directo.
- Ajustar `CHUNK_SIZE` vs. RAM disponible y tamaño de ZIP.
