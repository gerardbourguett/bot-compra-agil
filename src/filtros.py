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
    """
    if isinstance(palabras_clave, str):
        palabras = [p.strip().lower() for p in palabras_clave.split(',')]
    else:
        palabras = [p.lower() for p in palabras_clave]
    
    conn = db_ext.get_connection()
    cursor = conn.cursor()
    
    # Definir placeholder según DB
    placeholder = '%s' if db_ext.USE_POSTGRES else '?'
    like_op = 'ILIKE' if db_ext.USE_POSTGRES else 'LIKE' # Postgres es case-sensitive con LIKE, usar ILIKE
    
    # Construir query con OR para cada palabra
    condiciones = []
    parametros = []
    
    for palabra in palabras:
        if db_ext.USE_POSTGRES:
            # Para Postgres usamos ILIKE para case-insensitive
            condiciones.append(f"(nombre {like_op} {placeholder} OR organismo {like_op} {placeholder})")
        else:
            # Para SQLite usamos LOWER()
            condiciones.append(f"(LOWER(nombre) LIKE {placeholder} OR LOWER(organismo) LIKE {placeholder})")
            
        parametros.extend([f"%{palabra}%", f"%{palabra}%"])
    
    query = f'''
        SELECT id, codigo, nombre, fecha_publicacion, fecha_cierre, organismo, 
               unidad, estado, monto_disponible, moneda, cantidad_proveedores_cotizando
        FROM licitaciones
        WHERE ({" OR ".join(condiciones)})
        AND id_estado = 2
        ORDER BY fecha_cierre ASC
        LIMIT {placeholder}
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
    """
    conn = db_ext.get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if db_ext.USE_POSTGRES else '?'
    
    # Calculamos fechas en Python para evitar problemas de zona horaria en BD
    ahora = datetime.now()
    fecha_limite = (ahora + timedelta(days=dias)).strftime("%Y-%m-%d 23:59")
    fecha_actual = ahora.strftime("%Y-%m-%d %H:%M")
    
    query = f'''
        SELECT id, codigo, nombre, fecha_publicacion, fecha_cierre, organismo,
               unidad, estado, monto_disponible, moneda, cantidad_proveedores_cotizando
        FROM licitaciones
        WHERE id_estado = 2
        AND fecha_cierre <= {placeholder}
        AND fecha_cierre >= {placeholder}
        ORDER BY fecha_cierre ASC
        LIMIT {placeholder}
    '''
    
    cursor.execute(query, (fecha_limite, fecha_actual, limite))
    
    resultados = cursor.fetchall()
    conn.close()
    
    return [dict(zip(['id', 'codigo', 'nombre', 'fecha_publicacion', 'fecha_cierre',
                      'organismo', 'unidad', 'estado', 'monto_disponible', 'moneda',
                      'cantidad_proveedores_cotizando'], row)) for row in resultados]


def buscar_por_monto(monto_min=None, monto_max=None, limite=20):
    """
    Busca licitaciones por rango de monto.
    """
    conn = db_ext.get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if db_ext.USE_POSTGRES else '?'
    
    condiciones = ["id_estado = 2"]
    parametros = []
    
    if monto_min is not None:
        condiciones.append(f"monto_disponible >= {placeholder}")
        parametros.append(monto_min)
    
    if monto_max is not None:
        condiciones.append(f"monto_disponible <= {placeholder}")
        parametros.append(monto_max)
    
    query = f'''
        SELECT id, codigo, nombre, fecha_publicacion, fecha_cierre, organismo,
               unidad, estado, monto_disponible, moneda, cantidad_proveedores_cotizando
        FROM licitaciones
        WHERE {" AND ".join(condiciones)}
        ORDER BY monto_disponible ASC
        LIMIT {placeholder}
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


import unicodedata

def normalizar_texto(texto):
    """Elimina acentos y convierte a minúsculas."""
    if not texto:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto))
                  if unicodedata.category(c) != 'Mn').lower()

def calcular_score_compatibilidad_simple(licitacion, perfil):
    """
    Calcula un score simple de compatibilidad (0-100) mejorado.
    """
    score = 0
    
    # 1. Obtener y normalizar palabras clave del perfil
    palabras_perfil = set()
    if perfil.get('palabras_clave'):
        palabras_perfil.update([normalizar_texto(p).strip() for p in perfil['palabras_clave'].split(',')])
    if perfil.get('productos_servicios'):
        palabras_perfil.update([normalizar_texto(p).strip() for p in perfil['productos_servicios'].split(',')])
    
    # Filtrar palabras vacías
    palabras_perfil = {p for p in palabras_perfil if p and len(p) > 2}
    
    if not palabras_perfil:
        return 0
        
    # 2. Normalizar texto de la licitación
    nombre_lic = normalizar_texto(licitacion.get('nombre', ''))
    organismo_lic = normalizar_texto(licitacion.get('organismo', ''))
    texto_completo = f"{nombre_lic} {organismo_lic}"
    
    # 3. Calcular coincidencias con peso
    coincidencias = 0
    palabras_encontradas = set()
    
    for palabra in palabras_perfil:
        # Coincidencia exacta de la palabra/frase
        if palabra in texto_completo:
            coincidencias += 1
            palabras_encontradas.add(palabra)
        else:
            # Coincidencia parcial (palabra dentro de otra, ej: "silla" en "sillas")
            # Solo si la palabra clave es simple (no frase)
            if " " not in palabra:
                for palabra_lic in texto_completo.split():
                    if palabra in palabra_lic:
                        coincidencias += 0.8  # Un poco menos de puntaje
                        palabras_encontradas.add(palabra)
                        break
    
    # 4. Calcular puntajes parciales
    
    # Puntaje Palabras (Base 100)
    score_palabras = 0
    if coincidencias > 0:
        score_palabras = 40 + (min(coincidencias, 4) * 15)  # 1->55, 2->70, 3->85, 4+->100
    
    # Puntaje Competencia (Base 100)
    score_competencia = 0
    competidores = licitacion.get('cantidad_proveedores_cotizando', 0)
    if competidores == 0:
        score_competencia = 100
    elif competidores <= 2:
        score_competencia = 80
    elif competidores <= 5:
        score_competencia = 50
    elif competidores <= 10:
        score_competencia = 20
        
    # Puntaje Monto (Base 100)
    score_monto = 0
    monto = licitacion.get('monto_disponible', 0)
    monto_min = perfil.get('monto_minimo_interes', 500000)
    monto_max = perfil.get('monto_maximo_capacidad', 5000000)
    
    if monto_min <= monto <= monto_max:
        score_monto = 100
    elif monto_min * 0.8 <= monto <= monto_max * 1.2:
        score_monto = 50
        
    # 5. Aplicar Pesos del Perfil
    # 1=Bajo(0.5), 2=Medio(1.0), 3=Alto(1.5)
    mapa_pesos = {1: 0.5, 2: 1.0, 3: 1.5}
    
    p_palabras = mapa_pesos.get(perfil.get('peso_palabras', 2), 1.0)
    p_competencia = mapa_pesos.get(perfil.get('peso_competencia', 2), 1.0)
    p_monto = mapa_pesos.get(perfil.get('peso_monto', 2), 1.0)
    
    # Calcular promedio ponderado
    suma_pesos = p_palabras + p_competencia + p_monto
    score_final = (score_palabras * p_palabras + 
                   score_competencia * p_competencia + 
                   score_monto * p_monto) / suma_pesos
    
    return min(100, int(score_final))


    return min(100, int(score_final))


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


def buscar_oportunidades_baja_competencia(perfil, dias=3, max_competencia=2, limite=10):
    """
    Busca licitaciones compatibles que cierran pronto y tienen poca competencia.
    """
    # 1. Buscar licitaciones compatibles con el perfil
    candidatas = buscar_compatibles_con_perfil(perfil, limite=limite*3)
    
    oportunidades = []
    ahora = datetime.now()
    limite_fecha = ahora + timedelta(days=dias)
    
    for lic in candidatas:
        # Filtro 1: Baja competencia
        competencia = lic.get('cantidad_proveedores_cotizando', 0)
        if competencia > max_competencia:
            continue
            
        # Filtro 2: Cierra pronto (pero no ha cerrado aún)
        try:
            # Intentar parsear fecha cierre (formato esperado: YYYY-MM-DD HH:MM:SS o similar)
            # La BD puede tener formatos variados, intentamos ser flexibles o asumir string ISO
            fecha_cierre_str = lic.get('fecha_cierre', '')
            # Asumimos que fecha_cierre_str viene en formato ISO o compatible para comparación de strings
            # Si es string YYYY-MM-DD HH:MM, la comparación léxica funciona
            
            # Comparación simple de strings ISO (funciona si el formato es consistente)
            fecha_actual_str = ahora.strftime("%Y-%m-%d %H:%M")
            fecha_limite_str = limite_fecha.strftime("%Y-%m-%d %H:%M")
            
            if fecha_actual_str <= fecha_cierre_str <= fecha_limite_str:
                oportunidades.append(lic)
                
        except Exception:
            continue
            
    return oportunidades[:limite]


if __name__ == "__main__":
    # Pruebas
    print("Probando filtros...")
    
    # Buscar urgentes
    urgentes = buscar_urgentes(dias=3, limite=5)
    print(f"\nLicitaciones urgentes (proximos 3 dias): {len(urgentes)}")
    
    # Buscar por monto
    por_monto = buscar_por_monto(monto_min=500000, monto_max=2000000, limite=5)
    print(f"Licitaciones entre $500k y $2M: {len(por_monto)}")
    
    # Buscar servicios
    servicios = buscar_por_tipo_producto('servicios', limite=5)
    print(f"Licitaciones de servicios: {len(servicios)}")
