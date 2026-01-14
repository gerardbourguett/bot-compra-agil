"""
Script de migración para agregar tabla de API keys.
Ejecutar una sola vez para agregar autenticación a la API.
"""
import os
import sys
from datetime import datetime

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import database_extended as db

def migrate_api_keys_schema():
    """Crea la tabla api_keys para autenticación de API"""
    
    print("=" * 60)
    print("MIGRACIÓN: Tabla de API Keys")
    print("=" * 60)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Serial para PostgreSQL, AUTOINCREMENT para SQLite
    id_serial = "SERIAL PRIMARY KEY" if db.USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    try:
        # Tabla de API keys
        print("\n[*] Creando tabla: api_keys...")
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS api_keys (
                id {id_serial},
                user_id BIGINT NOT NULL,
                key_hash TEXT NOT NULL UNIQUE,
                nombre TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        print("[OK] Tabla api_keys creada")
        
        # Índices para performance
        print("\n[*] Creando indices...")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_keys_user
            ON api_keys(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_keys_hash
            ON api_keys(key_hash)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_keys_active
            ON api_keys(user_id, is_active)
        """)
        
        print("[OK] Indices creados")
        
        # Commit de cambios
        conn.commit()
        
        print("\n" + "=" * 60)
        print("[OK] MIGRACION COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        
        # Mostrar resumen
        print("\n[INFO] Resumen:")
        print("  - api_keys: Almacena API keys hasheadas para autenticación")
        print("  - Índices: Optimizados para validación rápida")
        
        print("\n[TIP] Proximos pasos:")
        print("  1. Usuarios con tier PROFESIONAL pueden generar API keys")
        print("  2. Usar POST /api/v3/auth/generate-key para crear una key")
        print("  3. Incluir header 'X-API-Key: tu-key' en requests a la API")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error en la migracion: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


def verify_migration():
    """Verifica que la tabla se creó correctamente"""
    
    print("\n[CHECK] Verificando migracion...")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        if db.USE_POSTGRES:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'api_keys'
            """)
        else:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='table' AND name='api_keys'
            """)
        
        exists = cursor.fetchone()[0] > 0
        status = "[OK]" if exists else "[FAIL]"
        print(f"  {status} Tabla api_keys")
        
        if exists:
            # Contar índices
            if db.USE_POSTGRES:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM pg_indexes 
                    WHERE tablename = 'api_keys'
                """)
            else:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM sqlite_master 
                    WHERE type='index' AND tbl_name='api_keys'
                """)
            
            indices = cursor.fetchone()[0]
            print(f"  [OK] {indices} indices creados")
        
        return exists
        
    except Exception as e:
        print(f"[ERROR] Error al verificar: {e}")
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    print("\n[START] Iniciando migracion de base de datos...\n")
    
    # Verificar tipo de BD
    print(f"[DB] Tipo de BD: {'PostgreSQL' if db.USE_POSTGRES else 'SQLite'}")
    print(f"[DB] DATABASE_URL: {db.DATABASE_URL[:30]}..." if db.DATABASE_URL else "[DB] SQLite Local")
    
    # Ejecutar migración
    success = migrate_api_keys_schema()
    
    if success:
        # Verificar
        verify_migration()
        print("\n[DONE] Listo para usar autenticacion API!\n")
    else:
        print("\n[WARNING] La migracion fallo. Revisa los errores arriba.\n")
        sys.exit(1)
