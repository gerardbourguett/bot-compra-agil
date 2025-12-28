"""
Scheduler para ejecutar los scrapers de forma independiente y periódica.
"""
import schedule
import time
import subprocess
import threading
import logging
import asyncio
from datetime import datetime
import metrics_server
import logger_config

# Configurar logging estructurado
logger = logger_config.setup_logging(service='scraper', level=logging.INFO)

def run_scraper_lista():
    """Ejecuta el scraper de listado (rápido)"""
    logger.info("🕷️ Iniciando Scraper de Lista...")
    try:
        # Ejecutar como subproceso para aislar memoria y errores
        result = subprocess.run(['python', 'src/scraper.py'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("✅ Scraper de Lista finalizado correctamente")
        else:
            logger.error(f"❌ Error en Scraper de Lista: {result.stderr}")
    except Exception as e:
        logger.error(f"❌ Excepción en Scraper de Lista: {e}")

def run_scraper_detalles():
    """Ejecuta el scraper de detalles (lento)"""
    logger.info("🔍 Iniciando Scraper de Detalles...")
    try:
        # Ejecutar como subproceso
        result = subprocess.run(['python', 'src/obtener_detalles.py'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("✅ Scraper de Detalles finalizado correctamente")
        else:
            logger.error(f"❌ Error en Scraper de Detalles: {result.stderr}")
    except Exception as e:
        logger.error(f"❌ Excepción en Scraper de Detalles: {e}")

def run_threaded(job_func):
    """Ejecuta una tarea en un hilo separado para no bloquear el scheduler"""
    job_thread = threading.Thread(target=job_func)
    job_thread.start()

# Configurar horarios
# Scraper de lista: Cada 10 minutos
schedule.every(60).minutes.do(run_threaded, run_scraper_lista)

# Scraper de detalles: Cada 30 minutos
schedule.every(120).minutes.do(run_threaded, run_scraper_detalles)

if __name__ == "__main__":
    logger.info("⏰ Scheduler iniciado")
    logger.info("📅 Tareas programadas:")
    logger.info("   - Scraper Lista: Cada 60 min")
    logger.info("   - Scraper Detalles: Cada 120 min")

    # Iniciar servidor de métricas en background
    try:
        def run_metrics_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(metrics_server.start_metrics_server(port=8000))
            loop.run_forever()

        metrics_thread = threading.Thread(target=run_metrics_server, daemon=True)
        metrics_thread.start()
        logger.info("✅ Servidor de métricas: http://0.0.0.0:8000/metrics")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo iniciar servidor de métricas: {e}")

    # Ejecutar inmediatamente al inicio
    run_threaded(run_scraper_lista)
    run_threaded(run_scraper_detalles)

    while True:
        schedule.run_pending()
        time.sleep(1)
