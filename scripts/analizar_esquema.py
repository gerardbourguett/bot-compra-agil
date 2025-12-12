"""
Script para analizar el esquema de la base de datos y generar reporte
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import database_extended as db
import psycopg2

def analizar_esquema():
    """Analiza todas las tablas y sus columnas"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Obtener todas las tablas
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    
    tablas = [row[0] for row in cursor.fetchall()]
    
    print("=" * 80)
    print("ESQUEMA DE BASE DE DATOS - COMPRA ÁGIL")
    print("=" * 80)
    print()
    
    for tabla in tablas:
        # Obtener columnas
        cursor.execute(f"""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{tabla}'
            ORDER BY ordinal_position
        """)
        
        columnas = cursor.fetchall()
        
        # Contar registros
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            count = cursor.fetchone()[0]
        except:
            count = "N/A"
        
        #Obtener índices
        cursor.execute(f"""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = '{tabla}'
        """)
        indices = cursor.fetchall()
        
        print(f"📊 TABLA: {tabla}")
        print(f"   Registros: {count:,}" if count != "N/A" else f"   Registros: {count}")
        print()
        print("   Columnas:")
        for col_name, col_type, col_default, is_null in columnas:
            nullable = "NULL" if is_null == 'YES' else "NOT NULL"
            default = f" DEFAULT {col_default}" if col_default else ""
            print(f"      • {col_name}: {col_type} {nullable}{default}")
        
        if indices:
            print()
            print("   Índices:")
            for idx_name, idx_def in indices:
                print(f"      • {idx_name}")
        
        print()
        print("-" * 80)
        print()
    
    conn.close()

if __name__ == "__main__":
    analizar_esquema()
