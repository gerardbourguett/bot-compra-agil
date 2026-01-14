"""
Script para obtener detalles de licitaciones que ya están en la base de datos
pero no tienen detalles completos.
"""
import api_client
import database_extended as db
import time
import logging

# Logger para este módulo
logger = logging.getLogger('compra_agil.obtener_detalles')

def obtener_detalles(max_licitaciones=None, pausa_entre_requests=0.5):
    """
    Obtiene los detalles completos de licitaciones que aún no los tienen.

    Args:
        max_licitaciones: Número máximo de licitaciones a procesar (None = todas)
        pausa_entre_requests: Segundos de pausa entre cada licitación
    """
    logger.info("Iniciando obtención de detalles...")

    # Asegurar que la base de datos esté inicializada
    db.iniciar_db_extendida()

    # Obtener licitaciones sin detalle
    limite = max_licitaciones if max_licitaciones else 10000
    codigos = db.obtener_licitaciones_sin_detalle(limite)
    
    if not codigos:
        logger.info("No hay licitaciones pendientes de procesar")
        return 0
    
    logger.info(f"Encontradas {len(codigos)} licitaciones sin detalles")
    
    procesadas = 0
    errores = 0
    
    for i, codigo in enumerate(codigos, 1):
        logger.info(f"[{i}/{len(codigos)}] Procesando {codigo}...")
        
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
                    
                    # Mostrar resumen
                    productos = len(detalle['ficha'].get('productos_solicitados', []))
                    historial_count = len(detalle['historial']) if detalle['historial'] else 0
                    adjuntos_count = len(detalle['adjuntos']) if detalle['adjuntos'] else 0
                    
                    logger.info(f"  Guardado: {productos} productos, {historial_count} historial, {adjuntos_count} adjuntos")
                else:
                    errores += 1
                    logger.error(f"  Error al guardar {codigo}")
            else:
                errores += 1
                logger.error(f"  No se pudo obtener la ficha de {codigo}")
            
            # Pausa entre requests
            time.sleep(pausa_entre_requests)
            
        except Exception as e:
            errores += 1
            logger.error(f"  Excepción procesando {codigo}: {e}")
    
    logger.info("=" * 60)
    logger.info("Proceso de detalles terminado")
    logger.info("=" * 60)
    logger.info(f"Procesadas exitosamente: {procesadas}")
    logger.info(f"Errores: {errores}")
    logger.info(f"Tasa de éxito: {(procesadas/len(codigos)*100):.1f}%")
    
    # Registrar timestamp de ejecución
    try:
        import database_bot as db_bot
        from datetime import datetime
        db_bot.update_system_status('last_scrape_details', datetime.now().isoformat())
        logger.info("Timestamp actualizado en system_status")
    except Exception as e:
        logger.warning(f"No se pudo actualizar timestamp: {e}")
    
    return procesadas
    
    return procesadas


if __name__ == "__main__":
    # Configurar logging para ejecución standalone
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    # Opciones de uso:
    
    # Opción 1: Procesar solo 50 licitaciones (para prueba)
    # obtener_detalles(max_licitaciones=50)
    
    # Opción 2: Procesar 500 licitaciones
    # obtener_detalles(max_licitaciones=500)
    
    # Opción 3: Procesar TODAS las licitaciones pendientes
    obtener_detalles(max_licitaciones=None)
    
    # Nota: Puedes ajustar la pausa entre requests si es necesario
    # obtener_detalles(max_licitaciones=100, pausa_entre_requests=1.0)
