# 🤖 CompraÁgil - Sistema Inteligente de Licitaciones

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

Sistema avanzado de análisis de licitaciones públicas con IA, Machine Learning y Bot de Telegram.

## 🎯 Características Principales

### Bot de Telegram 🤖
- ✅ Búsqueda inteligente de licitaciones
- ✅ Análisis automático con IA (Gemini)
- ✅ Sistema de alertas personalizadas
- ✅ Gestión de favoritos
- ✅ Comandos ML para precio óptimo y competencia

### Sistema ML/IA 🧠
- ✅ **Precio Óptimo**: Recomendación basada en 10.6M registros históricos
- ✅ **RAG**: Búsqueda de casos similares con ranking inteligente
- ✅ **Análisis de Competencia**: Proveedores exitosos y tasas de victoria
- ✅ **Estadísticas Avanzadas**: Por región, organismo, producto

### API REST v2.0 🚀
- ✅ **30+ Endpoints**: Cobertura completa de todas las tablas
- ✅ **Paginación**: Manejo eficiente de grandes datasets
- ✅ **Filtros Avanzados**: Estado, organismo, monto, fechas
- ✅ **Cache Redis**: Performance 50-100x mejorada
- ✅ **Rate Limiting**: Control de uso por endpoint
- ✅ **Swagger Docs**: Documentación interactiva

### Base de Datos 📊
- ✅ **10.6M** registros históricos
- ✅ **17 índices optimizados** para ML/RAG
- ✅ PostgreSQL con índices compuestos
- ✅ Cache distribuido con Redis

---

## 📁 Estructura del Proyecto

```
bot-compra-agil/
├── 📂 api/                        # REST API
│   ├── api_backend.py             # v1
│   └── api_backend_v2.py          # v2 expandida
│
├── 📂 docs/                       # 📚 Documentación
│   ├── api/                       # Docs de API
│   ├── architecture/              # Arquitectura
│   ├── guides/                    # Guías de uso
│   └── reports/                   # Reportes
│
├── 📂 src/                        # 🐍 Código fuente
│   ├── bot_*.py                   # Bot Telegram
│   ├── ml_*.py                    # Machine Learning
│   ├── rag_historico.py           # Sistema RAG
│   ├── gemini_ai.py               # Integración IA
│   ├── database_extended.py       # BD
│   └── redis_cache.py             # Caché
│
├── 📂 scripts/                    # 🔧 Scripts
│   ├── create_indexes.py          # Índices BD
│   └── analizar_esquema.py        # Análisis BD
│
└── 📂 tests/                      # 🧪 Tests
    └── test_ml_system.py          # Tests ML
```

Ver [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) para detalle completo.

---

## 🚀 Quick Start

### 1. Instalación

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/bot-compra-agil.git
cd bot-compra-agil

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar dependencias ML
install_ml_deps.bat  # Windows
# O: pip install xgboost lightgbm shap fuzzywuzzy python-Levenshtein
```

### 2. Configuración

```bash
# Copiar ejemplo de .env
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

**Variables requeridas:**
```bash
# Telegram
TELEGRAM_TOKEN=tu_token_aqui

# Base de Datos
DATABASE_URL=postgresql://user:password@host:port/database

# IA
GEMINI_API_KEY=tu_api_key_aqui

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0
```

### 3. Iniciar Base de Datos

```bash
# Crear tablas
python -c "from src.database_extended import iniciar_db_extendida; iniciar_db_extendida()"

# Crear índices optimizados
python scripts/create_indexes.py
```

### 4. Ejecutar

#### Bot de Telegram:
```bash
python src/bot_inteligente_parte1.py
```

#### API REST:
```bash
# API v2 (recomendado)
python api_backend_v2.py

# Documentación: http://localhost:8000/api/docs
```

#### Tests:
```bash
python tests/test_ml_system.py
```

---

## 📚 Documentación

### Para Usuarios
- [Guía de Testing](docs/guides/GUIA_TESTING.md)
- [Sistema ML](docs/guides/README_ML.md)
- [API para Next.js](docs/api/API_NEXTJS.md)
- [Redis Cache](docs/guides/REDIS_IMPLEMENTATION.md)

### Para Desarrolladores
- [Arquitectura Backend](docs/architecture/ARQUITECTURA_BACKEND_SAAS.md)
- [Estrategia SaaS](docs/architecture/ESTRATEGIA_SAAS.md)
- [Optimización BD](docs/architecture/DB_OPTIMIZATION_REPORT.md)
- [Testing API v2](docs/api/API_V2_TESTING.md)

---

## 🔧 Tecnologías

### Backend
- **Python 3.11+**
- **FastAPI** - REST API
- **PostgreSQL** - Base de datos
- **Redis** - Cache y rate limiting
- **SQLAlchemy** - ORM

### ML/IA
- **Google Gemini** - Análisis de IA
- **XGBoost** - Modelos predictivos
- **pandas** - Análisis de datos
- **fuzzywuzzy** - Búsqueda difusa

### Bot
- **python-telegram-bot** - Bot de Telegram
- **asyncio** - Operaciones asíncronas

### DevOps
- **Docker** - Containerización
- **GitHub Actions** - CI/CD
- **Alembic** - Migraciones BD

---

## 📊 Performance

### Con Optimizaciones (Redis + Índices):
- **Stats generales**: ~10ms (antes: 500ms) - **50x**
- **Búsqueda RAG**: ~15ms (antes: 2s) - **130x**
- **ML precio**: ~20ms (antes: 1.5s) - **75x**

### Base de Datos:
- **10.6M** registros históricos
- **17 índices** optimizados
- **1.5GB** en índices
- **Queries**: <100ms promedio

---

## 🧪 Testing

```bash
# Suite completa
python tests/test_ml_system.py

# Test específicos
python src/ml_precio_optimo.py    # Test precio óptimo
python src/rag_historico.py       # Test sistema RAG
python src/redis_cache.py         # Test Redis
```

Ver [docs/guides/GUIA_TESTING.md](docs/guides/GUIA_TESTING.md) para más detalles.

---

## 📈 Roadmap

### Fase Actual (v2.0)
- [x] Sistema ML de precio óptimo
- [x] RAG con 10.6M registros
- [x] API REST expandida (30+ endpoints)
- [x] Cache Redis
- [x] 17 índices optimizados

### Próximas Fases
- [ ] Modelo de probabilidad de ganar (XGBoost)
- [ ] Frontend Next.js
- [ ] Sistema de suscripciones (Stripe)
- [ ] Deploy en producción
- [ ] Webhooks y notificaciones
- [ ] Dashboard de analytics

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 Licencia

Este proyecto es privado y confidencial.

---

## 👥 Equipo

**Desarrollador Principal**: Gerard Bourguett

---

## 📞 Contacto

- 📧 Email: tu-email@ejemplo.com
- 🐦 Twitter: @tu-usuario
- 💼 LinkedIn: tu-perfil

---

## ⭐ Agradecimientos

- Google Gemini AI
- Mercado Público API
- Comunidad FastAPI
- python-telegram-bot

---

**Última actualización:** 2025-12-11  
**Versión:** 2.0.0  
**Estado:** ✅ En Desarrollo Activo
