"""
Script de migración para agregar tablas de suscripciones y monetización.
Ejecutar una sola vez para actualizar el esquema de la base de datos.
"""
import os
import sys
from datetime import datetime

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import database_extended as db

def migrate_subscriptions_schema():
    """Crea las tablas necesarias para el sistema de suscripciones"""
    
    print("=" * 60)
    print("MIGRACIÓN: Sistema de Suscripciones")
    print("=" * 60)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Serial para PostgreSQL, AUTOINCREMENT para SQLite
    id_serial = "SERIAL PRIMARY KEY" if db.USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    try:
        # 1. Tabla de suscripciones
        print("\n[*] Creando tabla: subscriptions...")
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id BIGINT PRIMARY KEY,
                tier VARCHAR(20) DEFAULT 'free',
                status VARCHAR(20) DEFAULT 'active',
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                current_period_start DATE,
                current_period_end DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Tabla subscriptions creada")
        
        # 2. Tabla de tracking de uso
        print("\n[*] Creando tabla: usage_tracking...")
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS usage_tracking (
                id {id_serial},
                user_id BIGINT NOT NULL,
                action VARCHAR(50) NOT NULL,
                resource_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata {'JSONB' if db.USE_POSTGRES else 'TEXT'}
            )
        """)
        print("[OK] Tabla usage_tracking creada")
        
        # 3. Índices para performance
        print("\n[*] Creando indices...")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_user_action 
            ON usage_tracking(user_id, action, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_timestamp 
            ON usage_tracking(timestamp)
        """)
        
        print("[OK] Indices creados")
        
        # 4. Tabla de pagos (para futuro)
        print("\n[*] Creando tabla: payments...")
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS payments (
                id {id_serial},
                user_id BIGINT NOT NULL,
                amount INTEGER NOT NULL,
                currency VARCHAR(3) DEFAULT 'CLP',
                status VARCHAR(20),
                stripe_payment_id TEXT,
                stripe_invoice_id TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Tabla payments creada")
        
        # Commit de cambios
        conn.commit()
        
        print("\n" + "=" * 60)
        print("[OK] MIGRACION COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        
        # Mostrar resumen
        print("\n[INFO] Resumen:")
        print("  - subscriptions: Sistema de tiers y estados")
        print("  - usage_tracking: Tracking de uso por usuario")
        print("  - payments: Historial de pagos")
        print("  - Índices: Optimizados para consultas frecuentes")
        
        print("\n[TIP] Proximos pasos:")
        print("  1. Todos los usuarios nuevos tendrán tier 'free' por defecto")
        print("  2. El sistema trackeará automáticamente el uso")
        print("  3. Puedes empezar a usar subscriptions.py")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error en la migracion: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


def verify_migration():
    """Verifica que las tablas se crearon correctamente"""
    
    print("\n[CHECK] Verificando migracion...")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        tables_to_check = ['subscriptions', 'usage_tracking', 'payments']
        
        for table in tables_to_check:
            if db.USE_POSTGRES:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name = %s
                """, (table,))
            else:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table,))
            
            exists = cursor.fetchone()[0] > 0
            status = "[OK]" if exists else "[FAIL]"
            print(f"  {status} Tabla {table}")
        
        return True
        
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
    success = migrate_subscriptions_schema()
    
    if success:
        # Verificar
        verify_migration()
        print("\n[DONE] Listo para monetizar!\n")
    else:
        print("\n[WARNING] La migracion fallo. Revisa los errores arriba.\n")
        sys.exit(1)
