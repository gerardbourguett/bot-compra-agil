"""
Configuración de logging estructurado para CompraAgil
Formato JSON compatible con Loki/Promtail
"""
import logging
import json
from datetime import datetime
import sys


class LokiFormatter(logging.Formatter):
    """
    Formatter que genera logs en formato JSON para Promtail/Loki
    """

    def format(self, record):
        """
        Formatea un record de logging en JSON estructurado

        Campos base:
        - timestamp: ISO 8601 con timezone UTC
        - level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        - app: "compra_agil"
        - service: "telegram_bot" o "scraper"
        - message: Mensaje del log

        Campos opcionales (via extra={}):
        - user_id: ID del usuario de Telegram
        - tier: Tier de suscripción
        - command: Comando ejecutado
        - duration_ms: Duración en milisegundos
        - error: Tipo de error
        """

        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "app": "compra_agil",
            "service": getattr(record, 'service', 'unknown'),
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Contexto adicional pasado via extra={}
        optional_fields = [
            'user_id',
            'tier',
            'command',
            'duration_ms',
            'error',
            'licitacion_id',
            'query_type',
            'cache_result',
            'api_service'
        ]

        for field in optional_fields:
            if hasattr(record, field):
                log_obj[field] = getattr(record, field)

        # Stack trace si es un error
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            log_obj['exc_type'] = record.exc_info[0].__name__ if record.exc_info[0] else None

        # Información del módulo y línea para debugging
        if record.levelno >= logging.ERROR:
            log_obj['file'] = record.filename
            log_obj['line'] = record.lineno
            log_obj['function'] = record.funcName

        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(service='telegram_bot', level=logging.INFO):
    """
    Configura el logging estructurado para el servicio

    Args:
        service: Nombre del servicio ('telegram_bot', 'scraper', 'api')
        level: Nivel de logging (default: INFO)

    Returns:
        logger: LoggerAdapter con contexto de servicio
    """

    # Clase de filtro que aplica service a todos los logs
    class ServiceFilter(logging.Filter):
        def __init__(self, service_name):
            super().__init__()
            self.service_name = service_name

        def filter(self, record):
            # FORZAR el atributo service en TODOS los records
            record.service = self.service_name
            return True

    # Crear formatter
    formatter = LokiFormatter()

    # Handler para stdout (Promtail lo capturará)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(ServiceFilter(service))

    # Handler para stderr (solo errores)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    stderr_handler.addFilter(ServiceFilter(service))
    stderr_handler.setLevel(logging.ERROR)

    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = []  # Limpiar handlers existentes
    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(stderr_handler)

    # Logger específico de la app
    app_logger = logging.getLogger('compra_agil')
    app_logger.setLevel(level)

    # Silenciar loggers ruidosos de terceros
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

    # Usar LoggerAdapter para inyectar 'service' en TODOS los logs
    # Esto es más confiable que el filtro solo
    class ServiceAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            # Asegurar que 'extra' existe y contiene 'service'
            if 'extra' not in kwargs:
                kwargs['extra'] = {}
            kwargs['extra']['service'] = self.extra['service']
            return msg, kwargs

    return ServiceAdapter(app_logger, {'service': service})


# ==================== FUNCIONES DE UTILIDAD ====================

def log_command(logger, command: str, user_id: int, tier: str, status: str = 'success', duration_ms: int = None):
    """
    Log estructurado para ejecución de comandos

    Args:
        logger: Logger instance
        command: Nombre del comando
        user_id: ID del usuario
        tier: Tier de suscripción
        status: 'success', 'error', 'blocked'
        duration_ms: Duración en milisegundos (opcional)
    """
    extra = {
        'command': command,
        'user_id': user_id,
        'tier': tier
    }

    if duration_ms:
        extra['duration_ms'] = duration_ms

    if status == 'success':
        logger.info(f"Comando ejecutado: /{command}", extra=extra)
    elif status == 'blocked':
        logger.warning(f"Comando bloqueado por límite: /{command}", extra=extra)
    elif status == 'error':
        logger.error(f"Error en comando: /{command}", extra=extra)


def log_ml_analysis(logger, analysis_type: str, user_id: int, duration_ms: int, status: str = 'success'):
    """
    Log estructurado para análisis ML

    Args:
        logger: Logger instance
        analysis_type: Tipo de análisis ('precio', 'rag', 'competencia', 'scoring')
        user_id: ID del usuario
        duration_ms: Duración en milisegundos
        status: 'success' o 'error'
    """
    extra = {
        'user_id': user_id,
        'command': analysis_type,
        'duration_ms': duration_ms
    }

    if status == 'success':
        logger.info(f"Análisis ML completado: {analysis_type} ({duration_ms}ms)", extra=extra)
    else:
        logger.error(f"Error en análisis ML: {analysis_type}", extra=extra)


def log_db_query(logger, query_type: str, duration_ms: int, rows_affected: int = None):
    """
    Log estructurado para queries de BD

    Args:
        logger: Logger instance
        query_type: Tipo de query ('search', 'ml_data', 'insert', 'update')
        duration_ms: Duración en milisegundos
        rows_affected: Número de filas afectadas (opcional)
    """
    extra = {
        'query_type': query_type,
        'duration_ms': duration_ms
    }

    if rows_affected is not None:
        extra['rows_affected'] = rows_affected

    if duration_ms > 1000:  # Slow query (>1s)
        logger.warning(f"Slow query detected: {query_type} ({duration_ms}ms)", extra=extra)
    else:
        logger.debug(f"Query executed: {query_type} ({duration_ms}ms)", extra=extra)


def log_cache_operation(logger, key: str, hit: bool, duration_ms: int = None):
    """
    Log estructurado para operaciones de cache

    Args:
        logger: Logger instance
        key: Clave de cache
        hit: True si fue hit, False si fue miss
        duration_ms: Duración en milisegundos (opcional)
    """
    result = 'hit' if hit else 'miss'
    extra = {'cache_result': result}

    if duration_ms:
        extra['duration_ms'] = duration_ms

    logger.debug(f"Cache {result}: {key}", extra=extra)


def log_api_error(logger, service: str, error_type: str, error_message: str, user_id: int = None):
    """
    Log estructurado para errores de APIs externas

    Args:
        logger: Logger instance
        service: Servicio que falló ('gemini', 'telegram', 'mercado_publico')
        error_type: Tipo de error ('timeout', 'connection_error', 'api_error', 'rate_limit')
        error_message: Mensaje de error
        user_id: ID del usuario afectado (opcional)
    """
    extra = {
        'api_service': service,
        'error': error_type
    }

    if user_id:
        extra['user_id'] = user_id

    logger.error(f"API error [{service}]: {error_message}", extra=extra)


# ==================== EJEMPLO DE USO ====================

if __name__ == '__main__':
    # Configurar logger
    logger = setup_logging(service='telegram_bot', level=logging.DEBUG)

    # Ejemplos de logs estructurados
    logger.info("Bot iniciado correctamente")

    log_command(logger, 'buscar', user_id=123456, tier='free', status='success', duration_ms=250)
    log_command(logger, 'precio', user_id=123456, tier='free', status='blocked')

    log_ml_analysis(logger, 'precio', user_id=789012, duration_ms=2500, status='success')

    log_db_query(logger, 'ml_data', duration_ms=850, rows_affected=1500)
    log_db_query(logger, 'search', duration_ms=1200)  # Slow query

    log_cache_operation(logger, 'ml:precio:computadores', hit=True, duration_ms=5)
    log_cache_operation(logger, 'ml:rag:mobiliario', hit=False)

    log_api_error(logger, 'gemini', 'rate_limit', 'API quota exceeded', user_id=123456)

    # Error con stack trace
    try:
        raise ValueError("Ejemplo de error")
    except Exception as e:
        logger.error("Error inesperado", exc_info=True, extra={'user_id': 123456})

    print("\n✅ Logs JSON generados correctamente")
    print("Los logs arriba están en formato JSON listo para Promtail/Loki")
