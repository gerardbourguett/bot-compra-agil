"""
Script de verificación rápida del setup
Ejecuta este script después de setup_dev.bat
"""
import sys
import os

print("=" * 70)
print("COMPRAAGIL - Verificación de Setup")
print("=" * 70)
print()

# Test 1: Versión de Python
print("✓ Test 1: Versión de Python")
print(f"  Python {sys.version}")
if sys.version_info < (3, 11):
    print("  ⚠️  ADVERTENCIA: Se recomienda Python 3.11+")
else:
    print("  ✅ Versión correcta")
print()

# Test 2: Variables de entorno
print("✓ Test 2: Variables de entorno")
env_file = '.env'
if os.path.exists(env_file):
    print(f"  ✅ Archivo {env_file} existe")
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['TELEGRAM_TOKEN', 'GEMINI_API_KEY']
    optional_vars = ['DATABASE_URL', 'REDIS_URL', 'API_SECRET_KEY']
    
    for var in required_vars:
        value = os.getenv(var)
        if value and value != 'tu_token_aqui' and value != 'tu_api_key_gemini_aqui':
            print(f"  ✅ {var} configurado")
        else:
            print(f"  ⚠️  {var} NO configurado (requerido)")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var} configurado")
        else:
            print(f"  ℹ️  {var} no configurado (opcional)")
else:
    print(f"  ❌ Archivo {env_file} NO existe")
    print(f"  💡 Copia .env.dev a .env y configura tus credenciales")
print()

# Test 3: Importaciones críticas
print("✓ Test 3: Dependencias instaladas")
dependencies = [
    ('fastapi', 'FastAPI'),
    ('uvicorn', 'Uvicorn'),
    ('telegram', 'python-telegram-bot'),
    ('dotenv', 'python-dotenv'),
    ('pandas', 'pandas'),
    ('redis', 'redis'),
]

missing = []
for module, name in dependencies:
    try:
        __import__(module)
        print(f"  ✅ {name}")
    except ImportError:
        print(f"  ❌ {name} - NO instalado")
        missing.append(name)

if missing:
    print()
    print("  💡 Instala dependencias faltantes con:")
    print("     pip install -r requirements.txt")
print()

# Test 4: Módulos del proyecto
print("✓ Test 4: Módulos del proyecto")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

project_modules = [
    'database_extended',
    'auth_service',
    'subscriptions',
    'redis_cache',
]

for module in project_modules:
    try:
        __import__(module)
        print(f"  ✅ {module}")
    except Exception as e:
        print(f"  ⚠️  {module} - {str(e)[:50]}")
print()

# Test 5: Base de datos
print("✓ Test 5: Conexión a base de datos")
try:
    import database_extended as db
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Verificar tipo de BD
    if db.USE_POSTGRES:
        print("  ✅ PostgreSQL conectado")
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"     {version[:50]}...")
    else:
        print("  ✅ SQLite (modo desarrollo)")
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"     SQLite {version}")
    
    conn.close()
    
except Exception as e:
    print(f"  ⚠️  Error de conexión: {str(e)[:60]}")
    print("  💡 Asegúrate de tener PostgreSQL corriendo o usa SQLite")
print()

# Test 6: Migraciones
print("✓ Test 6: Tablas de base de datos")
try:
    import database_extended as db
    conn = db.get_connection()
    cursor = conn.cursor()
    
    tables_to_check = ['subscriptions', 'usage_tracking', 'api_keys']
    
    for table in tables_to_check:
        try:
            if db.USE_POSTGRES:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name = '{table}'
                """)
            else:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM sqlite_master 
                    WHERE type='table' AND name='{table}'
                """)
            
            exists = cursor.fetchone()[0] > 0
            if exists:
                print(f"  ✅ Tabla {table} existe")
            else:
                print(f"  ⚠️  Tabla {table} NO existe")
                print(f"     Ejecuta: python scripts/migrate_subscriptions.py")
                print(f"     Ejecuta: python scripts/migrate_api_keys.py")
        except Exception as e:
            print(f"  ⚠️  Error verificando {table}: {str(e)[:40]}")
    
    conn.close()
    
except Exception as e:
    print(f"  ⚠️  No se pudo verificar: {str(e)[:60]}")
print()

print("=" * 70)
print("RESUMEN")
print("=" * 70)
print()
print("Si todos los tests pasaron (✅), estás listo para:")
print("  1. Ejecutar migraciones si faltan tablas")
print("  2. Iniciar la API: python api_backend_v3.py")
print("  3. Probar autenticación: curl http://localhost:8000/health")
print()
print("Si hay warnings (⚠️), revisa las sugerencias arriba.")
print()
