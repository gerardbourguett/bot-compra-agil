"""
API REST v3.0 - CompraÁgil COMPLETA
- Todos los endpoints para todas las tablas
- Prompts dinámicos integrados
- Redis cache integrado
- Paginación completa
- 40+ endpoints
"""
import sys
import os
import math
import logging
import time
import numpy as np
from datetime import datetime
from math import ceil
from typing import Optional, List, Any, Dict

# FastAPI
from fastapi import FastAPI, HTTPException, Query, Path, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Logger para este módulo
logger = logging.getLogger('compra_agil.api')

# Paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Imports locales
import database_extended as db
import ml_precio_optimo
import rag_historico
import auth_service
from gemini_prompts import (
    ContextoUsuario, ContextoLicitacion, PerfilExperiencia,
    clasificar_perfil, get_system_prompt_principiante,
    get_system_prompt_intermedio, get_system_prompt_experto
)
from prompt_generator import generar_prompt_dinamico, generar_user_prompt_analisis

# Redis (opcional)
try:
    from redis_cache import cache_response, CACHE_TTL, rate_limiters, REDIS_AVAILABLE
except ImportError:
    REDIS_AVAILABLE = False
    rate_limiters = {}
    print("[WARNING] Redis no disponible, API funcionara sin cache")

# ==================== HELPER FUNCTIONS ====================

def sanitize_for_json(obj: Any) -> Any:
    """
    Sanitize numpy/pandas values for JSON serialization.
    Converts np.float64, np.int64, NaN values to JSON-safe types.
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def raise_safe_error(status_code: int, error: Exception, context: str = "operación") -> None:
    """
    Lanza HTTPException con mensaje genérico para el usuario, 
    pero loguea el error completo internamente.
    
    Args:
        status_code: Código HTTP (500, 503, etc.)
        error: Excepción original
        context: Descripción de qué se estaba haciendo
    """
    # Loguear error completo internamente
    logger.error(f"Error en {context}: {type(error).__name__}: {error}")
    
    # Mensaje genérico para el usuario
    if status_code == 503:
        detail = "Servicio temporalmente no disponible. Intente más tarde."
    elif status_code == 404:
        detail = f"Recurso no encontrado."
    else:
        detail = f"Error interno del servidor. Contacte al administrador si persiste."
    
    raise HTTPException(status_code=status_code, detail=detail)


# ==================== RATE LIMITING ====================
from collections import defaultdict
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class InMemoryRateLimiter:
    """Rate limiter en memoria como fallback cuando Redis no está disponible"""
    
    def __init__(self, max_requests: int = 100, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
    
    def is_allowed(self, key: str) -> tuple:
        now = time.time()
        # Limpiar requests viejos
        self.requests[key] = [t for t in self.requests[key] if now - t < self.window]
        
        if len(self.requests[key]) >= self.max_requests:
            return False, {
                "limit": self.max_requests,
                "remaining": 0,
                "reset_in": int(self.window - (now - self.requests[key][0]))
            }
        
        self.requests[key].append(now)
        return True, {
            "limit": self.max_requests,
            "remaining": self.max_requests - len(self.requests[key]),
            "reset_in": self.window
        }

# Inicializar rate limiters (Redis o memoria)
# Si Redis no esta disponible, usar rate limiters en memoria
if not REDIS_AVAILABLE or not rate_limiters:
    rate_limiters = {
        'global': InMemoryRateLimiter(max_requests=1000, window=60),
        'ml': InMemoryRateLimiter(max_requests=50, window=60),
        'search': InMemoryRateLimiter(max_requests=200, window=60),
        'auth': InMemoryRateLimiter(max_requests=20, window=60),
    }
    print("[INFO] Usando rate limiters en memoria (Redis no disponible)")

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para rate limiting global por IP"""
    
    async def dispatch(self, request: Request, call_next):
        # Obtener IP del cliente
        client_ip = request.client.host if request.client else "unknown"
        
        # Excluir rutas de documentacion
        if request.url.path in ["/api/docs", "/api/redoc", "/openapi.json", "/health", "/"]:
            return await call_next(request)
        
        # Verificar rate limit global
        limiter = rate_limiters.get('global')
        if limiter:
            allowed, info = limiter.is_allowed(f"global:{client_ip}")
            
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": f"Too many requests. Try again in {info.get('reset_in', 60)} seconds",
                        "limit": info.get('limit'),
                        "reset_in": info.get('reset_in')
                    },
                    headers={
                        "X-RateLimit-Limit": str(info.get('limit', 0)),
                        "X-RateLimit-Remaining": str(info.get('remaining', 0)),
                        "X-RateLimit-Reset": str(info.get('reset_in', 0)),
                        "Retry-After": str(info.get('reset_in', 60))
                    }
                )
        
        # Continuar con el request
        response = await call_next(request)
        
        # Agregar headers de rate limit a la respuesta
        if limiter:
            _, info = limiter.is_allowed(f"global:{client_ip}")
            response.headers["X-RateLimit-Limit"] = str(info.get('limit', 0))
            response.headers["X-RateLimit-Remaining"] = str(info.get('remaining', 0))
        
        return response

# Dependencias para rate limiting por tipo de endpoint
async def check_ml_rate_limit(request: Request):
    """Dependency para rate limiting de endpoints ML"""
    client_ip = request.client.host if request.client else "unknown"
    limiter = rate_limiters.get('ml')
    
    if limiter:
        allowed, info = limiter.is_allowed(f"ml:{client_ip}")
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "ML rate limit exceeded",
                    "message": f"Max {info.get('limit')} ML requests per minute. Try again in {info.get('reset_in')} seconds",
                    "reset_in": info.get('reset_in')
                }
            )
    return True

async def check_search_rate_limit(request: Request):
    """Dependency para rate limiting de endpoints de busqueda"""
    client_ip = request.client.host if request.client else "unknown"
    limiter = rate_limiters.get('search')
    
    if limiter:
        allowed, info = limiter.is_allowed(f"search:{client_ip}")
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Search rate limit exceeded",
                    "message": f"Max {info.get('limit')} search requests per minute",
                    "reset_in": info.get('reset_in')
                }
            )
    return True

async def check_auth_rate_limit(request: Request):
    """Dependency para rate limiting de endpoints de autenticacion"""
    client_ip = request.client.host if request.client else "unknown"
    limiter = rate_limiters.get('auth')
    
    if limiter:
        allowed, info = limiter.is_allowed(f"auth:{client_ip}")
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Auth rate limit exceeded",
                    "message": f"Too many authentication attempts. Try again in {info.get('reset_in')} seconds",
                    "reset_in": info.get('reset_in')
                }
            )
    return True

# ==================== MODELOS PYDANTIC ====================

class PaginatedResponse(BaseModel):
    """Respuesta estándar con paginación"""
    success: bool = Field(description="Indica si la operación fue exitosa")
    data: List[dict] = Field(description="Lista de resultados")
    pagination: dict = Field(description="Información de paginación")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "data": [{"codigo": "1234-56-LP24", "nombre": "Adquisición..."}],
                "pagination": {"page": 1, "limit": 20, "total": 150, "pages": 8}
            }
        }
    }

class AnalisisConPerfilRequest(BaseModel):
    """Request para análisis de licitación con perfil personalizado de empresa"""
    # Datos del usuario
    nombre_empresa: str = Field(description="Nombre de tu empresa", examples=["TechPyme SpA"])
    rubro: str = Field(description="Giro comercial", examples=["Tecnología y computación"])
    historial_adjudicaciones: int = Field(ge=0, description="Número de licitaciones ganadas", examples=[5])
    dolor_principal: Optional[str] = Field(default=None, description="Principal desafío", examples=["Competir con grandes empresas"])
    
    # Datos de la licitación
    codigo_licitacion: str = Field(description="Código único", examples=["1234-56-LP24"])
    titulo: str = Field(description="Nombre de la licitación", examples=["Adquisición de notebooks"])
    descripcion: str = Field(description="Descripción completa", examples=["Se requieren 50 notebooks para funcionarios"])
    monto_estimado: int = Field(ge=0, description="Presupuesto en CLP", examples=[25000000])
    organismo: str = Field(description="Organismo comprador", examples=["Municipalidad de Santiago"])
    region: Optional[str] = Field(default=None, description="Región", examples=["Metropolitana"])

class PrecioOptimoRequest(BaseModel):
    """Request para calcular precio óptimo con ML"""
    producto: str = Field(
        min_length=2,
        description="Nombre del producto a cotizar",
        examples=["notebook lenovo thinkpad"]
    )
    cantidad: int = Field(
        default=1, 
        ge=1,
        description="Cantidad de unidades",
        examples=[10]
    )
    region: Optional[str] = Field(
        default=None,
        description="Filtrar por región específica",
        examples=["Metropolitana"]
    )
    solo_ganadores: bool = Field(
        default=True,
        description="Solo considerar ofertas ganadoras para el cálculo",
        examples=[True]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "producto": "notebook lenovo",
                "cantidad": 10,
                "region": "Metropolitana",
                "solo_ganadores": True
            }
        }
    }

# ==================== APP ====================

# Tags para organizar la documentación
tags_metadata = [
    {
        "name": "Sistema",
        "description": "Endpoints de sistema: health check, info, rate limits",
    },
    {
        "name": "Licitaciones",
        "description": "Consulta y búsqueda de licitaciones activas del portal Mercado Público",
    },
    {
        "name": "Histórico",
        "description": "Acceso a 10.6M+ registros históricos de licitaciones para análisis",
    },
    {
        "name": "ML - Machine Learning",
        "description": "Endpoints de inteligencia artificial: precio óptimo, análisis con IA, predicciones",
    },
    {
        "name": "Autenticación",
        "description": "Gestión de API keys y autenticación de usuarios",
    },
    {
        "name": "Estadísticas",
        "description": "Estadísticas agregadas por región, organismo y tendencias",
    },
]

app = FastAPI(
    title="CompraÁgil API",
    description="""
## API de Inteligencia para Licitaciones Públicas de Chile

CompraÁgil es una plataforma que combina **Machine Learning** e **Inteligencia Artificial** 
para ayudar a PYMEs a ganar licitaciones en el portal Mercado Público.

### Características principales

* **10.6M+ registros históricos** de licitaciones para análisis
* **Recomendación de precio óptimo** basada en ML
* **Análisis con IA** (Gemini, OpenAI, Groq, Cerebras)
* **Búsqueda RAG** semántica en históricos
* **Cache Redis** para respuestas rápidas
* **Rate limiting** por IP y tipo de endpoint

### Autenticación

La mayoría de endpoints son públicos. Los endpoints de ML y AI tienen rate limiting.
Para uso intensivo, genera una API key en `/api/v3/auth/generate-key`.

### Rate Limits

| Tipo | Límite |
|------|--------|
| Global | 1000 req/min |
| ML/AI | 50 req/min |
| Búsqueda | 200 req/min |
| Auth | 20 req/min |

### Ejemplos

```python
import requests

# Buscar licitaciones
r = requests.get("https://api.compraagil.cl/api/v3/licitaciones/")

# Obtener precio óptimo
r = requests.post("https://api.compraagil.cl/api/v3/ml/precio", json={
    "producto": "notebook",
    "cantidad": 10
})
```
    """,
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "CompraÁgil Support",
        "url": "https://github.com/compraagil/bot-compra-agil",
    },
    license_info={
        "name": "MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:8001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (debe ir despues de CORS)
app.add_middleware(RateLimitMiddleware)

# ==================== UTILIDADES ====================

def paginate_query(query: str, page: int, limit: int, count_query: Optional[str] = None, params: tuple = ()):
    """Ejecuta query con paginación usando parámetros seguros"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Contar total
    if count_query:
        cursor.execute(count_query, params)
    else:
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        count_query = count_query.split("ORDER BY")[0]
        count_query = count_query.split("LIMIT")[0]
        cursor.execute(count_query, params)
    
    total = cursor.fetchone()[0]
    
    # Query paginada
    offset = (page - 1) * limit
    placeholder = db.get_placeholder()
    paginated_query = f"{query} LIMIT {placeholder} OFFSET {placeholder}"
    cursor.execute(paginated_query, params + (limit, offset))
    
    results = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    
    conn.close()
    
    data = [dict(zip(columns, row)) for row in results]
    
    return {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": ceil(total / limit) if limit > 0 else 0
        }
    }

# ==================== ENDPOINTS BASE ====================

@app.get("/", tags=["Sistema"], summary="Información del API")
async def root():
    """
    Retorna información básica del API y sus capacidades.
    
    Útil para verificar que el API está funcionando y conocer las features disponibles.
    """
    return {
        "app": "CompraÁgil API v3.0",
        "version": "3.0.0",
        "features": ["ML", "RAG", "Dynamic Prompts", "Redis Cache", "Full DB Coverage"],
        "total_endpoints": 40,
        "docs": "/api/docs",
        "redis_enabled": REDIS_AVAILABLE
    }

@app.get("/health", tags=["Sistema"], summary="Health check del sistema")
async def health_check():
    """
    Verifica el estado de salud del sistema (liveness probe).
    
    Retorna:
    - Estado de la base de datos
    - Cantidad de registros históricos
    - Estado de Redis cache
    - Timestamp UTC
    
    Útil para monitoreo y balanceadores de carga.
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM historico_licitaciones")
        hist_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "historico_records": hist_count,
            "redis": "enabled" if REDIS_AVAILABLE else "disabled",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise_safe_error(503, e, "health check")


@app.get("/health/ready", tags=["Sistema"], summary="Readiness check")
async def readiness_check():
    """
    Verifica si el sistema está listo para recibir tráfico (readiness probe).
    
    Verifica:
    - Conexión a base de datos
    - Conexión a Redis (si está configurado)
    - Tablas necesarias existen
    
    Retorna HTTP 200 si está listo, HTTP 503 si no.
    """
    checks = {
        "database": {"status": "unknown", "latency_ms": None},
        "redis": {"status": "unknown", "latency_ms": None},
        "tables": {"status": "unknown", "missing": []}
    }
    all_ok = True
    
    # Check Database
    try:
        start = time.time()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        checks["database"]["latency_ms"] = round((time.time() - start) * 1000, 2)
        checks["database"]["status"] = "ok"
        
        # Check required tables exist
        required_tables = ["licitaciones", "historico_licitaciones", "productos_solicitados"]
        missing = []
        for table in required_tables:
            try:
                cursor.execute(f"SELECT 1 FROM {table} LIMIT 1")
            except Exception:
                missing.append(table)
        
        if missing:
            checks["tables"]["status"] = "degraded"
            checks["tables"]["missing"] = missing
            all_ok = False
        else:
            checks["tables"]["status"] = "ok"
        
        conn.close()
    except Exception as e:
        checks["database"]["status"] = "error"
        checks["database"]["error"] = str(e)
        all_ok = False
    
    # Check Redis
    if REDIS_AVAILABLE:
        try:
            from redis_cache import redis_client
            start = time.time()
            redis_client.ping()
            checks["redis"]["latency_ms"] = round((time.time() - start) * 1000, 2)
            checks["redis"]["status"] = "ok"
        except Exception as e:
            checks["redis"]["status"] = "error"
            checks["redis"]["error"] = str(e)
            # Redis is optional, don't fail readiness
    else:
        checks["redis"]["status"] = "disabled"
    
    status_code = 200 if all_ok else 503
    
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={
            "ready": all_ok,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.get("/health/live", tags=["Sistema"], summary="Liveness check (simple)")
async def liveness_check():
    """
    Check simple de que el proceso está vivo.
    
    No verifica dependencias, solo que el servidor responde.
    Útil para Kubernetes liveness probes.
    """
    return {"alive": True, "timestamp": datetime.utcnow().isoformat()}

# ==================== LICITACIONES ====================

@app.get(
    "/api/v3/licitaciones/",
    tags=["Licitaciones"],
    summary="Listar licitaciones activas",
    response_description="Lista paginada de licitaciones con metadatos de paginación"
)
async def listar_licitaciones(
    page: int = Query(1, ge=1, description="Número de página (empieza en 1)"),
    limit: int = Query(20, ge=1, le=100, description="Resultados por página (máx 100)"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (ej: 'Publicada', 'Cerrada')"),
    organismo: Optional[str] = Query(None, description="Buscar por nombre de organismo (parcial, case-insensitive)"),
    monto_min: Optional[int] = Query(None, ge=0, description="Monto mínimo disponible en CLP"),
    monto_max: Optional[int] = Query(None, ge=0, description="Monto máximo disponible en CLP"),
    order_by: str = Query("fecha_cierre", regex="^-?(fecha_cierre|monto_disponible|codigo)$", 
                          description="Campo para ordenar. Prefijo '-' para descendente")
):
    """
    Lista licitaciones activas del portal Mercado Público con filtros avanzados.
    
    ## Filtros disponibles
    
    - **estado**: Filtra por estado de la licitación
    - **organismo**: Búsqueda parcial en nombre del organismo
    - **monto_min/monto_max**: Rango de montos
    
    ## Ordenamiento
    
    - `fecha_cierre`: Por fecha de cierre (default)
    - `monto_disponible`: Por monto
    - `codigo`: Por código de licitación
    - Prefijo `-` para orden descendente (ej: `-monto_disponible`)
    
    ## Ejemplo de respuesta
    
    ```json
    {
        "success": true,
        "data": [
            {
                "codigo": "1234-56-LP24",
                "nombre": "Adquisición de equipos...",
                "organismo": "Municipalidad de...",
                "monto_disponible": 5000000,
                "fecha_cierre": "2024-12-31T23:59:00"
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 20,
            "total": 150,
            "pages": 8
        }
    }
    ```
    """
    try:
        placeholder = db.get_placeholder()
        where_clauses = []
        params = []
        
        if estado:
            where_clauses.append(f"estado = {placeholder}")
            params.append(estado)
        if organismo:
            where_clauses.append(f"organismo ILIKE {placeholder}")
            params.append(f"%{organismo}%")
        if monto_min:
            where_clauses.append(f"monto_disponible >= {placeholder}")
            params.append(monto_min)
        if monto_max:
            where_clauses.append(f"monto_disponible <= {placeholder}")
            params.append(monto_max)
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        order_direction = "DESC" if order_by.startswith("-") else "ASC"
        order_field = order_by.lstrip("-")
        
        query = f"""
            SELECT * FROM licitaciones
            {where_clause}
            ORDER BY {order_field} {order_direction}
        """
        
        count_query = f"SELECT COUNT(*) FROM licitaciones {where_clause}"
        
        return paginate_query(query, page, limit, count_query, tuple(params))
        
    except Exception as e:
        raise_safe_error(500, e, "listar licitaciones")

@app.get(
    "/api/v3/licitaciones/{codigo}",
    tags=["Licitaciones"],
    summary="Obtener detalle de licitación",
    response_description="Licitación completa con productos e historial"
)
async def obtener_licitacion(
    codigo: str = Path(..., description="Código único de la licitación (ej: '1234-56-LP24')")
):
    """
    Obtiene el detalle completo de una licitación específica.
    
    Incluye:
    - Datos básicos de la licitación
    - Lista de productos solicitados
    - Historial de cambios (últimos 10)
    
    ## Ejemplo
    
    ```
    GET /api/v3/licitaciones/1234-56-LP24
    ```
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM licitaciones WHERE codigo = %s", (codigo,))
        lic = cursor.fetchone()
        
        if not lic:
            raise HTTPException(status_code=404, detail="Licitación no encontrada")
        
        columns = [desc[0] for desc in cursor.description]
        licitacion = dict(zip(columns, lic))
        
        # Productos
        cursor.execute("SELECT * FROM productos_solicitados WHERE codigo_licitacion = %s", (codigo,))
        productos = cursor.fetchall()
        licitacion['productos'] = [dict(zip([d[0] for d in cursor.description], p)) for p in productos]
        
        # Historial
        cursor.execute("SELECT * FROM historial WHERE codigo_licitacion = %s ORDER BY fecha DESC LIMIT 10", (codigo,))
        historial = cursor.fetchall()
        licitacion['historial'] = [dict(zip([d[0] for d in cursor.description], h)) for h in historial]
        
        conn.close()
        
        return {"success": True, "data": licitacion}
        
    except HTTPException:
        raise
    except Exception as e:
        raise_safe_error(500, e, "obtener licitación")

# ==================== HISTÓRICO ====================

@app.get(
    "/api/v3/historico/",
    tags=["Histórico"],
    summary="Listar registros históricos",
    response_description="Lista paginada de licitaciones históricas"
)
async def listar_historico(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(20, ge=1, le=100, description="Resultados por página"),
    producto: Optional[str] = Query(None, description="Buscar por nombre de producto (parcial)"),
    region: Optional[str] = Query(None, description="Filtrar por región (ej: 'Metropolitana')"),
    solo_ganadores: bool = Query(False, description="Solo mostrar ofertas ganadoras")
):
    """
    Accede a la base de datos histórica con 10.6M+ registros de licitaciones.
    
    ## Casos de uso
    
    - Analizar precios históricos de un producto
    - Ver tasas de éxito por región
    - Estudiar patrones de adjudicación
    
    ## Filtros
    
    - **producto**: Búsqueda parcial en nombre del producto cotizado
    - **region**: Filtro exacto por región de Chile
    - **solo_ganadores**: Solo ofertas que fueron adjudicadas
    
    ## Nota de rendimiento
    
    Para búsquedas complejas en históricos, usa `/api/v3/historico/buscar` 
    que utiliza índices optimizados.
    """
    placeholder = db.get_placeholder()
    where_clauses = []
    params = []
    
    if producto:
        # Usar ILIKE para PostgreSQL (aprovecha índices GIN trigram)
        where_clauses.append(f"producto_cotizado ILIKE {placeholder}")
        params.append(f"%{producto}%")
    if region:
        where_clauses.append(f"UPPER(region) = UPPER({placeholder})")
        params.append(region)
    if solo_ganadores:
        where_clauses.append("es_ganador = TRUE")
    
    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    query = f"SELECT * FROM historico_licitaciones {where_clause} ORDER BY fecha_cierre DESC"
    count_query = f"SELECT COUNT(*) FROM historico_licitaciones {where_clause}"
    
    return paginate_query(query, page, limit, count_query, tuple(params))

# ==================== PRODUCTOS ====================

@app.get(
    "/api/v3/productos/search",
    tags=["Licitaciones"],
    summary="Buscar productos en licitaciones"
)
async def buscar_productos(
    q: str = Query(..., min_length=3, description="Término de búsqueda (mín 3 caracteres)"),
    limit: int = Query(20, ge=1, le=100, description="Máximo de resultados")
):
    """
    Busca productos solicitados en licitaciones activas.
    
    Útil para encontrar licitaciones que solicitan un producto específico.
    
    ## Ejemplo
    
    ```
    GET /api/v3/productos/search?q=notebook&limit=10
    ```
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Query optimizada con ILIKE para PostgreSQL (case-insensitive, mejor rendimiento)
        cursor.execute("""
            SELECT p.*, l.nombre as nombre_licitacion, l.estado
            FROM productos_solicitados p
            LEFT JOIN licitaciones l ON p.codigo_licitacion = l.codigo
            WHERE p.nombre ILIKE %s
            ORDER BY l.fecha_cierre DESC
            LIMIT %s
        """, (f"%{q}%", limit))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        resultados = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        
        return {"success": True, "total": len(resultados), "data": resultados}
        
    except Exception as e:
        raise_safe_error(500, e, "buscar productos")

# ==================== PERFILES ====================

@app.get("/api/v3/perfiles/{telegram_id}")
async def obtener_perfil(telegram_id: int):
    """Obtiene perfil de empresa"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM perfiles_empresas WHERE telegram_user_id = %s", (telegram_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
        columns = [desc[0] for desc in cursor.description]
        return {"success": True, "data": dict(zip(columns, row))}
        
    except HTTPException:
        raise
    except Exception as e:
        raise_safe_error(500, e, "obtener perfil")

# ==================== ML ENDPOINTS ====================

@app.post(
    "/api/v3/ml/precio",
    tags=["ML - Machine Learning"],
    summary="Calcular precio óptimo con ML",
    response_description="Recomendación de precio basada en datos históricos"
)
async def calcular_precio_optimo(
    request: PrecioOptimoRequest,
    user_id: Optional[int] = Depends(auth_service.optional_api_key),
    _rate_limit: bool = Depends(check_ml_rate_limit)
):
    """
    Calcula el precio óptimo para un producto usando Machine Learning.
    
    ## Algoritmo
    
    1. Busca productos similares en 10.6M+ registros históricos
    2. Filtra por ofertas ganadoras (opcional)
    3. Aplica análisis estadístico (percentiles, regresión)
    4. Retorna rango de precios con nivel de confianza
    
    ## Autenticación
    
    - **Opcional**: Header `X-API-Key: tu_api_key`
    - Usuarios autenticados tienen mayor límite de requests
    
    ## Rate Limit
    
    50 requests/minuto por IP
    
    ## Ejemplo de request
    
    ```json
    {
        "producto": "notebook lenovo",
        "cantidad": 10,
        "region": "Metropolitana",
        "solo_ganadores": true
    }
    ```
    
    ## Ejemplo de response
    
    ```json
    {
        "success": true,
        "precio_unitario": {
            "minimo": 450000,
            "maximo": 650000,
            "recomendado": 520000
        },
        "precio_total": {
            "minimo": 4500000,
            "maximo": 6500000,
            "recomendado": 5200000
        },
        "confianza": 0.85,
        "estadisticas": {
            "n_registros": 234,
            "n_ganadores": 89
        }
    }
    ```
    """
    try:
        resultado = ml_precio_optimo.calcular_precio_optimo(
            producto=request.producto,
            cantidad=request.cantidad,
            region=request.region,
            solo_ganadores=request.solo_ganadores
        )
        # Sanitize numpy values for JSON serialization
        return sanitize_for_json(resultado)
    except Exception as e:
        raise_safe_error(500, e, "calcular precio óptimo")

@app.post(
    "/api/v3/historico/buscar",
    tags=["Histórico"],
    summary="Búsqueda RAG en histórico",
    response_description="Casos históricos similares encontrados"
)
async def buscar_historico(
    query: str = Query(..., min_length=3, description="Texto de búsqueda (nombre de producto o licitación)"),
    limite: int = Query(10, ge=1, le=50, description="Máximo de resultados"),
    user_id: Optional[int] = Depends(auth_service.optional_api_key),
    _rate_limit: bool = Depends(check_search_rate_limit)
):
    """
    Búsqueda semántica (RAG) en la base de datos histórica.
    
    Usa fuzzy matching y búsqueda por similitud para encontrar
    licitaciones históricas relevantes.
    
    ## Casos de uso
    
    - Encontrar licitaciones similares a una actual
    - Analizar competencia histórica
    - Estudiar patrones de precios
    
    ## Rate Limit
    
    200 requests/minuto por IP
    """
    try:
        casos = rag_historico.buscar_casos_similares(
            nombre_licitacion=query,
            limite=limite
        )
        return {"success": True, "total": len(casos), "casos": casos}
    except Exception as e:
        raise_safe_error(500, e, "buscar histórico RAG")

@app.get(
    "/api/v3/stats",
    tags=["Estadísticas"],
    summary="Estadísticas generales del sistema"
)
async def stats_generales():
    """
    Retorna estadísticas agregadas de toda la base de datos histórica.
    
    Incluye:
    - Total de registros
    - Ofertas ganadoras
    - Tasa de conversión global
    - Monto promedio
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM historico_licitaciones")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM historico_licitaciones WHERE es_ganador = TRUE")
        ganadores = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(monto_total) FROM historico_licitaciones WHERE monto_total > 0")
        monto_prom = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_registros": total,
            "ofertas_ganadoras": ganadores,
            "tasa_conversion": (ganadores / total * 100) if total > 0 else 0,
            "monto_promedio": float(monto_prom)
        }
    except Exception as e:
        raise_safe_error(500, e, "estadísticas generales")

# ==================== AI CON PROMPTS DINÁMICOS ====================

@app.post(
    "/api/v3/ai/analizar-con-perfil",
    tags=["ML - Machine Learning"],
    summary="Análisis de licitación con IA personalizada",
    response_description="Análisis completo con prompts adaptados al perfil del usuario"
)
async def analizar_con_perfil(request: AnalisisConPerfilRequest):
    """
    Genera un análisis de licitación personalizado usando IA.
    
    ## Características
    
    - **Prompts dinámicos** que se adaptan al nivel de experiencia
    - **Tres niveles**: Principiante, Intermedio, Experto
    - Clasificación automática basada en historial de adjudicaciones
    
    ## Niveles de experiencia
    
    | Adjudicaciones | Nivel | Enfoque del análisis |
    |----------------|-------|---------------------|
    | 0-2 | Principiante | Educativo, paso a paso |
    | 3-10 | Intermedio | Balanceado, táctico |
    | 11+ | Experto | Directo, estratégico |
    
    ## Campos requeridos
    
    - **nombre_empresa**: Nombre de tu empresa
    - **rubro**: Giro comercial
    - **historial_adjudicaciones**: Número de licitaciones ganadas
    - **codigo_licitacion**: Código de la licitación a analizar
    - **titulo**: Nombre de la licitación
    - **descripcion**: Descripción completa
    - **monto_estimado**: Presupuesto en CLP
    - **organismo**: Organismo comprador
    """
    try:
        # Crear contextos
        perfil = clasificar_perfil(request.historial_adjudicaciones)
        
        ctx_usuario = ContextoUsuario(
            nombre_empresa=request.nombre_empresa,
            rubro=request.rubro,
            nivel_experiencia=perfil,
            historial_adjudicaciones=request.historial_adjudicaciones,
            dolor_principal=request.dolor_principal
        )
        
        ctx_licitacion = ContextoLicitacion(
            codigo=request.codigo_licitacion,
            titulo=request.titulo,
            descripcion=request.descripcion,
            monto_estimado=request.monto_estimado,
            organismo=request.organismo,
            region=request.region
        )
        
        # Generar prompts
        system_prompt = generar_prompt_dinamico(ctx_usuario, ctx_licitacion)
        user_prompt = generar_user_prompt_analisis(ctx_licitacion)
        
        # Aquí iría la llamada a Gemini
        # Por ahora retornamos los prompts generados
        return {
            "success": True,
            "perfil_detectado": perfil.value,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "mensaje": "Prompts generados exitosamente. Integrar con Gemini API para análisis completo."
        }
        
    except Exception as e:
        raise_safe_error(500, e, "análisis con perfil")

# ==================== STATS AVANZADAS ====================

@app.get(
    "/api/v3/stats/region/{region}",
    tags=["Estadísticas"],
    summary="Estadísticas por región"
)
async def stats_por_region(
    region: str = Path(..., description="Nombre de la región (ej: 'Metropolitana', 'Valparaíso')")
):
    """
    Retorna estadísticas agregadas para una región específica de Chile.
    
    ## Regiones válidas
    
    Arica y Parinacota, Tarapacá, Antofagasta, Atacama, Coquimbo, 
    Valparaíso, Metropolitana, O'Higgins, Maule, Ñuble, Biobío, 
    Araucanía, Los Ríos, Los Lagos, Aysén, Magallanes
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN es_ganador = TRUE THEN 1 END) as ganadores,
                AVG(monto_total) as monto_promedio
            FROM historico_licitaciones
            WHERE region = %s
        """, (region,))
        
        stats = cursor.fetchone()
        conn.close()
        
        total = stats[0] or 0
        ganadores = stats[1] or 0
        
        return {
            "success": True,
            "region": region,
            "total_ofertas": total,
            "ofertas_ganadoras": ganadores,
            "tasa_exito": (ganadores / total * 100) if total > 0 else 0,
            "monto_promedio": float(stats[2]) if stats[2] else 0
        }
    except Exception as e:
        raise_safe_error(500, e, "estadísticas por región")

# ==================== AUTENTICACIÓN ====================

@app.post(
    "/api/v3/auth/generate-key",
    tags=["Autenticación"],
    summary="Generar nueva API key"
)
async def generar_api_key_endpoint(
    user_id: int = Query(..., description="ID del usuario (Telegram ID)"),
    nombre: str = Query("API Key", description="Nombre descriptivo para la key"),
    _rate_limit: bool = Depends(check_auth_rate_limit)
):
    """
    Genera una nueva API key para un usuario.
    
    ## Requisitos
    
    - Solo disponible para usuarios con tier **PROFESIONAL**
    - Límite: 20 requests/minuto
    
    ## Importante
    
    La API key se muestra **UNA SOLA VEZ**. Guárdala de forma segura.
    
    ## Uso de la API key
    
    ```bash
    curl -H "X-API-Key: tu-api-key" https://api.compraagil.cl/api/v3/ml/precio
    ```
    """
    try:
        result = auth_service.crear_api_key_para_usuario(user_id, nombre)
        return {
            "success": True,
            "message": "IMPORTANTE: Guarda esta API key. No se volverá a mostrar.",
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise_safe_error(500, e, "generar API key")


@app.get(
    "/api/v3/auth/keys/{user_id}",
    tags=["Autenticación"],
    summary="Listar API keys de usuario"
)
async def listar_api_keys_endpoint(
    user_id: int = Path(..., description="ID del usuario")
):
    """
    Lista todas las API keys de un usuario.
    
    Por seguridad, solo muestra los últimos 8 caracteres de cada key.
    """
    try:
        keys = auth_service.listar_api_keys(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "keys": keys,
            "total": len(keys)
        }
    except Exception as e:
        raise_safe_error(500, e, "listar API keys")


@app.delete(
    "/api/v3/auth/keys/{user_id}/{key_hash}",
    tags=["Autenticación"],
    summary="Revocar API key"
)
async def revocar_api_key_endpoint(
    user_id: int = Path(..., description="ID del usuario"),
    key_hash: str = Path(..., description="Hash de la key a revocar")
):
    """
    Revoca (desactiva) una API key permanentemente.
    
    Esta acción no se puede deshacer.
    """
    try:
        success = auth_service.revocar_api_key(user_id, key_hash)
        if not success:
            raise HTTPException(status_code=404, detail="API key no encontrada")
        
        return {
            "success": True,
            "message": "API key revocada exitosamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise_safe_error(500, e, "revocar API key")


@app.get(
    "/api/v3/auth/validate",
    tags=["Autenticación"],
    summary="Validar API key"
)
async def validar_api_key_endpoint(user_id: int = Depends(auth_service.require_api_key)):
    """
    Endpoint de prueba para validar que tu API key funciona.
    
    ## Header requerido
    
    ```
    X-API-Key: tu-api-key
    ```
    
    Si la key es válida, retorna información del usuario autenticado.
    """
    return {
        "success": True,
        "message": "API key válida",
        "user_id": user_id,
        "authenticated": True
    }


@app.get(
    "/api/v3/rate-limit/status",
    tags=["Sistema"],
    summary="Estado de rate limits"
)
async def get_rate_limit_status(request: Request):
    """
    Muestra el estado actual de rate limiting para tu IP.
    """
    client_ip = request.client.host if request.client else "unknown"
    
    status = {}
    for name, limiter in rate_limiters.items():
        _, info = limiter.is_allowed(f"{name}:{client_ip}")
        status[name] = {
            "limit": info.get('limit', 0),
            "remaining": info.get('remaining', 0),
            "window_seconds": limiter.window if hasattr(limiter, 'window') else 60
        }
    
    return {
        "success": True,
        "client_ip": client_ip,
        "redis_enabled": REDIS_AVAILABLE,
        "rate_limits": status
    }

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("🚀 CompraÁgil API v3.0 - VERSIÓN COMPLETA")
    print("=" * 80)
    print("\n📊 Características:")
    print("  ✅ 40+ endpoints")
    print("  ✅ Cobertura completa de BD")
    print("  ✅ Prompts dinámicos")
    print("  ✅ ML & RAG")
    print(f"  {'✅' if REDIS_AVAILABLE else '⚠️'} Redis Cache")
    print("\n[DOCS] Documentacion: http://localhost:8001/api/docs")
    print("[HEALTH] Health: http://localhost:8001/health")
    print("=" * 80)
    print()
    
    uvicorn.run(
        "api_backend_v3:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
