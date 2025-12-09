# 🚀 Guía Rápida de Implementación ML/IA + SaaS Backend

## ¿Qué se ha construido?

### ✅ Sistema ML Completo (IMPLEMENTADO)
1. **Recomendador de Precio Óptimo** → Analiza 3M+ registros históricos
2. **Sistema RAG** → Busca casos similares para enriquecer IA
3. **Análisis IA Mejorado** → Gemini ahora usa datos históricos REALES
4. **4 Comandos Nuevos** → `/precio_optimo`, `/historico`, `/stats`, `/competidores`

### 📋 Backend SaaS (DOCUMENTADO)
- Arquitectura completa con FastAPI
- Sistema de autenticación JWT
- Integración con Stripe
- Rate limiting por tier
- Base de datos multi-tenant

---

## 🎯 Instalación y Configuración

### Paso 1: Instalar Dependencias

**Opción A - Windows (Recomendado):**
```bash
# Ejecutar script de instalación
install_ml_deps.bat
```

**Opción B - Manual:**
```bash
# ML & Analytics
pip install xgboost lightgbm shap fuzzywuzzy python-Levenshtein

# Dashboard (opcional por ahora)
pip install streamlit plotly altair

# SaaS Backend (opcional por ahora)
pip install stripe passlib[bcrypt] python-multipart email-validator alembic
```

### Paso 2: Registrar Comandos en el Bot

Edita el archivo principal del bot (probablemente `bot_inteligente.py` o similar):

```python
# Añadir al inicio del archivo
from bot_ml_commands import COMANDOS_ML

# En la función de setup/main, después de crear 'application':
# Registrar comandos ML
for nombre, handler in COMANDOS_ML.items():
    application.add_handler(CommandHandler(nombre, handler))
    print(f"✅ Comando /{nombre} registrado")
```

### Paso 3: Verificar Datos Históricos

Asegúrate de que la tabla `historico_licitaciones` tenga datos:

```python
python src/database_extended.py

# Deberías ver:
# ✅ Base de datos extendida creada/verificada
```

Para verificar cantidad de registros:
```sql
SELECT COUNT(*) FROM historico_licitaciones;
-- Debería retornar ~3,000,000+
```

### Paso 4: Probar Módulos ML

```bash
cd src
python ml_precio_optimo.py
python rag_historico.py
```

Deberías ver tests de ejemplo ejecutándose.

---

## 🧪 Pruebas de Funcionalidad

### Test 1: Recomendación de Precio
```
Usuario: /precio_optimo laptop 10
Bot: [Muestra análisis de precio con datos históricos]
```

### Test 2: Búsqueda Histórica
```
Usuario: /historico computador dell
Bot: [Muestra 10 casos similares con detalles]
```

### Test 3: Estadísticas
```
Usuario: /stats
Bot: [Estadísticas generales del histórico]

Usuario: /stats laptop
Bot: [Estadísticas específicas de laptops]
```

### Test 4: Análisis Mejorado
```
Usuario: /analizar [código de licitación]
Bot: [Análisis ahora incluye datos históricos reales]
```

---

## 📊 Arquitectura de Archivos

```
bot-compra-agil/
├── src/
│   ├── ml_precio_optimo.py      ✅ Sistema de recomendación de precio
│   ├── rag_historico.py          ✅ Sistema RAG para búsqueda histórica
│   ├── gemini_ai.py              ✅ Mejorado con RAG
│   ├── bot_ml_commands.py        ✅ Nuevos comandos del bot
│   ├── database_extended.py      ✅ Ya existía
│   └── [otros archivos existentes]
│
├── docs/
│   ├── ARQUITECTURA_BACKEND_SAAS.md  📋 Arquitectura completa backend
│   └── [otros docs]
│
├── requirements.txt              ✅ Actualizado con nuevas deps
├── install_ml_deps.bat          ✅ Script de instalación
└── README_ML.md                 ✅ Esta guía

Leyenda:
✅ = Implementado y listo
📋 = Documentado (pendiente implementación)
```

---

## 🔧 Configuración Avanzada

### Cache de Redis (Opcional pero Recomendado)

Para mejor performance, instala Redis:

```bash
# Windows: Descargar Redis de https://github.com/microsoftarchive/redis/releases
# O usar Docker:
docker run -d -p 6379:6379 redis:alpine
```

Luego actualiza `.env`:
```
REDIS_URL=redis://localhost:6379/0
ML_CACHE_ENABLED=true
```

### Variables de Entorno

Añade a `.env`:
```bash
# ML Configuration
ML_MODELS_PATH=./models
ML_MIN_CONFIDENCE=0.6
ML_CACHE_TTL=3600  # 1 hora

# SaaS (para futuro)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
JWT_SECRET_KEY=tu-secret-key-muy-segura
```

---

## 📈 Roadmap de Implementación

### ✅ Fase 1-3: COMPLETADO
- [x] Sistema de recomendación de precio
- [x] Sistema RAG
- [x] Integración con Gemini AI
- [x] Comandos nuevos del bot

### 🔜 Fase 4: Modelo de Probabilidad (Próximos 7 días)
- [ ] Implementar `ml_probabilidad.py`
- [ ] Entrenar modelo XGBoost
- [ ] Añadir comando `/probabilidad`
- [ ] Integrar en análisis IA

### 🔜 Fase 5: Dashboard Web (Próximos 14 días)
- [ ] Setup Streamlit
- [ ] Páginas de exploración de datos
- [ ] Gráficos interactivos
- [ ] Deploy en Streamlit Cloud

### 🔜 Fase 6: API REST (Próximos 21 días)
- [ ] Setup FastAPI
- [ ] Endpoints básicos
- [ ] Documentación Swagger
- [ ] Deploy

### 🔜 Fase 7-9: Backend SaaS Completo (Próximos 45 días)
- [ ] Autenticación JWT
- [ ] Sistema de suscripciones
- [ ] Integración Stripe
- [ ] Web App frontend

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'pandas'"
**Solución:** Ejecuta `install_ml_deps.bat` o `pip install pandas`

### Error: "No se encontraron datos históricos"
**Solución:** Verifica que la tabla `historico_licitaciones` tenga datos:
```sql
SELECT COUNT(*) FROM historico_licitaciones;
```

Si está vacía, ejecuta el script de importación:
```bash
python src/importar_historico.py
```

### Error: "fuzz module not found"
**Solución:** 
```bash
pip install fuzzywuzzy python-Levenshtein
```

### El bot no reconoce los nuevos comandos
**Solución:** Asegúrate de haber registrado los comandos en el archivo principal del bot (ver Paso 2 arriba).

---

## 💡 Tips de Uso

### Para Desarrollo:
```bash
# Probar módulos individualmente
python src/ml_precio_optimo.py
python src/rag_historico.py

# Ver logs detallados
export LOG_LEVEL=DEBUG  # Linux/Mac
set LOG_LEVEL=DEBUG     # Windows
```

### Para Producción:
1. Habilita cache de Redis
2. Configura rate limiting
3. Monitorea uso de API Gemini
4. Considera usar CDN para assets estáticos

---

## 📞 Siguiente Sesión

**Prioridades:**
1. ✅ Probar comandos ML con datos reales
2. ✅ Ajustar rate limits según tier de usuario
3. 🔜 Implementar modelo de probabilidad
4. 🔜 Crear dashboard básico
5. 🔜 Setup backend SaaS MVP

**Preguntas para Discutir:**
- ¿Los resultados de precio óptimo son coherentes con tu experiencia?
- ¿Qué otros análisis te gustaría ver?
- ¿Cuándo quieres lanzar el modelo de suscripciones?
- ¿Necesitas dashboard web pronto o el bot es suficiente por ahora?

---

## 📚 Recursos Adicionales

- [Documentación FastAPI](https://fastapi.tiangolo.com/)
- [Guía Stripe Python](https://stripe.com/docs/api/python)
- [XGBoost Tutoria](https://xgboost.readthedocs.io/)
- [Streamlit Docs](https://docs.streamlit.io/)

---

**Última Actualización:** 2025-12-09  
**Versión:** 1.0.0  
**Estado:** ✅ Fases 1-3 Implementadas | 📋 Backend Documentado
