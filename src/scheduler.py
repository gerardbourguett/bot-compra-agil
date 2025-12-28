"""
Scheduler para ejecutar los scrapers de forma independiente y periódica.
"""
import schedule
import time
import subprocess
import threading
import logging
from datetime import datetime

# Configurar logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
    
    # Ejecutar inmediatamente al inicio
    run_threaded(run_scraper_lista)
    run_threaded(run_scraper_detalles)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
