"""
Módulo de filtros y búsquedas inteligentes para licitaciones.
Incluye filtrado por tipo de producto/servicio y ranking por compatibilidad.
"""
import sqlite3
from datetime import datetime, timedelta
import database_extended as db_ext

DB_NAME = 'compra_agil.db'


def buscar_por_palabras_clave(palabras_clave, limite=20):
    """
    Busca licitaciones que coincidan con palabras clave específicas.
    
    Args:
        palabras_clave: String con palabras separadas por comas o lista
        limite: Número máximo de resultados
    
    Returns:
        Lista de licitaciones que coinciden
    """
    if isinstance(palabras_clave, str):
        palabras = [p.strip().lower() for p in palabras_clave.split(',')]
    else:
        palabras = [p.lower() for p in palabras_clave]
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Construir query con OR para cada palabra
    condiciones = []
    parametros = []
    
    for palabra in palabras:
        condiciones.append("(LOWER(nombre) LIKE ? OR LOWER(organismo) LIKE ?)")
        parametros.extend([f"%{palabra}%", f"%{palabra}%"])
    
    query = f'''
        SELECT id, codigo, nombre, fecha_publicacion, fecha_cierre, organismo, 
               unidad, estado, monto_disponible, moneda, cantidad_proveedores_cotizando
        FROM licitaciones
        WHERE ({" OR ".join(condiciones)})
        AND id_estado = 2
        ORDER BY fecha_cierre ASC
        LIMIT ?
    '''
    
    parametros.append(limite)
    
    cursor.execute(query, parametros)
    resultados = cursor.fetchall()
    conn.close()
    
    return [dict(zip(['id', 'codigo', 'nombre', 'fecha_publicacion', 'fecha_cierre', 
                      'organismo', 'unidad', 'estado', 'monto_disponible', 'moneda',
                      'cantidad_proveedores_cotizando'], row)) for row in resultados]


def buscar_por_tipo_producto(tipo, limite=20):
    """
    Busca licitaciones por tipo de producto/servicio.
    
    Args:
        tipo: 'productos' o 'servicios' o palabras específicas
        limite: Número máximo de resultados
    """
    # Palabras clave asociadas a productos
    palabras_productos = ['compra', 'adquisición', 'suministro', 'equipamiento', 
                         'mobiliario', 'materiales', 'insumos', 'artículos']
    
    # Palabras clave asociadas a servicios
    palabras_servicios = ['servicio', 'mantención', 'reparación', 'instalación',
                         'capacitación', 'asesoría', 'consultoría', 'arriendo']
    
    if tipo.lower() in ['producto', 'productos', 'bienes']:
        palabras = palabras_productos
    elif tipo.lower() in ['servicio', 'servicios']:
        palabras = palabras_servicios
    else:
        # Buscar por palabra específica
        return buscar_por_palabras_clave(tipo, limite)
    
    return buscar_por_palabras_clave(','.join(palabras), limite)


def buscar_urgentes(dias=3, limite=20):
    """
    Busca licitaciones que cierran pronto.
    
    Args:
        dias: Número de días hacia adelante
        limite: Número máximo de resultados
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    fecha_limite = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")
    
    cursor.execute('''
        SELECT id, codigo, nombre, fecha_publicacion, fecha_cierre, organismo,
               unidad, estado, monto_disponible, moneda, cantidad_proveedores_cotizando
        FROM licitaciones
        WHERE id_estado = 2
        AND fecha_cierre <= ?
        AND fecha_cierre >= datetime('now')
        ORDER BY fecha_cierre ASC
        LIMIT ?
    ''', (fecha_limite, limite))
    
    resultados = cursor.fetchall()
    conn.close()
    
    return [dict(zip(['id', 'codigo', 'nombre', 'fecha_publicacion', 'fecha_cierre',
                      'organismo', 'unidad', 'estado', 'monto_disponible', 'moneda',
                      'cantidad_proveedores_cotizando'], row)) for row in resultados]


def buscar_por_monto(monto_min=None, monto_max=None, limite=20):
    """
    Busca licitaciones por rango de monto.
    
    Args:
        monto_min: Monto mínimo en CLP
        monto_max: Monto máximo en CLP
        limite: Número máximo de resultados
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    condiciones = ["id_estado = 2"]
    parametros = []
    
    if monto_min is not None:
        condiciones.append("monto_disponible >= ?")
        parametros.append(monto_min)
    
    if monto_max is not None:
        condiciones.append("monto_disponible <= ?")
        parametros.append(monto_max)
    
    query = f'''
        SELECT id, codigo, nombre, fecha_publicacion, fecha_cierre, organismo,
               unidad, estado, monto_disponible, moneda, cantidad_proveedores_cotizando
        FROM licitaciones
        WHERE {" AND ".join(condiciones)}
        ORDER BY monto_disponible ASC
        LIMIT ?
    '''
    
    parametros.append(limite)
    
    cursor.execute(query, parametros)
    resultados = cursor.fetchall()
    conn.close()
    
    return [dict(zip(['id', 'codigo', 'nombre', 'fecha_publicacion', 'fecha_cierre',
                      'organismo', 'unidad', 'estado', 'monto_disponible', 'moneda',
                      'cantidad_proveedores_cotizando'], row)) for row in resultados]


def buscar_compatibles_con_perfil(perfil, limite=10):
    """
    Busca licitaciones compatibles con el perfil de la empresa.
    
    Args:
        perfil: Dict con el perfil de la empresa
        limite: Número máximo de resultados
    
    Returns:
        Lista de licitaciones ordenadas por relevancia
    """
    # Obtener palabras clave del perfil
    palabras_clave = perfil.get('palabras_clave', '')
    productos_servicios = perfil.get('productos_servicios', '')
    
    # Combinar palabras clave
    todas_palabras = f"{palabras_clave},{productos_servicios}"
    
    # Buscar licitaciones
    licitaciones = buscar_por_palabras_clave(todas_palabras, limite * 2)
    
    # Filtrar por capacidad de entrega si está definida
    capacidad_dias = perfil.get('capacidad_entrega_dias')
    if capacidad_dias:
        # Aquí podríamos filtrar por plazo de entrega si tuviéramos ese dato
        # Por ahora solo retornamos las licitaciones encontradas
        pass
    
    return licitaciones[:limite]


def calcular_score_compatibilidad_simple(licitacion, perfil):
    """
    Calcula un score simple de compatibilidad (0-100) sin IA.
    Basado en coincidencia de palabras clave.
    
    Args:
        licitacion: Dict con datos de la licitación
        perfil: Dict con perfil de la empresa
    
    Returns:
        int: Score de 0 a 100
    """
    score = 0
    
    # Palabras clave del perfil
    palabras_perfil = set()
    if perfil.get('palabras_clave'):
        palabras_perfil.update([p.strip().lower() for p in perfil['palabras_clave'].split(',')])
    if perfil.get('productos_servicios'):
        palabras_perfil.update([p.strip().lower() for p in perfil['productos_servicios'].split(',')])
    
    # Texto de la licitación
    texto_licitacion = f"{licitacion.get('nombre', '')} {licitacion.get('organismo', '')}".lower()
    
    # Contar coincidencias
    coincidencias = sum(1 for palabra in palabras_perfil if palabra in texto_licitacion)
    
    if palabras_perfil:
        score = min(100, int((coincidencias / len(palabras_perfil)) * 100))
    
    # Bonus por baja competencia
    competidores = licitacion.get('cantidad_proveedores_cotizando', 0)
    if competidores == 0:
        score += 10
    elif competidores <= 2:
        score += 5
    
    # Bonus por monto razonable (no muy alto ni muy bajo)
    monto = licitacion.get('monto_disponible', 0)
    if 500000 <= monto <= 5000000:  # Rango ideal para PYMEs
        score += 10
    
    return min(100, score)


def obtener_estadisticas_busqueda(palabras_clave):
    """
    Obtiene estadísticas sobre licitaciones que coinciden con palabras clave.
    
    Returns:
        dict con estadísticas
    """
    licitaciones = buscar_por_palabras_clave(palabras_clave, limite=1000)
    
    if not licitaciones:
        return {
            'total': 0,
            'monto_promedio': 0,
            'competencia_promedio': 0
        }
    
    total = len(licitaciones)
    monto_total = sum(l.get('monto_disponible', 0) for l in licitaciones)
    competencia_total = sum(l.get('cantidad_proveedores_cotizando', 0) for l in licitaciones)
    
    return {
        'total': total,
        'monto_promedio': int(monto_total / total) if total > 0 else 0,
        'competencia_promedio': round(competencia_total / total, 1) if total > 0 else 0,
        'monto_minimo': min(l.get('monto_disponible', 0) for l in licitaciones),
        'monto_maximo': max(l.get('monto_disponible', 0) for l in licitaciones)
    }


if __name__ == "__main__":
    # Pruebas
    print("Probando filtros...")
    
    # Buscar urgentes
    urgentes = buscar_urgentes(dias=3, limite=5)
    print(f"\n✅ Licitaciones urgentes (próximos 3 días): {len(urgentes)}")
    
    # Buscar por monto
    por_monto = buscar_por_monto(monto_min=500000, monto_max=2000000, limite=5)
    print(f"✅ Licitaciones entre $500k y $2M: {len(por_monto)}")
    
    # Buscar servicios
    servicios = buscar_por_tipo_producto('servicios', limite=5)
    print(f"✅ Licitaciones de servicios: {len(servicios)}")
