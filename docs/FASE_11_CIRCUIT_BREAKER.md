# Fase 11: Circuit Breaker & Métricas Prometheus

## Resumen

Implementación del patrón **Circuit Breaker** para proteger servicios externos y agregado de **métricas Prometheus** para el connection pool de PostgreSQL.

---

## Circuit Breaker

### ¿Qué es?

El Circuit Breaker es un patrón de diseño que previene:
- **Cascading failures**: Evita que un servicio externo caído afecte todo el sistema
- **Sobrecarga**: No sigue intentando llamar a servicios que están fallando
- **Recovery**: Permite tiempo de recuperación automático

### Estados

```
CLOSED (Normal) → OPEN (Bloqueado) → HALF_OPEN (Probando) → CLOSED
      ↑                                        ↓
      └────────────────────────────────────────┘
```

- **CLOSED**: Funcionamiento normal, todas las requests pasan
- **OPEN**: Circuito abierto, rechaza todas las requests inmediatamente
- **HALF_OPEN**: Permite 1 request de prueba para verificar recuperación

### Implementación

#### Uso como Decorador

```python
from circuit_breaker import circuit_breaker

@circuit_breaker(
    name='mi_servicio',
    failure_threshold=5,      # Abrir después de 5 fallos
    recovery_timeout=60        # Reintentar después de 60s
)
def llamar_servicio_externo():
    response = requests.get("https://api.externa.com/data")
    return response.json()

# Uso
try:
    data = llamar_servicio_externo()
except CircuitBreakerError:
    # El circuito está abierto - servicio temporalmente no disponible
    return {"error": "Service temporarily unavailable"}
```

#### Uso Manual

```python
from circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(
    name='gemini_ai',
    failure_threshold=3,
    recovery_timeout=30
)

try:
    result = breaker.call(lambda: generate_ai_response(prompt))
except CircuitBreakerError:
    # Usar fallback
    result = simple_rule_based_response(prompt)
```

### Circuit Breakers Pre-configurados

En `src/circuit_breaker.py`:

| Breaker | Threshold | Timeout | Uso |
|---------|-----------|---------|-----|
| `mercado_publico_breaker` | 5 fallos | 60s | API Mercado Público |
| `gemini_breaker` | 3 fallos | 30s | Gemini AI |
| `redis_breaker` | 5 fallos | 10s | Redis cache |

### Monitoreo

```python
from circuit_breaker import get_circuit_breaker

# Obtener estadísticas
breaker = get_circuit_breaker('mercado_publico')
stats = breaker.get_stats()
print(stats)
# {
#   'name': 'mercado_publico',
#   'state': 'CLOSED',
#   'failure_count': 0,
#   'failure_threshold': 5,
#   'last_failure_time': None,
#   'last_success_time': 1704067200.0,
#   'recovery_timeout': 60
# }

# Ver todos los breakers
from circuit_breaker import get_all_circuit_breakers
all_breakers = get_all_circuit_breakers()
```

---

## Métricas Prometheus

### Nuevas Métricas del Connection Pool

| Métrica | Tipo | Descripción |
|---------|------|-------------|
| `compra_agil_db_pool_size{status}` | Gauge | Tamaño del pool (min/max/current) |
| `compra_agil_db_pool_connections{state}` | Gauge | Conexiones por estado (available/in_use) |

### Métricas del Circuit Breaker

| Métrica | Tipo | Descripción |
|---------|------|-------------|
| `compra_agil_circuit_breaker_state{service}` | Gauge | Estado (0=closed, 1=open, 2=half_open) |
| `compra_agil_circuit_breaker_failures_total{service}` | Counter | Total de fallos detectados |
| `compra_agil_circuit_breaker_successes_total{service}` | Counter | Total de éxitos después de fallos |

### Endpoint

Las métricas se exponen en:
```
http://localhost:8000/metrics
```

### Ejemplo de Métricas

```prometheus
# HELP compra_agil_db_pool_size Tamaño del connection pool
# TYPE compra_agil_db_pool_size gauge
compra_agil_db_pool_size{status="min"} 2
compra_agil_db_pool_size{status="max"} 10

# HELP compra_agil_db_pool_connections Conexiones en el pool por estado
# TYPE compra_agil_db_pool_connections gauge
compra_agil_db_pool_connections{state="in_use"} 3

# HELP compra_agil_circuit_breaker_state Estado del circuit breaker
# TYPE compra_agil_circuit_breaker_state gauge
compra_agil_circuit_breaker_state{service="mercado_publico"} 0
compra_agil_circuit_breaker_state{service="gemini_ai"} 0

# HELP compra_agil_circuit_breaker_failures_total Total de fallos
# TYPE compra_agil_circuit_breaker_failures_total counter
compra_agil_circuit_breaker_failures_total{service="mercado_publico"} 12

# HELP compra_agil_circuit_breaker_successes_total Total de éxitos
# TYPE compra_agil_circuit_breaker_successes_total counter
compra_agil_circuit_breaker_successes_total{service="mercado_publico"} 1547
```

---

## Query Logging

### Configuración

Variables de entorno en `.env`:

```bash
# Umbral para loguear queries lentas (default: 100ms)
SLOW_QUERY_THRESHOLD_MS=100

# Habilitar logging de todas las queries (default: false)
# Solo para debugging - genera mucho log
ENABLE_QUERY_LOGGING=false
```

### Uso

```python
from database_extended import get_connection_context, execute_with_timing

with get_connection_context() as conn:
    cursor = conn.cursor()
    
    # La query se ejecuta y se loguea automáticamente si es lenta
    elapsed_ms = execute_with_timing(
        cursor,
        "SELECT * FROM historico_licitaciones WHERE producto ILIKE %s",
        ('%laptop%',)
    )
    
    # Si elapsed_ms > SLOW_QUERY_THRESHOLD_MS, se loguea automáticamente:
    # WARNING: Slow query (245.3ms): SELECT * FROM historico_licitaciones WHERE producto...
```

---

## Testing

### Test del Circuit Breaker

```bash
python src/circuit_breaker.py
```

Output esperado:
```
--- Attempt 1 ---
State: CLOSED
Failures: 0/3
❌ FAILED: Service failure #1

--- Attempt 2 ---
State: CLOSED
Failures: 1/3
❌ FAILED: Service failure #2

--- Attempt 3 ---
State: CLOSED
Failures: 2/3
❌ FAILED: Service failure #3

--- Attempt 4 ---
State: OPEN
Failures: 3/3
⚡ CIRCUIT OPEN: Circuit breaker 'test_service' is OPEN

💤 Waiting for recovery timeout...

--- Attempt 7 ---
State: HALF_OPEN
Failures: 3/3
✅ SUCCESS: Success!
```

---

## Integración con API Cliente

### Antes (sin circuit breaker)

```python
def obtener_licitaciones(date_from, date_to):
    response = requests.get(API_URL, params=...)
    return response.json()
```

### Después (con circuit breaker)

```python
def obtener_licitaciones(date_from, date_to):
    def _fetch():
        response = requests.get(API_URL, params=...)
        return response.json()
    
    try:
        return _safe_api_call(_fetch)  # Protegido por circuit breaker
    except CircuitBreakerError:
        logger.warning("Mercado Público API circuit breaker is OPEN")
        return None
```

---

## Beneficios

### Circuit Breaker

1. **Protección**: Evita sobrecarga de servicios externos caídos
2. **Fail Fast**: Respuestas rápidas cuando un servicio está caído (no espera timeout)
3. **Recovery**: Permite recuperación automática sin intervención manual
4. **Observabilidad**: Métricas Prometheus para monitoreo

### Connection Pool

1. **Performance**: Reutiliza conexiones (~50-100ms ahorrados por request)
2. **Recursos**: Límite controlado de conexiones simultáneas
3. **Estabilidad**: No agota conexiones de PostgreSQL
4. **Métricas**: Visibilidad del uso del pool en Prometheus

### Query Logging

1. **Debug**: Identifica queries lentas automáticamente
2. **Optimización**: Focaliza esfuerzos de optimización
3. **Alertas**: Puede integrarse con alertas de logging

---

## Prometheus + Grafana

### Dashboards Recomendados

#### Panel 1: Circuit Breakers
```promql
# Estado de circuit breakers
compra_agil_circuit_breaker_state

# Tasa de fallos por servicio
rate(compra_agil_circuit_breaker_failures_total[5m])

# Ratio éxito/fallo
rate(compra_agil_circuit_breaker_successes_total[5m]) 
/ 
rate(compra_agil_circuit_breaker_failures_total[5m])
```

#### Panel 2: Connection Pool
```promql
# Uso del pool (porcentaje)
100 * compra_agil_db_pool_connections{state="in_use"} 
/ 
compra_agil_db_pool_size{status="max"}

# Conexiones disponibles
compra_agil_db_pool_size{status="max"} 
- 
compra_agil_db_pool_connections{state="in_use"}
```

#### Panel 3: Query Performance
```promql
# Latencia de queries DB (percentil 95)
histogram_quantile(0.95, 
  rate(compra_agil_db_query_duration_seconds_bucket[5m])
)

# Queries por segundo
rate(compra_agil_db_query_duration_seconds_count[1m])
```

---

## Próximos Pasos

1. **Alertas**: Configurar alertas cuando circuit breaker se abre
2. **Auto-scaling**: Ajustar pool size basado en carga
3. **Distributed tracing**: Integrar OpenTelemetry
4. **Retry policies**: Implementar backoff exponencial
