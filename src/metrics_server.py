"""
Servidor de métricas de Prometheus para CompraAgil
Expone métricas de negocio y performance en el puerto 8000
"""
import asyncio
import logging
import os
import psutil
from aiohttp import web
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY, CollectorRegistry

logger = logging.getLogger(__name__)

# ==================== MÉTRICAS DE NEGOCIO ====================

# Comandos ejecutados
command_counter = Counter(
    'compra_agil_commands_total',
    'Total de comandos ejecutados',
    ['command', 'tier', 'status']
)

# Usuarios únicos activos
active_users = Gauge(
    'compra_agil_active_users',
    'Usuarios activos en las últimas 24 horas'
)

# Suscripciones activas por tier
subscriptions_gauge = Gauge(
    'compra_agil_subscriptions',
    'Suscripciones activas por tier',
    ['tier']
)

# Features premium bloqueadas (oportunidad de conversión)
premium_blocked = Counter(
    'compra_agil_premium_blocked_total',
    'Features premium bloqueadas por límite de tier',
    ['feature', 'tier']
)

# ==================== MÉTRICAS DE PERFORMANCE ====================

# Latencia de análisis ML
ml_latency = Histogram(
    'compra_agil_ml_duration_seconds',
    'Duración de análisis ML',
    ['analysis_type'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0]
)

# Latencia de queries a BD
db_query_latency = Histogram(
    'compra_agil_db_query_duration_seconds',
    'Duración de queries a PostgreSQL',
    ['query_type'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# Cache hits/misses
cache_operations = Counter(
    'compra_agil_cache_operations_total',
    'Operaciones de cache (hits/misses)',
    ['result']  # 'hit' o 'miss'
)

# Errores de API
api_errors = Counter(
    'compra_agil_errors_total',
    'Errores de API/servicios externos',
    ['service', 'error_type']
)

# Licitaciones procesadas por el scraper
licitaciones_scraped = Counter(
    'compra_agil_licitaciones_scraped_total',
    'Licitaciones procesadas por el scraper',
    ['status']  # 'new', 'updated', 'unchanged'
)

# Licitaciones activas en BD
licitaciones_activas = Gauge(
    'compra_agil_licitaciones_activas',
    'Número total de licitaciones activas en la base de datos'
)

# Búsquedas realizadas
busquedas_realizadas = Counter(
    'compra_agil_busquedas_total',
    'Búsquedas realizadas por los usuarios',
    ['tipo']  # 'texto', 'region', 'organismo', 'fecha'
)

# ==================== MÉTRICAS DE API ====================

# Requests HTTP a la API
api_requests = Counter(
    'compra_agil_api_requests_total',
    'Total de requests HTTP a la API',
    ['method', 'endpoint', 'status']
)

# Latencia de API
api_latency = Histogram(
    'compra_agil_api_latency_seconds',
    'Latencia de requests HTTP en segundos',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# ==================== MÉTRICAS DE SAAS / REVENUE ====================

# Revenue mensual por tier
revenue_mensual = Gauge(
    'compra_agil_revenue_mensual_clp',
    'Revenue mensual estimado en CLP',
    ['tier']
)

# Conversiones entre tiers
conversiones = Counter(
    'compra_agil_conversiones_total',
    'Conversiones de un tier a otro',
    ['tier_origen', 'tier_destino']
)

# Límites alcanzados (oportunidad de upsell)
limite_alcanzado = Counter(
    'compra_agil_limite_alcanzado_total',
    'Veces que un usuario alcanzó su límite de uso',
    ['tier', 'recurso']  # recurso: 'busquedas', 'ml_calls', 'api_calls'
)

# ==================== MÉTRICAS DE SISTEMA ====================

# Uso de memoria
memoria_uso_bytes = Gauge(
    'compra_agil_memoria_uso_bytes',
    'Uso de memoria del proceso en bytes',
    ['tipo']  # 'rss', 'vms', 'percent'
)

# Uso de CPU
cpu_uso_percent = Gauge(
    'compra_agil_cpu_uso_percent',
    'Uso de CPU del proceso'
)

# PostgreSQL
db_conexiones_activas = Gauge(
    'compra_agil_db_conexiones_activas',
    'Conexiones activas a PostgreSQL'
)

# Redis
redis_conexiones_activas = Gauge(
    'compra_agil_redis_conexiones_activas',
    'Conexiones activas a Redis'
)

redis_memoria_uso = Gauge(
    'compra_agil_redis_memoria_bytes',
    'Uso de memoria de Redis en bytes'
)

# ==================== SERVIDOR DE MÉTRICAS ====================

async def metrics_handler(request):
    """Handler para el endpoint /metrics"""
    try:
        # Actualizar métricas dinámicas antes de exponer
        update_system_metrics()
        update_database_metrics()
        update_redis_metrics()
        update_revenue_metrics()

        metrics_output = generate_latest(REGISTRY)
        return web.Response(
            body=metrics_output,
            content_type='text/plain'
        )
    except Exception as e:
        logger.error(f"Error generando métricas: {e}")
        return web.Response(text=f"Error: {e}", status=500)


async def health_handler(request):
    """Handler para el endpoint /health"""
    return web.Response(text='OK', status=200)


async def start_metrics_server(port=8000, host='0.0.0.0'):
    """
    Inicia el servidor HTTP para métricas de Prometheus

    Args:
        port: Puerto donde escuchar (default: 8000)
        host: Host donde escuchar (default: 0.0.0.0)
    """
    app = web.Application()
    app.router.add_get('/metrics', metrics_handler)
    app.router.add_get('/health', health_handler)
    app.router.add_get('/', health_handler)  # Para healthcheck básico

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    logger.info(f"📊 Metrics server started on http://{host}:{port}/metrics")
    logger.info(f"💚 Health check available at http://{host}:{port}/health")

    return runner


# ==================== FUNCIONES DE UTILIDAD ====================

def track_command(command: str, tier: str, status: str = 'success'):
    """
    Registra la ejecución de un comando

    Args:
        command: Nombre del comando (ej: 'precio', 'buscar')
        tier: Tier del usuario ('free', 'emprendedor', 'pyme', 'profesional')
        status: Estado ('success', 'error', 'blocked')
    """
    command_counter.labels(command=command, tier=tier, status=status).inc()


def track_ml_latency(analysis_type: str, duration_seconds: float):
    """
    Registra la latencia de un análisis ML

    Args:
        analysis_type: Tipo de análisis ('precio', 'rag', 'competencia', 'scoring')
        duration_seconds: Duración en segundos
    """
    ml_latency.labels(analysis_type=analysis_type).observe(duration_seconds)


def track_db_query(query_type: str, duration_seconds: float):
    """
    Registra la latencia de una query a BD

    Args:
        query_type: Tipo de query ('search', 'ml_data', 'insert', 'update')
        duration_seconds: Duración en segundos
    """
    db_query_latency.labels(query_type=query_type).observe(duration_seconds)


def track_cache(hit: bool):
    """
    Registra operación de cache

    Args:
        hit: True si fue hit, False si fue miss
    """
    result = 'hit' if hit else 'miss'
    cache_operations.labels(result=result).inc()


def track_premium_blocked(feature: str, tier: str):
    """
    Registra cuando un usuario intenta usar una feature premium bloqueada

    Args:
        feature: Feature bloqueada ('alertas_ia', 'generador_propuestas', etc)
        tier: Tier del usuario
    """
    premium_blocked.labels(feature=feature, tier=tier).inc()


def track_error(service: str, error_type: str):
    """
    Registra un error de servicio externo

    Args:
        service: Servicio que falló ('gemini', 'telegram', 'postgres', 'redis')
        error_type: Tipo de error ('timeout', 'connection_error', 'api_error')
    """
    api_errors.labels(service=service, error_type=error_type).inc()


def update_subscriptions(subscriptions_by_tier: dict):
    """
    Actualiza el gauge de suscripciones activas

    Args:
        subscriptions_by_tier: Dict con conteo por tier
            Ejemplo: {'free': 100, 'emprendedor': 20, 'pyme': 5, 'profesional': 2}
    """
    for tier, count in subscriptions_by_tier.items():
        subscriptions_gauge.labels(tier=tier).set(count)


def update_active_users(count: int):
    """
    Actualiza el número de usuarios activos

    Args:
        count: Número de usuarios activos en las últimas 24h
    """
    active_users.set(count)


def update_system_metrics():
    """
    Actualiza métricas de sistema (CPU, memoria)
    Llamar periódicamente o antes de exponer /metrics
    """
    try:
        process = psutil.Process(os.getpid())

        # Memoria
        mem_info = process.memory_info()
        memoria_uso_bytes.labels(tipo='rss').set(mem_info.rss)
        memoria_uso_bytes.labels(tipo='vms').set(mem_info.vms)
        memoria_uso_bytes.labels(tipo='percent').set(process.memory_percent())

        # CPU
        cpu_percent = process.cpu_percent(interval=0.1)
        cpu_uso_percent.set(cpu_percent)

    except Exception as e:
        logger.error(f"Error actualizando métricas de sistema: {e}")


def update_database_metrics():
    """
    Actualiza métricas de base de datos
    Llamar periódicamente o antes de exponer /metrics
    """
    try:
        import database_extended as db

        conn = db.get_connection()
        cursor = conn.cursor()

        # Licitaciones activas
        cursor.execute("SELECT COUNT(*) FROM licitaciones")
        count = cursor.fetchone()[0]
        licitaciones_activas.set(count)

        # Conexiones activas (solo PostgreSQL)
        if db.USE_POSTGRES:
            cursor.execute("""
                SELECT count(*)
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)
            conexiones = cursor.fetchone()[0]
            db_conexiones_activas.set(conexiones)

        conn.close()

    except Exception as e:
        logger.error(f"Error actualizando métricas de BD: {e}")


def update_redis_metrics():
    """
    Actualiza métricas de Redis
    Llamar periódicamente o antes de exponer /metrics
    """
    try:
        import redis_cache

        if redis_cache.REDIS_AVAILABLE and redis_cache.redis_client:
            # Conexiones
            info_clients = redis_cache.redis_client.info('clients')
            redis_conexiones_activas.set(info_clients.get('connected_clients', 0))

            # Memoria
            info_memory = redis_cache.redis_client.info('memory')
            redis_memoria_uso.set(info_memory.get('used_memory', 0))

    except Exception as e:
        logger.error(f"Error actualizando métricas de Redis: {e}")


def update_revenue_metrics():
    """
    Actualiza métricas de revenue y suscripciones
    Llamar periódicamente o antes de exponer /metrics
    """
    try:
        import database_extended as db

        conn = db.get_connection()
        cursor = conn.cursor()

        # Pricing plan (CLP por mes)
        pricing = {
            'free': 0,
            'emprendedor': 15000,
            'pyme': 45000,
            'profesional': 150000
        }

        # Contar suscripciones activas y calcular revenue
        cursor.execute("""
            SELECT subscription_tier, COUNT(*)
            FROM subscriptions
            WHERE status = 'active'
            GROUP BY subscription_tier
        """)

        for tier, count in cursor.fetchall():
            # Actualizar gauge de suscripciones
            subscriptions_gauge.labels(tier=tier).set(count)

            # Calcular revenue mensual
            revenue = pricing.get(tier, 0) * count
            revenue_mensual.labels(tier=tier).set(revenue)

        conn.close()

    except Exception as e:
        logger.error(f"Error actualizando métricas de revenue: {e}")


def track_search(tipo: str):
    """
    Registra una búsqueda realizada

    Args:
        tipo: Tipo de búsqueda ('texto', 'region', 'organismo', 'fecha')
    """
    busquedas_realizadas.labels(tipo=tipo).inc()


def track_api_request(method: str, endpoint: str, status: int, duration: float):
    """
    Registra un request HTTP a la API

    Args:
        method: Método HTTP (GET, POST, etc)
        endpoint: Endpoint llamado
        status: Status code HTTP
        duration: Duración en segundos
    """
    api_requests.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    api_latency.labels(method=method, endpoint=endpoint).observe(duration)


def track_limite_alcanzado(tier: str, recurso: str):
    """
    Registra cuando un usuario alcanza su límite de uso

    Args:
        tier: Tier del usuario
        recurso: Recurso limitado ('busquedas', 'ml_calls', 'api_calls')
    """
    limite_alcanzado.labels(tier=tier, recurso=recurso).inc()


def track_conversion(tier_origen: str, tier_destino: str):
    """
    Registra una conversión entre tiers

    Args:
        tier_origen: Tier anterior
        tier_destino: Tier nuevo
    """
    conversiones.labels(tier_origen=tier_origen, tier_destino=tier_destino).inc()


if __name__ == '__main__':
    # Test del servidor de métricas
    async def main():
        runner = await start_metrics_server()
        print("Servidor de métricas corriendo en http://localhost:8000/metrics")
        print("Presiona Ctrl+C para detener")

        # Simular algunas métricas de prueba
        track_command('buscar', 'free', 'success')
        track_command('precio', 'emprendedor', 'success')
        track_command('precio', 'free', 'blocked')
        track_ml_latency('precio', 2.5)
        track_cache(True)
        track_cache(False)
        update_subscriptions({'free': 100, 'emprendedor': 20})

        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\nDeteniendo servidor...")
            await runner.cleanup()

    asyncio.run(main())
