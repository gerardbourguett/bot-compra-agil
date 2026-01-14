import os
import time
import logging
from datetime import datetime, timedelta
from curl_cffi import requests
from dotenv import load_dotenv
import database_extended as db

load_dotenv()

# Logger para este módulo
logger = logging.getLogger('compra_agil.scraper')

# Configuración de la API
API_BASE_URL = "https://api.buscador.mercadopublico.cl/compra-agil"
API_KEY = os.getenv('MERCADO_PUBLICO_API_KEY')


def obtener_headers():
    """
    Construye los headers necesarios para las peticiones a la API.
    Solo necesitamos la X-API-Key, no se requiere token Bearer.
    """
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "es-ES,es;q=0.9",
        "origin": "https://buscador.mercadopublico.cl",
        "referer": "https://buscador.mercadopublico.cl/",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/142.0.0.0 Safari/537.36"
        ),
        "x-api-key": API_KEY
    }


def obtener_licitaciones(date_from, date_to, status=2, page_number=1):
    """
    Obtiene las licitaciones de la API para una página específica.

    Args:
        date_from: Fecha inicial (formato: YYYY-MM-DD)
        date_to: Fecha final (formato: YYYY-MM-DD)
        status: Estado de las licitaciones (2 = Publicada)
        page_number: Número de página a obtener

    Returns:
        dict: Respuesta JSON de la API o None si hay error
    """
    params = {
        "date_from": date_from,
        "date_to": date_to,
        "order_by": "recent",
        "page_number": page_number
    }
    
    if status is not None:
        params["status"] = status

    headers = obtener_headers()

    try:
        response = requests.get(
            API_BASE_URL,
            params=params,
            headers=headers,
            impersonate="chrome120"
        )
        response.raise_for_status()
        return response.json()
    except Exception as error:
        logger.error(f"Error al obtener licitaciones (página {page_number}): {error}")
        return None


def ejecutar_scraper(dias_atras=30, max_paginas=None):
    """
    Ejecuta el scraper completo obteniendo todas las páginas de resultados.

    Args:
        dias_atras: Número de días hacia atrás para buscar licitaciones (default: 30)
        max_paginas: Número máximo de páginas a procesar (None = todas)
    """
    print("🕷️ Iniciando Scraper de Compra Ágil...")
    db.iniciar_db_extendida()  # Aseguramos que la tabla exista

    # Calcular fechas
    fecha_hasta = datetime.now()
    fecha_desde = fecha_hasta - timedelta(days=dias_atras)

    date_from = fecha_desde.strftime("%Y-%m-%d")
    date_to = fecha_hasta.strftime("%Y-%m-%d")

    logger.info(f"Buscando licitaciones desde {date_from} hasta {date_to}")

    nuevos_total = 0
    page_number = 1

    while True:
        # Verificar si alcanzamos el máximo de páginas
        if max_paginas and page_number > max_paginas:
            logger.info(f"Alcanzado el límite de {max_paginas} páginas")
            break

        logger.debug(f"Procesando página {page_number}...")

        # Pasamos status=None para obtener todos los estados
        data = obtener_licitaciones(date_from, date_to, status=None, page_number=page_number)

        if not data or data.get('success') != 'OK':
            logger.error("Error en la respuesta de la API")
            break

        payload = data.get('payload', {})
        items = payload.get('resultados', [])

        if not items:
            logger.info("No hay más resultados")
            break

        # Mostrar información de progreso
        if page_number == 1:
            total_resultados = payload.get('resultCount', 0)
            total_paginas = payload.get('pageCount', 0)
            logger.info(f"Total de licitaciones encontradas: {total_resultados}")
            logger.info(f"Total de páginas: {total_paginas}")

        logger.debug(f"Procesando {len(items)} licitaciones...")

        for item in items:
            datos_tupla = (
                item.get('id'),
                item.get('codigo'),
                item.get('nombre'),
                item.get('fecha_publicacion'),
                item.get('fecha_cierre'),
                item.get('organismo'),
                item.get('unidad'),
                item.get('id_estado'),
                item.get('estado'),
                item.get('monto_disponible'),
                item.get('moneda'),
                item.get('monto_disponible_CLP'),
                item.get('fecha_cambio'),
                item.get('valor_cambio_moneda'),
                item.get('cantidad_proveedores_cotizando'),
                item.get('estado_convocatoria')
            )
            nuevos_total += db.guardar_licitacion_basica(datos_tupla)

        # Verificar si hay más páginas
        page_count = payload.get('pageCount', 0)
        if page_number >= page_count:
            logger.info(f"Todas las páginas procesadas ({page_count} páginas)")
            break

        page_number += 1
        time.sleep(0.5)  # Pequeña pausa entre peticiones para no sobrecargar el servidor

    logger.info(f"Proceso terminado. Se guardaron {nuevos_total} licitaciones nuevas.")
    
    # Registrar timestamp de ejecución
    try:
        import database_bot as db_bot
        db_bot.update_system_status('last_scrape_list', datetime.now().isoformat())
        logger.debug("Timestamp actualizado en system_status")
    except Exception as e:
        logger.warning(f"No se pudo actualizar timestamp: {e}")

    if 'items' in locals():
        logger.info(f"Total de licitaciones procesadas: {(page_number - 1) * 15 + len(items)}")
    else:
        logger.info("Total de licitaciones procesadas: 0")


if __name__ == "__main__":
    # Por defecto busca los últimos 30 días
    # Puedes cambiar el número de días o limitar las páginas para pruebas
    # Ejemplo: ejecutar_scraper(dias_atras=7, max_paginas=5)
    ejecutar_scraper(dias_atras=30)
