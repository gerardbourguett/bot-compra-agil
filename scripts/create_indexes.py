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
    
    indices = [
        # ========== HISTÓRICO_LICITACIONES (10.6M registros) ==========
        # Índices para búsquedas de texto (ML/RAG)
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
        
        # ========== PRODUCTOS_SOLICITADOS (89K registros) ==========
        ("idx_prod_codigo", """
            CREATE INDEX IF NOT EXISTS idx_prod_codigo 
            ON productos_solicitados(codigo_licitacion)
        """, "Código licitación (joins)"),
        
        ("idx_prod_nombre", """
            CREATE INDEX IF NOT EXISTS idx_prod_nombre 
            ON productos_solicitados(LOWER(nombre))
        """, "Nombre producto (búsqueda)"),
        
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
