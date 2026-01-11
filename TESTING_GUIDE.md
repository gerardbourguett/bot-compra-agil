# 🧪 Guía de Testing - CompraAgil

Esta guía te ayudará a probar todos los cambios implementados en **Semana 1**.

---

## 📋 Pre-requisitos

### 1. Instalar Python 3.11

**Windows:**
1. Descarga: https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
2. Ejecuta el instalador
3. ✅ **IMPORTANTE:** Marca "Add Python 3.11 to PATH"
4. Clic en "Install Now"
5. Reinicia la terminal

**Verificar:**
```bash
python --version
# Debe mostrar: Python 3.11.x
```

---

## 🚀 Setup del Proyecto

### Opción A: Setup Automático (Recomendado)

```bash
# Ejecuta el script de setup
setup_dev.bat

# Esto hará:
# - Crear entorno virtual (.venv)
# - Instalar todas las dependencias
# - Actualizar pip
```

### Opción B: Setup Manual

```bash
# 1. Crear entorno virtual
python -m venv .venv

# 2. Activar entorno virtual
.venv\Scripts\activate

# 3. Actualizar pip
python -m pip install --upgrade pip

# 4. Instalar dependencias
pip install -r requirements.txt
```

---

## ⚙️ Configuración

### 1. Crear archivo .env

```bash
# Copiar plantilla
copy .env.dev .env

# Editar con tus credenciales
notepad .env
```

### 2. Configurar variables mínimas

Para testing básico, solo necesitas:

```env
# Opcional para pruebas sin Telegram
TELEGRAM_TOKEN=

# Opcional para pruebas sin IA
GEMINI_API_KEY=

# SQLite para desarrollo (más fácil)
DATABASE_URL=

# Secret para API keys
API_SECRET_KEY=dev-secret-testing-abc123
```

---

## 🧪 Verificar Setup

```bash
# Ejecutar script de verificación
python test_setup.py
```

**Salida esperada:**
```
✓ Test 1: Versión de Python
  ✅ Python 3.11.x
  
✓ Test 2: Variables de entorno
  ✅ Archivo .env existe
  
✓ Test 3: Dependencias instaladas
  ✅ FastAPI
  ✅ Uvicorn
  ✅ pandas
  ...
  
✓ Test 4: Módulos del proyecto
  ✅ database_extended
  ✅ auth_service
  ...
  
✓ Test 5: Conexión a base de datos
  ✅ SQLite (modo desarrollo)
  
✓ Test 6: Tablas de base de datos
  ⚠️  Tablas no existen (normal en primera ejecución)
```

---

## 🗄️ Ejecutar Migraciones

```bash
# 1. Migración de suscripciones
python scripts/migrate_subscriptions.py

# Salida esperada:
# ============================================================
# MIGRACIÓN: Sistema de Suscripciones
# ============================================================
# 
# 📋 Creando tabla: subscriptions...
# ✅ Tabla subscriptions creada
# ...
# ✅ MIGRACIÓN COMPLETADA EXITOSAMENTE

# 2. Migración de API keys
python scripts/migrate_api_keys.py

# Salida esperada:
# ============================================================
# MIGRACIÓN: Tabla de API Keys
# ============================================================
# 
# 📋 Creando tabla: api_keys...
# ✅ Tabla api_keys creada
# ...
# ✅ MIGRACIÓN COMPLETADA EXITOSAMENTE
```

---

## 🔧 Testing de Bugs Corregidos

### Test 1: SQL Injection (CORREGIDO ✅)

**Antes:** SQL injection posible
**Ahora:** Parámetros seguros

```bash
# Iniciar API
python api_backend_v3.py

# En otra terminal, intentar SQL injection (debe fallar):
curl "http://localhost:8000/api/v3/licitaciones/?organismo=test' OR '1'='1"

# Debe retornar resultados normales sin ejecutar el injection
```

### Test 2: Bug RAG `top_k` (CORREGIDO ✅)

**Antes:** Crash con `NameError: name 'top_k' is not defined`
**Ahora:** Funciona correctamente

```bash
# Test en Python
python -c "
import sys
sys.path.insert(0, 'src')
import rag_historico
result = rag_historico.buscar_casos_similares('laptop', limite=5)
print(f'✅ RAG funciona: {len(result)} casos encontrados')
"
```

### Test 3: Import `filtros` (CORREGIDO ✅)

```bash
# Test de import
python -c "
import sys
sys.path.insert(0, 'src')
import bot_inteligente
print('✅ Import de filtros OK')
"
```

### Test 4: Credenciales en .env (CORREGIDO ✅)

```bash
# Verificar que no hay credenciales hardcodeadas
grep -r "redis://64" src/
# Debe retornar vacío

grep -r "e93089e4-437c" src/*.py
# Debe retornar vacío o solo comentarios
```

---

## 🔐 Testing de Autenticación API

### 1. Iniciar la API

```bash
python api_backend_v3.py
```

**Salida esperada:**
```
================================================================================
🚀 CompraÁgil API v3.0 - VERSIÓN COMPLETA
================================================================================

📊 Características:
  ✅ Endpoints completos para todas las tablas
  ✅ Paginación automática
  ✅ Filtros avanzados
  ✅ Cache con Redis (opcional)
  ✅ Prompts dinámicos integrados
  ✅ Sistema de autenticación con API keys

🔗 URLs:
  📚 Documentación: http://localhost:8000/api/docs
  🔄 Health check: http://localhost:8000/health

INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Test Health Check

```bash
curl http://localhost:8000/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-11T20:00:00",
  "database": "connected",
  "redis": "unavailable"
}
```

### 3. Test Sin Autenticación (Endpoints Públicos)

```bash
# Listar licitaciones (sin auth)
curl http://localhost:8000/api/v3/licitaciones/?limit=5

# Stats generales (sin auth)
curl http://localhost:8000/api/v3/stats
```

### 4. Test Generar API Key

**Nota:** Requiere tier PROFESIONAL en la BD.

Primero, crear usuario PROFESIONAL en BD:

```bash
python -c "
import sys
sys.path.insert(0, 'src')
import database_extended as db
import subscriptions

# Crear usuario de prueba
conn = db.get_connection()
cursor = conn.cursor()

placeholder = '%s' if db.USE_POSTGRES else '?'
cursor.execute(f'''
    INSERT INTO subscriptions (user_id, tier, status)
    VALUES ({placeholder}, {placeholder}, {placeholder})
    ON CONFLICT (user_id) DO UPDATE SET tier = 'profesional'
''', (999999, 'profesional', 'active'))

conn.commit()
conn.close()
print('✅ Usuario de prueba creado (ID: 999999, tier: PROFESIONAL)')
"
```

Luego, generar API key:

```bash
curl -X POST http://localhost:8000/api/v3/auth/generate-key \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 999999,
    "nombre": "Test API Key"
  }'
```

**Respuesta esperada:**
```json
{
  "success": true,
  "message": "⚠️ IMPORTANTE: Guarda esta API key. No se volverá a mostrar.",
  "api_key": "abc123...xyz789",
  "nombre": "Test API Key",
  "created_at": "2026-01-11T20:00:00",
  "tier": "profesional"
}
```

**⚠️ IMPORTANTE:** Copia el `api_key` retornado!

### 5. Test con API Key

```bash
# Guardar tu API key
set API_KEY=abc123...xyz789

# Test validación
curl -H "X-API-Key: %API_KEY%" \
  http://localhost:8000/api/v3/auth/validate

# Test endpoint ML con autenticación
curl -X POST http://localhost:8000/api/v3/ml/precio \
  -H "X-API-Key: %API_KEY%" \
  -H "Content-Type: application/json" \
  -d '{
    "producto": "laptop",
    "cantidad": 10,
    "solo_ganadores": true
  }'
```

### 6. Test Listar API Keys

```bash
curl http://localhost:8000/api/v3/auth/keys/999999
```

**Respuesta esperada:**
```json
{
  "success": true,
  "user_id": 999999,
  "keys": [
    {
      "key_hash": "a1b2c3d4e5f6...",
      "nombre": "Test API Key",
      "created_at": "2026-01-11T20:00:00",
      "last_used": "2026-01-11T20:05:00",
      "is_active": true
    }
  ],
  "total": 1
}
```

### 7. Test Revocar API Key

```bash
curl -X DELETE http://localhost:8000/api/v3/auth/keys/999999/a1b2c3d4e5f6...
```

**Respuesta esperada:**
```json
{
  "success": true,
  "message": "API key revocada exitosamente"
}
```

Intentar usar la key revocada:

```bash
curl -H "X-API-Key: %API_KEY%" \
  http://localhost:8000/api/v3/auth/validate

# Debe retornar 403 Forbidden
```

---

## 🌐 Testing con Swagger UI

La forma más fácil de probar:

1. **Abrir navegador:** http://localhost:8000/api/docs
2. **Explorar endpoints** en la interfaz interactiva
3. **Probar autenticación:**
   - Clic en "Authorize" (candado verde arriba a la derecha)
   - Ingresa tu API key
   - Clic en "Authorize"
4. **Probar endpoints protegidos:**
   - Expandir `/api/v3/ml/precio`
   - Clic en "Try it out"
   - Ingresar datos de prueba
   - Clic en "Execute"

---

## ✅ Checklist de Verificación

Marca cada item cuando pase:

- [ ] Python 3.11 instalado
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas
- [ ] Archivo .env configurado
- [ ] `test_setup.py` pasa todos los tests
- [ ] Migración `migrate_subscriptions.py` ejecutada
- [ ] Migración `migrate_api_keys.py` ejecutada
- [ ] API inicia sin errores
- [ ] `/health` retorna status healthy
- [ ] SQL injection test pasa (no ejecuta código malicioso)
- [ ] RAG funciona sin crash de `top_k`
- [ ] Import `filtros` funciona
- [ ] Usuario PROFESIONAL creado
- [ ] API key generada exitosamente
- [ ] Autenticación con API key funciona
- [ ] Revocación de API key funciona

---

## 🐛 Troubleshooting

### Error: "Python no encontrado"
- Reinstala Python 3.11 marcando "Add to PATH"
- Reinicia la terminal

### Error: "ModuleNotFoundError: No module named 'fastapi'"
```bash
# Asegúrate de estar en el entorno virtual
.venv\Scripts\activate

# Re-instalar dependencias
pip install -r requirements.txt
```

### Error: "database_extended" not found
```bash
# El script debe ejecutarse desde la raíz del proyecto
cd D:\gabc_\OneDrive\Documentos\python\bot-compra-agil
python api_backend_v3.py
```

### Error: "Unable to connect to database"
- Si usas PostgreSQL, verifica que esté corriendo
- Para desarrollo, deja `DATABASE_URL` vacío para usar SQLite

### Error: Tabla no existe
```bash
# Ejecutar migraciones
python scripts/migrate_subscriptions.py
python scripts/migrate_api_keys.py
```

---

## 📞 Soporte

Si encuentras algún problema:
1. Revisa este documento
2. Verifica los logs de la API
3. Ejecuta `python test_setup.py` para diagnóstico

---

**¡Listo para testing!** 🚀
