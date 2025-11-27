"""
Extensión de base de datos para el bot inteligente compatible con PostgreSQL y SQLite.
Incluye tablas para perfiles de empresa, licitaciones guardadas y caché de análisis.
"""
import os
import json
from datetime import datetime

# Detectar tipo de base de datos
DATABASE_URL = os.getenv('DATABASE_URL', '')
USE_POSTGRES = DATABASE_URL.startswith('postgresql')

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
else:
    import sqlite3
    DB_NAME = 'compra_agil.db'


def get_connection():
    """Obtiene una conexión a la base de datos"""
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect(DB_NAME)


def iniciar_db_bot():
    """
    Crea las tablas adicionales necesarias para el bot inteligente.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ajustar sintaxis según el tipo de BD
    id_type = "SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    # Tabla de perfiles de empresas
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS perfiles_empresas (
            telegram_user_id BIGINT PRIMARY KEY,
            nombre_empresa TEXT,
            tipo_negocio TEXT,
            productos_servicios TEXT,
            palabras_clave TEXT,
            capacidad_entrega_dias INTEGER,
            ubicacion TEXT,
            experiencia_anos INTEGER,
            certificaciones TEXT,
            alertas_activas INTEGER DEFAULT 1,
            fecha_creacion TEXT,
            fecha_actualizacion TEXT
        )
    ''')
    
    # Tabla de licitaciones guardadas
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS licitaciones_guardadas (
            id {id_type},
            telegram_user_id BIGINT,
            codigo_licitacion TEXT,
            fecha_guardado TEXT,
            notas TEXT,
            alerta_cierre INTEGER DEFAULT 1
        )
    ''')
    
    # Tabla de caché de análisis de IA
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analisis_cache (
            codigo_licitacion TEXT PRIMARY KEY,
            analisis_json TEXT,
            fecha_analisis TEXT,
            version_prompt TEXT
        )
    ''')
    
    # Tabla de historial de interacciones
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS historial_interacciones (
            id {id_type},
            telegram_user_id BIGINT,
            accion TEXT,
            codigo_licitacion TEXT,
            fecha TEXT
        )
    ''')
    
    # Tabla de feedback para ML
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS feedback_analisis (
            id {id_type},
            telegram_user_id BIGINT,
            codigo_licitacion TEXT,
            feedback INTEGER,
            fecha TEXT
        )
    ''')
    
    # Tabla de configuración de alertas granulares
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS alertas_config (
            id {id_type},
            telegram_user_id BIGINT,
            termino_busqueda TEXT,
            monto_minimo INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            fecha_creacion TEXT
        )
    ''')
    
    # Tabla de estado del sistema (para timestamps de scrapers)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_status (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
    ''')
    
    # Índices
    if USE_POSTGRES:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_guardadas_user ON licitaciones_guardadas(telegram_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_guardadas_codigo ON licitaciones_guardadas(codigo_licitacion)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_historial_user ON historial_interacciones(telegram_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_codigo ON feedback_analisis(codigo_licitacion)')
    else:
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_guardadas_user ON licitaciones_guardadas(telegram_user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_guardadas_codigo ON licitaciones_guardadas(codigo_licitacion)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_historial_user ON historial_interacciones(telegram_user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_codigo ON feedback_analisis(codigo_licitacion)')
        except:
            pass  # Índices ya existen
    
    conn.commit()
    conn.close()
    print("✅ Tablas del bot inteligente creadas/verificadas")


# ==================== SYSTEM STATUS ====================

def update_system_status(key, value):
    """Actualiza el estado del sistema (ej: timestamp de scraper)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if USE_POSTGRES else '?'
    ahora = datetime.now().isoformat()
    
    try:
        if USE_POSTGRES:
            cursor.execute(f'''
                INSERT INTO system_status (key, value, updated_at)
                VALUES ({placeholder}, {placeholder}, {placeholder})
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    updated_at = EXCLUDED.updated_at
            ''', (key, value, ahora))
        else:
            cursor.execute(f'''
                INSERT OR REPLACE INTO system_status (key, value, updated_at)
                VALUES ({placeholder}, {placeholder}, {placeholder})
            ''', (key, value, ahora))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar system_status: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_system_status(key):
    """Obtiene el valor de una clave de estado."""
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if USE_POSTGRES else '?'
    
    cursor.execute(f'SELECT value, updated_at FROM system_status WHERE key = {placeholder}', (key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {'value': row[0], 'updated_at': row[1]}
    return None


# ==================== PERFILES ====================

def guardar_perfil(user_id, perfil_data):
    """Guarda o actualiza el perfil de una empresa."""
    conn = get_connection()
    cursor = conn.cursor()
    
    ahora = datetime.now().isoformat()
    placeholder = '%s' if USE_POSTGRES else '?'
    
    try:
        if USE_POSTGRES:
            cursor.execute(f'''
                INSERT INTO perfiles_empresas 
                (telegram_user_id, nombre_empresa, tipo_negocio, productos_servicios, 
                 palabras_clave, capacidad_entrega_dias, ubicacion, experiencia_anos, 
                 certificaciones, alertas_activas, fecha_creacion, fecha_actualizacion)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 
                        {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 
                        {placeholder}, {placeholder})
                ON CONFLICT (telegram_user_id) DO UPDATE SET
                    nombre_empresa = EXCLUDED.nombre_empresa,
                    tipo_negocio = EXCLUDED.tipo_negocio,
                    productos_servicios = EXCLUDED.productos_servicios,
                    palabras_clave = EXCLUDED.palabras_clave,
                    capacidad_entrega_dias = EXCLUDED.capacidad_entrega_dias,
                    ubicacion = EXCLUDED.ubicacion,
                    experiencia_anos = EXCLUDED.experiencia_anos,
                    certificaciones = EXCLUDED.certificaciones,
                    alertas_activas = EXCLUDED.alertas_activas,
                    fecha_actualizacion = EXCLUDED.fecha_actualizacion
            ''', (
                user_id,
                perfil_data.get('nombre_empresa'),
                perfil_data.get('tipo_negocio'),
                perfil_data.get('productos_servicios'),
                perfil_data.get('palabras_clave'),
                perfil_data.get('capacidad_entrega_dias'),
                perfil_data.get('ubicacion'),
                perfil_data.get('experiencia_anos'),
                perfil_data.get('certificaciones'),
                perfil_data.get('alertas_activas', 1),
                ahora,
                ahora
            ))
        else:
            cursor.execute(f'''
                INSERT OR REPLACE INTO perfiles_empresas 
                (telegram_user_id, nombre_empresa, tipo_negocio, productos_servicios, 
                 palabras_clave, capacidad_entrega_dias, ubicacion, experiencia_anos, 
                 certificaciones, alertas_activas, fecha_creacion, fecha_actualizacion)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 
                        {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 
                        COALESCE((SELECT fecha_creacion FROM perfiles_empresas WHERE telegram_user_id = {placeholder}), {placeholder}), 
                        {placeholder})
            ''', (
                user_id,
                perfil_data.get('nombre_empresa'),
                perfil_data.get('tipo_negocio'),
                perfil_data.get('productos_servicios'),
                perfil_data.get('palabras_clave'),
                perfil_data.get('capacidad_entrega_dias'),
                perfil_data.get('ubicacion'),
                perfil_data.get('experiencia_anos'),
                perfil_data.get('certificaciones'),
                perfil_data.get('alertas_activas', 1),
                user_id,
                ahora,
                ahora
            ))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al guardar perfil: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def obtener_perfil(user_id):
    """Obtiene el perfil de una empresa."""
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if USE_POSTGRES else '?'
    cursor.execute(f'SELECT * FROM perfiles_empresas WHERE telegram_user_id = {placeholder}', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        'telegram_user_id': row[0],
        'nombre_empresa': row[1],
        'tipo_negocio': row[2],
        'productos_servicios': row[3],
        'palabras_clave': row[4],
        'capacidad_entrega_dias': row[5],
        'ubicacion': row[6],
        'experiencia_anos': row[7],
        'certificaciones': row[8],
        'alertas_activas': row[9],
        'fecha_creacion': row[10],
        'fecha_actualizacion': row[11]
    }


# ==================== LICITACIONES GUARDADAS ====================

def guardar_licitacion(user_id, codigo, notas=None):
    """Guarda una licitación para seguimiento."""
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if USE_POSTGRES else '?'
    
    try:
        cursor.execute(f'''
            INSERT INTO licitaciones_guardadas 
            (telegram_user_id, codigo_licitacion, fecha_guardado, notas)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
        ''', (user_id, codigo, datetime.now().isoformat(), notas))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al guardar licitación: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def obtener_licitaciones_guardadas(user_id):
    """Obtiene las licitaciones guardadas por un usuario."""
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if USE_POSTGRES else '?'
    
    cursor.execute(f'''
        SELECT lg.codigo_licitacion, lg.fecha_guardado, lg.notas,
               l.nombre, l.organismo, l.monto_disponible, l.fecha_cierre
        FROM licitaciones_guardadas lg
        JOIN licitaciones l ON lg.codigo_licitacion = l.codigo
        WHERE lg.telegram_user_id = {placeholder}
        ORDER BY lg.fecha_guardado DESC
    ''', (user_id,))
    
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def eliminar_licitacion_guardada(user_id, codigo):
    """Elimina una licitación guardada."""
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if USE_POSTGRES else '?'
    
    cursor.execute(f'''
        DELETE FROM licitaciones_guardadas 
        WHERE telegram_user_id = {placeholder} AND codigo_licitacion = {placeholder}
    ''', (user_id, codigo))
    
    rows_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_deleted > 0


# ==================== CACHÉ DE ANÁLISIS ====================

def guardar_analisis_cache(codigo, analisis, version_prompt="v1"):
    """Guarda el análisis de IA en caché."""
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if USE_POSTGRES else '?'
    
    try:
        if USE_POSTGRES:
            cursor.execute(f'''
                INSERT INTO analisis_cache 
                (codigo_licitacion, analisis_json, fecha_analisis, version_prompt)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                ON CONFLICT (codigo_licitacion) DO UPDATE SET
                    analisis_json = EXCLUDED.analisis_json,
                    fecha_analisis = EXCLUDED.fecha_analisis
            ''', (codigo, json.dumps(analisis, ensure_ascii=False), datetime.now().isoformat(), version_prompt))
        else:
            cursor.execute(f'''
                INSERT OR REPLACE INTO analisis_cache 
                (codigo_licitacion, analisis_json, fecha_analisis, version_prompt)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (codigo, json.dumps(analisis, ensure_ascii=False), datetime.now().isoformat(), version_prompt))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al guardar análisis en caché: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def obtener_analisis_cache(codigo, max_edad_horas=24):
    """Obtiene el análisis de IA desde caché si existe y no está muy antiguo."""
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if USE_POSTGRES else '?'
    
    cursor.execute(f'''
        SELECT analisis_json, fecha_analisis 
        FROM analisis_cache 
        WHERE codigo_licitacion = {placeholder}
    ''', (codigo,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    # Verificar edad del análisis
    fecha_analisis = datetime.fromisoformat(row[1])
    edad_horas = (datetime.now() - fecha_analisis).total_seconds() / 3600
    
    if edad_horas > max_edad_horas:
        return None  # Muy antiguo
    
    return json.loads(row[0])


# ==================== HISTORIAL ====================

def registrar_interaccion(user_id, accion, codigo=None):
    """Registra una interacción del usuario."""
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if USE_POSTGRES else '?'
    
    try:
        cursor.execute(f'''
            INSERT INTO historial_interacciones 
            (telegram_user_id, accion, codigo_licitacion, fecha)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
        ''', (user_id, accion, codigo, datetime.now().isoformat()))
        conn.commit()
    except Exception as e:
        print(f"Error al registrar interacción: {e}")
        conn.rollback()
    finally:
        conn.close()


def registrar_feedback(user_id, codigo, feedback):
    """
    Registra el feedback del usuario sobre un análisis (1=Like, 0=Dislike).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if USE_POSTGRES else '?'
    
    try:
        cursor.execute(f'''
            INSERT INTO feedback_analisis 
            (telegram_user_id, codigo_licitacion, feedback, fecha)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
        ''', (user_id, codigo, feedback, datetime.now().isoformat()))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al registrar feedback: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    # Inicializar tablas del bot
    iniciar_db_bot()
    print("Base de datos del bot lista")
