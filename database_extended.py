"""
Versión extendida de la base de datos que incluye tablas para:
- Licitaciones (tabla principal)
- Detalles de licitaciones
- Productos solicitados
- Historial de acciones
- Adjuntos
"""
import sqlite3
import json

DB_NAME = 'compra_agil.db'


def iniciar_db_extendida():
    """
    Crea todas las tablas necesarias para almacenar información completa
    de las licitaciones de Compra Ágil.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla principal de licitaciones (resumen)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licitaciones (
            id INTEGER PRIMARY KEY,
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
            valor_cambio_moneda INTEGER,
            cantidad_proveedores_cotizando INTEGER,
            estado_convocatoria INTEGER,
            detalle_obtenido INTEGER DEFAULT 0
        )
    ''')
    
    # Tabla de detalles completos de licitaciones
    cursor.execute('''
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos_solicitados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_licitacion TEXT,
            codigo_producto INTEGER,
            nombre TEXT,
            descripcion TEXT,
            cantidad REAL,
            unidad_medida TEXT,
            FOREIGN KEY (codigo_licitacion) REFERENCES licitaciones(codigo)
        )
    ''')
    
    # Tabla de historial
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_licitacion TEXT,
            id_registro_historial INTEGER,
            accion TEXT,
            usuario TEXT,
            organismo TEXT,
            unidad TEXT,
            fecha TEXT,
            FOREIGN KEY (codigo_licitacion) REFERENCES licitaciones(codigo)
        )
    ''')
    
    # Tabla de adjuntos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS adjuntos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_licitacion TEXT,
            id_adjunto TEXT,
            nombre_archivo TEXT,
            FOREIGN KEY (codigo_licitacion) REFERENCES licitaciones(codigo)
        )
    ''')
    
    # Crear índices para mejorar búsquedas
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_licitaciones_codigo ON licitaciones(codigo)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_licitaciones_fecha ON licitaciones(fecha_publicacion)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_productos_codigo ON productos_solicitados(codigo_licitacion)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_historial_codigo ON historial(codigo_licitacion)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_adjuntos_codigo ON adjuntos(codigo_licitacion)')
    
    conn.commit()
    conn.close()
    print("✅ Base de datos extendida creada/verificada")


def guardar_licitacion_basica(datos):
    """
    Guarda los datos básicos de una licitación (desde el listado).
    
    Args:
        datos: Tupla con todos los campos de la licitación desde el JSON de la API
    
    Returns:
        int: 1 si se guardó, 0 si ya existía
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO licitaciones 
            (id, codigo, nombre, fecha_publicacion, fecha_cierre, organismo, unidad, 
             id_estado, estado, monto_disponible, moneda, monto_disponible_CLP, 
             fecha_cambio, valor_cambio_moneda, cantidad_proveedores_cotizando, estado_convocatoria)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', datos)
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        print(f"Error BD: {e}")
        return 0
    finally:
        conn.close()


def guardar_detalle_completo(codigo, ficha, historial=None, adjuntos=None):
    """
    Guarda los detalles completos de una licitación.
    
    Args:
        codigo: Código de la licitación
        ficha: Diccionario con los datos de la ficha
        historial: Lista de registros del historial (opcional)
        adjuntos: Lista de archivos adjuntos (opcional)
    
    Returns:
        bool: True si se guardó exitosamente
    """
    if not ficha:
        return False
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Guardar detalle de la licitación
        info_inst = ficha.get('informacion_institucion', {})
        
        cursor.execute('''
            INSERT OR REPLACE INTO licitaciones_detalle 
            (codigo, detalle_id, nombre, descripcion, fecha_publicacion, fecha_cierre,
             id_estado, estado, direccion_entrega, plazo_entrega, presupuesto_estimado,
             moneda, multa_sancion, cantidad_proveedores_invitados, organismo_comprador,
             rut_organismo_comprador, division, fecha_cierre_primer_llamado,
             fecha_cierre_segundo_llamado, tipo_presupuesto, estado_convocatoria,
             total_demandas, total_ofertas_recibidas, considera_requisitos_medioambientales,
             considera_requisitos_impacto_social_economico, datos_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            codigo,
            ficha.get('detalle_id'),
            ficha.get('nombre'),
            ficha.get('descripcion'),
            ficha.get('fecha_publicacion'),
            ficha.get('fecha_cierre'),
            ficha.get('id_estado'),
            ficha.get('estado'),
            ficha.get('direccion_entrega'),
            ficha.get('plazo_entrega'),
            ficha.get('presupuesto_estimado'),
            ficha.get('moneda'),
            ficha.get('multa_sancion'),
            ficha.get('cantidad_proveedores_invitados'),
            info_inst.get('organismo_comprador'),
            info_inst.get('rut_organismo_comprador'),
            info_inst.get('division'),
            ficha.get('fecha_cierre_primer_llamado'),
            ficha.get('fecha_cierre_segundo_llamado'),
            ficha.get('tipo_presupuesto'),
            ficha.get('estado_convocatoria'),
            ficha.get('total_demandas'),
            ficha.get('total_ofertas_recibidas'),
            1 if ficha.get('considera_requisitos_medioambientales') else 0,
            1 if ficha.get('considera_requisitos_impacto_social_economico') else 0,
            json.dumps(ficha, ensure_ascii=False)
        ))
        
        # Guardar productos solicitados
        productos = ficha.get('productos_solicitados', [])
        if productos:
            # Eliminar productos anteriores
            cursor.execute('DELETE FROM productos_solicitados WHERE codigo_licitacion = ?', (codigo,))
            
            for producto in productos:
                cursor.execute('''
                    INSERT INTO productos_solicitados 
                    (codigo_licitacion, codigo_producto, nombre, descripcion, cantidad, unidad_medida)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    codigo,
                    producto.get('codigo_producto'),
                    producto.get('nombre'),
                    producto.get('descripcion'),
                    producto.get('cantidad'),
                    producto.get('unidad_medida')
                ))
        
        # Guardar historial
        if historial:
            # Eliminar historial anterior
            cursor.execute('DELETE FROM historial WHERE codigo_licitacion = ?', (codigo,))
            
            for registro in historial:
                cursor.execute('''
                    INSERT INTO historial 
                    (codigo_licitacion, id_registro_historial, accion, usuario, organismo, unidad, fecha)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    codigo,
                    registro.get('id_registro_historial'),
                    registro.get('accion'),
                    registro.get('usuario'),
                    registro.get('organismo'),
                    registro.get('unidad'),
                    registro.get('fecha')
                ))
        
        # Guardar adjuntos
        if adjuntos:
            # Eliminar adjuntos anteriores
            cursor.execute('DELETE FROM adjuntos WHERE codigo_licitacion = ?', (codigo,))
            
            for adjunto in adjuntos:
                cursor.execute('''
                    INSERT INTO adjuntos 
                    (codigo_licitacion, id_adjunto, nombre_archivo)
                    VALUES (?, ?, ?)
                ''', (
                    codigo,
                    adjunto.get('id'),
                    adjunto.get('nombreArchivo')
                ))
        
        # Marcar que se obtuvo el detalle
        cursor.execute('''
            UPDATE licitaciones 
            SET detalle_obtenido = 1 
            WHERE codigo = ?
        ''', (codigo,))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar detalle de {codigo}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def buscar_por_palabra(palabra_clave):
    """
    Busca licitaciones por palabra clave en nombre u organismo.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = f"%{palabra_clave}%"
    cursor.execute('''
        SELECT codigo, nombre, organismo, fecha_cierre 
        FROM licitaciones 
        WHERE nombre LIKE ? OR organismo LIKE ?
        ORDER BY fecha_cierre DESC LIMIT 10
    ''', (query, query))
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def obtener_licitaciones_sin_detalle(limite=100):
    """
    Obtiene licitaciones que aún no tienen detalles completos.
    
    Args:
        limite: Número máximo de licitaciones a retornar
    
    Returns:
        list: Lista de códigos de licitaciones sin detalle
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT codigo 
        FROM licitaciones 
        WHERE detalle_obtenido = 0
        LIMIT ?
    ''', (limite,))
    resultados = [row[0] for row in cursor.fetchall()]
    conn.close()
    return resultados


if __name__ == "__main__":
    # Inicializar base de datos extendida
    iniciar_db_extendida()
    print("Base de datos lista para usar")
