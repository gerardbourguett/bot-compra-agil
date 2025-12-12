# 📁 Estructura del Proyecto - CompraÁgil

```
bot-compra-agil/
│
├── 📂 .github/                    # GitHub Actions y workflows
│   └── workflows/
│       └── ci-cd.yml              # Pipeline CI/CD
│
├── 📂 docs/                       # 📚 DOCUMENTACIÓN
│   ├── api/                       # Documentación de API
│   │   ├── API_NEXTJS.md          # Guía para Next.js
│   │   ├── API_V2_TESTING.md      # Testing API v2
│   │   ├── API_EXPANDED.md        # Endpoints expandidos
│   │   └── API_RUNNING.md         # Guía de ejecución
│   │
│   ├── architecture/              # Arquitectura del sistema
│   │   ├── ARQUITECTURA_BACKEND_SAAS.md
│   │   ├── ESTRATEGIA_SAAS.md
│   │   └── DB_OPTIMIZATION_REPORT.md
│   │
│   ├── guides/                    # Guías de uso
│   │   ├── README_ML.md           # Guía sistema ML
│   │   ├── GUIA_TESTING.md        # Guía de testing
│   │   ├── REDIS_IMPLEMENTATION.md
│   │   └── BACKUP_RESTORE.md
│   │
│   └── reports/                   # Reportes y resultados
│       └── TEST_RESULTS.md        # Resultados de tests
│
├── 📂 src/                        # 🐍 CÓDIGO FUENTE
│   ├── bot/                       # Bot de Telegram
│   │   ├── bot_inteligente_parte1.py
│   │   ├── bot_inteligente_parte2.py
│   │   ├── bot_inteligente_parte3.py
│   │   └── bot_ml_commands.py     # Comandos ML del bot
│   │
│   ├── ml/                        # Machine Learning
│   │   ├── ml_precio_optimo.py    # Recomendación de precio
│   │   ├── rag_historico.py       # Sistema RAG
│   │   └── ml_probabilidad.py     # Predicción (futuro)
│   │
│   ├── core/                      # Funcionalidades core
│   │   ├── database_extended.py   # Gestión BD
│   │   ├── gemini_ai.py           # Integración IA
│   │   ├── mercado_api.py         # API Mercado Público
│   │   └── redis_cache.py         # Sistema de caché
│   │
│   ├── services/                  # Servicios de negocio
│   │   ├── subscriptions.py       # Suscripciones
│   │   ├── config.py              # Configuración
│   │   └── notifications.py       # Notificaciones
│   │
│   └── utils/                     # Utilidades
│       ├── api_client.py
│       └── formatters.py
│
├── 📂 api/                        # 🚀 REST API
│   ├── v1/
│   │   └── api_backend.py         # API v1
│   ├── v2/
│   │   ├── api_backend_v2.py      # API v2 expandida
│   │   └── endpoints/
│   │       └── api_endpoints_complete.py
│   └── shared/
│       └── models.py              # Modelos Pydantic
│
├── 📂 scripts/                    # 🔧 SCRIPTS
│   ├── create_indexes.py          # Crear índices BD
│   ├── analizar_esquema.py        # Análisis BD
│   ├── entrenar_modelo.py         # Entrenar ML (futuro)
│   └── actualizar_estadisticas.py
│
├── 📂 tests/                      # 🧪 TESTS
│   ├── unit/
│   │   └── test_ml_system.py
│   ├── integration/
│   └── e2e/
│
├── 📂 logs/                       # 📝 LOGS
│   └── app.log
│
├── 📂 models/                     # 🤖 MODELOS ML
│   └── (modelos entrenados .pkl)
│
├── 📄 requirements.txt            # Dependencias Python
├── 📄 .env.example                # Variables de entorno ejemplo
├── 📄 docker-compose.yml          # Configuración Docker
├── 📄 Dockerfile                  # Imagen Docker
└── 📄 README.md                   # Documentación principal

```

## 📋 Organización por Tipo

### Documentación (`docs/`)
- **api/**: Todo relacionado con la API REST
- **architecture/**: Diseño y arquitectura del sistema  
- **guides/**: Guías de uso y tutoriales
- **reports/**: Reportes de testing y performance

### Código Fuente (`src/`)
- **bot/**: Código del bot de Telegram
- **ml/**: Modelos y algoritmos ML
- **core/**: Funcionalidades base (BD, IA, caché)
- **services/**: Lógica de negocio
- **utils/**: Utilidades compartidas

### API (`api/`)
- **v1/**: Primera versión
- **v2/**: Versión expandida con todas las tablas
- **shared/**: Código compartido entre versiones

### Scripts (`scripts/`)
- Scripts de mantenimiento, índices, estadísticas

### Tests (`tests/`)
- **unit/**: Tests unitarios
- **integration/**: Tests de integración
- **e2e/**: Tests end-to-end

## 🎯 Convenciones de Nombres

### Archivos Python
- Módulos: `snake_case.py`
- Clases: `PascalCase`
- Funciones: `snake_case()`
- Constantes: `UPPER_SNAKE_CASE`

### Documentación
- Guías: `README_*.md`, `GUIA_*.md`
- Arquitectura: `ARQUITECTURA_*.md`
- Reportes: `*_REPORT.md`, `TEST_*.md`

### Carpetas
- Minúsculas: `docs/`, `src/`, `api/`
- Sin espacios ni caracteres especiales

## 🔄 Migración Actual

### Archivos movidos:
- ✅ `API_RUNNING.md` → `docs/api/`
- ✅ `README_ML.md` → `docs/guides/`
- ✅ `TEST_RESULTS.md` → `docs/reports/`

### Próximos pasos:
1. Reorganizar archivos en `src/` por subcarpetas
2. Mover archivos de API a carpeta dedicada
3. Crear subcarpetas en `docs/`
4. Actualizar imports en código

---

**Versión:** 2.0  
**Última actualización:** 2025-12-11  
**Estado:** 🔄 En reorganización
