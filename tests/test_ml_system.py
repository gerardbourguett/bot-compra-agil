"""
Script de Testing para Sistema ML
Prueba todos los módulos implementados
"""
import sys
import os

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

print("=" * 70)
print("TESTING SISTEMA ML - COMPRA ÁGIL")
print("=" * 70)
print()

# Test 1: Importaciones
print("📦 TEST 1: Verificando importaciones...")
try:
    import database_extended as db
    print("  ✅ database_extended")
    
    import ml_precio_optimo
    print("  ✅ ml_precio_optimo")
    
    import rag_historico
    print("  ✅ rag_historico")
    
    import gemini_ai
    print("  ✅ gemini_ai")
    
    import bot_ml_commands
    print("  ✅ bot_ml_commands")
    
    print("  ✅ TODAS LAS IMPORTACIONES OK\n")
except ImportError as e:
    print(f"  ❌ ERROR: {e}")
    print("  💡 Ejecuta: pip install -r requirements.txt\n")
    sys.exit(1)

# Test 2: Conexión a Base de Datos
print("🗄️  TEST 2: Verificando conexión a base de datos...")
try:
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Verificar tabla historico_licitaciones
    if db.USE_POSTGRES:
        cursor.execute("SELECT COUNT(*) FROM historico_licitaciones")
    else:
        cursor.execute("SELECT COUNT(*) FROM historico_licitaciones")
    
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"  ✅ Conexión exitosa")
    print(f"  📊 Registros históricos: {count:,}")
    
    if count == 0:
        print("  ⚠️  ADVERTENCIA: No hay datos históricos")
        print("  💡 Ejecuta: python src/importar_historico.py")
    elif count < 1000:
        print("  ⚠️  ADVERTENCIA: Pocos datos históricos (mínimo recomendado: 10,000)")
    else:
        print("  ✅ Cantidad de datos suficiente\n")
    
except Exception as e:
    print(f"  ❌ ERROR: {e}")
    print("  💡 Verifica DATABASE_URL en .env\n")
    sys.exit(1)

# Test 3: Sistema de Recomendación de Precio
print("💰 TEST 3: Probando recomendación de precio...")
try:
    resultado = ml_precio_optimo.calcular_precio_optimo(
        producto="laptop",
        cantidad=10,
        solo_ganadores=True
    )
    
    if resultado['success']:
        print(f"  ✅ Recomendación generada exitosamente")
        print(f"  📊 Registros analizados: {resultado['estadisticas']['n_registros']}")
        print(f"  💵 Precio recomendado: ${resultado['precio_total']['recomendado']:,.0f}")
        print(f"  📈 Confianza: {resultado['confianza']*100:.0f}%")
        
        if resultado['confianza'] < 0.5:
            print(f"  ⚠️  Confianza baja - pocos datos para este producto")
    else:
        print(f"  ⚠️  No hay datos suficientes: {resultado.get('error')}")
    
    print()
    
except Exception as e:
    print(f"  ❌ ERROR: {e}\n")

# Test 4: Sistema RAG
print("🔍 TEST 4: Probando sistema RAG...")
try:
    casos = rag_historico.buscar_casos_similares(
        nombre_licitacion="Adquisición de computadores portátiles",
        limite=5
    )
    
    if casos:
        print(f"  ✅ Casos similares encontrados: {len(casos)}")
        print(f"  📊 Top caso - Similitud: {casos[0]['similitud']:.1f}%")
        print(f"  💰 Monto: ${casos[0]['monto']:,}")
        print(f"  {'✅' if casos[0]['es_ganador'] else '❌'} Ganador: {casos[0]['es_ganador']}")
    else:
        print(f"  ⚠️  No se encontraron casos similares")
    
    print()
    
except Exception as e:
    print(f"  ❌ ERROR: {e}\n")

# Test 5: Enriquecimiento de Análisis
print("🤖 TEST 5: Probando enriquecimiento de análisis...")
try:
    datos = rag_historico.enriquecer_analisis_licitacion(
        nombre_licitacion="Adquisición de equipos computacionales",
        monto_estimado=5000000
    )
    
    if datos['tiene_datos']:
        print(f"  ✅ Análisis enriquecido generado")
        print(f"  📊 Casos encontrados: {datos['n_casos_encontrados']}")
        
        if datos.get('recomendacion_precio'):
            precio = datos['recomendacion_precio']
            print(f"  💰 Precio promedio ganadores: ${precio['precio_promedio']:,}")
            print(f"  📈 Rango: ${precio['rango_min']:,} - ${precio['rango_max']:,}")
    else:
        print(f"  ⚠️  {datos['mensaje']}")
    
    print()
    
except Exception as e:
    print(f"  ❌ ERROR: {e}\n")

# Test 6: Análisis de Competencia
print("🎯 TEST 6: Probando análisis de competencia...")
try:
    resultado = ml_precio_optimo.analizar_competencia_precios(
        producto="laptop"
    )
    
    if resultado['success']:
        print(f"  ✅ Análisis de competencia generado")
        print(f"  👥 Total competidores: {resultado['total_competidores']}")
        
        if resultado['top_competidores']:
            top = list(resultado['top_competidores'].items())[0]
            print(f"  🏆 Top competidor: {top[0][:50]}")
            print(f"  📊 Ofertas: {top[1]['monto_total_count']:.0f}")
            print(f"  ✅ Tasa éxito: {top[1]['tasa_exito']:.1f}%")
    else:
        print(f"  ⚠️  {resultado.get('error')}")
    
    print()
    
except Exception as e:
    print(f"  ❌ ERROR: {e}\n")

# Test 7: Gemini AI (requiere API key)
print("🧠 TEST 7: Verificando configuración Gemini AI...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('GEMINI_API_KEY')
    
    if api_key:
        print(f"  ✅ GEMINI_API_KEY configurada")
        print(f"  🔑 Key: {api_key[:8]}...{api_key[-4:]}")
        
        # No hacemos llamada real para no gastar quota
        print(f"  ℹ️  Integración con RAG lista")
    else:
        print(f"  ⚠️  GEMINI_API_KEY no encontrada en .env")
        print(f"  💡 El análisis IA no funcionará sin esta key")
    
    print()
    
except Exception as e:
    print(f"  ❌ ERROR: {e}\n")

# Resumen Final
print("=" * 70)
print("RESUMEN DE TESTING")
print("=" * 70)

tests_passed = 0
tests_total = 7

# Contar tests pasados (simplificado)
print("\n✅ Tests pasados: Revisa los resultados arriba")
print("⚠️  Si hay advertencias, revisa las recomendaciones")
print("\n💡 Siguiente paso: Ejecutar el bot y probar comandos ML")
print("   Ejemplo: /precio_optimo laptop 10")
print("\n" + "=" * 70)
