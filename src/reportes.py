"""
Módulo para generar reportes administrativos y de inteligencia de mercado.
"""
import database_extended as db

def generar_reporte_competencia(top_n=5):
    """
    Genera un reporte de los competidores más activos y exitosos.
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 1. Top Ganadores (Más adjudicaciones)
    # Usamos parámetros para evitar inyección SQL
    if db.USE_POSTGRES:
        query_ganadores = 'SELECT nombre, total_adjudicaciones FROM competidores ORDER BY total_adjudicaciones DESC LIMIT %s'
        query_participativos = '''
            SELECT c.nombre, COUNT(o.id) as total_ofertas
            FROM competidores c
            JOIN ofertas_competidores o ON c.rut = o.rut_competidor
            GROUP BY c.rut, c.nombre
            ORDER BY total_ofertas DESC
            LIMIT %s
        '''
    else:
        query_ganadores = 'SELECT nombre, total_adjudicaciones FROM competidores ORDER BY total_adjudicaciones DESC LIMIT ?'
        query_participativos = '''
            SELECT c.nombre, COUNT(o.id) as total_ofertas
            FROM competidores c
            JOIN ofertas_competidores o ON c.rut = o.rut_competidor
            GROUP BY c.rut, c.nombre
            ORDER BY total_ofertas DESC
            LIMIT ?
        '''

    cursor.execute(query_ganadores, (top_n,))
    top_ganadores = cursor.fetchall()
    
    # 2. Top Participativos (Más ofertas presentadas)
    cursor.execute(query_participativos, (top_n,))
    top_participativos = cursor.fetchall()
    
    conn.close()
    
    return {
        'top_ganadores': top_ganadores,
        'top_participativos': top_participativos
    }


def generar_reporte_mercado(top_n=5):
    """
    Genera estadísticas generales del mercado capturado.
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Total licitaciones por estado
    cursor.execute('''
        SELECT estado, COUNT(*) 
        FROM licitaciones 
        GROUP BY estado
    ''')
    estados = cursor.fetchall()
    
    # Monto promedio de adjudicaciones (donde hubo ganador)
    cursor.execute('''
        SELECT AVG(monto_total) 
        FROM ofertas_competidores 
        WHERE es_ganador = 1
    ''')
    promedio_adjudicado = cursor.fetchone()[0] or 0
    
    # Organismos más activos
    if db.USE_POSTGRES:
        query_organismos = '''
            SELECT organismo, COUNT(*) as total
            FROM licitaciones
            GROUP BY organismo
            ORDER BY total DESC
            LIMIT %s
        '''
    else:
        query_organismos = '''
            SELECT organismo, COUNT(*) as total
            FROM licitaciones
            GROUP BY organismo
            ORDER BY total DESC
            LIMIT ?
        '''
        
    cursor.execute(query_organismos, (top_n,))
    top_organismos = cursor.fetchall()
    
    conn.close()
    
    return {
        'estados': estados,
        'promedio_adjudicado': int(promedio_adjudicado),
        'top_organismos': top_organismos
    }


def generar_excel_mercado():
    """Genera un archivo Excel con el reporte de mercado"""
    import pandas as pd
    import io
    
    # Obtener datos (Top 10 solicitado por usuario)
    comp_data = generar_reporte_competencia(top_n=10)
    mercado_data = generar_reporte_mercado(top_n=10)
    
    # Crear buffer
    output = io.BytesIO()
    
    # Crear DataFrames
    df_competidores = pd.DataFrame(comp_data['top_ganadores'], columns=['Empresa', 'Adjudicaciones'])
    df_participativos = pd.DataFrame(comp_data['top_participativos'], columns=['Empresa', 'Ofertas'])
    df_organismos = pd.DataFrame(mercado_data['top_organismos'], columns=['Organismo', 'Licitaciones'])
    
    df_resumen = pd.DataFrame([
        {'Métrica': 'Promedio Adjudicado', 'Valor': mercado_data['promedio_adjudicado']},
        {'Métrica': 'Total Competidores (Top 10 Ganadores)', 'Valor': df_competidores['Adjudicaciones'].sum()},
        {'Métrica': 'Total Ofertas (Top 10 Participativos)', 'Valor': df_participativos['Ofertas'].sum()}
    ])
    
    # Escribir a Excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
        df_competidores.to_excel(writer, sheet_name='Top Ganadores', index=False)
        df_participativos.to_excel(writer, sheet_name='Top Participativos', index=False)
        df_organismos.to_excel(writer, sheet_name='Top Organismos', index=False)
        
    output.seek(0)
    return output
