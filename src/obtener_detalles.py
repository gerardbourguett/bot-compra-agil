"""
Script para obtener detalles de licitaciones que ya están en la base de datos
pero no tienen detalles completos.
"""
import api_client
import database_extended as db
import time

def obtener_detalles(max_licitaciones=None, pausa_entre_requests=0.5):
    """
    Obtiene los detalles completos de licitaciones que aún no los tienen.
    
    Args:
        max_licitaciones: Número máximo de licitaciones a procesar (None = todas)
        pausa_entre_requests: Segundos de pausa entre cada licitación
    """
    print("\n🔍 Iniciando obtención de detalles...")
    
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
    
    print(f"\n{'='*60}")
    print(f"✅ Proceso de detalles terminado")
    print(f"{'='*60}")
    print(f"📊 Procesadas exitosamente: {procesadas}")
    print(f"❌ Errores: {errores}")
    print(f"📈 Tasa de éxito: {(procesadas/len(codigos)*100):.1f}%")
    
    return procesadas


if __name__ == "__main__":
    # Opciones de uso:
    
    # Opción 1: Procesar solo 50 licitaciones (para prueba)
    # obtener_detalles(max_licitaciones=50)
    
    # Opción 2: Procesar 500 licitaciones
    # obtener_detalles(max_licitaciones=500)
    
    # Opción 3: Procesar TODAS las licitaciones pendientes
    obtener_detalles(max_licitaciones=None)
    
    # Nota: Puedes ajustar la pausa entre requests si es necesario
    # obtener_detalles(max_licitaciones=100, pausa_entre_requests=1.0)
