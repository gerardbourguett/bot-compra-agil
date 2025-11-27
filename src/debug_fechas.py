import database_extended as db_ext

def debug_fechas():
    conn = db_ext.get_connection()
    cursor = conn.cursor()
    
    print("Verificando formatos de fecha en BD...")
    
    cursor.execute("SELECT fecha_cierre FROM licitaciones LIMIT 5")
    fechas = cursor.fetchall()
    
    if not fechas:
        print("No hay licitaciones en la BD.")
    else:
        for f in fechas:
            print(f"Fecha cierre: {f[0]}")
            
    conn.close()

if __name__ == "__main__":
    debug_fechas()
