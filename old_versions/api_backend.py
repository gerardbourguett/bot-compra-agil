"""
API REST Backend con FastAPI
Endpoints para consumir desde frontend Next.js
"""
from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
import os

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import ml_precio_optimo
import rag_historico
import database_extended as db

# Configuración de la app
app = FastAPI(
    title="CompraÁgil API",
    description="API REST para sistema de análisis de licitaciones con ML/IA",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS para Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        "http://localhost:3001",
        "https://tu-dominio.com",  # Producción
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELOS PYDANTIC ====================

class PrecioOptimoRequest(BaseModel):
    producto: str = Field(..., description="Nombre del producto", example="laptop dell")
    cantidad: int = Field(1, ge=1, description="Cantidad solicitada", example=10)
    region: Optional[str] = Field(None, description="Región (opcional)", example="RM")
    solo_ganadores: bool = Field(True, description="Solo analizar ofertas ganadoras")

class PrecioOptimoResponse(BaseModel):
    success: bool
    precio_unitario: Optional[Dict[str, float]] = None
    precio_total: Optional[Dict[str, float]] = None
    estadisticas: Optional[Dict[str, Any]] = None
    confianza: Optional[float] = None
    recomendacion: Optional[str] = None
    error: Optional[str] = None

class HistoricoSearchRequest(BaseModel):
    query: str = Field(..., description="Búsqueda", example="laptop dell")
    limite: int = Field(10, ge=1, le=50, description="Máximo de resultados")
    umbral_similitud: int = Field(50, ge=0, le=100, description="Similitud mínima (%)")

class CasoHistorico(BaseModel):
    codigo: str
    nombre: str
    producto: str
    proveedor: str
    monto: int
    cantidad: int
    precio_unitario: int
    es_ganador: bool
    fecha_cierre: Optional[str]
    region: str
    similitud: float
    antiguedad_dias: Optional[int]

class HistoricoSearchResponse(BaseModel):
    success: bool
    total: int
    casos: List[CasoHistorico]

class AnalisisEnriquecidoRequest(BaseModel):
    nombre_licitacion: str = Field(..., example="Adquisición de computadores")
    monto_estimado: Optional[int] = Field(None, example=5000000)
    descripcion: Optional[str] = Field(None, example="Laptops para oficina")

class AnalisisEnriquecidoResponse(BaseModel):
    success: bool
    n_casos: int
    insights: Optional[str] = None
    contexto: Optional[str] = None
    recomendacion_precio: Optional[Dict[str, int]] = None
    error: Optional[str] = None

class StatsGeneralResponse(BaseModel):
    total_registros: int
    ofertas_ganadoras: int
    tasa_conversion: float
    monto_promedio: float
    top_regiones: List[Dict[str, Any]]

class StatsProductoRequest(BaseModel):
    producto: str = Field(..., example="laptop")
    limite: int = Field(1000, ge=100, le=5000)

class StatsProductoResponse(BaseModel):
    success: bool
    total_ofertas: int
    ofertas_ganadoras: int
    tasa_conversion: float
    precio_unitario: Dict[str, float]
    top_proveedores: List[Dict[str, Any]]
    error: Optional[str] = None

class CompetenciaResponse(BaseModel):
    success: bool
    total_competidores: int
    top_competidores: List[Dict[str, Any]]
    estadisticas_generales: Dict[str, float]
    error: Optional[str] = None

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Endpoint raíz - Info de la API"""
    return {
        "app": "CompraÁgil API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/api/docs",
        "endpoints": {
            "precio_optimo": "POST /api/v1/ml/precio",
            "historico": "POST /api/v1/historico/buscar",
            "analisis": "POST /api/v1/ml/analisis",
            "stats": "GET /api/v1/stats",
            "competencia": "POST /api/v1/ml/competencia"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Verificar conexión a BD
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )

# ==================== ML ENDPOINTS ====================

@app.post("/api/v1/ml/precio", response_model=PrecioOptimoResponse)
async def calcular_precio_optimo(request: PrecioOptimoRequest):
    """
    Calcula el precio óptimo basado en datos históricos.
    
    - **producto**: Nombre del producto a buscar
    - **cantidad**: Cantidad solicitada (default: 1)
    - **region**: Filtrar por región (opcional)
    - **solo_ganadores**: Solo analizar ofertas ganadoras (default: true)
    """
    try:
        resultado = ml_precio_optimo.calcular_precio_optimo(
            producto=request.producto,
            cantidad=request.cantidad,
            region=request.region,
            solo_ganadores=request.solo_ganadores
        )
        
        return PrecioOptimoResponse(**resultado)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular precio: {str(e)}"
        )

@app.post("/api/v1/ml/analisis", response_model=AnalisisEnriquecidoResponse)
async def analisis_enriquecido(request: AnalisisEnriquecidoRequest):
    """
    Genera análisis enriquecido con datos históricos (RAG).
    
    - **nombre_licitacion**: Nombre de la licitación
    - **monto_estimado**: Monto estimado (opcional)
    - **descripcion**: Descripción adicional (opcional)
    """
    try:
        datos = rag_historico.enriquecer_analisis_licitacion(
            nombre_licitacion=request.nombre_licitacion,
            monto_estimado=request.monto_estimado,
            descripcion=request.descripcion
        )
        
        if datos['tiene_datos']:
            return AnalisisEnriquecidoResponse(
                success=True,
                n_casos=datos['n_casos_encontrados'],
                insights=datos['insights'],
                contexto=datos['contexto_para_prompt'],
                recomendacion_precio=datos.get('recomendacion_precio')
            )
        else:
            return AnalisisEnriquecidoResponse(
                success=False,
                n_casos=0,
                error=datos['mensaje']
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en análisis: {str(e)}"
        )

@app.post("/api/v1/ml/competencia", response_model=CompetenciaResponse)
async def analizar_competencia(producto: str):
    """
    Analiza la competencia para un producto específico.
    
    - **producto**: Nombre del producto
    """
    try:
        resultado = ml_precio_optimo.analizar_competencia_precios(producto)
        
        if resultado['success']:
            # Formatear top competidores
            top_comp = []
            for nombre, datos in list(resultado['top_competidores'].items())[:10]:
                top_comp.append({
                    'nombre': nombre,
                    'ofertas': int(datos['monto_total_count']),
                    'tasa_exito': float(datos['tasa_exito']),
                    'precio_promedio': float(datos['precio_unitario_mean'])
                })
            
            return CompetenciaResponse(
                success=True,
                total_competidores=resultado['total_competidores'],
                top_competidores=top_comp,
                estadisticas_generales=resultado['estadisticas_generales']
            )
        else:
            return CompetenciaResponse(
                success=False,
                total_competidores=0,
                top_competidores=[],
                estadisticas_generales={},
                error=resultado.get('error')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en análisis de competencia: {str(e)}"
        )

# ==================== HISTÓRICO ENDPOINTS ====================

@app.post("/api/v1/historico/buscar", response_model=HistoricoSearchResponse)
async def buscar_historico(request: HistoricoSearchRequest):
    """
    Busca casos similares en el histórico.
    
    - **query**: Texto de búsqueda
    - **limite**: Máximo de resultados (1-50)
    - **umbral_similitud**: Similitud mínima en % (0-100)
    """
    try:
        casos = rag_historico.buscar_casos_similares(
            nombre_licitacion=request.query,
            limite=request.limite,
            umbral_similitud=request.umbral_similitud
        )
        
        casos_formateados = [CasoHistorico(**caso) for caso in casos]
        
        return HistoricoSearchResponse(
            success=True,
            total=len(casos_formateados),
            casos=casos_formateados
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en búsqueda histórica: {str(e)}"
        )

# ==================== STATS ENDPOINTS ====================

@app.get("/api/v1/stats", response_model=StatsGeneralResponse)
async def stats_generales():
    """
    Estadísticas generales del histórico.
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Total registros
        cursor.execute("SELECT COUNT(*) FROM historico_licitaciones")
        total = cursor.fetchone()[0]
        
        # Ganadores
        cursor.execute("SELECT COUNT(*) FROM historico_licitaciones WHERE es_ganador = TRUE")
        ganadores = cursor.fetchone()[0]
        
        # Monto promedio
        cursor.execute("SELECT AVG(monto_total) FROM historico_licitaciones WHERE monto_total > 0")
        monto_prom = cursor.fetchone()[0] or 0
        
        # Top regiones
        query_regiones = """
            SELECT region, COUNT(*) as total
            FROM historico_licitaciones
            WHERE region IS NOT NULL
            GROUP BY region
            ORDER BY total DESC
            LIMIT 5
        """
        cursor.execute(query_regiones)
        regiones = [{'region': r[0], 'total': r[1]} for r in cursor.fetchall()]
        
        conn.close()
        
        return StatsGeneralResponse(
            total_registros=total,
            ofertas_ganadoras=ganadores,
            tasa_conversion=(ganadores / total * 100) if total > 0 else 0,
            monto_promedio=float(monto_prom),
            top_regiones=regiones
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )

@app.post("/api/v1/stats/producto", response_model=StatsProductoResponse)
async def stats_producto(request: StatsProductoRequest):
    """
    Estadísticas de un producto específico.
    
    - **producto**: Nombre del producto
    - **limite**: Máximo de registros a analizar
    """
    try:
        df = ml_precio_optimo.buscar_productos_similares(
            producto=request.producto,
            limite=request.limite
        )
        
        if df.empty:
            return StatsProductoResponse(
                success=False,
                total_ofertas=0,
                ofertas_ganadoras=0,
                tasa_conversion=0,
                precio_unitario={},
                top_proveedores=[],
                error="No hay datos suficientes para este producto"
            )
        
        # Calcular estadísticas
        total = len(df)
        ganadores = len(df[df['es_ganador'] == True])
        
        # Top proveedores
        top_prov = df[df['es_ganador'] == True]['nombre_proveedor'].value_counts().head(5)
        proveedores = [
            {'nombre': prov, 'victorias': int(count)}
            for prov, count in top_prov.items()
        ]
        
        return StatsProductoResponse(
            success=True,
            total_ofertas=total,
            ofertas_ganadoras=ganadores,
            tasa_conversion=(ganadores / total * 100) if total > 0 else 0,
            precio_unitario={
                'minimo': float(df['precio_unitario'].min()),
                'promedio': float(df['precio_unitario'].mean()),
                'mediana': float(df['precio_unitario'].median()),
                'maximo': float(df['precio_unitario'].max())
            },
            top_proveedores=proveedores
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas de producto: {str(e)}"
        )

# ==================== ERROR HANDLERS ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)
        }
    )

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Iniciando CompraÁgil API...")
    print("📚 Documentación: http://localhost:8000/api/docs")
    print("🔧 Health check: http://localhost:8000/health")
    print()
    
    uvicorn.run(
        "api_backend:app",  # Usar string para reload
        host="0.0.0.0",
        port=8000,
        reload=True  # Hot reload en desarrollo
    )
