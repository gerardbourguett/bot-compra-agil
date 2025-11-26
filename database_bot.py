"""
Extensión de base de datos para el bot inteligente.
Incluye tablas para perfiles de empresa, licitaciones guardadas y caché de análisis.
"""
import sqlite3
import json
from datetime import datetime

DB_NAME = 'compra_agil.db'


def iniciar_db_bot():
    """
    Crea las tablas adicionales necesarias para el bot inteligente.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla de perfiles de empresas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perfiles_empresas (
            telegram_user_id INTEGER PRIMARY KEY,
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licitaciones_guardadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER,
            codigo_licitacion TEXT,
            fecha_guardado TEXT,
            notas TEXT,
            alerta_cierre INTEGER DEFAULT 1,
            FOREIGN KEY (codigo_licitacion) REFERENCES licitaciones(codigo)
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_interacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER,
            accion TEXT,
            codigo_licitacion TEXT,
            fecha TEXT
        )
    ''')
    
    # Índices
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_guardadas_user ON licitaciones_guardadas(telegram_user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_guardadas_codigo ON licitaciones_guardadas(codigo_licitacion)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_historial_user ON historial_interacciones(telegram_user_id)')
    
    conn.commit()
    conn.close()
    print("✅ Tablas del bot inteligente creadas/verificadas")


# ==================== PERFILES ====================

def guardar_perfil(user_id, perfil_data):
    """
    Guarda o actualiza el perfil de una empresa.
    
    Args:
        user_id: ID del usuario de Telegram
        perfil_data: Diccionario con los datos del perfil
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    ahora = datetime.now().isoformat()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO perfiles_empresas 
            (telegram_user_id, nombre_empresa, tipo_negocio, productos_servicios, 
             palabras_clave, capacidad_entrega_dias, ubicacion, experiencia_anos, 
             certificaciones, alertas_activas, fecha_creacion, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                    COALESCE((SELECT fecha_creacion FROM perfiles_empresas WHERE telegram_user_id = ?), ?), 
                    ?)
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
        return False
    finally:
        conn.close()


def obtener_perfil(user_id):
    """
    Obtiene el perfil de una empresa.
    
    Returns:
        dict o None si no existe
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM perfiles_empresas WHERE telegram_user_id = ?', (user_id,))
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
    """
    Guarda una licitación para seguimiento.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO licitaciones_guardadas 
            (telegram_user_id, codigo_licitacion, fecha_guardado, notas)
            VALUES (?, ?, ?, ?)
        ''', (user_id, codigo, datetime.now().isoformat(), notas))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Ya existe
    except Exception as e:
        print(f"Error al guardar licitación: {e}")
        return False
    finally:
        conn.close()


def obtener_licitaciones_guardadas(user_id):
    """
    Obtiene las licitaciones guardadas por un usuario.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT lg.codigo_licitacion, lg.fecha_guardado, lg.notas,
               l.nombre, l.organismo, l.monto_disponible, l.fecha_cierre
        FROM licitaciones_guardadas lg
        JOIN licitaciones l ON lg.codigo_licitacion = l.codigo
        WHERE lg.telegram_user_id = ?
        ORDER BY lg.fecha_guardado DESC
    ''', (user_id,))
    
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def eliminar_licitacion_guardada(user_id, codigo):
    """
    Elimina una licitación guardada.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM licitaciones_guardadas 
        WHERE telegram_user_id = ? AND codigo_licitacion = ?
    ''', (user_id, codigo))
    
    rows_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_deleted > 0


# ==================== CACHÉ DE ANÁLISIS ====================

def guardar_analisis_cache(codigo, analisis, version_prompt="v1"):
    """
    Guarda el análisis de IA en caché.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO analisis_cache 
            (codigo_licitacion, analisis_json, fecha_analisis, version_prompt)
            VALUES (?, ?, ?, ?)
        ''', (codigo, json.dumps(analisis, ensure_ascii=False), datetime.now().isoformat(), version_prompt))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al guardar análisis en caché: {e}")
        return False
    finally:
        conn.close()


def obtener_analisis_cache(codigo, max_edad_horas=24):
    """
    Obtiene el análisis de IA desde caché si existe y no está muy antiguo.
    
    Returns:
        dict o None
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT analisis_json, fecha_analisis 
        FROM analisis_cache 
        WHERE codigo_licitacion = ?
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
    """
    Registra una interacción del usuario.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO historial_interacciones 
            (telegram_user_id, accion, codigo_licitacion, fecha)
            VALUES (?, ?, ?, ?)
        ''', (user_id, accion, codigo, datetime.now().isoformat()))
        conn.commit()
    except Exception as e:
        print(f"Error al registrar interacción: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    # Inicializar tablas del bot
    iniciar_db_bot()
    print("Base de datos del bot lista")
