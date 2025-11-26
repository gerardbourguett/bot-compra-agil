# Estructura del Proyecto - Bot Inteligente de Compra Ágil

## 📁 Estructura Actual

```
Nueva carpeta/
├── README.md                    # Documentación principal
├── .env                         # Variables de entorno (no en git)
├── .env.example                 # Ejemplo de configuración
├── .gitignore                   # Archivos ignorados por git
├── requirements.txt             # Dependencias Python
├── Dockerfile                   # Imagen Docker
├── docker-compose.yml           # Orquestación Docker
├── init.sql                    # Inicialización PostgreSQL
├── .dockerignore               # Archivos ignorados por Docker
│
├── src/                        # 🐍 Código fuente (USAR ESTOS)
│   ├── bot_inteligente.py      # ⭐ Bot principal con IA
│   ├── database_extended.py    # BD principal (PostgreSQL/SQLite)
│   ├── database_bot.py         # BD del bot (perfiles, guardadas)
│   ├── gemini_ai.py            # Integración Gemini AI
│   ├── filtros.py              # Filtros y búsquedas inteligentes
│   ├── api_client.py           # Cliente API Mercado Público
│   ├── scraper.py              # ⭐ Scraper principal
│   └── obtener_detalles.py     # Script para detalles
│
├── docs/                       # 📚 Documentación
│   ├── GUIA_BOT.md             # Guía de uso del bot
│   ├── DOCKER.md               # Guía completa de Docker
│   ├── INICIO_RAPIDO_DOCKER.md # Inicio rápido con Docker
│   ├── MIGRACION_POSTGRES.md   # Guía de migración a PostgreSQL
│   ├── CAMBIOS.md              # Historial de cambios
│   └── ORGANIZACION.md         # Este archivo
│
├── legacy/                     # 🗄️ Archivos antiguos (NO USAR)
│   ├── bot.py                  # Bot antiguo sin IA
│   ├── scraper_completo.py     # Scraper antiguo
│   ├── bot_inteligente_parte1.py  # Partes del bot (ya integradas)
│   ├── bot_inteligente_parte2.py
│   ├── bot_inteligente_parte3.py
│   └── db_adapter.py           # Adaptador (ya integrado)
│
└── logs/                       # 📝 Logs (creado automáticamente)
```

## ✅ Archivos Principales

### Para Desarrollo Local
- **`src/scraper.py`** - Obtener licitaciones de la API
- **`src/obtener_detalles.py`** - Obtener detalles completos
- **`src/bot_inteligente.py`** - Bot de Telegram con IA

### Para Producción (Docker)
- **`docker-compose.yml`** - Orquestación completa (PostgreSQL + Bot + Scraper)
- **`Dockerfile`** - Imagen del contenedor

## 🚀 Comandos Rápidos

### Desarrollo Local
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar scraper
python src/scraper.py

# Ejecutar bot
python src/bot_inteligente.py
```

### Docker
```bash
# Iniciar todo
docker-compose up -d

# Ver logs
docker-compose logs -f

# Reiniciar
docker-compose restart

# Detener
docker-compose down
```

## 📝 Notas

- **src/** contiene el código activo que Docker usa
- **legacy/** contiene archivos antiguos por si se necesitan referencias
- **docs/** contiene toda la documentación
- Los archivos en la raíz son configuración (Docker, requirements, etc.)

## 🔄 Migración Completada

✅ PostgreSQL como base de datos principal
✅ Detección automática SQLite/PostgreSQL
✅ Bot inteligente con Gemini AI
✅ Scraper automático cada 6 horas
✅ Sistema de perfiles y alertas
✅ Estructura organizada y limpia
