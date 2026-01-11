"""
Sistema RAG (Retrieval Augmented Generation)
Busca casos históricos similares para enriquecer análisis con IA
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import database_extended as db
from fuzzywuzzy import fuzz
import logging

logger = logging.getLogger(__name__)


def buscar_casos_similares(
    nombre_licitacion: str,
    monto_estimado: Optional[int] = None,
    limite: int = 10,
    umbral_similitud: int = 50
) -> List[Dict]:
    """
    Busca licitaciones históricas similares para enriquecer el contexto.
    
    Args:
        nombre_licitacion: Nombre/descripción de la licitación actual
        monto_estimado: Monto estimado de la licitación (opcional)
        limite: Número máximo de casos a retornar
        umbral_similitud: Umbral mínimo de similitud textual (0-100)
    
    Returns:
        Lista de diccionarios con casos similares rankeados
    """
    try:
        conn = db.get_connection()
        
        # Query para obtener datos históricos
        query = """
            SELECT 
                codigo_cotizacion,
                nombre_cotizacion,
                producto_cotizado,
                region,
                rut_proveedor,
                nombre_proveedor,
                monto_total,
                cantidad,
                detalle_oferta,
                es_ganador,
                fecha_cierre
            FROM historico_licitaciones
            WHERE nombre_cotizacion IS NOT NULL
            AND monto_total > 0
            ORDER BY fecha_cierre DESC
            LIMIT 1000
        """

        # Optimización PostgreSQL con pg_trgm
        if db.USE_POSTGRES:
            query = """
                SELECT
                    codigo_licitacion,
                    nombre_cotizacion,
                    producto_cotizado,
                    region,
                    rut_proveedor,
                    nombre_proveedor,
                    monto_total,
                    cantidad,
                    detalle_oferta,
                    es_ganador,
                    fecha_cierre,
                    GREATEST(
                        similarity(nombre_cotizacion, %s),
                        similarity(COALESCE(producto_cotizado, ''), %s)
                    ) as score_similitud
                FROM historico_licitaciones
                WHERE (nombre_cotizacion %% %s OR producto_cotizado %% %s)
                AND nombre_cotizacion IS NOT NULL
                AND monto_total > 0
                AND fecha_cierre >= CURRENT_DATE - INTERVAL '3 years'
                ORDER BY score_similitud DESC, fecha_cierre DESC
                LIMIT %s
            """
            params = (nombre_licitacion, nombre_licitacion, nombre_licitacion,
                     nombre_licitacion, limite * 3)
            df = pd.read_sql(query, conn, params=params)
        else:
            df = pd.read_sql(query, conn)

        conn.close()

        if df.empty:
            logger.warning("No se encontraron datos históricos")
            return []
        
        # Calcular similitud con fuzzy matching
        nombre_lower = nombre_licitacion.lower()
        df['similitud_nombre'] = df['nombre_cotizacion'].apply(
            lambda x: fuzz.token_set_ratio(nombre_lower, str(x).lower()) 
            if pd.notna(x) else 0
        )
        
        # También buscar similitud en producto
        df['similitud_producto'] = df['producto_cotizado'].apply(
            lambda x: fuzz.token_set_ratio(nombre_lower, str(x).lower())
            if pd.notna(x) else 0
        )
        
        # Score combinado (70% nombre, 30% producto)
        df['score_similitud'] = (
            df['similitud_nombre'] * 0.7 + 
            df['similitud_producto'] * 0.3
        )
        
        # Bonus por relevancia temporal (más reciente = mejor)
        df['fecha_cierre'] = pd.to_datetime(df['fecha_cierre'], errors='coerce')
        fecha_max = df['fecha_cierre'].max()
        df['antiguedad_dias'] = (fecha_max - df['fecha_cierre']).dt.days
        
        # Bonus: reducir score de casos muy antiguos
        df['bonus_temporal'] = np.where(
            df['antiguedad_dias'] <= 180, 10,  # Últimos 6 meses: +10 puntos
            np.where(df['antiguedad_dias'] <= 365, 5, 0)  # Último año: +5 puntos
        )
        
        df['score_final'] = df['score_similitud'] + df['bonus_temporal']
        
        # Filtrar por umbral y ordenar
        df_filtrado = df[df['score_similitud'] >= umbral_similitud].copy()
        df_filtrado = df_filtrado.nlargest(limite, 'score_final')
        
        # Si hay monto estimado, priorizar casos con monto similar
        if monto_estimado and not df_filtrado.empty:
            df_filtrado['diferencia_monto'] = abs(
                df_filtrado['monto_total'] - monto_estimado
            ) / monto_estimado
            # Reordenar dando peso a similitud de monto
            df_filtrado['score_ajustado'] = (
                df_filtrado['score_final'] * 0.7 +
                (1 - df_filtrado['diferencia_monto'].clip(0, 1)) * 30
            )
            df_filtrado = df_filtrado.nlargest(limite, 'score_ajustado')
        
        # Convertir a lista de diccionarios
        casos = []
        for _, row in df_filtrado.iterrows():
            casos.append({
                'codigo': row['codigo_cotizacion'],
                'nombre': row['nombre_cotizacion'],
                'producto': row['producto_cotizado'],
                'proveedor': row['nombre_proveedor'],
                'rut_proveedor': row['rut_proveedor'],
                'monto': int(row['monto_total']) if pd.notna(row['monto_total']) else 0,
                'cantidad': int(row['cantidad']) if pd.notna(row['cantidad']) else 0,
                'precio_unitario': int(row['monto_total'] / row['cantidad']) if row['cantidad'] > 0 else 0,
                'es_ganador': bool(row['es_ganador']),
                'fecha_cierre': row['fecha_cierre'].strftime('%Y-%m-%d') if pd.notna(row['fecha_cierre']) else None,
                'region': row['region'],
                'detalle': row['detalle_oferta'][:200] if pd.notna(row['detalle_oferta']) else '',
                'similitud': round(row['score_similitud'], 1),
                'antiguedad_dias': int(row['antiguedad_dias']) if pd.notna(row['antiguedad_dias']) else None
            })
        
        logger.info(f"Encontrados {len(casos)} casos similares para '{nombre_licitacion}'")
        return casos
        
    except Exception as e:
        logger.error(f"Error buscando casos similares: {e}", exc_info=True)
        return []


def construir_contexto_historico(casos: List[Dict], max_casos: int = 5) -> str:
    """
    Construye contexto textual enriquecido para el prompt de IA.
    
    Args:
        casos: Lista de casos similares
        max_casos: Máximo de casos a incluir en el contexto
    
    Returns:
        Texto formateado para incluir en el prompt
    """
    if not casos:
        return "No se encontraron casos históricos similares."
    
    # Limitar casos
    casos_top = casos[:max_casos]
    
    # Separar ganadores y perdedores
    ganadores = [c for c in casos_top if c['es_ganador']]
    perdedores = [c for c in casos_top if not c['es_ganador']]
    
    contexto = "📚 DATOS HISTÓRICOS DE LICITACIONES SIMILARES:\n\n"
    
    # Mostrar ganadores primero
    if ganadores:
        contexto += "✅ OFERTAS GANADORAS:\n"
        for i, caso in enumerate(ganadores, 1):
            meses_atras = caso['antiguedad_dias'] // 30 if caso['antiguedad_dias'] else 0
            contexto += f"""
{i}. {caso['nombre'][:80]}
   • Proveedor: {caso['proveedor']}
   • Monto Total: ${caso['monto']:,}
   • Precio Unitario: ${caso['precio_unitario']:,}
   • Región: {caso['region']}
   • Hace {meses_atras} meses
   • Similitud: {caso['similitud']}%
"""
    
    # Mostrar perdedores
    if perdedores:
        contexto += "\n❌ OFERTAS NO GANADORAS:\n"
        for i, caso in enumerate(perdedores[:3], 1):  # Máx 3 perdedores
            meses_atras = caso['antiguedad_dias'] // 30 if caso['antiguedad_dias'] else 0
            contexto += f"""
{i}. {caso['proveedor']}
   • Monto ofertado: ${caso['monto']:,}
   • Hace {meses_atras} meses
"""
    
    return contexto.strip()


def analizar_patrones_ganadores(casos: List[Dict]) -> Dict:
    """
    Analiza patrones en las ofertas ganadoras.
    
    Returns:
        Dict con insights sobre qué características tienen los ganadores
    """
    if not casos:
        return {'success': False}
    
    ganadores = [c for c in casos if c['es_ganador']]
    
    if not ganadores:
        return {
            'success': True,
            'n_ganadores': 0,
            'mensaje': 'No hay ofertas ganadoras en los casos similares'
        }
    
    # Calcular estadísticas
    montos_ganadores = [c['monto'] for c in ganadores if c['monto'] > 0]
    precios_unitarios = [c['precio_unitario'] for c in ganadores if c['precio_unitario'] > 0]
    
    # Proveedores que ganan frecuentemente
    proveedores = {}
    for caso in ganadores:
        prov = caso['proveedor']
        proveedores[prov] = proveedores.get(prov, 0) + 1
    
    proveedor_top = max(proveedores.items(), key=lambda x: x[1]) if proveedores else None
    
    # Regiones más exitosas
    regiones = {}
    for caso in ganadores:
        reg = caso['region']
        if reg:
            regiones[reg] = regiones.get(reg, 0) + 1
    
    return {
        'success': True,
        'n_ganadores': len(ganadores),
        'n_perdedores': len(casos) - len(ganadores),
        'tasa_conversion': len(ganadores) / len(casos) * 100,
        'estadisticas_precio': {
            'promedio': int(np.mean(montos_ganadores)) if montos_ganadores else 0,
            'mediana': int(np.median(montos_ganadores)) if montos_ganadores else 0,
            'minimo': int(min(montos_ganadores)) if montos_ganadores else 0,
            'maximo': int(max(montos_ganadores)) if montos_ganadores else 0,
        },
        'precio_unitario_promedio': int(np.mean(precios_unitarios)) if precios_unitarios else 0,
        'proveedor_mas_frecuente': proveedor_top[0] if proveedor_top else None,
        'victorias_proveedor_top': proveedor_top[1] if proveedor_top else 0,
        'regiones_exitosas': regiones
    }


def generar_insights_para_ia(casos: List[Dict]) -> str:
    """
    Genera insights específicos que la IA puede usar en su análisis.
    
    Returns:
        Texto con insights clave
    """
    patrones = analizar_patrones_ganadores(casos)
    
    if not patrones['success'] or patrones['n_ganadores'] == 0:
        return "⚠️ No hay suficientes datos históricos para generar insights."
    
    insights = f"""
📊 INSIGHTS BASADOS EN {len(casos)} CASOS HISTÓRICOS:

✅ Ofertas Ganadoras: {patrones['n_ganadores']} ({patrones['tasa_conversion']:.1f}%)
❌ Ofertas No Ganadoras: {patrones['n_perdedores']}

💰 Rango de Precios Ganadores:
   • Mínimo: ${patrones['estadisticas_precio']['minimo']:,}
   • Promedio: ${patrones['estadisticas_precio']['promedio']:,}
   • Mediana: ${patrones['estadisticas_precio']['mediana']:,}
   • Máximo: ${patrones['estadisticas_precio']['maximo']:,}

🏆 Proveedor más exitoso en casos similares:
   • {patrones['proveedor_mas_frecuente']} ({patrones['victorias_proveedor_top']} victorias)

📍 Regiones con más éxito:
"""
    
    for region, count in sorted(
        patrones['regiones_exitosas'].items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:3]:
        insights += f"   • {region}: {count} victorias\n"
    
    return insights.strip()


# Función principal para integración con bot
def enriquecer_analisis_licitacion(
    nombre_licitacion: str,
    monto_estimado: Optional[int] = None,
    descripcion: Optional[str] = None
) -> Dict:
    """
    Función principal que combina búsqueda + análisis + contexto.
    Lista para integrar con el análisis IA del bot.
    
    Returns:
        Dict con todo el contexto enriquecido
    """
    # Combinar nombre y descripción para mejor matching
    texto_busqueda = nombre_licitacion
    if descripcion:
        texto_busqueda += " " + descripcion[:200]
    
    # Buscar casos similares
    casos = buscar_casos_similares(
        texto_busqueda, 
        monto_estimado=monto_estimado,
        limite=10
    )
    
    if not casos:
        return {
            'tiene_datos': False,
            'mensaje': 'No se encontraron casos históricos similares'
        }
    
    # Generar contexto y análisis
    contexto = construir_contexto_historico(casos, max_casos=5)
    insights = generar_insights_para_ia(casos)
    patrones = analizar_patrones_ganadores(casos)
    
    return {
        'tiene_datos': True,
        'n_casos_encontrados': len(casos),
        'casos_similares': casos,
        'contexto_para_prompt': contexto,
        'insights': insights,
        'patrones': patrones,
        'recomendacion_precio': {
            'basado_en_ganadores': True,
            'precio_promedio': patrones.get('estadisticas_precio', {}).get('promedio', 0),
            'precio_mediana': patrones.get('estadisticas_precio', {}).get('mediana', 0),
            'rango_min': patrones.get('estadisticas_precio', {}).get('minimo', 0),
            'rango_max': patrones.get('estadisticas_precio', {}).get('maximo', 0),
        } if patrones.get('success') and patrones.get('n_ganadores', 0) > 0 else None
    }


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("TEST: Búsqueda RAG para licitación de laptops")
    print("=" * 60)
    
    resultado = enriquecer_analisis_licitacion(
        "Adquisición de computadores portátiles para ministerio",
        monto_estimado=5000000
    )
    
    if resultado['tiene_datos']:
        print(f"\n✅ Encontrados {resultado['n_casos_encontrados']} casos similares\n")
        print(resultado['insights'])
        print("\n" + "=" * 60)
        print("CONTEXTO PARA PROMPT:")
        print("=" * 60)
        print(resultado['contexto_para_prompt'])
    else:
        print(f"\n❌ {resultado['mensaje']}")
