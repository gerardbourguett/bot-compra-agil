import database_extended as db
import os
import sys

def verificar_salud():
    print("🏥 Verificando salud del scraper...")
    
    # 1. Verificar conexión a BD
    try:
        conn = db.get_connection()
        conn.close()
        print("✅ Conexión a BD exitosa")
    except Exception as e:
        print(f"❌ Error de conexión a BD: {e}")
        sys.exit(1)
        
    # 2. Verificar que se están escribiendo logs
    log_path = "/app/logs/ultima_ejecucion.txt"
    if os.path.exists(log_path):
         print(f"✅ Log de última ejecución encontrado en {log_path}")
         with open(log_path, 'r') as f:
             print(f"   Última ejecución: {f.read().strip()}")
    else:
         print(f"⚠️ No se encontró log de última ejecución en {log_path}")

    print("✅ Sistema saludable")

if __name__ == "__main__":
    verificar_salud()
