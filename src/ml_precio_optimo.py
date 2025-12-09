"""
Sistema de Recomendación de Precio Óptimo
Analiza datos históricos para sugerir precios competitivos
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import database_extended as db
from fuzzywuzzy import fuzz
import logging

logger = logging.getLogger(__name__)


def buscar_productos_similares(
    producto: str,
    region: Optional[str] = None,
    limite: int = 500,
    umbral_similitud: int = 60
) -> pd.DataFrame:
    """
    Busca productos similares en el histórico usando fuzzy matching.
    
    Args:
        producto: Nombre del producto a buscar
        region: Filtrar por región específica (opcional)
        limite: Máximo de registros a retornar
        umbral_similitud: Umbral mínimo de similitud (0-100)
    
    Returns:
        DataFrame con productos similares y sus datos
    """
    try:
        conn = db.get_connection()
        
        # Query base
        query = """
            SELECT 
                producto_cotizado,
                monto_total,
                cantidad,
                region,
                es_ganador,
                fecha_cierre,
                nombre_proveedor
            FROM historico_licitaciones
            WHERE monto_total > 0 
            AND cantidad > 0
        """
        
        params = []
        
        # Filtro por región si se especifica
        if region:
            if db.USE_POSTGRES:
                query += " AND UPPER(region) = UPPER(%s)"
            else:
                query += " AND UPPER(region) = UPPER(?)"
            params.append(region)
        
        # Ordenar por fecha reciente y limitar
        query += " ORDER BY fecha_cierre DESC"
        
        if db.USE_POSTGRES:
            query += f" LIMIT {limite * 3}"  # Traer más para filtrar después
        else:
            query += f" LIMIT {limite * 3}"
        
        # Ejecutar query
        if params:
            df = pd.read_sql(query, conn, params=tuple(params))
        else:
            df = pd.read_sql(query, conn)
        
        conn.close()
        
        if df.empty:
            logger.warning(f"No se encontraron datos históricos")
            return pd.DataFrame()
        
        # Calcular similitud con fuzzy matching
        producto_lower = producto.lower()
        df['similitud'] = df['producto_cotizado'].apply(
            lambda x: fuzz.token_set_ratio(producto_lower, str(x).lower()) 
            if pd.notna(x) else 0
        )
        
        # Filtrar por umbral de similitud
        df_filtrado = df[df['similitud'] >= umbral_similitud].copy()
        
        # Ordenar por similitud y tomar los mejores
        df_filtrado = df_filtrado.nlargest(limite, 'similitud')
        
        # Calcular precio unitario
        df_filtrado['precio_unitario'] = (
            df_filtrado['monto_total'] / df_filtrado['cantidad']
        )
        
        logger.info(
            f"Encontrados {len(df_filtrado)} productos similares "
            f"(similitud >= {umbral_similitud}%)"
        )
        
        return df_filtrado
        
    except Exception as e:
        logger.error(f"Error buscando productos similares: {e}")
        return pd.DataFrame()


def calcular_precio_optimo(
    producto: str,
    cantidad: int,
    region: Optional[str] = None,
    solo_ganadores: bool = True
) -> Dict:
    """
    Calcula el precio óptimo basado en análisis estadístico de históricos.
    
    Args:
        producto: Nombre del producto
        cantidad: Cantidad solicitada
        region: Región (opcional)
        solo_ganadores: Si True, solo considera ofertas ganadoras
    
    Returns:
        Dict con recomendación de precio y estadísticas
    """
    df = buscar_productos_similares(producto, region, limite=500)
    
    if df.empty:
        return {
            'success': False,
            'error': 'No se encontraron datos históricos suficientes',
            'confianza': 0
        }
    
    # Filtrar solo ganadores si se requiere
    if solo_ganadores:
        df_analisis = df[df['es_ganador'] == True].copy()
        if df_analisis.empty:
            # Fallback: usar todos los datos
            df_analisis = df.copy()
            solo_ganadores = False
    else:
        df_analisis = df.copy()
    
    # Remover outliers (fuera de 3 desviaciones estándar)
    precio_mean = df_analisis['precio_unitario'].mean()
    precio_std = df_analisis['precio_unitario'].std()
    df_analisis = df_analisis[
        (df_analisis['precio_unitario'] >= precio_mean - 3*precio_std) &
        (df_analisis['precio_unitario'] <= precio_mean + 3*precio_std)
    ]
    
    # Calcular percentiles
    p25 = df_analisis['precio_unitario'].quantile(0.25)
    p50 = df_analisis['precio_unitario'].quantile(0.50)
    p75 = df_analisis['precio_unitario'].quantile(0.75)
    p90 = df_analisis['precio_unitario'].quantile(0.90)
    
    # Precio recomendado: percentil 40-45 (sweet spot)
    precio_unitario_recomendado = df_analisis['precio_unitario'].quantile(0.42)
    precio_total_recomendado = precio_unitario_recomendado * cantidad
    
    # Calcular confianza (basado en cantidad de datos)
    n_registros = len(df_analisis)
    if n_registros >= 100:
        confianza = 0.95
    elif n_registros >= 50:
        confianza = 0.85
    elif n_registros >= 20:
        confianza = 0.70
    elif n_registros >= 10:
        confianza = 0.60
    else:
        confianza = 0.40
    
    # Análisis de ganadores vs perdedores
    n_ganadores = len(df[df['es_ganador'] == True])
    tasa_conversion = (n_ganadores / len(df) * 100) if len(df) > 0 else 0
    
    return {
        'success': True,
        'precio_unitario': {
            'recomendado': round(precio_unitario_recomendado, 2),
            'p25': round(p25, 2),
            'p50': round(p50, 2),
            'p75': round(p75, 2),
            'p90': round(p90, 2),
            'promedio': round(df_analisis['precio_unitario'].mean(), 2),
        },
        'precio_total': {
            'recomendado': round(precio_total_recomendado, 2),
            'minimo_competitivo': round(p25 * cantidad, 2),
            'maximo_aceptable': round(p75 * cantidad, 2),
        },
        'estadisticas': {
            'n_registros': n_registros,
            'n_ganadores': n_ganadores,
            'tasa_conversion': round(tasa_conversion, 2),
            'solo_ganadores': solo_ganadores,
            'region': region or 'Todas',
        },
        'confianza': confianza,
        'recomendacion': generar_recomendacion(
            precio_unitario_recomendado, p50, confianza, n_registros
        )
    }


def generar_recomendacion(
    precio_rec: float, 
    mediana: float, 
    confianza: float,
    n_registros: int
) -> str:
    """Genera texto de recomendación basado en el análisis"""
    
    if confianza >= 0.85:
        nivel_confianza = "Alta confianza"
    elif confianza >= 0.70:
        nivel_confianza = "Confianza moderada"
    else:
        nivel_confianza = "Confianza baja"
    
    diferencia_pct = ((precio_rec - mediana) / mediana * 100) if mediana > 0 else 0
    
    recomendacion = f"""
📊 {nivel_confianza} (basado en {n_registros} registros históricos)

💰 Precio Recomendado: ${precio_rec:,.0f} por unidad
   • {abs(diferencia_pct):.1f}% {'por debajo' if diferencia_pct < 0 else 'por encima'} de la mediana histórica

🎯 Estrategia:
"""
    
    if diferencia_pct < -5:
        recomendacion += "   • Precio muy competitivo - Alta probabilidad de ganar\n"
        recomendacion += "   • Considera si el margen es suficiente"
    elif diferencia_pct > 5:
        recomendacion += "   • Precio conservador - Buen margen pero menor probabilidad\n"
        recomendacion += "   • Evalúa bajar si la licitación es estratégica"
    else:
        recomendacion += "   • Precio equilibrado - Balance óptimo margen/probabilidad\n"
        recomendacion += "   • Sweet spot según datos históricos"
    
    return recomendacion.strip()


def analizar_competencia_precios(
    producto: str, 
    region: Optional[str] = None
) -> Dict:
    """
    Analiza la distribución de precios de la competencia.
    
    Returns:
        Dict con análisis de competencia y distribución
    """
    df = buscar_productos_similares(producto, region, limite=1000)
    
    if df.empty:
        return {'success': False, 'error': 'No hay datos suficientes'}
    
    # Agrupar por proveedor
    competidores = df.groupby('nombre_proveedor').agg({
        'monto_total': ['count', 'mean'],
        'es_ganador': 'sum',
        'precio_unitario': ['mean', 'min', 'max']
    }).round(2)
    
    competidores.columns = ['_'.join(col).strip() for col in competidores.columns]
    competidores['tasa_exito'] = (
        competidores['es_ganador_sum'] / competidores['monto_total_count'] * 100
    ).round(2)
    
    # Top 10 competidores por participación
    top_competidores = competidores.nlargest(10, 'monto_total_count')
    
    # Top 5 ganadores frecuentes
    ganadores_frecuentes = competidores[
        competidores['monto_total_count'] >= 3
    ].nlargest(5, 'tasa_exito')
    
    return {
        'success': True,
        'top_competidores': top_competidores.to_dict('index'),
        'ganadores_frecuentes': ganadores_frecuentes.to_dict('index'),
        'total_competidores': len(competidores),
        'estadisticas_generales': {
            'precio_min': df['precio_unitario'].min(),
            'precio_max': df['precio_unitario'].max(),
            'precio_promedio': df['precio_unitario'].mean(),
            'desviacion_std': df['precio_unitario'].std(),
        }
    }


# Función de conveniencia para uso directo
def obtener_recomendacion_rapida(
    producto: str, 
    cantidad: int = 1,
    region: Optional[str] = None
) -> str:
    """
    Retorna recomendación de precio en formato texto legible.
    Útil para integración directa con el bot.
    """
    resultado = calcular_precio_optimo(producto, cantidad, region)
    
    if not resultado['success']:
        return f"❌ {resultado['error']}"
    
    precio = resultado['precio_total']['recomendado']
    rango = f"${resultado['precio_total']['minimo_competitivo']:,.0f} - ${resultado['precio_total']['maximo_aceptable']:,.0f}"
    
    mensaje = f"""
💰 RECOMENDACIÓN DE PRECIO

Producto: {producto}
Cantidad: {cantidad} unidades

{resultado['recomendacion']}

📈 Rango Competitivo: {rango}
💵 Precio Total Sugerido: ${precio:,.0f}

📊 Datos: {resultado['estadisticas']['n_registros']} licitaciones analizadas
   • {resultado['estadisticas']['n_ganadores']} ofertas ganadoras
   • Tasa de conversión: {resultado['estadisticas']['tasa_conversion']:.1f}%
"""
    
    return mensaje.strip()


if __name__ == "__main__":
    # Tests básicos
    logging.basicConfig(level=logging.INFO)
    
    # Test 1: Buscar laptop
    print("=" * 60)
    print("TEST 1: Recomendación para laptop")
    print("=" * 60)
    resultado = obtener_recomendacion_rapida("laptop", cantidad=10)
    print(resultado)
    
    print("\n" + "=" * 60)
    print("TEST 2: Análisis de competencia")
    print("=" * 60)
    competencia = analizar_competencia_precios("computador")
    if competencia['success']:
        print(f"Total competidores: {competencia['total_competidores']}")
        print(f"\nTop 3 competidores frecuentes:")
        for proveedor, datos in list(competencia['top_competidores'].items())[:3]:
            print(f"  • {proveedor}: {datos['monto_total_count']} ofertas")
