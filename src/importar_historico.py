import os
import requests
import zipfile
import io
import csv
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import database_extended as db

# Configuración
CHUNK_SIZE = 1024 * 1024 * 10  # 10 MB
BATCH_SIZE = 5000

def descargar_y_procesar(url):
    print(f"Descargando archivo desde: {url}")
    
    # Descargar archivo temporalmente
    local_filename = "temp_historico.zip"
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    f.write(chunk)
        print("Descarga completada.")
        
        # Procesar ZIP
        with zipfile.ZipFile(local_filename, 'r') as z:
            csv_files = [f for f in z.namelist() if f.endswith('.csv')]
            print(f"Archivos CSV encontrados: {csv_files}")
            
            conn = db.get_connection()
            
            for csv_file in csv_files:
                procesar_csv(z, csv_file, conn)
                
            conn.close()
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(local_filename):
            os.remove(local_filename)
            print("Archivo temporal eliminado.")

def procesar_csv(zip_ref, filename, conn):
    print(f"Procesando {filename}...")
    
    with zip_ref.open(filename) as f:
        text_file = io.TextIOWrapper(f, encoding='utf-8', errors='replace')
        reader = csv.DictReader(text_file, delimiter=';')
        
        batch = []
        count = 0
        
        cursor = conn.cursor()
        
        for row in reader:
            # Mapeo de columnas
            try:
                item = (
                    row.get('CodigoCotizacion'),
                    row.get('NombreCotizacion'),
                    row.get('Region'),
                    row.get('RUTProveedor'),
                    row.get('RazonSocialProveedor'),
                    row.get('ProductoCotizado'),
                    int(row.get('CantidadSolicitada', 0) or 0),
                    int(row.get('MontoTotal', 0) or 0),
                    row.get('DetalleCotizacion'),
                    True if row.get('ProveedorSeleccionado', '').lower() == 'si' else False,
                    row.get('FechaCierreParaCotizar')
                )
                batch.append(item)
                
                if len(batch) >= BATCH_SIZE:
                    insertar_batch(cursor, batch)
                    count += len(batch)
                    batch = []
                    print(f"   Insertados {count} registros...", end='\r')
                    
            except ValueError:
                continue # Saltar filas con errores de formato
                
        if batch:
            insertar_batch(cursor, batch)
            count += len(batch)
            
        conn.commit()
        print(f"\nFinalizado {filename}: {count} registros insertados.")

def insertar_batch(cursor, batch):
    query = """
        INSERT INTO historico_licitaciones (
            codigo_cotizacion, nombre_cotizacion, region, rut_proveedor, 
            nombre_proveedor, producto_cotizado, cantidad, monto_total, 
            detalle_oferta, es_ganador, fecha_cierre
        ) VALUES %s
    """
    execute_values(cursor, query, batch)

def verificar_existencia(url, conn):
    """Verifica si ya existen datos para el mes del archivo"""
    import re
    
    # Extraer fecha del nombre del archivo (COT_YYYY-MM.zip)
    match = re.search(r'COT_(\d{4}-\d{2})', url)
    if not match:
        print("⚠️ No se pudo determinar el mes desde la URL. Se procederá sin verificación.")
        return False
        
    mes = match.group(1)
    print(f"📅 Mes detectado: {mes}")
    
    cursor = conn.cursor()
    
    # Consultar si hay registros de ese mes
    # Asumimos que fecha_cierre está en formato YYYY-MM-DD
    if db.USE_POSTGRES:
        query = "SELECT COUNT(*) FROM historico_licitaciones WHERE TO_CHAR(fecha_cierre, 'YYYY-MM') = %s"
    else:
        query = "SELECT COUNT(*) FROM historico_licitaciones WHERE strftime('%Y-%m', fecha_cierre) = ?"
        
    cursor.execute(query, (mes,))
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"⚠️ Ya existen {count} registros para el mes {mes}.")
        return True
        
    return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Importar histórico de licitaciones')
    parser.add_argument('--url', default="https://transparenciachc.blob.core.windows.net/trnspchc/COT_2025-01.zip", help='URL del archivo ZIP')
    parser.add_argument('--db-url', help='URL de conexión a la base de datos (sobrescribe .env)')
    parser.add_argument('--force', action='store_true', help='Forzar importación aunque existan datos')
    
    args = parser.parse_args()
    
    # Sobrescribir URL de BD si se proporciona
    if args.db_url:
        os.environ['DATABASE_URL'] = args.db_url
        import importlib
        importlib.reload(db)
    
    # Asegurar que la tabla exista
    db.iniciar_db_extendida()
    
    # Verificar duplicados
    conn = db.get_connection()
    existe = verificar_existencia(args.url, conn)
    conn.close()
    
    if existe and not args.force:
        print("❌ Importación cancelada para evitar duplicados.")
        print("Usa --force para importar de todas formas.")
    else:
        start_time = datetime.now()
        descargar_y_procesar(args.url)
        duration = datetime.now() - start_time
        print(f"Tiempo total: {duration}")
