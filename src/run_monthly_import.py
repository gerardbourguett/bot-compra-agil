import os
from datetime import datetime, timedelta
import logging
import importar_historico as ih

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def build_month_str(target_month=None):
    if target_month:
        return target_month
    today = datetime.utcnow().date().replace(day=1)
    prev = today - timedelta(days=1)
    return f"{prev.year}-{prev.month:02d}"

def build_url(month_str):
    return f"https://transparenciachc.blob.core.windows.net/trnspchc/COT_{month_str}.zip"

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Importación mensual de histórico")
    parser.add_argument("--month", help="Mes a importar en formato YYYY-MM")
    parser.add_argument("--db-url", help="URL de conexión a la base de datos")
    parser.add_argument("--force", action="store_true", help="Forzar importación")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("IMPORTACIÓN MENSUAL DE HISTÓRICO - MERCADO PÚBLICO")
    logger.info("=" * 60)

    # Configurar base de datos si se proporciona URL
    if args.db_url:
        logger.info("Usando URL de base de datos personalizada")
        os.environ["DATABASE_URL"] = args.db_url
        import importlib
        importlib.reload(ih.db)

    # Inicializar base de datos
    logger.info("Inicializando estructura de base de datos...")
    try:
        ih.db.iniciar_db_extendida()
        logger.info("Base de datos lista")
    except Exception as e:
        logger.error(f"Error al inicializar base de datos: {e}")
        return

    # Determinar mes a importar
    month_str = build_month_str(args.month)
    url = build_url(month_str)
    
    logger.info(f"Mes a importar: {month_str}")
    logger.info(f"URL del archivo: {url}")

    # Verificar duplicados
    logger.info("Verificando si ya existen datos para este mes...")
    try:
        conn = ih.db.get_connection()
        exists = ih.verificar_existencia(url, conn)
        conn.close()
    except Exception as e:
        logger.error(f"Error al verificar existencia: {e}")
        return

    if exists and not args.force:
        logger.warning("=" * 60)
        logger.warning("IMPORTACIÓN CANCELADA")
        logger.warning("Ya existen datos para este mes en la base de datos.")
        logger.warning("Usa --force para importar de todas formas.")
        logger.warning("=" * 60)
        return
    
    if exists and args.force:
        logger.warning("Ya existen datos para este mes, pero se continuará (--force activo)")

    # Ejecutar importación
    logger.info("=" * 60)
    logger.info("INICIANDO PROCESO DE IMPORTACIÓN")
    logger.info("=" * 60)
    
    try:
        ih.descargar_y_procesar(url)
        logger.info("=" * 60)
        logger.info("✓ IMPORTACIÓN COMPLETADA EXITOSAMENTE")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("=" * 60)
        logger.error("✗ ERROR EN LA IMPORTACIÓN")
        logger.error(f"Detalles: {e}")
        logger.error("=" * 60)
        raise

if __name__ == "__main__":
    main()
