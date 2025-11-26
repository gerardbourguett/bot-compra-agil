"""
Adaptador de base de datos que soporta tanto SQLite como PostgreSQL.
Detecta automáticamente cuál usar basándose en DATABASE_URL.
"""
import os
from urllib.parse import urlparse

# Detectar tipo de base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///compra_agil.db')
parsed = urlparse(DATABASE_URL)
DB_TYPE = parsed.scheme.split('+')[0] if parsed.scheme else 'sqlite'

print(f"📊 Usando base de datos: {DB_TYPE}")

if DB_TYPE == 'postgresql':
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import psycopg2.pool
    
    # Pool de conexiones
    connection_pool = None
    
    def get_connection():
        """Obtiene una conexión del pool"""
        global connection_pool
        if connection_pool is None:
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,  # min y max conexiones
                DATABASE_URL
            )
        return connection_pool.getconn()
    
    def return_connection(conn):
        """Devuelve una conexión al pool"""
        global connection_pool
        if connection_pool:
            connection_pool.putconn(conn)
    
    def execute_query(query, params=None, fetch=False, fetchone=False):
        """Ejecuta una query en PostgreSQL"""
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or ())
                if fetch:
                    return cursor.fetchall()
                elif fetchone:
                    return cursor.fetchone()
                conn.commit()
                return cursor.rowcount
        finally:
            return_connection(conn)
    
    def execute_many(query, params_list):
        """Ejecuta múltiples inserts"""
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
        finally:
            return_connection(conn)

else:  # SQLite
    import sqlite3
    
    DB_NAME = 'compra_agil.db'
    
    def get_connection():
        """Obtiene una conexión SQLite"""
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn
    
    def return_connection(conn):
        """Cierra la conexión SQLite"""
        conn.close()
    
    def execute_query(query, params=None, fetch=False, fetchone=False):
        """Ejecuta una query en SQLite"""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            elif fetchone:
                return cursor.fetchone()
            conn.commit()
            return cursor.rowcount
        finally:
            return_connection(conn)
    
    def execute_many(query, params_list):
        """Ejecuta múltiples inserts"""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
        finally:
            return_connection(conn)


# Funciones de utilidad comunes
def adapt_placeholder(query):
    """Adapta placeholders de ? a %s para PostgreSQL"""
    if DB_TYPE == 'postgresql':
        return query.replace('?', '%s')
    return query


def get_db_type():
    """Retorna el tipo de base de datos en uso"""
    return DB_TYPE


if __name__ == "__main__":
    print(f"✅ Adaptador de BD configurado: {DB_TYPE}")
    if DB_TYPE == 'postgresql':
        print(f"🔗 URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
