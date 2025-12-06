import os
import requests
import zipfile
import io
import csv
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import logging
from tqdm import tqdm
import database_extended as db

# Configuración
CHUNK_SIZE = 1024 * 1024 * 10  # 10 MB
BATCH_SIZE = 5000

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def descargar_y_procesar(url):
    logger.info(f"Iniciando importación desde: {url}")
    
    # Descargar archivo temporalmente
    local_filename = "temp_historico.zip"
    start_time = datetime.now()
    
    try:
        # Obtener tamaño del archivo
        logger.info("Obteniendo información del archivo...")
        response = requests.head(url, allow_redirects=True)
        total_size = int(response.headers.get('content-length', 0))
        
        if total_size > 0:
            logger.info(f"Tamaño del archivo: {total_size / (1024*1024):.2f} MB")
        
        # Descargar con barra de progreso
        logger.info("Iniciando descarga...")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            
            with open(local_filename, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, 
                         desc="Descargando", ncols=100) as pbar:
                    for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        download_duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Descarga completada en {download_duration:.1f}s")
        
        # Obtener tamaño del archivo descargado
        file_size = os.path.getsize(local_filename)
        logger.info(f"Archivo descargado: {file_size / (1024*1024):.2f} MB")
        
        # Procesar ZIP
        logger.info("Extrayendo archivos ZIP...")
        with zipfile.ZipFile(local_filename, 'r') as z:
            csv_files = [f for f in z.namelist() if f.endswith('.csv')]
            logger.info(f"Encontrados {len(csv_files)} archivo(s) CSV: {csv_files}")
            
            conn = db.get_connection()
            total_records = 0
            
            for csv_file in csv_files:
                records = procesar_csv(z, csv_file, conn)
                total_records += records
                
            conn.close()
            
            total_duration = (datetime.now() - start_time).total_seconds()
            logger.info("=" * 60)
            logger.info("RESUMEN DE IMPORTACIÓN")
            logger.info("=" * 60)
            logger.info(f"Total registros procesados: {total_records:,}")
            logger.info(f"Tiempo total: {total_duration:.1f}s ({total_duration/60:.1f} min)")
            if total_records > 0:
                logger.info(f"Velocidad promedio: {total_records/total_duration:.1f} registros/s")
            logger.info("=" * 60)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red al descargar archivo: {e}")
        raise
    except zipfile.BadZipFile as e:
        logger.error(f"Error: Archivo ZIP corrupto o inválido: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        raise
    finally:
        if os.path.exists(local_filename):
            os.remove(local_filename)
            logger.info("Archivo temporal eliminado.")

def procesar_csv(zip_ref, filename, conn):
    logger.info(f"Procesando archivo: {filename}")
    start_time = datetime.now()
    
    with zip_ref.open(filename) as f:
        text_file = io.TextIOWrapper(f, encoding='utf-8-sig', errors='replace')
        reader = csv.DictReader(text_file, delimiter=';')
        
        batch = []
        count = 0
        errors = 0
        
        cursor = conn.cursor()
        
        # Primera pasada para contar filas (opcional, para mejor barra de progreso)
        logger.info("Contando registros en el archivo...")
        text_file.seek(0)
        total_rows = sum(1 for _ in csv.DictReader(text_file, delimiter=';'))
        text_file.seek(0)
        reader = csv.DictReader(text_file, delimiter=';')
        
        logger.info(f"Total de filas a procesar: {total_rows:,}")
        
        with tqdm(total=total_rows, desc=f"Procesando {filename}", 
                 unit=" registros", ncols=100) as pbar:
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
                        pbar.update(BATCH_SIZE)
                        
                except ValueError as e:
                    errors += 1
                    continue # Saltar filas con errores de formato
                    
        # Insertar batch final
        if batch:
            insertar_batch(cursor, batch)
            count += len(batch)
            pbar.update(len(batch))
            
        conn.commit()
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Archivo {filename} procesado:")
        logger.info(f"  - Registros insertados: {count:,}")
        if errors > 0:
            logger.warning(f"  - Filas con errores omitidas: {errors:,}")
        logger.info(f"  - Tiempo: {duration:.1f}s")
        logger.info(f"  - Velocidad: {count/duration:.1f} registros/s")
        
        return count

def insertar_batch(cursor, batch):
    if db.USE_POSTGRES:
        query = """
            INSERT INTO historico_licitaciones (
                codigo_cotizacion, nombre_cotizacion, region, rut_proveedor, 
                nombre_proveedor, producto_cotizado, cantidad, monto_total, 
                detalle_oferta, es_ganador, fecha_cierre
            ) VALUES %s
        """
        execute_values(cursor, query, batch)
    else:
        query = """
            INSERT INTO historico_licitaciones (
                codigo_cotizacion, nombre_cotizacion, region, rut_proveedor, 
                nombre_proveedor, producto_cotizado, cantidad, monto_total, 
                detalle_oferta, es_ganador, fecha_cierre
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.executemany(query, batch)

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
