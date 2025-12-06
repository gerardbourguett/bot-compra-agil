# Migraciones de Base de Datos

## ¿Qué son las migraciones?

Las migraciones son scripts que actualizan el esquema de la base de datos (agregan tablas, columnas, índices, etc.) sin perder datos existentes.

## Migraciones Disponibles

### `migrate_subscriptions.py`

Crea las tablas necesarias para el sistema de monetización:
- `subscriptions` - Tiers y estados de usuario
- `usage_tracking` - Tracking de uso de features
- `payments` - Historial de pagos

**Status:** ✅ Creada  
**Ejecutada en desarrollo:** ✅ Sí  
**Ejecutada en producción:** ⏳ Pendiente

---

## Cómo funcionan las migraciones

### En Desarrollo (Local)

```bash
# Ejecutar manualmente
python scripts/migrate_subscriptions.py
```

### En Producción (Automático) ✅

Las migraciones se ejecutan **automáticamente** en cada deploy a través de GitHub Actions:

1. **Push a `main`** → Trigger workflow
2. **Build** de imágenes Docker
3. **Pull** de nuevas imágenes
4. **Backup** automático de BD
5. **Restart** servicios
6. **🗄️ Ejecutar migraciones** ← NUEVO
7. Verificación de datos

### Flujo del Workflow

```yaml
# .github/workflows/ci-cd.yml (línea ~125)

# 9.5. Ejecutar migraciones de base de datos
echo "🗄️ Ejecutando migraciones de base de datos..."
sleep 15  # Esperar a que PostgreSQL esté listo

# Ejecutar todas las migraciones en orden
if [ -d "scripts" ]; then
  for migration_script in scripts/migrate_*.py; do
    echo "📋 Ejecutando: $migration_script"
    python "$migration_script" || echo "⚠️ Ya ejecutada (ok)"
  done
fi
```

---

## Características de Seguridad

### ✅ Idempotentes

Las migraciones usan `CREATE TABLE IF NOT EXISTS`, por lo que:
- **Primera vez:** Crea las tablas
- **Segunda vez:** No hace nada (ya existen)
- **N veces:** Siempre seguro ejecutar

### ✅ No destructivas

- NO borran tablas existentes
- NO eliminan columnas
- Solo AGREGAN elementos nuevos

### ✅ Con rollback

Si una migración falla:
```python
try:
    cursor.execute("CREATE TABLE ...")
    conn.commit()
except Exception as e:
    conn.rollback()  # Revierte cambios
```

---

## Agregar una Nueva Migración

### 1. Crear el script

```bash
# Nombre: scripts/migrate_NOMBRE_DESCRIPTIVO.py
# Ejemplo: scripts/migrate_add_user_preferences.py
```

### 2. Template básico

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import database_extended as db

def migrate():
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Tu SQL aquí
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nueva_tabla (
                id SERIAL PRIMARY KEY,
                ...
            )
        """)
        
        conn.commit()
        print("✅ Migración completada")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
```

### 3. Probar en desarrollo

```bash
python scripts/migrate_add_user_preferences.py
```

### 4. Commit y push

```bash
git add scripts/migrate_add_user_preferences.py
git commit -m "feat: add user preferences table"
git push origin main
```

### 5. Automático en producción

El workflow ejecutará **todas** las migraciones en `scripts/migrate_*.py`.

---

## Verificar Migraciones en Producción

### Opción 1: Logs de GitHub Actions

1. Ve a **Actions** tab
2. Click en el último workflow
3. Busca step "9.5. Ejecutar migraciones de base de datos"
4. Verifica output:
   ```
   🗄️ Ejecutando migraciones de base de datos...
   📋 Ejecutando: scripts/migrate_subscriptions.py
   ✅ Migración completada
   ```

### Opción 2: Conectarse a la BD

```bash
# Desde el servidor
docker compose exec postgres psql -U compra_agil_user -d compra_agil

# Listar tablas
\dt

# Deberías ver:
# subscriptions
# usage_tracking
# payments
# (más las tablas anteriores)
```

---

## Troubleshooting

### ❌ Error: "No se encontró directorio scripts/"

**Causa:** El directorio `scripts/` no fue incluido en el repo.

**Solución:**
```bash
git add scripts/
git commit -m "add: migrations directory"
git push
```

### ⚠️ Migración ya ejecutada

**Mensaje:** `⚠️ Migración ya ejecutada o error (continuando...)`

**Causa:** Las tablas ya existen (normal).

**Acción:** Ninguna, es esperado.

### ❌ Error de conexión a PostgreSQL

**Causa:** PostgreSQL no está listo aún.

**Solución:** El workflow ya tiene un `sleep 15` que debería ser suficiente. Si persiste, aumentar a `sleep 30`.

---

## Rollback de Migración

Si necesitas deshacer una migración:

### Método 1: Desde backup

```bash
# Restaurar desde backup automático
LATEST=$(ls -t backups/backup_*.sql | head -1)
docker compose exec -T postgres psql -U compra_agil_user compra_agil < "$LATEST"
```

### Método 2: DROP manual

```bash
docker compose exec postgres psql -U compra_agil_user -d compra_agil

-- En psql:
DROP TABLE IF EXISTS subscriptions CASCADE;
DROP TABLE IF EXISTS usage_tracking CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
```

> ⚠️ **CUIDADO:** Esto elimina datos permanentemente.

---

## Best Practices

1. **Siempre probar en desarrollo primero**
2. **Usar `IF NOT EXISTS`** en todos los CREATE
3. **Incluir verificación** al final del script
4. **Nombrar con prefijo** `migrate_` para auto-discovery
5. **Documentar** qué hace cada migración
6. **Nunca modificar** migraciones ya ejecutadas en prod

---

## Historial de Migraciones

| Fecha | Script | Descripción | Status |
|-------|--------|-------------|--------|
| 2025-12-06 | `migrate_subscriptions.py` | Sistema de monetización | ✅ Dev, ⏳ Prod |

---

## Referencias

- [Walkthrough de Fase 1](file:///../docs/WALKTHROUGH_FASE1.md)
- [Estrategia SaaS](file:///../docs/ESTRATEGIA_SAAS.md)
- [CI/CD Workflow](file:///../.github/workflows/ci-cd.yml)
