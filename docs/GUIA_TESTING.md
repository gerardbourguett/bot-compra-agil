# 🧪 Guía de Testing - Sistema ML + API

## Quick Start: Cómo Probar Todo

### Opción 1: Test Automatizado Completo

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar suite de tests
python tests/test_ml_system.py
```

Esto verificará:
- ✅ Todas las importaciones
- ✅ Conexión a base de datos
- ✅ Datos históricos disponibles
- ✅ Sistema de recomendación de precio
- ✅ Sistema RAG
- ✅ Análisis de competencia
- ✅ Configuración Gemini AI

---

### Opción 2: Test Manual Módulo por Módulo

#### 1. Test de Precio Óptimo

```bash
cd src
python ml_precio_optimo.py
```

**Salida esperada:**
```
============================================================
TEST 1: Recomendación para laptop
============================================================
💰 RECOMENDACIÓN DE PRECIO

Producto: laptop
Cantidad: 10 unidades

📊 Alta confianza (basado en 156 registros históricos)
💰 Precio Recomendado: $625,820 por unidad
...
```

**Si falla:** Verifica que `historico_licitaciones` tenga datos.

---

#### 2. Test de Sistema RAG

```bash
cd src
python rag_historico.py
```

**Salida esperada:**
```
============================================================
TEST: Búsqueda RAG para licitación de laptops
============================================================
✅ Encontrados 10 casos similares

📊 INSIGHTS BASADOS EN 10 CASOS HISTÓRICOS:
✅ Ofertas Ganadoras: 5 (50.0%)
...
```

---

#### 3. Test de la API REST

```bash
# Terminal 1: Iniciar servidor
python api_backend.py
```

**Salida esperada:**
```
🚀 Iniciando CompraÁgil API...
📚 Documentación: http://localhost:8000/api/docs
🔧 Health check: http://localhost:8000/health
INFO:     Uvicorn running on http://0.0.0.0:8000
```

```bash
# Terminal 2: Probar endpoints

# Health check
curl http://localhost:8000/health

# Precio óptimo
curl -X POST http://localhost:8000/api/v1/ml/precio \
  -H "Content-Type: application/json" \
  -d '{"producto": "laptop", "cantidad": 10}'

# Stats generales
curl http://localhost:8000/api/v1/stats

# Búsqueda histórica
curl -X POST http://localhost:8000/api/v1/historico/buscar \
  -H "Content-Type: application/json" \
  -d '{"query": "laptop dell", "limite": 5}'
```

---

### Opción 3: Test Interactivo (Swagger UI)

1. Inicia la API: `python api_backend.py`
2. Abre el navegador: http://localhost:8000/api/docs
3. Prueba cada endpoint con la interfaz visual

**Ejemplo:**
- Click en "POST /api/v1/ml/precio"
- Click en "Try it out"
- Ingresa:
  ```json
  {
    "producto": "laptop",
    "cantidad": 10
  }
  ```
- Click en "Execute"
- Ve la respuesta JSON

---

## Testing del Bot de Telegram

### Registrar Comandos ML en el Bot

Edita `bot_inteligente.py` o tu archivo principal del bot:

```python
# Al inicio del archivo
from bot_ml_commands import COMANDOS_ML

# En la función de setup (donde creas 'application')
def main():
    application = Application.builder().token(TOKEN).build()
    
    # ... tus comandos existentes ...
    
    # ✅ AÑADIR: Registrar comandos ML
    for nombre, handler in COMANDOS_ML.items():
        application.add_handler(CommandHandler(nombre, handler))
        print(f"✅ Comando /{nombre} registrado")
    
    # ... resto del código ...
```

### Probar Comandos en Telegram

Una vez registrados, prueba en tu bot:

```
/precio_optimo laptop 10
/historico computador dell
/stats
/stats laptop
/competidores laptop
```

**Salida esperada:**
```
/precio_optimo laptop 10

💰 RECOMENDACIÓN DE PRECIO

Producto: laptop
Cantidad: 10 unidades

📊 Alta confianza (basado en 156 registros históricos)

💰 Precio Recomendado: $625,820 por unidad
   • 4.2% por debajo de la mediana histórica

🎯 Estrategia:
   • Precio equilibrado - Balance óptimo margen/probabilidad
   • Sweet spot según datos históricos

📈 Rango Competitivo: $450,000 - $850,000
💵 Precio Total Sugerido: $6,258,200

📊 Datos: 156 licitaciones analizadas
   • 78 ofertas ganadoras
   • Tasa de conversión: 50.0%
```

---

## Troubleshooting

### Problema 1: ModuleNotFoundError

**Error:**
```
ModuleNotFoundError: No module named 'pandas'
```

**Solución:**
```bash
# Opción A: Script de instalación
install_ml_deps.bat

# Opción B: Manual
pip install pandas numpy scikit-learn xgboost fuzzywuzzy python-Levenshtein
```

---

### Problema 2: No se encuentran datos históricos

**Error:**
```
⚠️ No se encontraron datos históricos suficientes
```

**Solución:**
```bash
# Verificar tabla
python -c "import database_extended as db; conn = db.get_connection(); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM historico_licitaciones'); print(f'Registros: {cursor.fetchone()[0]}')"

# Si está vacía, importar datos
python src/importar_historico.py --url https://...
```

---

### Problema 3: API no inicia

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solución:**
```bash
pip install fastapi uvicorn pydantic
```

---

### Problema 4: CORS error en Next.js

**Error en consola del navegador:**
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**Solución:**
El backend ya está configurado para localhost:3000, pero asegúrate de que el servidor esté corriendo.

---

### Problema 5: Análisis IA no usa datos históricos

**Síntoma:** El bot responde pero no menciona datos históricos.

**Verificar:**
```python
# En gemini_ai.py, verifica que la función tenga:
def analizar_licitacion_completo(licitacion, perfil_empresa, productos_detalle=None, usar_historicos=True):
    ...
```

Si `usar_historicos=False` por defecto, cámbialo a `True`.

---

## Checklist de Verificación

Antes de considerar que todo funciona:

- [ ] `python tests/test_ml_system.py` pasa todos los tests
- [ ] `python api_backend.py` inicia sin errores
- [ ] http://localhost:8000/api/docs muestra la documentación
- [ ] http://localhost:8000/health retorna `{"status": "healthy"}`
- [ ] Puedes hacer POST a `/api/v1/ml/precio` y obtienes resultado
- [ ] Los comandos del bot (`/precio_optimo`, etc.) funcionan
- [ ] El análisis `/analizar` menciona datos históricos

---

## Performance Benchmarks

### Mínimo Aceptable:
- Precio óptimo: < 1s
- Búsqueda RAG: < 2s
- Stats generales: < 500ms
- Análisis enriquecido: < 3s

### Óptimo:
- Precio óptimo: < 500ms
- Búsqueda RAG: < 1s
- Stats generales: < 200ms
- Análisis enriquecido: < 1.5s

Si los tiempos son mayores:
1. Verifica índices en la BD
2. Considera añadir cache (Redis)
3. Limita el `limite` en búsquedas

---

## Next Steps

Una vez que todos los tests pasen:

1. **Integrar con Next.js**
   - Usa los ejemplos de `docs/API_NEXTJS.md`
   - Crea componentes para cada endpoint
   
2. **Deploy Backend**
   - Railway, Render, o similar
   - Actualiza CORS con tu dominio de producción
   
3. **Monitoreo**
   - Añade logging
   - Configura Sentry para errores
   - Usa Posthog/Mixpanel para analytics

---

**Pro Tip:** Usa Swagger UI (http://localhost:8000/api/docs) durante desarrollo. Es mucho más rápido que curl para probar endpoints.
