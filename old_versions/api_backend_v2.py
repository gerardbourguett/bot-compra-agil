"""
API REST EXPANDIDA - CompraÁgil
Versión 2.0 con soporte completo para todas las tablas
Incluye paginación, filtros avanzados y optimizaciones
"""
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import sys
import os
from math import ceil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import ml_precio_optimo
import rag_historico
import database_extended as db

# ==================== MODELOS PYDANTIC ====================

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Número de página")
    limit: int = Field(20, ge=1, le=100, description="Resultados por página")

class PaginatedResponse(BaseModel):
    success: bool
    data: List[Any]
    pagination: Dict[str, int]

class Licitacion(BaseModel):
    codigo: str
    nombre: Optional[str]
    fecha_publicacion: Optional[str]
    fecha_cierre: Optional[str]
    organismo: Optional[str]
    estado: Optional[str]
    monto_disponible: Optional[int]
    cantidad_proveedores_cotizando: Optional[int]

class ProductoSolicitado(BaseModel):
    id: int
    codigo_licitacion: str
    nombre: str
    cantidad: float
    unidad_medida: Optional[str]

class HistorialItem(BaseModel):
    id: int
    codigo_licitacion: str
    fecha: str
    accion: str
    usuario: Optional[str]

class GuardarLicitacionRequest(BaseModel):
    telegram_user_id: int
    codigo_licitacion: str
    notas: Optional[str] = None

class FeedbackRequest(BaseModel):
    telegram_user_id: int
    codigo_licitacion: str
    feedback: int  # 1 = útil, 0 = no útil

class PerfilEmpresaUpdate(BaseModel):
    nombre_empresa: Optional[str] = None
    tipo_negocio: Optional[str] = None
    productos_servicios: Optional[str] = None
    palabras_clave: Optional[str] = None
    capacidad_entrega_dias: Optional[int] = None
    ubicacion: Optional[str] = None

# ==================== APP CONFIGURATION ====================

app = FastAPI(
    title="CompraÁgil API v2.0",
    description="API REST expandida con soporte completo para BD",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://tu-dominio.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== UTILITY FUNCTIONS ====================

def paginate_query(query: str, page: int, limit: int, count_query: str = None):
    """Ejecuta query con paginación"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Contar total
    if count_query:
        cursor.execute(count_query)
    else:
        # Extraer COUNT de la query original
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        count_query = count_query.split("ORDER BY")[0]  # Remover ORDER BY
        count_query = count_query.split("LIMIT")[0]     # Remover LIMIT
        cursor.execute(count_query)
    
    total = cursor.fetchone()[0]
    
    # Query paginada
    offset = (page - 1) * limit
    paginated_query = f"{query} LIMIT {limit} OFFSET {offset}"
    cursor.execute(paginated_query)
    
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

@app.get("/")
async def root():
    """Info de la API"""
    return {
        "app": "CompraÁgil API v2.0",
        "version": "2.0.0",
        "features": ["ML", "RAG", "Pagination", "Full DB Coverage"],
        "docs": "/api/docs",
        "endpoints_count": 30
    }

@app.get("/health")
async def health_check():
    """Health check"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        
        # Verificar tabla crítica
        cursor.execute("SELECT COUNT(*) FROM historico_licitaciones")
        hist_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "historico_records": hist_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB error: {str(e)}")

# ==================== LICITACIONES ENDPOINTS ====================

@app.get("/api/v1/licitaciones/")
async def listar_licitaciones(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    estado: Optional[str] = None,
    organismo: Optional[str] = None,
    monto_min: Optional[int] = None,
    monto_max: Optional[int] = None,
    order_by: str = Query("fecha_cierre", regex="^-?(fecha_cierre|monto_disponible|codigo)$")
):
    """
    Lista licitaciones con filtros y paginación
    
    - **page**: Número de página
    - **limit**: Resultados por página (máx 100)
    - **estado**: Filtrar por estado
    - **organismo**: Filtrar por organismo
    - **monto_min**: Monto mínimo
    - **monto_max**: Monto máximo
    - **order_by**: Campo para ordenar (agregar - para DESC)
    """
    try:
        # Construir query
        where_clauses = []
        if estado:
            where_clauses.append(f"estado = '{estado}'")
        if organismo:
            where_clauses.append(f"organismo ILIKE '%{organismo}%'")
        if monto_min:
            where_clauses.append(f"monto_disponible >= {monto_min}")
        if monto_max:
            where_clauses.append(f"monto_disponible <= {monto_max}")
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Ordenamiento
        order_direction = "DESC" if order_by.startswith("-") else "ASC"
        order_field = order_by.lstrip("-")
        
        query = f"""
            SELECT * FROM licitaciones
            {where_clause}
            ORDER BY {order_field} {order_direction}
        """
        
        count_query = f"SELECT COUNT(*) FROM licitaciones {where_clause}"
        
        return paginate_query(query, page, limit, count_query)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/licitaciones/{codigo}")
async def obtener_licitacion(codigo: str = Path(..., description="Código de licitación")):
    """
    Obtiene detalle completo de una licitación
    Incluye productos solicitados e historial
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Licitación básica
        cursor.execute("SELECT * FROM licitaciones WHERE codigo = %s", (codigo,))
        lic = cursor.fetchone()
        
        if not lic:
            raise HTTPException(status_code=404, detail="Licitación no encontrada")
        
        columns = [desc[0] for desc in cursor.description]
        licitacion = dict(zip(columns, lic))
        
        # Detalle extendido
        cursor.execute("SELECT * FROM licitaciones_detalle WHERE codigo = %s", (codigo,))
        det = cursor.fetchone()
        if det:
            det_columns = [desc[0] for desc in cursor.description]
            licitacion['detalle'] = dict(zip(det_columns, det))
        
        # Productos solicitados
        cursor.execute("""
            SELECT id, nombre, cantidad, unidad_medida, descripcion
            FROM productos_solicitados
            WHERE codigo_licitacion = %s
        """, (codigo,))
        productos = cursor.fetchall()
        licitacion['productos'] = [
            {
                'id': p[0],
                'nombre': p[1],
                'cantidad': p[2],
                'unidad_medida': p[3],
                'descripcion': p[4]
            }
            for p in productos
        ]
        
        # Historial
        cursor.execute("""
            SELECT id, fecha, accion, usuario
            FROM historial
            WHERE codigo_licitacion = %s
            ORDER BY fecha DESC
            LIMIT 10
        """, (codigo,))
        historial = cursor.fetchall()
        licitacion['historial'] = [
            {
                'id': h[0],
                'fecha': h[1],
                'accion': h[2],
                'usuario': h[3]
            }
            for h in historial
        ]
        
        conn.close()
        
        return {"success": True, "data": licitacion}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PRODUCTOS ENDPOINTS ====================

@app.get("/api/v1/productos/search")
async def buscar_productos(
    q: str = Query(..., min_length=3, description="Término de búsqueda"),
    limit: int = Query(20, ge=1, le=100)
):
    """Búsqueda de productos solicitados"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.id,
                p.codigo_licitacion,
                p.nombre,
                p.cantidad,
                p.unidad_medida,
                l.nombre as nombre_licitacion,
                l.estado,
                l.monto_disponible
            FROM productos_solicitados p
            LEFT JOIN licitaciones l ON p.codigo_licitacion = l.codigo
            WHERE LOWER(p.nombre) LIKE LOWER(%s)
            OR LOWER(p.descripcion) LIKE LOWER(%s)
            ORDER BY l.fecha_cierre DESC
            LIMIT %s
        """, (f"%{q}%", f"%{q}%", limit))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        resultados = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        
        return {
            "success": True,
            "query": q,
            "total": len(resultados),
            "data": resultados
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/productos/licitacion/{codigo}")
async def productos_licitacion(codigo: str):
    """Productos de una licitación específica"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nombre, cantidad, unidad_medida, descripcion
            FROM productos_solicitados
            WHERE codigo_licitacion = %s
            ORDER BY id
        """, (codigo,))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        productos = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        
        return {
            "success": True,
            "codigo_licitacion": codigo,
            "total": len(productos),
            "data": productos
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== HISTORIAL ENDPOINTS ====================

@app.get("/api/v1/historial/{codigo}")
async def historial_licitacion(
    codigo: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Timeline de actividad de una licitación"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, fecha, accion, usuario
            FROM historial
            WHERE codigo_licitacion = %s
            ORDER BY fecha DESC
            LIMIT %s
        """, (codigo, limit))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        historial = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        
        return {
            "success": True,
            "codigo": codigo,
            "total": len(historial),
            "data": historial
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/historial/user/{telegram_id}")
async def historial_usuario(
    telegram_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Historial de interacciones de un usuario"""
    query = f"""
        SELECT id, accion, codigo_licitacion, fecha
        FROM historial_interacciones
        WHERE telegram_user_id = {telegram_id}
        ORDER BY fecha DESC
    """
    
    count_query = f"""
        SELECT COUNT(*)
        FROM historial_interacciones
        WHERE telegram_user_id = {telegram_id}
    """
    
    return paginate_query(query, page, limit, count_query)

# ==================== GUARDADAS ENDPOINTS ====================

@app.get("/api/v1/guardadas/user/{telegram_id}")
async def licitaciones_guardadas(
    telegram_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Licitaciones guardadas de un usuario"""
    query = f"""
        SELECT 
            g.id,
            g.codigo_licitacion,
            g.fecha_guardado,
            g.notas,
            l.nombre,
            l.estado,
            l.monto_disponible,
            l.fecha_cierre
        FROM licitaciones_guardadas g
        LEFT JOIN licitaciones l ON g.codigo_licitacion = l.codigo
        WHERE g.telegram_user_id = {telegram_id}
        ORDER BY g.fecha_guardado DESC
    """
    
    count_query = f"""
        SELECT COUNT(*)
        FROM licitaciones_guardadas
        WHERE telegram_user_id = {telegram_id}
    """
    
    return paginate_query(query, page, limit, count_query)

@app.post("/api/v1/guardadas")
async def guardar_licitacion(request: GuardarLicitacionRequest):
    """Guardar una licitación"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar si ya está guardada
        cursor.execute("""
            SELECT id FROM licitaciones_guardadas
            WHERE telegram_user_id = %s AND codigo_licitacion = %s
        """, (request.telegram_user_id, request.codigo_licitacion))
        
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Licitación ya guardada")
        
        # Insertar
        cursor.execute("""
            INSERT INTO licitaciones_guardadas 
            (telegram_user_id, codigo_licitacion, fecha_guardado, notas)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            request.telegram_user_id,
            request.codigo_licitacion,
            datetime.now().isoformat(),
            request.notas
        ))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "id": new_id,
            "message": "Licitación guardada exitosamente"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/guardadas/{id}")
async def eliminar_guardada(id: int):
    """Eliminar licitación guardada"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM licitaciones_guardadas WHERE id = %s RETURNING id", (id,))
        deleted = cursor.fetchone()
        
        if not deleted:
            conn.close()
            raise HTTPException(status_code=404, detail="No encontrada")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Eliminada exitosamente"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ANÁLISIS ENDPOINTS ====================

@app.get("/api/v1/analisis/cache/{codigo}")
async def obtener_analisis_cache(codigo: str):
    """Obtiene análisis en caché"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT analisis_json, fecha_analisis, version_prompt
            FROM analisis_cache
            WHERE codigo_licitacion = %s
        """, (codigo,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="No hay análisis en caché")
        
        import json
        return {
            "success": True,
            "codigo": codigo,
            "analisis": json.loads(row[0]) if row[0] else {},
            "fecha": row[1],
            "version": row[2]
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analisis/feedback")
async def registrar_feedback(request: FeedbackRequest):
    """Registra feedback de análisis"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO feedback_analisis 
            (telegram_user_id, codigo_licitacion, feedback, fecha)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            request.telegram_user_id,
            request.codigo_licitacion,
            request.feedback,
            datetime.now().isoformat()
        ))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "id": new_id,
            "message": "Feedback registrado"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PERFILES ENDPOINTS ====================

@app.get("/api/v1/perfiles/{telegram_id}")
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
        perfil = dict(zip(columns, row))
        
        return {"success": True, "data": perfil}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/perfiles/{telegram_id}")
async def actualizar_perfil(telegram_id: int, perfil: PerfilEmpresaUpdate):
    """Actualiza perfil de empresa"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Construir UPDATE dinámico
        updates = []
        values = []
        for field, value in perfil.dict(exclude_unset=True).items():
            if value is not None:
                updates.append(f"{field} = %s")
                values.append(value)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        values.append(telegram_id)
        
        cursor.execute(f"""
            UPDATE perfiles_empresas
            SET {', '.join(updates)}, fecha_actualizacion = %s
            WHERE telegram_user_id = %s
            RETURNING *
        """, values + [datetime.now().isoformat(), telegram_id])
        
        row = cursor.fetchone()
        conn.commit()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
        columns = [desc[0] for desc in cursor.description]
        perfil_actualizado = dict(zip(columns, row))
        
        return {"success": True, "data": perfil_actualizado}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== STATS AVANZADAS ====================

@app.get("/api/v1/stats/advanced/organismo/{nombre}")
async def stats_organismo(nombre: str):
    """Estadísticas de un organismo específico"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_licitaciones,
                AVG(monto_disponible) as monto_promedio,
                SUM(monto_disponible) as monto_total,
                COUNT(DISTINCT estado) as estados_unicos
            FROM licitaciones
            WHERE organismo ILIKE %s
        """, (f"%{nombre}%",))
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            "success": True,
            "organismo": nombre,
            "total_licitaciones": stats[0],
            "monto_promedio": float(stats[1]) if stats[1] else 0,
            "monto_total": stats[2] or 0,
            "estados_unicos": stats[3]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stats/advanced/region/{nombre}")
async def stats_region(nombre: str):
    """Estadísticas de una región"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN es_ganador = TRUE THEN 1 END) as ganadores,
                AVG(monto_total) as monto_promedio,
                SUM(monto_total) as monto_total
            FROM historico_licitaciones
            WHERE region = %s
        """, (nombre,))
        
        stats = cursor.fetchone()
        conn.close()
        
        total = stats[0] or 0
        ganadores = stats[1] or 0
        
        return {
            "success": True,
            "region": nombre,
            "total_ofertas": total,
            "ofertas_ganadoras": ganadores,
            "tasa_exito": (ganadores / total * 100) if total > 0 else 0,
            "monto_promedio": float(stats[2]) if stats[2] else 0,
            "monto_total": stats[3] or 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ML ENDPOINTS ====================

# Re-definir endpoints ML aquí para evitar circular import

from pydantic import BaseModel as PydanticBaseModel

class PrecioOptimoRequest(PydanticBaseModel):
    producto: str
    cantidad: int = 1
    region: Optional[str] = None
    solo_ganadores: bool = True

@app.post("/api/v1/ml/precio")
async def calcular_precio_optimo_endpoint(request: PrecioOptimoRequest):
    """Calcula precio óptimo basado en datos históricos"""
    try:
        resultado = ml_precio_optimo.calcular_precio_optimo(
            producto=request.producto,
            cantidad=request.cantidad,
            region=request.region,
            solo_ganadores=request.solo_ganadores
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class HistoricoSearchRequest(PydanticBaseModel):
    query: str
    limite: int = 10
    umbral_similitud: int = 50

@app.post("/api/v1/historico/buscar")
async def buscar_historico_endpoint(request: HistoricoSearchRequest):
    """Busca casos similares en el histórico"""
    try:
        casos = rag_historico.buscar_casos_similares(
            nombre_licitacion=request.query,
            limite=request.limite,
            umbral_similitud=request.umbral_similitud
        )
        
        return {
            "success": True,
            "total": len(casos),
            "casos": casos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stats")
async def stats_generales_endpoint():
    """Estadísticas generales del histórico"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM historico_licitaciones")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM historico_licitaciones WHERE es_ganador = TRUE")
        ganadores = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(monto_total) FROM historico_licitaciones WHERE monto_total > 0")
        monto_prom = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT region, COUNT(*) as total
            FROM historico_licitaciones
            WHERE region IS NOT NULL
            GROUP BY region
            ORDER BY total DESC
            LIMIT 5
        """)
        regiones = [{'region': r[0], 'total': r[1]} for r in cursor.fetchall()]
        
        conn.close()
        
        return {
            "total_registros": total,
            "ofertas_ganadoras": ganadores,
            "tasa_conversion": (ganadores / total * 100) if total > 0 else 0,
            "monto_promedio": float(monto_prom),
            "top_regiones": regiones
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ml/competencia")
async def analizar_competencia_endpoint(producto: str = Query(...)):
    """Analiza la competencia para un producto"""
    try:
        resultado = ml_precio_optimo.analizar_competencia_precios(producto)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Iniciando CompraÁgil API v2.0 EXPANDIDA...")
    print("📚 Documentación: http://localhost:8000/api/docs")
    print("🔧 Health check: http://localhost:8000/health")
    print("✨ Nuevas features: Paginación, CRUD completo, 30+ endpoints")
    print()
    
    uvicorn.run(
        "api_backend_v2:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
