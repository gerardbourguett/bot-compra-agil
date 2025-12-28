"""
Servidor de métricas de Prometheus para CompraAgil
Expone métricas de negocio y performance en el puerto 8000
"""
import asyncio
import logging
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

# ==================== SERVIDOR DE MÉTRICAS ====================

async def metrics_handler(request):
    """Handler para el endpoint /metrics"""
    try:
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
