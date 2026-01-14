"""
Redis Cache Module para CompraÁgil API
Implementa caching inteligente para mejorar performance
"""
import redis
import json
import functools
import logging
from typing import Optional, Callable, Any
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Logger para este módulo
logger = logging.getLogger('compra_agil.redis_cache')

# Configuración Redis
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis conectado exitosamente")
except Exception as e:
    redis_client = None
    REDIS_AVAILABLE = False
    logger.warning(f"Redis no disponible: {e}")

# TTLs configurados por tipo de dato
CACHE_TTL = {
    # Stats y dashboards
    'stats_general': timedelta(hours=1),      # Stats generales: 1 hora
    'stats_region': timedelta(minutes=30),     # Stats por región: 30 min
    'stats_organismo': timedelta(minutes=30),  # Stats por organismo: 30 min

    # Licitaciones
    'licitacion': timedelta(minutes=15),       # Detalle de licitación: 15 min
    'licitacion_list': timedelta(minutes=10),  # Listados: 10 min (cambian rápido)
    'productos': timedelta(minutes=15),        # Productos: 15 min

    # Búsquedas históricas
    'historico_search': timedelta(minutes=30),  # Búsqueda histórica: 30 min
    'rag_search': timedelta(hours=1),          # RAG (más estable): 1 hora

    # Machine Learning (más costosos, TTL más largo)
    'ml_precio': timedelta(hours=2),           # ML precio óptimo: 2 horas
    'ml_competencia': timedelta(hours=1),      # ML competencia: 1 hora
    'ml_scoring': timedelta(hours=2),          # ML scoring: 2 horas
    'ml_rag': timedelta(hours=1),              # ML RAG: 1 hora

    # Embeddings y vectores (muy costosos, TTL largo)
    'embeddings': timedelta(days=1),           # Embeddings: 24 horas

    # Default
    'default': timedelta(minutes=15),          # Default: 15 min
}

def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Genera una clave de cache consistente
    
    Ejemplos:
        get_cache_key('stats', 'general') -> 'stats:general'
        get_cache_key('licitacion', codigo='123') -> 'licitacion:codigo:123'
    """
    parts = [prefix]
    
    # Añadir args
    for arg in args:
        if arg is not None:
            parts.append(str(arg))
    
    # Añadir kwargs
    for key, value in sorted(kwargs.items()):
        if value is not None:
            parts.append(f"{key}:{value}")
    
    return ":".join(parts)

# Métricas de caché (importar metrics_server si está disponible)
try:
    from metrics_server import cache_operations
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    cache_operations = None


def _track_cache_hit():
    """Track cache hit en métricas de Prometheus"""
    if METRICS_AVAILABLE and cache_operations:
        cache_operations.labels(result='hit').inc()


def _track_cache_miss():
    """Track cache miss en métricas de Prometheus"""
    if METRICS_AVAILABLE and cache_operations:
        cache_operations.labels(result='miss').inc()


def cache_response(
    prefix: str,
    ttl: Optional[timedelta] = None,
    enabled: bool = True
):
    """
    Decorator para cachear respuestas de funciones ASYNC

    Usage:
        @cache_response('stats_general', ttl=CACHE_TTL['stats_general'])
        async def get_stats():
            return {"data": ...}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Si Redis no está disponible o cache deshabilitado, ejecutar directamente
            if not REDIS_AVAILABLE or not enabled:
                return await func(*args, **kwargs)

            # Generar key de cache
            cache_key = get_cache_key(prefix, *args, **kwargs)

            # Intentar obtener del cache
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"CACHE HIT: {cache_key}")
                    _track_cache_hit()
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Error leyendo cache: {e}")

            # Cache miss - ejecutar función
            logger.debug(f"CACHE MISS: {cache_key}")
            _track_cache_miss()
            result = await func(*args, **kwargs)

            # Guardar en cache
            try:
                redis_client.setex(
                    cache_key,
                    ttl or CACHE_TTL.get('default', timedelta(minutes=15)),
                    json.dumps(result, default=str)
                )
                logger.debug(f"CACHE SAVE: {cache_key}")
            except Exception as e:
                logger.warning(f"Error guardando cache: {e}")

            return result

        return wrapper
    return decorator


def cache_response_sync(
    prefix: str,
    ttl: Optional[timedelta] = None,
    enabled: bool = True
):
    """
    Decorator para cachear respuestas de funciones SÍNCRONAS

    Usage:
        @cache_response_sync('ml_precio', ttl=CACHE_TTL['ml_precio'])
        def calcular_precio_optimo(producto):
            return {"precio": ...}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Si Redis no está disponible o cache deshabilitado, ejecutar directamente
            if not REDIS_AVAILABLE or not enabled:
                return func(*args, **kwargs)

            # Generar key de cache
            cache_key = get_cache_key(prefix, *args, **kwargs)

            # Intentar obtener del cache
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"CACHE HIT: {cache_key}")
                    _track_cache_hit()
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Error leyendo cache: {e}")

            # Cache miss - ejecutar función
            logger.debug(f"CACHE MISS: {cache_key}")
            _track_cache_miss()
            result = func(*args, **kwargs)

            # Guardar en cache
            try:
                redis_client.setex(
                    cache_key,
                    ttl or CACHE_TTL.get('default', timedelta(minutes=15)),
                    json.dumps(result, default=str)
                )
                logger.debug(f"CACHE SAVE: {cache_key}")
            except Exception as e:
                logger.warning(f"Error guardando cache: {e}")

            return result

        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """
    Invalida cache por patrón
    
    Usage:
        invalidate_cache('licitacion:*')  # Invalida todas las licitaciones
        invalidate_cache('stats:*')        # Invalida todas las stats
    """
    if not REDIS_AVAILABLE:
        return 0
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            count = redis_client.delete(*keys)
            logger.debug(f"Invalidated {count} keys con patrón: {pattern}")
            return count
        return 0
    except Exception as e:
        logger.warning(f"Error invalidando cache: {e}")
        return 0

def get_cache_stats() -> dict:
    """Obtiene estadísticas del cache"""
    if not REDIS_AVAILABLE:
        return {
            "available": False,
            "message": "Redis no disponible"
        }
    
    try:
        info = redis_client.info('stats')
        keyspace = redis_client.info('keyspace')
        
        db0 = keyspace.get('db0', {})
        
        return {
            "available": True,
            "total_keys": sum(int(v.get('keys', 0)) for v in keyspace.values() if isinstance(v, dict)),
            "hits": info.get('keyspace_hits', 0),
            "misses": info.get('keyspace_misses', 0),
            "hit_rate": (info.get('keyspace_hits', 0) / 
                        (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)) * 100),
            "memory_used": redis_client.info('memory').get('used_memory_human', 'N/A')
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }

def clear_all_cache():
    """Limpia todo el cache - usar con cuidado"""
    if not REDIS_AVAILABLE:
        return False
    
    try:
        redis_client.flushdb()
        logger.info("Todo el cache ha sido limpiado")
        return True
    except Exception as e:
        logger.warning(f"Error limpiando cache: {e}")
        return False

# Rate Limiting con Redis
class RateLimiter:
    """Sistema de rate limiting usando Redis"""
    
    def __init__(self, max_requests: int = 100, window: int = 60):
        """
        Args:
            max_requests: Máximo de requests permitidos
            window: Ventana de tiempo en segundos
        """
        self.max_requests = max_requests
        self.window = window
    
    def is_allowed(self, key: str) -> tuple[bool, dict]:
        """
        Verifica si una request está permitida
        
        Returns:
            (allowed: bool, info: dict)
        """
        if not REDIS_AVAILABLE:
            return True, {"rate_limit": "disabled"}
        
        try:
            current = redis_client.incr(key)
            
            if current == 1:
                # Primera request en esta ventana
                redis_client.expire(key, self.window)
            
            remaining = max(0, self.max_requests - current)
            
            return current <= self.max_requests, {
                "limit": self.max_requests,
                "remaining": remaining,
                "reset_in": redis_client.ttl(key)
            }
        except Exception as e:
            logger.warning(f"Error en rate limiting: {e}")
            return True, {"error": str(e)}

# Instancias de rate limiters
rate_limiters = {
    'global': RateLimiter(max_requests=1000, window=60),    # 1000/min global
    'ml': RateLimiter(max_requests=50, window=60),          # 50/min para ML
    'search': RateLimiter(max_requests=200, window=60),      # 200/min para búsquedas
}

if __name__ == "__main__":
    # Test basico - configurar logging para ver output
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    logger.info("=" * 60)
    logger.info("REDIS CACHE MODULE - TEST")
    logger.info("=" * 60)
    
    if REDIS_AVAILABLE:
        logger.info("Redis disponible")
        logger.info(f"URL: {REDIS_URL}")
        
        # Test cache stats
        stats = get_cache_stats()
        logger.info("Cache Stats:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
        # Test rate limiting
        limiter = rate_limiters['global']
        allowed, info = limiter.is_allowed("test_key")
        logger.info("Rate Limit Test:")
        logger.info(f"  Allowed: {allowed}")
        logger.info(f"  Info: {info}")
    else:
        logger.warning("Redis NO disponible")
        logger.info("Instala Redis:")
        logger.info("  Windows: https://github.com/microsoftarchive/redis/releases")
        logger.info("  Docker: docker run -d -p 6379:6379 redis:alpine")
        logger.info("  Linux: sudo apt-get install redis-server")
    
    logger.info("=" * 60)
