"""
Módulo de utilidades de Machine Learning y análisis de datos.
"""
import re
from collections import Counter
import database_bot as db_bot
import database_extended as db_ext

# Palabras comunes a ignorar (stop words)
STOP_WORDS = {
    'de', 'la', 'el', 'en', 'y', 'a', 'los', 'del', 'las', 'por', 'un', 'para', 
    'con', 'no', 'una', 'su', 'al', 'lo', 'como', 'mas', 'pero', 'sus', 'le', 
    'ya', 'o', 'fue', 'este', 'ha', 'si', 'porque', 'esta', 'son', 'entre', 
    'cuando', 'muy', 'sin', 'sobre', 'tambien', 'me', 'hasta', 'hay', 'donde', 
    'quien', 'desde', 'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 
    'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mi', 'antes', 
    'algunos', 'que', 'unos', 'yo', 'otro', 'otras', 'otra', 'el', 'ella', 
    'servicio', 'adquisicion', 'compra', 'contratacion', 'suministro', 'licitacion'
}

def normalizar_texto(texto):
    """Convierte a minúsculas y elimina caracteres no alfanuméricos."""
    if not texto:
        return ""
    # Eliminar puntuación y números, dejar solo letras y espacios
    texto = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', str(texto))
    return texto.lower()

def obtener_palabras_frecuentes(textos, top_n=10):
    """Obtiene las palabras más frecuentes de una lista de textos."""
    palabras = []
    for texto in textos:
        tokens = normalizar_texto(texto).split()
        palabras.extend([p for p in tokens if p not in STOP_WORDS and len(p) > 3])
    
    contador = Counter(palabras)
    return contador.most_common(top_n)

def analizar_preferencias(user_id):
    """
    Analiza las licitaciones con feedback positivo del usuario
    y sugiere nuevas palabras clave.
    """
    conn = db_bot.get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if db_bot.USE_POSTGRES else '?'
    
    # 1. Obtener códigos de licitaciones con Like (feedback=1)
    cursor.execute(f'''
        SELECT codigo_licitacion 
        FROM feedback_analisis 
        WHERE telegram_user_id = {placeholder} AND feedback = 1
    ''', (user_id,))
    
    codigos = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not codigos:
        return []
        
    # 2. Obtener detalles de esas licitaciones (nombre y descripción)
    conn_ext = db_ext.get_connection()
    cursor_ext = conn_ext.cursor()
    
    textos_analisis = []
    
    # Construir query dinámica para IN clause
    placeholders_in = ','.join([placeholder] * len(codigos))
    
    # Buscar nombres en tabla principal
    cursor_ext.execute(f'''
        SELECT nombre, organismo 
        FROM licitaciones 
        WHERE codigo IN ({placeholders_in})
    ''', tuple(codigos))
    
    for row in cursor_ext.fetchall():
        textos_analisis.append(row[0]) # Nombre
        textos_analisis.append(row[1]) # Organismo
        
    conn_ext.close()
    
    # 3. Obtener palabras clave actuales del usuario
    perfil = db_bot.obtener_perfil(user_id)
    if not perfil:
        return []
        
    palabras_actuales = set()
    if perfil['palabras_clave']:
        palabras_actuales.update([p.strip().lower() for p in perfil['palabras_clave'].split(',')])
    
    # 4. Encontrar palabras frecuentes que NO están en el perfil
    frecuentes = obtener_palabras_frecuentes(textos_analisis, top_n=20)
    
    sugerencias = []
    for palabra, count in frecuentes:
        if palabra not in palabras_actuales and count >= 2: # Al menos 2 apariciones
            sugerencias.append(palabra)
            
    return sugerencias[:5] # Retornar top 5 sugerencias
