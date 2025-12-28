"""
Script para verificar el estado de optimizaciones de la base de datos
Útil para debugging y para asegurar que todo está correctamente configurado
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import database_extended as db

def check_extensions():
    """Verifica que las extensiones necesarias están instaladas"""
    conn = db.get_connection()
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("VERIFICANDO EXTENSIONES DE POSTGRESQL")
    print("=" * 80)

    cursor.execute("""
        SELECT extname, extversion
        FROM pg_extension
        WHERE extname IN ('pg_trgm', 'pg_stat_statements')
        ORDER BY extname
    """)

    extensiones = cursor.fetchall()
    extensiones_dict = {ext[0]: ext[1] for ext in extensiones}

    # Verificar pg_trgm
    if 'pg_trgm' in extensiones_dict:
        print(f"✅ pg_trgm instalado (versión {extensiones_dict['pg_trgm']})")
    else:
        print("❌ pg_trgm NO instalado - Fuzzy matching no funcionará")

    # Verificar pg_stat_statements
    if 'pg_stat_statements' in extensiones_dict:
        print(f"✅ pg_stat_statements instalado (versión {extensiones_dict['pg_stat_statements']})")
    else:
        print("⚠️  pg_stat_statements NO instalado - No hay estadísticas de queries")

    conn.close()
    return len(extensiones_dict)


def check_indexes():
    """Verifica los índices críticos de la tabla historico_licitaciones"""
    conn = db.get_connection()
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("VERIFICANDO ÍNDICES CRÍTICOS")
    print("=" * 80)

    # Índices críticos esperados
    indices_criticos = [
        'idx_hist_producto_trgm',     # Fuzzy matching producto
        'idx_hist_nombre_trgm',        # Fuzzy matching nombre
        'idx_hist_precio_optimo',      # ML precio
        'idx_hist_rag_composite',      # RAG queries
        'idx_hist_fecha_producto',     # Análisis temporal
    ]

    cursor.execute("""
        SELECT
            indexname,
            pg_size_pretty(pg_relation_size(indexname::regclass)) as size,
            idx_scan as index_scans
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        AND tablename = 'historico_licitaciones'
        ORDER BY indexname
    """)

    indices_existentes = {idx[0]: (idx[1], idx[2]) for idx in cursor.fetchall()}

    print(f"\n📊 Total de índices en historico_licitaciones: {len(indices_existentes)}")
    print("\n🔍 Verificando índices críticos:")

    for idx_name in indices_criticos:
        if idx_name in indices_existentes:
            size, scans = indices_existentes[idx_name]
            print(f"  ✅ {idx_name:35} Size: {size:>8}  Scans: {scans:>8}")
        else:
            print(f"  ❌ {idx_name:35} NO EXISTE")

    # Mostrar top 5 índices más usados
    print("\n📈 Top 5 índices más utilizados:")
    cursor.execute("""
        SELECT
            indexname,
            idx_scan as scans,
            pg_size_pretty(pg_relation_size(indexname::regclass)) as size
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        AND tablename = 'historico_licitaciones'
        AND idx_scan > 0
        ORDER BY idx_scan DESC
        LIMIT 5
    """)

    for idx_name, scans, size in cursor.fetchall():
        print(f"  • {idx_name:40} {scans:>10} scans  ({size})")

    conn.close()
    return len([idx for idx in indices_criticos if idx in indices_existentes])


def check_partitioning():
    """Verifica si la tabla está particionada"""
    conn = db.get_connection()
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("VERIFICANDO PARTICIONAMIENTO")
    print("=" * 80)

    try:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_partitioned_table
                WHERE partrelid = 'historico_licitaciones'::regclass
            )
        """)
        esta_particionada = cursor.fetchone()[0]

        if esta_particionada:
            print("✅ Tabla historico_licitaciones está PARTICIONADA")

            # Contar particiones
            cursor.execute("""
                SELECT COUNT(*)
                FROM pg_inherits
                JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
                WHERE parent.relname = 'historico_licitaciones'
            """)
            num_particiones = cursor.fetchone()[0]
            print(f"📊 Número de particiones: {num_particiones}")

            # Mostrar primeras 3 y últimas 3 particiones
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

            print("\n📅 Primeras 3 particiones:")
            for nombre, size in particiones[:3]:
                print(f"  • {nombre:45} {size:>10}")

            if len(particiones) > 6:
                print(f"  ... ({len(particiones) - 6} particiones más)")

            print("\n📅 Últimas 3 particiones:")
            for nombre, size in particiones[-3:]:
                print(f"  • {nombre:45} {size:>10}")

        else:
            print("⚠️  Tabla historico_licitaciones NO está particionada")
            print("   Ejecutar: python scripts/partition_historico.py")

            # Mostrar tamaño de la tabla sin particionar
            cursor.execute("""
                SELECT pg_size_pretty(pg_total_relation_size('historico_licitaciones'))
            """)
            size = cursor.fetchone()[0]
            print(f"📊 Tamaño actual de la tabla: {size}")

    except Exception as e:
        print(f"❌ Error verificando particionamiento: {e}")

    conn.close()


def check_table_stats():
    """Muestra estadísticas generales de las tablas principales"""
    conn = db.get_connection()
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("ESTADÍSTICAS DE TABLAS")
    print("=" * 80)

    cursor.execute("""
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
            n_live_tup as row_count,
            last_vacuum,
            last_autovacuum
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        AND tablename IN ('historico_licitaciones', 'licitaciones', 'productos_solicitados', 'subscriptions')
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    """)

    print(f"\n{'Tabla':<30} {'Tamaño':>12} {'Filas':>12} {'Último VACUUM':>20}")
    print("-" * 80)

    for schema, tabla, size, rows, last_vac, last_autovac in cursor.fetchall():
        ultimo_vacuum = last_autovac or last_vac or "Nunca"
        if isinstance(ultimo_vacuum, str):
            vac_str = ultimo_vacuum
        else:
            vac_str = ultimo_vacuum.strftime("%Y-%m-%d %H:%M")

        print(f"{tabla:<30} {size:>12} {rows:>12,} {vac_str:>20}")

    conn.close()


def check_redis_config():
    """Verifica la configuración de Redis en variables de entorno"""
    print("\n" + "=" * 80)
    print("VERIFICANDO CONFIGURACIÓN DE REDIS")
    print("=" * 80)

    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        print(f"✅ REDIS_URL configurado: {redis_url}")

        # Intentar conectar
        try:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            print("✅ Conexión a Redis exitosa")

            # Info de Redis
            info = r.info('server')
            print(f"📊 Redis versión: {info.get('redis_version', 'N/A')}")

            # Estadísticas de caché
            info_stats = r.info('stats')
            hits = info_stats.get('keyspace_hits', 0)
            misses = info_stats.get('keyspace_misses', 0)
            total = hits + misses

            if total > 0:
                hit_rate = (hits / total) * 100
                print(f"📈 Cache hit rate: {hit_rate:.1f}% ({hits} hits, {misses} misses)")
            else:
                print("📊 Sin estadísticas de caché aún")

        except ImportError:
            print("⚠️  Módulo redis no instalado")
        except Exception as e:
            print(f"❌ Error conectando a Redis: {e}")
    else:
        print("⚠️  REDIS_URL no configurado")
        print("   Agregar a .env: REDIS_URL=redis://localhost:6379/0")


def check_slow_queries():
    """Muestra las queries más lentas si pg_stat_statements está habilitado"""
    conn = db.get_connection()
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("QUERIES MÁS LENTAS (requiere pg_stat_statements)")
    print("=" * 80)

    try:
        cursor.execute("""
            SELECT
                LEFT(query, 80) as query_preview,
                calls,
                ROUND(mean_exec_time::numeric, 2) as avg_ms,
                ROUND(total_exec_time::numeric, 2) as total_ms
            FROM pg_stat_statements
            WHERE query NOT LIKE '%pg_stat_statements%'
            ORDER BY mean_exec_time DESC
            LIMIT 5
        """)

        print(f"\n{'Query (primeros 80 chars)':<82} {'Calls':>8} {'Avg (ms)':>10} {'Total (ms)':>12}")
        print("-" * 120)

        for query, calls, avg_ms, total_ms in cursor.fetchall():
            print(f"{query:<82} {calls:>8} {avg_ms:>10} {total_ms:>12}")

    except Exception as e:
        print(f"⚠️  pg_stat_statements no disponible o no configurado")
        print(f"   Error: {e}")

    conn.close()


def main():
    """Ejecuta todas las verificaciones"""
    print("\n" + "=" * 80)
    print(" " * 20 + "VERIFICACIÓN DE OPTIMIZACIONES DE BD")
    print("=" * 80)

    try:
        # 1. Extensiones
        ext_count = check_extensions()

        # 2. Índices
        idx_count = check_indexes()

        # 3. Particionamiento
        check_partitioning()

        # 4. Estadísticas de tablas
        check_table_stats()

        # 5. Redis
        check_redis_config()

        # 6. Queries lentas
        check_slow_queries()

        # Resumen final
        print("\n" + "=" * 80)
        print("RESUMEN")
        print("=" * 80)
        print(f"✅ Extensiones instaladas: {ext_count}/2")
        print(f"✅ Índices críticos presentes: {idx_count}/5")
        print("\n💡 Recomendaciones:")
        if ext_count < 2:
            print("  • Ejecutar scripts/create_indexes.py para instalar extensiones")
        if idx_count < 5:
            print("  • Ejecutar scripts/create_indexes.py para crear índices faltantes")
        print("  • Monitorear cache hit rate de Redis (objetivo: >60%)")
        print("  • Ejecutar VACUUM ANALYZE periódicamente en producción")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR durante verificación: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
