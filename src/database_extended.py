"""
Versión extendida de la base de datos compatible con PostgreSQL y SQLite.
Detecta automáticamente cuál usar basándose en DATABASE_URL.
"""
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Detectar tipo de base de datos
DATABASE_URL = os.getenv('DATABASE_URL', '')
print(f"DEBUG: DATABASE_URL='{DATABASE_URL}'")
USE_POSTGRES = DATABASE_URL.startswith('postgresql')
USE_POSTGRES = DATABASE_URL.startswith('postgresql')

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    print("Usando PostgreSQL")
else:
    import sqlite3
    DB_NAME = 'compra_agil.db'
    print("Usando SQLite")


def get_connection():
    """Obtiene una conexión a la base de datos"""
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect(DB_NAME)


def iniciar_db_extendida():
    """
    Crea todas las tablas necesarias para almacenar información completa
    de las licitaciones de Compra Ágil.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        raise
    
    # Ajustar sintaxis según el tipo de BD
    if USE_POSTGRES:
        # PostgreSQL usa SERIAL en lugar de INTEGER PRIMARY KEY
        id_type = "SERIAL PRIMARY KEY"
        text_type = "TEXT"
    else:
        id_type = "INTEGER PRIMARY KEY"
        text_type = "TEXT"
    
    # Tabla principal de licitaciones (resumen)
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS licitaciones (
            id {id_type if USE_POSTGRES else 'INTEGER PRIMARY KEY'},
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT,
            fecha_publicacion TEXT,
            fecha_cierre TEXT,
            organismo TEXT,
            unidad TEXT,
            id_estado INTEGER,
            estado TEXT,
            monto_disponible INTEGER,
            moneda TEXT,
            monto_disponible_CLP INTEGER,
            fecha_cambio TEXT,
            valor_cambio_moneda REAL,
            cantidad_proveedores_cotizando INTEGER,
            estado_convocatoria INTEGER,
            detalle_obtenido INTEGER DEFAULT 0
        )
    ''')
    
    # Tabla de detalles completos
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS licitaciones_detalle (
            codigo TEXT PRIMARY KEY,
            detalle_id INTEGER,
            nombre TEXT,
            descripcion TEXT,
            fecha_publicacion TEXT,
            fecha_cierre TEXT,
            id_estado INTEGER,
            estado TEXT,
            direccion_entrega TEXT,
            plazo_entrega INTEGER,
            presupuesto_estimado INTEGER,
            moneda TEXT,
            multa_sancion INTEGER,
            cantidad_proveedores_invitados INTEGER,
            organismo_comprador TEXT,
            rut_organismo_comprador TEXT,
            division TEXT,
            fecha_cierre_primer_llamado TEXT,
            fecha_cierre_segundo_llamado TEXT,
            tipo_presupuesto TEXT,
            estado_convocatoria INTEGER,
            total_demandas INTEGER,
            total_ofertas_recibidas INTEGER,
            considera_requisitos_medioambientales INTEGER,
            considera_requisitos_impacto_social_economico INTEGER,
            datos_json TEXT,
            FOREIGN KEY (codigo) REFERENCES licitaciones(codigo)
        )
    ''')
    
    # Tabla de productos solicitados
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS productos_solicitados (
            id {id_type if USE_POSTGRES else 'INTEGER PRIMARY KEY AUTOINCREMENT'},
            codigo_licitacion TEXT,
            nombre TEXT,
            descripcion TEXT,
            cantidad REAL,
            unidad_medida TEXT,
            FOREIGN KEY (codigo_licitacion) REFERENCES licitaciones(codigo)
        )
    ''')
    
    # Tabla de historial
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS historial (
            id {id_type if USE_POSTGRES else 'INTEGER PRIMARY KEY AUTOINCREMENT'},
            codigo_licitacion TEXT,
            fecha TEXT,
            accion TEXT,
            usuario TEXT,
            FOREIGN KEY (codigo_licitacion) REFERENCES licitaciones(codigo)
        )
    ''')
    
    # Tabla de adjuntos
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS adjuntos (
            id {id_type if USE_POSTGRES else 'INTEGER PRIMARY KEY AUTOINCREMENT'},
            codigo_licitacion TEXT,
            nombre_archivo TEXT,
            id_adjunto TEXT,
            FOREIGN KEY (codigo_licitacion) REFERENCES licitaciones(codigo)
        )
    ''')
    
    # Tabla de categorías (Tags)
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS categorias (
            id {id_type if USE_POSTGRES else 'INTEGER PRIMARY KEY AUTOINCREMENT'},
            nombre TEXT UNIQUE,
            descripcion TEXT
        )
    ''')
    
    # Tabla de relación Licitaciones <-> Categorías
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS licitaciones_categorias (
            codigo_licitacion TEXT,
            categoria_id INTEGER,
            PRIMARY KEY (codigo_licitacion, categoria_id),
            FOREIGN KEY (codigo_licitacion) REFERENCES licitaciones(codigo),
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    ''')
    
    # Tabla de Competidores (Placeholder para futuro análisis)
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS competidores (
            rut TEXT PRIMARY KEY,
            nombre TEXT,
            es_ganador_frecuente INTEGER DEFAULT 0,
            total_adjudicaciones INTEGER DEFAULT 0,
            fecha_ultima_oferta TEXT
        )
    ''')
    
    # Tabla de Ofertas de Competidores (Detalle de cada cotización)
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS ofertas_competidores (
            id {id_type if USE_POSTGRES else 'INTEGER PRIMARY KEY AUTOINCREMENT'},
            codigo_licitacion TEXT,
            rut_competidor TEXT,
            monto_total INTEGER,
            es_ganador INTEGER DEFAULT 0,
            fecha_oferta TEXT,
            descripcion TEXT,
            FOREIGN KEY (codigo_licitacion) REFERENCES licitaciones(codigo),
            FOREIGN KEY (rut_competidor) REFERENCES competidores(rut)
        )
    ''')
    
    # Tabla de histórico de licitaciones (para Big Data)
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS historico_licitaciones (
            id {id_type},
            codigo_cotizacion {text_type},
            nombre_cotizacion {text_type},
            region {text_type},
            rut_proveedor {text_type},
            nombre_proveedor {text_type},
            producto_cotizado {text_type},
            cantidad INTEGER,
            monto_total INTEGER,
            detalle_oferta {text_type},
            es_ganador BOOLEAN,
            fecha_cierre DATE,
            fecha_importacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Índices para búsquedas rápidas en histórico
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hist_codigo ON historico_licitaciones(codigo_cotizacion)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hist_producto ON historico_licitaciones(producto_cotizado)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hist_ganador ON historico_licitaciones(es_ganador)')

    try:
        conn.commit()
        conn.close()
        print("✅ Base de datos extendida creada/verificada - Todas las tablas existen")
    except Exception as e:
        print(f"❌ Error al crear/verificar tablas: {e}")
        try:
            conn.rollback()
        except:
            pass
        conn.close()
        raise


def guardar_licitacion_basica(datos):
    """
    Guarda los datos básicos de una licitación (desde el listado).

    Args:
        datos: Tupla con todos los campos de la licitación desde el JSON de la API

    Returns:
        int: 1 si se guardó, 0 si ya existía
    """
    try:
        # Asegurar que las tablas existen
        iniciar_db_extendida()

        conn = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Error al preparar base de datos: {e}")
        return 0

    try:
        if USE_POSTGRES:
            # PostgreSQL usa ON CONFLICT DO UPDATE
            cursor.execute('''
                INSERT INTO licitaciones 
                (id, codigo, nombre, fecha_publicacion, fecha_cierre, organismo, unidad, 
                 id_estado, estado, monto_disponible, moneda, monto_disponible_CLP, 
                 fecha_cambio, valor_cambio_moneda, cantidad_proveedores_cotizando, estado_convocatoria)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (codigo) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    fecha_cierre = EXCLUDED.fecha_cierre,
                    id_estado = EXCLUDED.id_estado,
                    estado = EXCLUDED.estado,
                    monto_disponible = EXCLUDED.monto_disponible,
                    moneda = EXCLUDED.moneda,
                    monto_disponible_CLP = EXCLUDED.monto_disponible_CLP,
                    fecha_cambio = EXCLUDED.fecha_cambio,
                    valor_cambio_moneda = EXCLUDED.valor_cambio_moneda,
                    cantidad_proveedores_cotizando = EXCLUDED.cantidad_proveedores_cotizando,
                    estado_convocatoria = EXCLUDED.estado_convocatoria
            ''', datos)
        else:
            # SQLite usa INSERT OR REPLACE
            cursor.execute('''
                INSERT OR REPLACE INTO licitaciones 
                (id, codigo, nombre, fecha_publicacion, fecha_cierre, organismo, unidad, 
                 id_estado, estado, monto_disponible, moneda, monto_disponible_CLP, 
                 fecha_cambio, valor_cambio_moneda, cantidad_proveedores_cotizando, estado_convocatoria)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', datos)
        
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        print(f"Error BD: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()


def guardar_detalle_completo(codigo, ficha, historial=None, adjuntos=None):
    """
    Guarda los detalles completos de una licitación.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Guardar ficha detallada
        info_inst = ficha.get('informacion_institucion', {})
        
        placeholder = '%s' if USE_POSTGRES else '?'
        
        if USE_POSTGRES:
            cursor.execute(f'''
                INSERT INTO licitaciones_detalle 
                (codigo, detalle_id, nombre, descripcion, fecha_publicacion, fecha_cierre,
                 id_estado, estado, direccion_entrega, plazo_entrega, presupuesto_estimado,
                 moneda, multa_sancion, cantidad_proveedores_invitados, organismo_comprador,
                 rut_organismo_comprador, division, fecha_cierre_primer_llamado,
                 fecha_cierre_segundo_llamado, tipo_presupuesto, estado_convocatoria,
                 total_demandas, total_ofertas_recibidas, considera_requisitos_medioambientales,
                 considera_requisitos_impacto_social_economico, datos_json)
                VALUES ({', '.join([placeholder]*26)})
                ON CONFLICT (codigo) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    descripcion = EXCLUDED.descripcion
            ''', (
                codigo, ficha.get('id'), ficha.get('nombre'), ficha.get('descripcion'),
                ficha.get('fecha_publicacion'), ficha.get('fecha_cierre'),
                ficha.get('id_estado'), ficha.get('estado'),
                ficha.get('direccion_entrega'), ficha.get('plazo_entrega'),
                ficha.get('presupuesto_estimado'), ficha.get('moneda'),
                ficha.get('multa_sancion'), ficha.get('cantidad_proveedores_invitados'),
                info_inst.get('organismo_comprador'), info_inst.get('rut_organismo_comprador'),
                info_inst.get('division'), ficha.get('fecha_cierre_primer_llamado'),
                ficha.get('fecha_cierre_segundo_llamado'), ficha.get('tipo_presupuesto'),
                ficha.get('estado_convocatoria'), ficha.get('total_demandas'),
                ficha.get('total_ofertas_recibidas'),
                int(bool(ficha.get('considera_requisitos_medioambientales'))),
                int(bool(ficha.get('considera_requisitos_impacto_social_economico'))),
                json.dumps(ficha, ensure_ascii=False)
            ))
        else:
            cursor.execute(f'''
                INSERT OR REPLACE INTO licitaciones_detalle 
                (codigo, detalle_id, nombre, descripcion, fecha_publicacion, fecha_cierre,
                 id_estado, estado, direccion_entrega, plazo_entrega, presupuesto_estimado,
                 moneda, multa_sancion, cantidad_proveedores_invitados, organismo_comprador,
                 rut_organismo_comprador, division, fecha_cierre_primer_llamado,
                 fecha_cierre_segundo_llamado, tipo_presupuesto, estado_convocatoria,
                 total_demandas, total_ofertas_recibidas, considera_requisitos_medioambientales,
                 considera_requisitos_impacto_social_economico, datos_json)
                VALUES ({', '.join([placeholder]*26)})
            ''', (
                codigo, ficha.get('id'), ficha.get('nombre'), ficha.get('descripcion'),
                ficha.get('fecha_publicacion'), ficha.get('fecha_cierre'),
                ficha.get('id_estado'), ficha.get('estado'),
                ficha.get('direccion_entrega'), ficha.get('plazo_entrega'),
                ficha.get('presupuesto_estimado'), ficha.get('moneda'),
                ficha.get('multa_sancion'), ficha.get('cantidad_proveedores_invitados'),
                info_inst.get('organismo_comprador'), info_inst.get('rut_organismo_comprador'),
                info_inst.get('division'), ficha.get('fecha_cierre_primer_llamado'),
                ficha.get('fecha_cierre_segundo_llamado'), ficha.get('tipo_presupuesto'),
                ficha.get('estado_convocatoria'), ficha.get('total_demandas'),
                ficha.get('total_ofertas_recibidas'),
                int(bool(ficha.get('considera_requisitos_medioambientales'))),
                int(bool(ficha.get('considera_requisitos_impacto_social_economico'))),
                json.dumps(ficha, ensure_ascii=False)
            ))
        
        # Guardar productos
        productos = ficha.get('productos_solicitados', [])
        for prod in productos:
            cursor.execute(f'''
                INSERT INTO productos_solicitados 
                (codigo_licitacion, nombre, descripcion, cantidad, unidad_medida)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                codigo,
                prod.get('nombre'),
                prod.get('descripcion'),
                prod.get('cantidad'),
                prod.get('unidad_medida')
            ))
        
        # Guardar historial
        if historial:
            for item in historial:
                cursor.execute(f'''
                    INSERT INTO historial 
                    (codigo_licitacion, fecha, accion, usuario)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                ''', (
                    codigo,
                    item.get('fecha'),
                    item.get('accion'),
                    item.get('usuario')
                ))
        
        # Guardar adjuntos
        if adjuntos:
            for adj in adjuntos:
                cursor.execute(f'''
                    INSERT INTO adjuntos 
                    (codigo_licitacion, nombre_archivo, id_adjunto)
                    VALUES ({placeholder}, {placeholder}, {placeholder})
                ''', (
                    codigo,
                    adj.get('nombreArchivo'),
                    adj.get('id')
                ))
        
        # Marcar como detalle obtenido
        cursor.execute(f'''
            UPDATE licitaciones 
            SET detalle_obtenido = 1 
            WHERE codigo = {placeholder}
        ''', (codigo,))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error al guardar detalle: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def obtener_licitaciones_sin_detalle(limite=100):
    """
    Obtiene códigos de licitaciones que no tienen detalles.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Usamos parámetros para evitar inyección SQL
    if USE_POSTGRES:
        query = 'SELECT codigo FROM licitaciones WHERE detalle_obtenido = 0 LIMIT %s'
    else:
        query = 'SELECT codigo FROM licitaciones WHERE detalle_obtenido = 0 LIMIT ?'
    
    cursor.execute(query, (limite,))
    
    # En ambos casos devuelve una lista de tuplas
    resultados = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return resultados


def buscar_por_palabra(palabra, limite=10):
    """
    Busca licitaciones por palabra clave.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    patron = f"%{palabra}%"
    
    if USE_POSTGRES:
        query = '''
            SELECT codigo, nombre, organismo, fecha_cierre
            FROM licitaciones
            WHERE LOWER(nombre) LIKE LOWER(%s)
            OR LOWER(organismo) LIKE LOWER(%s)
            ORDER BY fecha_cierre DESC
            LIMIT %s
        '''
    else:
        query = '''
            SELECT codigo, nombre, organismo, fecha_cierre
            FROM licitaciones
            WHERE LOWER(nombre) LIKE LOWER(?)
            OR LOWER(organismo) LIKE LOWER(?)
            ORDER BY fecha_cierre DESC
            LIMIT ?
        '''
    
    cursor.execute(query, (patron, patron, limite))
    
    resultados = cursor.fetchall()
    conn.close()
    return resultados


if __name__ == "__main__":
    iniciar_db_extendida()
    print("Base de datos lista para usar")
