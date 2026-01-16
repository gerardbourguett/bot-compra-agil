"""
Script para crear índices optimizados para el sistema
Especialmente importante para la tabla historico_licitaciones con 10M+ registros
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import database_extended as db

def crear_indices_optimizados():
    """Crea índices optimizados para queries del ML y API REST"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("CREANDO ÍNDICES OPTIMIZADOS")
    print("=" * 80)
    print()
    
    # Habilitar extensiones necesarias primero
    print("Habilitando extensiones de PostgreSQL...")
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")
        conn.commit()
        print("✅ Extensiones habilitadas: pg_trgm, pg_stat_statements\n")
    except Exception as e:
        print(f"⚠️  Error habilitando extensiones: {e}\n")

    indices = [
        # ========== HISTÓRICO_LICITACIONES (10.6M registros) ==========
        # Índices GIN para fuzzy matching (RAG/ML)
        ("idx_hist_producto_trgm", """
            CREATE INDEX IF NOT EXISTS idx_hist_producto_trgm
            ON historico_licitaciones
            USING gin(producto_cotizado gin_trgm_ops)
        """, "GIN Trigram: producto (fuzzy matching para RAG)"),

        ("idx_hist_nombre_trgm", """
            CREATE INDEX IF NOT EXISTS idx_hist_nombre_trgm
            ON historico_licitaciones
            USING gin(nombre_cotizacion gin_trgm_ops)
        """, "GIN Trigram: nombre (fuzzy matching para búsquedas)"),

        # Índices para búsquedas de texto (case-insensitive - legacy)
        ("idx_hist_nombre_lower", """
            CREATE INDEX IF NOT EXISTS idx_hist_nombre_lower
            ON historico_licitaciones(LOWER(nombre_cotizacion))
        """, "Texto nombre (case-insensitive)"),

        ("idx_hist_producto_lower", """
            CREATE INDEX IF NOT EXISTS idx_hist_producto_lower
            ON historico_licitaciones(LOWER(producto_cotizado))
        """, "Texto producto (case-insensitive)"),
        
        # Índices para filtros comunes
        ("idx_hist_region_ganador", """
            CREATE INDEX IF NOT EXISTS idx_hist_region_ganador 
            ON historico_licitaciones(region, es_ganador)
        """, "Región + ganador (filtros ML)"),
        
        ("idx_hist_fecha_cierre", """
            CREATE INDEX IF NOT EXISTS idx_hist_fecha_cierre 
            ON historico_licitaciones(fecha_cierre DESC)
        """, "Fecha cierre (ordenamiento temporal)"),
        
        ("idx_hist_monto_ganador", """
            CREATE INDEX IF NOT EXISTS idx_hist_monto_ganador 
            ON historico_licitaciones(monto_total, es_ganador)
        WHERE monto_total > 0
        """, "Monto + ganador (stats de precio)"),
        
        ("idx_hist_proveedor", """
            CREATE INDEX IF NOT EXISTS idx_hist_proveedor 
            ON historico_licitaciones(rut_proveedor, es_ganador)
        """, "Proveedor + ganador (competencia)"),
        
        # Índice compuesto para queries de RAG
        ("idx_hist_rag_composite", """
            CREATE INDEX IF NOT EXISTS idx_hist_rag_composite
            ON historico_licitaciones(es_ganador, fecha_cierre DESC, monto_total)
        WHERE monto_total > 0 AND nombre_cotizacion IS NOT NULL
        """, "Compuesto RAG (ganador, fecha, monto)"),

        # Índice compuesto para precio óptimo (ML)
        ("idx_hist_precio_optimo", """
            CREATE INDEX IF NOT EXISTS idx_hist_precio_optimo
            ON historico_licitaciones(producto_cotizado, es_ganador, monto_total, cantidad, fecha_cierre DESC)
        WHERE monto_total > 0 AND es_ganador = true
        """, "Compuesto precio óptimo (producto, ganador, monto, cantidad, fecha)"),

        # Índice para análisis temporal
        ("idx_hist_fecha_producto", """
            CREATE INDEX IF NOT EXISTS idx_hist_fecha_producto
            ON historico_licitaciones(fecha_cierre DESC, producto_cotizado)
        WHERE fecha_cierre >= '2020-01-01'
        """, "Fecha + producto (análisis temporal reciente)"),
        
        # ========== LICITACIONES (26K registros) ==========
        ("idx_lic_estado_fecha", """
            CREATE INDEX IF NOT EXISTS idx_lic_estado_fecha 
            ON licitaciones(estado, fecha_cierre)
        """, "Estado + fecha (licitaciones activas)"),
        
        ("idx_lic_monto", """
            CREATE INDEX IF NOT EXISTS idx_lic_monto 
            ON licitaciones(monto_disponible DESC)
        WHERE monto_disponible > 0
        """, "Monto (ordenamiento)"),
        
        ("idx_lic_organismo", """
            CREATE INDEX IF NOT EXISTS idx_lic_organismo 
            ON licitaciones(organismo)
        """, "Organismo (agrupamiento)"),

        # GIN Trigram para búsquedas ILIKE en nombre (buscar_por_palabra)
        ("idx_lic_nombre_trgm", """
            CREATE INDEX IF NOT EXISTS idx_lic_nombre_trgm
            ON licitaciones
            USING gin(nombre gin_trgm_ops)
        """, "GIN Trigram: nombre licitación (búsqueda fuzzy)"),

        # GIN Trigram para búsquedas ILIKE en organismo
        ("idx_lic_organismo_trgm", """
            CREATE INDEX IF NOT EXISTS idx_lic_organismo_trgm
            ON licitaciones
            USING gin(organismo gin_trgm_ops)
        """, "GIN Trigram: organismo (búsqueda fuzzy)"),
        
        # ========== HISTORICO: Índice para región ==========
        ("idx_hist_region", """
            CREATE INDEX IF NOT EXISTS idx_hist_region
            ON historico_licitaciones(UPPER(region))
        """, "Región uppercase (filtros por región)"),
        
        # ========== PRODUCTOS_SOLICITADOS (89K registros) ==========
        ("idx_prod_codigo", """
            CREATE INDEX IF NOT EXISTS idx_prod_codigo 
            ON productos_solicitados(codigo_licitacion)
        """, "Código licitación (joins)"),
        
        ("idx_prod_nombre", """
            CREATE INDEX IF NOT EXISTS idx_prod_nombre 
            ON productos_solicitados(LOWER(nombre))
        """, "Nombre producto (búsqueda legacy)"),

        # GIN Trigram para búsquedas ILIKE en nombre producto
        ("idx_prod_nombre_trgm", """
            CREATE INDEX IF NOT EXISTS idx_prod_nombre_trgm
            ON productos_solicitados
            USING gin(nombre gin_trgm_ops)
        """, "GIN Trigram: nombre producto (búsqueda fuzzy)"),
        
        # ========== LICITACIONES_DETALLE (24K registros) ==========
        ("idx_det_estado", """
            CREATE INDEX IF NOT EXISTS idx_det_estado 
            ON licitaciones_detalle(id_estado)
        """, "Estado (filtros)"),
        
        ("idx_det_presupuesto", """
            CREATE INDEX IF NOT EXISTS idx_det_presupuesto 
            ON licitaciones_detalle(presupuesto_estimado DESC)
        WHERE presupuesto_estimado > 0
        """, "Presupuesto (ordenamiento)"),
        
        # ========== HISTORIAL (41K registros) ==========
        ("idx_historial_codigo_fecha", """
            CREATE INDEX IF NOT EXISTS idx_historial_codigo_fecha 
            ON historial(codigo_licitacion, fecha DESC)
        """, "Código + fecha (timeline)"),
        
        # ========== PERFILES_EMPRESAS ==========
        ("idx_perfiles_alertas", """
            CREATE INDEX IF NOT EXISTS idx_perfiles_alertas 
            ON perfiles_empresas(alertas_activas)
        WHERE alertas_activas = 1
        """, "Alertas activas (notificaciones)"),
        
        # ========== LICITACIONES_GUARDADAS ==========
        ("idx_guardadas_user_fecha", """
            CREATE INDEX IF NOT EXISTS idx_guardadas_user_fecha 
            ON licitaciones_guardadas(telegram_user_id, fecha_guardado DESC)
        """, "Usuario + fecha (historial)"),
    ]
    
    total = len(indices)
    creados = 0
    existentes = 0
    errores = 0
    
    for i, (nombre, sql, descripcion) in enumerate(indices, 1):
        try:
            print(f"[{i}/{total}] Creando {nombre}...")
            print(f"         {descripcion}")
            cursor.execute(sql)
            conn.commit()
            creados += 1
            print(f"         ✅ Creado\n")
        except Exception as e:
            error_msg = str(e).lower()
            if "already exists" in error_msg:
                existentes += 1
                print(f"         ℹ️  Ya existe\n")
            else:
                errores += 1
                print(f"         ❌ Error: {e}\n")
    
    print("=" * 80)
    print("RESUMEN:")
    print(f"  • Índices creados: {creados}")
    print(f"  • Ya existían: {existentes}")
    print(f"  • Errores: {errores}")
    print("=" * 80)
    
    # Analizar tamaño de índices
    print("\nANALIZANDO TAMAÑO DE ÍNDICES...")
    cursor.execute("""
        SELECT 
            schemaname,
            tablename,
            indexname,
            pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename IN ('historico_licitaciones', 'licitaciones', 'productos_solicitados')
        ORDER BY pg_relation_size(indexname::regclass) DESC
        LIMIT 15
    """)
    
    print("\nTop 15 índices más grandes:")
    for schema, tabla, idx, size in cursor.fetchall():
        print(f"  • {idx[:50]:50} {size:>10} ({tabla})")
    
    conn.close()
    print("\n✅ Índices optimizados creados/verificados")

if __name__ == "__main__":
    crear_indices_optimizados()
