"""
Script para particionar la tabla historico_licitaciones por mes
Mejora el performance de queries en tablas con 10M+ registros

ADVERTENCIA: Este script realiza cambios estructurales en la BD.
Ejecutar en horario de baja actividad y con backup previo.

El script es IDEMPOTENTE - puede ejecutarse múltiples veces sin problemas.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import database_extended as db
from datetime import datetime, timedelta
import time

def verificar_si_esta_particionada():
    """Verifica si la tabla ya está particionada"""
    conn = db.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_partitioned_table
                WHERE partrelid = 'historico_licitaciones'::regclass
            )
        """)
        esta_particionada = cursor.fetchone()[0]
        conn.close()
        return esta_particionada
    except Exception as e:
        print(f"⚠️  Error verificando particionamiento: {e}")
        conn.close()
        return False


def obtener_rango_fechas():
    """Obtiene el rango de fechas de los datos históricos"""
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            MIN(fecha_cierre) as fecha_min,
            MAX(fecha_cierre) as fecha_max,
            COUNT(*) as total_registros
        FROM historico_licitaciones
        WHERE fecha_cierre IS NOT NULL
    """)

    fecha_min, fecha_max, total = cursor.fetchone()
    conn.close()

    return fecha_min, fecha_max, total


def crear_tabla_particionada():
    """Crea la nueva tabla particionada (sin datos aún)"""
    conn = db.get_connection()
    cursor = conn.cursor()

    print("\n📋 Creando tabla particionada...")

    # Renombrar tabla actual a _old
    print("  1. Renombrando tabla actual a historico_licitaciones_old...")
    cursor.execute("""
        ALTER TABLE IF EXISTS historico_licitaciones
        RENAME TO historico_licitaciones_old
    """)
    conn.commit()

    # Crear nueva tabla particionada
    print("  2. Creando nueva tabla particionada...")
    cursor.execute("""
        CREATE TABLE historico_licitaciones (
            id SERIAL,
            codigo_licitacion VARCHAR(100),
            nombre_cotizacion TEXT,
            producto_cotizado TEXT,
            cantidad INTEGER,
            monto_total NUMERIC(15,2),
            rut_proveedor VARCHAR(20),
            nombre_proveedor TEXT,
            region VARCHAR(100),
            fecha_cierre DATE,
            es_ganador BOOLEAN DEFAULT false,
            fecha_scraping TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id, fecha_cierre)
        ) PARTITION BY RANGE (fecha_cierre)
    """)
    conn.commit()

    print("  ✅ Tabla particionada creada")
    conn.close()


def crear_particiones_mensuales(fecha_inicio, fecha_fin):
    """Crea particiones mensuales desde fecha_inicio hasta fecha_fin"""
    conn = db.get_connection()
    cursor = conn.cursor()

    print("\n📅 Creando particiones mensuales...")

    fecha_actual = fecha_inicio.replace(day=1)  # Primer día del mes
    particiones_creadas = 0

    while fecha_actual <= fecha_fin:
        # Calcular fecha de fin de la partición (primer día del siguiente mes)
        if fecha_actual.month == 12:
            fecha_siguiente = datetime(fecha_actual.year + 1, 1, 1).date()
        else:
            fecha_siguiente = datetime(fecha_actual.year, fecha_actual.month + 1, 1).date()

        # Nombre de la partición
        partition_name = f"historico_licitaciones_{fecha_actual.year}_{fecha_actual.month:02d}"

        try:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF historico_licitaciones
                FOR VALUES FROM ('{fecha_actual}') TO ('{fecha_siguiente}')
            """)
            conn.commit()
            particiones_creadas += 1

            if particiones_creadas % 12 == 0:
                print(f"  ✓ {particiones_creadas} particiones creadas... ({fecha_actual.year})")

        except Exception as e:
            print(f"  ⚠️  Error creando partición {partition_name}: {e}")

        # Avanzar al siguiente mes
        fecha_actual = fecha_siguiente

    print(f"  ✅ Total de particiones creadas: {particiones_creadas}")
    conn.close()
    return particiones_creadas


def copiar_datos():
    """Copia datos de la tabla antigua a la particionada"""
    conn = db.get_connection()
    cursor = conn.cursor()

    print("\n📦 Copiando datos a tabla particionada...")
    print("  (Esto puede tomar varios minutos para 10M+ registros)")

    start_time = time.time()

    cursor.execute("""
        INSERT INTO historico_licitaciones
        SELECT * FROM historico_licitaciones_old
        ON CONFLICT DO NOTHING
    """)
    conn.commit()

    duration = time.time() - start_time
    print(f"  ✅ Datos copiados en {duration:.1f} segundos")

    # Verificar conteo
    cursor.execute("SELECT COUNT(*) FROM historico_licitaciones_old")
    old_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM historico_licitaciones")
    new_count = cursor.fetchone()[0]

    print(f"  📊 Registros en tabla antigua: {old_count:,}")
    print(f"  📊 Registros en tabla nueva:   {new_count:,}")

    if old_count == new_count:
        print("  ✅ Todos los registros copiados correctamente")
    else:
        print(f"  ⚠️  ADVERTENCIA: Discrepancia de {old_count - new_count} registros")

    conn.close()


def crear_indices_en_particiones():
    """Crea índices en la tabla particionada"""
    conn = db.get_connection()
    cursor = conn.cursor()

    print("\n📇 Creando índices en tabla particionada...")

    indices = [
        ("CREATE INDEX IF NOT EXISTS idx_hist_p_producto_trgm ON historico_licitaciones USING gin(producto_cotizado gin_trgm_ops)", "GIN Trigram producto"),
        ("CREATE INDEX IF NOT EXISTS idx_hist_p_ganador_monto ON historico_licitaciones(es_ganador, monto_total) WHERE monto_total > 0", "Ganador + monto"),
        ("CREATE INDEX IF NOT EXISTS idx_hist_p_fecha ON historico_licitaciones(fecha_cierre DESC)", "Fecha cierre"),
        ("CREATE INDEX IF NOT EXISTS idx_hist_p_region ON historico_licitaciones(region)", "Región"),
    ]

    for sql, desc in indices:
        try:
            print(f"  • {desc}...")
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            print(f"    ⚠️  Error: {e}")

    print("  ✅ Índices creados")
    conn.close()


def verificar_particionamiento():
    """Verifica que el particionamiento funciona correctamente"""
    conn = db.get_connection()
    cursor = conn.cursor()

    print("\n🔍 Verificando particionamiento...")

    # Listar particiones
    cursor.execute("""
        SELECT
            child.relname as partition_name,
            pg_size_pretty(pg_total_relation_size(child.oid)) as size
        FROM pg_inherits
        JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
        JOIN pg_class child ON pg_inherits.inhrelid = child.oid
        WHERE parent.relname = 'historico_licitaciones'
        ORDER BY child.relname
    """)

    particiones = cursor.fetchall()
    print(f"\n  📊 Total de particiones: {len(particiones)}")
    print(f"\n  Primeras 5 particiones:")
    for nombre, size in particiones[:5]:
        print(f"    • {nombre:40} {size:>10}")

    if len(particiones) > 5:
        print(f"    ... y {len(particiones) - 5} más")

    # Test de query en partición
    print("\n  🧪 Test de query con partición pruning...")
    cursor.execute("""
        EXPLAIN (ANALYZE, BUFFERS)
        SELECT COUNT(*) FROM historico_licitaciones
        WHERE fecha_cierre >= '2024-01-01' AND fecha_cierre < '2024-02-01'
    """)

    plan = cursor.fetchall()
    print("  ✅ Query ejecutada (ver EXPLAIN ANALYZE arriba para detalles)")

    conn.close()


def limpiar_tabla_antigua():
    """
    Elimina la tabla antigua SOLO si el usuario confirma
    ADVERTENCIA: Esta operación es irreversible
    """
    print("\n🗑️  LIMPIEZA DE TABLA ANTIGUA")
    print("=" * 80)
    print("La tabla 'historico_licitaciones_old' contiene los datos originales.")
    print("Ahora que los datos están en la tabla particionada, puedes eliminarla.")
    print()
    print("⚠️  ADVERTENCIA: Esta operación es IRREVERSIBLE")
    print()

    respuesta = input("¿Deseas eliminar la tabla antigua? (escribe 'SI' en mayúsculas): ")

    if respuesta != "SI":
        print("❌ Operación cancelada. La tabla antigua permanece como backup.")
        print("   Puedes eliminarla manualmente más tarde con:")
        print("   DROP TABLE historico_licitaciones_old;")
        return

    conn = db.get_connection()
    cursor = conn.cursor()

    print("\n🗑️  Eliminando tabla antigua...")
    cursor.execute("DROP TABLE IF EXISTS historico_licitaciones_old CASCADE")
    conn.commit()
    conn.close()

    print("✅ Tabla antigua eliminada")


def main():
    """Función principal de particionamiento"""
    print("=" * 80)
    print("PARTICIONAMIENTO DE HISTORICO_LICITACIONES")
    print("=" * 80)
    print()

    # Paso 0: Verificar si ya está particionada
    if verificar_si_esta_particionada():
        print("✅ La tabla ya está particionada.")
        print("   Si deseas re-particionar, elimina manualmente la tabla primero.")
        return

    # Paso 1: Obtener rango de fechas
    print("📊 Analizando datos existentes...")
    fecha_min, fecha_max, total = obtener_rango_fechas()

    print(f"  • Fecha más antigua: {fecha_min}")
    print(f"  • Fecha más reciente: {fecha_max}")
    print(f"  • Total de registros: {total:,}")
    print()

    if total == 0:
        print("⚠️  No hay datos para particionar. Abortando.")
        return

    # Paso 2: Confirmación del usuario
    print("⚠️  ADVERTENCIA:")
    print("  Este proceso va a:")
    print("  1. Renombrar la tabla actual a 'historico_licitaciones_old'")
    print("  2. Crear una nueva tabla particionada")
    print(f"  3. Crear ~{((fecha_max.year - fecha_min.year) * 12 + fecha_max.month - fecha_min.month + 1)} particiones mensuales")
    print(f"  4. Copiar {total:,} registros")
    print()
    print("  💾 ASEGÚRATE DE TENER UN BACKUP antes de continuar")
    print()

    respuesta = input("¿Continuar con el particionamiento? (escribe 'SI' en mayúsculas): ")

    if respuesta != "SI":
        print("❌ Operación cancelada por el usuario")
        return

    # Paso 3: Crear tabla particionada
    crear_tabla_particionada()

    # Paso 4: Crear particiones mensuales
    crear_particiones_mensuales(fecha_min, fecha_max)

    # Paso 5: Copiar datos
    copiar_datos()

    # Paso 6: Crear índices
    crear_indices_en_particiones()

    # Paso 7: Verificar
    verificar_particionamiento()

    # Paso 8: Limpiar tabla antigua (opcional)
    limpiar_tabla_antigua()

    print("\n" + "=" * 80)
    print("✅ PARTICIONAMIENTO COMPLETADO EXITOSAMENTE")
    print("=" * 80)
    print("\n📈 Beneficios:")
    print("  • Queries filtradas por fecha serán mucho más rápidas")
    print("  • Mantenimiento más eficiente (VACUUM por partición)")
    print("  • Mejor gestión de datos históricos")
    print()
    print("🔧 Próximos pasos:")
    print("  1. Ejecutar scripts/create_indexes.py para índices adicionales")
    print("  2. Monitorear performance de queries en producción")
    print("  3. Ajustar particiones futuras según crecimiento de datos")
    print()


if __name__ == "__main__":
    main()
