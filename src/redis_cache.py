"""
Redis Cache Module para CompraÁgil API
Implementa caching inteligente para mejorar performance
"""
import redis
import json
import functools
from typing import Optional, Callable, Any
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración Redis
REDIS_URL = os.getenv('REDIS_URL', 'redis://64.176.19.51:6379/0')

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
    print("✅ Redis conectado exitosamente")
except Exception as e:
    redis_client = None
    REDIS_AVAILABLE = False
    print(f"⚠️ Redis no disponible: {e}")

# TTLs configurados
CACHE_TTL = {
    'stats_general': timedelta(hours=1),      # Stats generales: 1 hora
    'stats_region': timedelta(minutes=30),     # Stats por región: 30 min
    'stats_organismo': timedelta(minutes=30),  # Stats por organismo: 30 min
    'licitacion': timedelta(minutes=15),       # Detalle de licitación: 15 min
    'productos': timedelta(minutes=15),         # Productos: 15 min
    'historico_search': timedelta(minutes=30),  # Búsqueda histórica: 30 min
    'ml_precio': timedelta(hours=2),           # ML precio óptimo: 2 horas
    'ml_competencia': timedelta(hours=1),      # ML competencia: 1 hora
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

def cache_response(
    prefix: str,
    ttl: Optional[timedelta] = None,
    enabled: bool = True
):
    """
    Decorator para cachear respuestas de funciones
    
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
                    print(f"📦 Cache HIT: {cache_key}")
                    return json.loads(cached)
            except Exception as e:
                print(f"⚠️ Error leyendo cache: {e}")
            
            # Cache miss - ejecutar función
            print(f"🔄 Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Guardar en cache
            try:
                redis_client.setex(
                    cache_key,
                    ttl or timedelta(minutes=15),
                    json.dumps(result, default=str)
                )
                print(f"💾 Guardado en cache: {cache_key}")
            except Exception as e:
                print(f"⚠️  Error guardando cache: {e}")
            
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
            print(f"🗑️ Invalidados {count} keys con patrón: {pattern}")
            return count
        return 0
    except Exception as e:
        print(f"⚠️ Error invalidando cache: {e}")
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
        print("🗑️ Todo el cache ha sido limpiado")
        return True
    except Exception as e:
        print(f"⚠️ Error limpiando cache: {e}")
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
            print(f"⚠️ Error en rate limiting: {e}")
            return True, {"error": str(e)}

# Instancias de rate limiters
rate_limiters = {
    'global': RateLimiter(max_requests=1000, window=60),    # 1000/min global
    'ml': RateLimiter(max_requests=50, window=60),          # 50/min para ML
    'search': RateLimiter(max_requests=200, window=60),      # 200/min para búsquedas
}

if __name__ == "__main__":
    # Test básico
    print("=" * 60)
    print("REDIS CACHE MODULE - TEST")
    print("=" * 60)
    
    if REDIS_AVAILABLE:
        print("\n✅ Redis disponible")
        print(f"URL: {REDIS_URL}")
        
        # Test cache stats
        stats = get_cache_stats()
        print(f"\n📊 Cache Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Test rate limiting
        limiter = rate_limiters['global']
        allowed, info = limiter.is_allowed("test_key")
        print(f"\n🚦 Rate Limit Test:")
        print(f"  Allowed: {allowed}")
        print(f"  Info: {info}")
    else:
        print("\n⚠️ Redis NO disponible")
        print("Instala Redis:")
        print("  Windows: https://github.com/microsoftarchive/redis/releases")
        print("  Docker: docker run -d -p 6379:6379 redis:alpine")
        print("  Linux: sudo apt-get install redis-server")
    
    print("\n" + "=" * 60)
