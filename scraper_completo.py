"""
Scraper completo que obtiene tanto el listado como los detalles de cada licitación.
Puede ejecutarse en dos modos:
1. Modo listado: Solo obtiene el listado de licitaciones
2. Modo completo: Obtiene listado + detalles de cada licitación
"""
import api_client
import database_extended as db
from datetime import datetime, timedelta
import time


def scraper_listado(dias_atras=30, max_paginas=None):
    """
    Obtiene solo el listado de licitaciones sin detalles.
    
    Args:
        dias_atras: Número de días hacia atrás para buscar
        max_paginas: Número máximo de páginas a procesar (None = todas)
    
    Returns:
        int: Número de licitaciones nuevas guardadas
    """
    print("🕷️ Iniciando Scraper - Modo Listado...")
    db.iniciar_db_extendida()
    
    # Calcular fechas
    fecha_hasta = datetime.now()
    fecha_desde = fecha_hasta - timedelta(days=dias_atras)
    
    date_from = fecha_desde.strftime("%Y-%m-%d")
    date_to = fecha_hasta.strftime("%Y-%m-%d")
    
    print(f"📅 Buscando licitaciones desde {date_from} hasta {date_to}")
    
    nuevos_total = 0
    page_number = 1
    
    while True:
        if max_paginas and page_number > max_paginas:
            print(f"✅ Alcanzado el límite de {max_paginas} páginas")
            break
        
        print(f"\n📄 Procesando página {page_number}...")
        
        data = api_client.obtener_licitaciones(date_from, date_to, status=2, page_number=page_number)
        
        if not data or data.get('success') != 'OK':
            print("❌ Error en la respuesta de la API")
            break
        
        payload = data.get('payload', {})
        items = payload.get('resultados', [])
        
        if not items:
            print("✅ No hay más resultados")
            break
        
        if page_number == 1:
            total_resultados = payload.get('resultCount', 0)
            total_paginas = payload.get('pageCount', 0)
            print(f"📊 Total de licitaciones encontradas: {total_resultados}")
            print(f"📄 Total de páginas: {total_paginas}")
        
        print(f"   Procesando {len(items)} licitaciones...")
        
        for item in items:
            datos_tupla = (
                item.get('id'),
                item.get('codigo'),
                item.get('nombre'),
                item.get('fecha_publicacion'),
                item.get('fecha_cierre'),
                item.get('organismo'),
                item.get('unidad'),
                item.get('id_estado'),
                item.get('estado'),
                item.get('monto_disponible'),
                item.get('moneda'),
                item.get('monto_disponible_CLP'),
                item.get('fecha_cambio'),
                item.get('valor_cambio_moneda'),
                item.get('cantidad_proveedores_cotizando'),
                item.get('estado_convocatoria')
            )
            nuevos_total += db.guardar_licitacion_basica(datos_tupla)
        
        page_count = payload.get('pageCount', 0)
        if page_number >= page_count:
            print(f"✅ Todas las páginas procesadas ({page_count} páginas)")
            break
        
        page_number += 1
        time.sleep(0.5)
    
    print(f"\n✅ Proceso terminado. Se guardaron {nuevos_total} licitaciones nuevas.")
    return nuevos_total


def scraper_detalles(max_licitaciones=None, pausa_entre_requests=0.5):
    """
    Obtiene los detalles completos de licitaciones que aún no los tienen.
    
    Args:
        max_licitaciones: Número máximo de licitaciones a procesar (None = todas)
        pausa_entre_requests: Segundos de pausa entre cada licitación
    
    Returns:
        int: Número de licitaciones procesadas
    """
    print("\n🔍 Iniciando Scraper - Modo Detalles...")
    
    # Obtener licitaciones sin detalle
    limite = max_licitaciones if max_licitaciones else 10000
    codigos = db.obtener_licitaciones_sin_detalle(limite)
    
    if not codigos:
        print("✅ No hay licitaciones pendientes de procesar")
        return 0
    
    print(f"📋 Encontradas {len(codigos)} licitaciones sin detalles")
    
    procesadas = 0
    errores = 0
    
    for i, codigo in enumerate(codigos, 1):
        print(f"\n[{i}/{len(codigos)}] Procesando {codigo}...")
        
        try:
            # Obtener todos los detalles
            detalle = api_client.obtener_detalle_completo(
                codigo, 
                incluir_historial=True, 
                incluir_adjuntos=True
            )
            
            # Guardar en base de datos
            if detalle['ficha']:
                exito = db.guardar_detalle_completo(
                    codigo,
                    detalle['ficha'],
                    detalle['historial'],
                    detalle['adjuntos']
                )
                
                if exito:
                    procesadas += 1
                    print(f"   ✅ Guardado exitosamente")
                    
                    # Mostrar resumen
                    productos = len(detalle['ficha'].get('productos_solicitados', []))
                    historial_count = len(detalle['historial']) if detalle['historial'] else 0
                    adjuntos_count = len(detalle['adjuntos']) if detalle['adjuntos'] else 0
                    
                    print(f"      📦 Productos: {productos}")
                    print(f"      📜 Historial: {historial_count} registros")
                    print(f"      📎 Adjuntos: {adjuntos_count} archivos")
                else:
                    errores += 1
                    print(f"   ❌ Error al guardar")
            else:
                errores += 1
                print(f"   ❌ No se pudo obtener la ficha")
            
            # Pausa entre requests
            time.sleep(pausa_entre_requests)
            
        except Exception as e:
            errores += 1
            print(f"   ❌ Excepción: {e}")
    
    print(f"\n✅ Proceso de detalles terminado")
    print(f"   📊 Procesadas: {procesadas}")
    print(f"   ❌ Errores: {errores}")
    
    return procesadas


def scraper_completo(dias_atras=30, max_paginas_listado=None, max_detalles=None):
    """
    Ejecuta el scraper completo: primero obtiene el listado y luego los detalles.
    
    Args:
        dias_atras: Días hacia atrás para el listado
        max_paginas_listado: Límite de páginas para el listado
        max_detalles: Límite de licitaciones para obtener detalles
    """
    print("=" * 70)
    print("🚀 SCRAPER COMPLETO DE COMPRA ÁGIL")
    print("=" * 70)
    
    # Fase 1: Obtener listado
    print("\n📋 FASE 1: Obteniendo listado de licitaciones")
    print("-" * 70)
    nuevas = scraper_listado(dias_atras, max_paginas_listado)
    
    # Fase 2: Obtener detalles
    print("\n" + "=" * 70)
    print("📋 FASE 2: Obteniendo detalles de licitaciones")
    print("-" * 70)
    procesadas = scraper_detalles(max_detalles)
    
    print("\n" + "=" * 70)
    print("✅ PROCESO COMPLETO FINALIZADO")
    print("=" * 70)
    print(f"📊 Licitaciones nuevas en listado: {nuevas}")
    print(f"📊 Licitaciones con detalles obtenidos: {procesadas}")


if __name__ == "__main__":
    # Ejemplo 1: Solo obtener listado de los últimos 7 días
    # scraper_listado(dias_atras=7)
    
    # Ejemplo 2: Solo obtener detalles de licitaciones pendientes (máximo 50)
    # scraper_detalles(max_licitaciones=50)
    
    # Ejemplo 3: Proceso completo - listado + detalles
    # Para pruebas, limitar a 2 páginas de listado y 10 detalles
    scraper_completo(dias_atras=30, max_paginas_listado=2, max_detalles=10)
    
    # Para producción (sin límites):
    # scraper_completo(dias_atras=30)
