# Plan de Escalabilidad y Mejoras SaaS - CompraAgil

**Fecha:** 2025-12-28
**Autor:** Diseño colaborativo con Claude Code
**Estado:** Diseño aprobado, pendiente implementación

---

## Índice

1. [Contexto y Objetivos](#contexto-y-objetivos)
2. [Arquitectura de Persistencia de Datos](#arquitectura-de-persistencia-de-datos)
3. [Optimización de Base de Datos y Caching](#optimización-de-base-de-datos-y-caching)
4. [Arquitectura de Workers y Queue de Tareas](#arquitectura-de-workers-y-queue-de-tareas)
5. [Mejoras de IA y Features Premium](#mejoras-de-ia-y-features-premium)
6. [Integración con Stack de Monitoreo](#integración-con-stack-de-monitoreo)
7. [Plan de Implementación por Fases](#plan-de-implementación-por-fases)

---

## Contexto y Objetivos

### Situación Actual

CompraAgil es un SaaS de inteligencia de licitaciones públicas chilenas con:
- **Bot de Telegram** con comandos interactivos y análisis IA
- **API REST v3** con 40+ endpoints
- **Base de datos PostgreSQL** con 10.6M de registros históricos
- **Sistema ML/AI**: Precio óptimo, RAG histórico, análisis de competencia
- **Sistema de suscripciones**: 4 tiers (FREE, EMPRENDEDOR, PYME, PROFESIONAL)

### Infraestructura Actual

- **Servidor:** VPS Vultr ($25/mes) con recursos compartidos para múltiples SaaS
- **Orquestación:** Docker Compose con servicios (bot, scraper, PostgreSQL)
- **CI/CD:** GitHub Actions con self-hosted runner
- **Monitoreo existente:** Traefik, Prometheus, Grafana, Loki/Promtail, Uptime Kuma, Portainer

### Pain Points Identificados

1. **Reseteo de BD en deploys** (crítico): Riesgo de perder 10.6M registros históricos
2. **Performance con alta concurrencia**: Queries lentas, bot bloqueado en análisis ML
3. **Falta de visibilidad**: No hay métricas de negocio (conversión, uso de features)
4. **Features IA básicas**: Matching por keyword, análisis de precios simple

### Objetivos del Plan

1. **Persistencia bulletproof**: Garantizar que nunca se pierdan datos históricos
2. **Performance**: Queries <1s, bot siempre responsivo
3. **Escalabilidad**: Preparar para 10x-100x más usuarios
4. **Diferenciación**: Features IA premium para monetización
5. **Observabilidad**: Métricas de negocio en tiempo real

---

## Arquitectura de Persistencia de Datos

### Problema

Actualmente existe riesgo de pérdida de datos por:
- Volúmenes Docker huérfanos (cambio de nombre de proyecto)
- Migración a otro servidor (volúmenes no se transfieren)
- Corrupciones de disco
- Limpieza accidental (`docker volume prune`)

### Solución: Arquitectura de 3 Capas

```
┌─────────────────────────────────────────────────────┐
│  CAPA 1: Volumen Docker (Operación diaria)         │
│  compra_agil_postgres_data                          │
│  • Acceso rápido                                    │
│  • Usado por PostgreSQL en runtime                  │
└─────────────┬───────────────────────────────────────┘
              │ Backup automático cada deploy
              ▼
┌─────────────────────────────────────────────────────┐
│  CAPA 2: Backups locales (Recuperación rápida)     │
│  backups/backup_YYYYMMDD_HHMMSS.sql                │
│  • Últimos 7 backups rotados automáticamente        │
│  • Restauración en < 5 minutos                      │
└─────────────┬───────────────────────────────────────┘
              │ Subida automática cada deploy
              ▼
┌─────────────────────────────────────────────────────┐
│  CAPA 3: Storage externo (Disaster recovery)       │
│  GitHub Artifacts / S3 / Backblaze B2              │
│  • Backups mensuales comprimidos                    │
│  • Histórico completo con datos históricos          │
│  • Recuperación ante pérdida total del servidor     │
└─────────────────────────────────────────────────────┘
```

### Mejoras al CI/CD

1. **Pre-deploy check**: Verificar que volumen existe antes de `docker compose down`
2. **Backup obligatorio**: Deploy falla si no se puede crear backup
3. **Post-deploy verification**: Confirmar conteo de registros post-deploy
4. **Backup upload**: Subir backups a GitHub Artifacts o almacenamiento externo

### Script de Restauración

```bash
# scripts/restore_backup.sh
#!/bin/bash
# Restaurar desde backup local o GitHub Artifacts
# Uso: ./scripts/restore_backup.sh [backup_file.sql.gz]
```

---

## Optimización de Base de Datos y Caching

### Particionamiento de Tabla Histórica

Con 10.6M de registros, particionar por mes mejora performance dramáticamente:

```sql
-- Convertir a tabla particionada
CREATE TABLE historico_licitaciones (
    id SERIAL,
    fecha_cierre DATE NOT NULL,
    producto_cotizado TEXT,
    monto_total INTEGER,
    -- ... otras columnas
) PARTITION BY RANGE (fecha_cierre);

-- Crear particiones mensuales
CREATE TABLE historico_licitaciones_2024_01
  PARTITION OF historico_licitaciones
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE historico_licitaciones_2024_02
  PARTITION OF historico_licitaciones
  FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- ... etc
```

**Ventajas:**
- Queries filtradas por fecha solo escanean una partición (10-100x más rápido)
- Índices más pequeños por partición
- Backups incrementales por mes

### Índices Optimizados

Índices críticos para queries ML/RAG:

```sql
-- Búsqueda de productos (RAG) con fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_historico_producto_trgm
  ON historico_licitaciones
  USING gin(producto_cotizado gin_trgm_ops);

-- Análisis de precios (lookup rápido)
CREATE INDEX idx_historico_precio_lookup
  ON historico_licitaciones
  (producto_cotizado, es_ganador, monto_total, fecha_cierre DESC);

-- Filtros por región
CREATE INDEX idx_historico_region_fecha
  ON historico_licitaciones
  (region, fecha_cierre DESC);

-- Búsqueda por organismo
CREATE INDEX idx_historico_organismo
  ON historico_licitaciones
  USING gin(nombre_cotizacion gin_trgm_ops);
```

### Estrategia de Caching con Redis

```
Usuario solicita análisis de precio de "computadores"
    ↓
[Cache L1: Redis - TTL 1 hora]
  • Key: "ml:precio:computadores:hash"
  • Hit? → Retornar inmediatamente (50-200ms)
  • Miss? → Continuar ↓
    ↓
[PostgreSQL Query + ML Processing]
  • Query a historico_licitaciones (2-5s)
  • Cálculo de precio óptimo (1-3s)
    ↓
[Guardar en Redis para próxima vez]
  • TTL: 1 hora para datos cambiantes
  • TTL: 24 horas para histórico estable
```

**Datos a cachear con prioridad:**
- Resultados de ML (precio óptimo, competencia) - TTL: 1h
- Búsquedas RAG frecuentes - TTL: 1h
- Listados de licitaciones activas - TTL: 15min
- Estadísticas de dashboard - TTL: 1h
- Embeddings de productos - TTL: 24h

### Query Optimization Patterns

**❌ Antipatrón (lento):**
```python
# Carga TODOS los registros en memoria
cursor.execute(
    "SELECT * FROM historico_licitaciones WHERE producto_cotizado LIKE %s",
    ('%computador%',)
)
all_records = cursor.fetchall()  # 100,000+ registros
```

**✅ Patrón optimizado:**
```python
# Limitar resultados + usar índices + filtro temporal
cursor.execute("""
    SELECT producto_cotizado, monto_total, cantidad, fecha_cierre
    FROM historico_licitaciones
    WHERE producto_cotizado % %s  -- Similaridad fuzzy (pg_trgm)
    AND fecha_cierre >= NOW() - INTERVAL '2 years'
    AND es_ganador = true
    ORDER BY fecha_cierre DESC
    LIMIT 1000
""", (search_term,))
```

---

## Arquitectura de Workers y Queue de Tareas

### Problema Actual

El bot y scraper corren síncronamente. Si un usuario solicita análisis ML pesado (10-15s), el bot se bloquea y no puede responder a otros usuarios.

### Solución: Celery + Redis

```
┌─────────────────┐
│  Telegram Bot   │ ← Responde instantáneamente
└────────┬────────┘
         │ Encola tarea
         ▼
┌─────────────────┐
│  Redis Queue    │ ← Broker de mensajes
└────────┬────────┘
         │ Consume tareas
         ▼
┌─────────────────────────────────────┐
│  Celery Workers (3 tipos)           │
│                                     │
│  Worker 1: ML Tasks (2 workers)     │
│  - /precio (cálculo óptimo)         │
│  - /rag (búsqueda histórica)        │
│  - /competencia (análisis)          │
│  - /scoring (probabilidad ganar)    │
│                                     │
│  Worker 2: Scraping (1 worker)      │
│  - Scraper cada 6h                  │
│  - Import histórico mensual         │
│                                     │
│  Worker 3: Exports & Reports        │
│  - Generación de Excel              │
│  - Generación de PDF (propuestas)   │
│  - Envío de alertas masivas         │
└─────────────────────────────────────┘
```

### Implementación

**Antes (bloqueante):**
```python
# bot_ml_commands.py
async def precio_command(update, context):
    # Esto toma 10-15 segundos y bloquea el bot
    resultado = calcular_precio_optimo(producto)
    await update.message.reply_text(resultado)
```

**Después (async):**
```python
# bot_ml_commands.py
async def precio_command(update, context):
    await update.message.reply_text(
        "🔄 Analizando precios históricos... (esto tomará ~10 seg)"
    )

    # Encolar tarea en background
    task = tasks.calcular_precio_optimo.delay(producto, user_id)

    # El bot queda libre para otras peticiones
```

**Worker task:**
```python
# src/tasks.py
from celery import Celery

celery = Celery('compra_agil', broker='redis://redis:6379/0')

@celery.task(bind=True, max_retries=3)
def calcular_precio_optimo(self, producto, user_id):
    try:
        # Procesamiento pesado aquí
        resultado = ml_precio_optimo.analizar(producto)

        # Notificar al usuario via Telegram
        bot.send_message(user_id, f"✅ Análisis completado:\n{resultado}")

        return resultado
    except Exception as e:
        # Reintentar hasta 3 veces con backoff exponencial
        self.retry(exc=e, countdown=2 ** self.request.retries)
```

### docker-compose.yml actualizado

```yaml
services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  bot:
    # ... (igual que antes)

  celery-worker-ml:
    image: ghcr.io/.../bot:latest
    command: celery -A tasks worker --queues=ml --concurrency=2 --loglevel=info
    depends_on:
      - redis
      - postgres
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      - GEMINI_API_KEY=${GEMINI_API_KEY}

  celery-worker-scraping:
    image: ghcr.io/.../scraper:latest
    command: celery -A tasks worker --queues=scraping --concurrency=1 --loglevel=info
    depends_on:
      - redis
      - postgres

  celery-beat:  # Scheduler para tareas periódicas
    image: ghcr.io/.../bot:latest
    command: celery -A tasks beat --loglevel=info
    depends_on:
      - redis

volumes:
  redis_data:
```

### Beneficios Inmediatos

1. **Bot siempre responsivo**: No se bloquea esperando ML
2. **Priorización**: Comandos rápidos tienen prioridad sobre exports pesados
3. **Rate limiting natural**: Queue limita carga al servidor
4. **Retry automático**: Si falla un análisis ML, se reintenta
5. **Escalabilidad horizontal**: Después puedes agregar más workers en otro servidor

---

## Mejoras de IA y Features Premium

### 4.1 Matching Inteligente con Embeddings

**Problema:** Alertas funcionan por keyword exacta, pierdes licitaciones relevantes.

**Solución:** Semantic search con embeddings.

```python
# Flujo mejorado de alertas
Usuario configura alerta: "Vendo laptops HP"
    ↓
Generar embedding con Gemini (vector de 768 dimensiones)
Almacenar en PostgreSQL con extensión pgvector
    ↓
Nueva licitación: "Renovación tecnológica equipamiento informático"
    ↓
Similarity search (cosine distance < 0.3)
✅ Match encontrado (85% similaridad)
🔔 Notificar al usuario
```

**Implementación técnica:**

```sql
-- Instalar pgvector en PostgreSQL
CREATE EXTENSION IF NOT EXISTS vector;

-- Nueva tabla para embeddings
CREATE TABLE licitacion_embeddings (
    id SERIAL PRIMARY KEY,
    licitacion_id INT REFERENCES licitaciones(id),
    embedding vector(768),  -- Dimensión de Gemini embeddings
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índice para búsqueda rápida
CREATE INDEX ON licitacion_embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Query de búsqueda semántica
SELECT l.*, 1 - (le.embedding <=> query_embedding) AS similarity
FROM licitaciones l
JOIN licitacion_embeddings le ON l.id = le.licitacion_id
WHERE 1 - (le.embedding <=> query_embedding) > 0.75
ORDER BY similarity DESC
LIMIT 20;
```

### 4.2 Análisis de Precios Históricos Mejorado

Ya existe `ml_precio_optimo.py`, mejorar con insights accionables:

```python
def analizar_precio_optimo_v2(producto, organismo=None, region=None):
    """
    Retorna análisis completo de precios con insights accionables
    """

    # 1. Buscar productos similares (embeddings + fuzzy)
    productos_similares = buscar_similares_semantico(producto)

    # 2. Filtrar por contexto
    query = """
        SELECT
            monto_total / NULLIF(cantidad, 0) AS precio_unitario,
            nombre_proveedor,
            region,
            fecha_cierre,
            es_ganador
        FROM historico_licitaciones
        WHERE producto_cotizado = ANY(%s)
        AND fecha_cierre >= NOW() - INTERVAL '2 years'
    """

    if organismo:
        query += " AND nombre_cotizacion ILIKE %s"
    if region:
        query += " AND region = %s"

    # 3. Análisis estadístico
    precios = obtener_datos(query)

    return {
        "precio_sugerido": percentil(precios, 40),  # Sweet spot
        "precio_competitivo": percentil(precios, 25),  # Agresivo
        "precio_seguro": percentil(precios, 60),  # Conservador

        # Insights específicos
        "insights": [
            f"⚠️ Este organismo suele pagar un {diff}% menos que el promedio nacional",
            f"💡 Los proveedores de {region} ganan el {win_rate}% de las veces",
            f"📊 Últimas 10 adjudicaciones: rango ${min:,} - ${max:,}"
        ],

        # Competencia
        "competidores_frecuentes": top_5_proveedores,
        "tu_probabilidad_ganar": calcular_win_probability(user_profile, context)
    }
```

### 4.3 Generador de Propuestas con LLM (Feature Premium)

Joya de la corona para planes PYME/PROFESIONAL:

```python
# Nuevo comando: /generar_propuesta
async def generar_propuesta_command(update, context):
    # Validar tier
    subscription = get_user_subscription(user_id)
    if subscription['tier'] not in ['pyme', 'profesional']:
        await update.message.reply_text(
            "🔒 Esta función requiere plan PYME o superior\n"
            "Usa /upgrade para mejorar tu plan"
        )
        return

    # Obtener detalles de la licitación
    licitacion = obtener_licitacion(licitacion_id)

    # Obtener perfil del usuario (histórico de propuestas ganadoras)
    perfil_empresa = obtener_perfil_usuario(user_id)

    # Generar con Gemini
    prompt = f"""
    Eres un experto en licitaciones públicas chilenas.

    LICITACIÓN:
    {licitacion['nombre']}
    Organismo: {licitacion['organismo']}
    Presupuesto: ${licitacion['presupuesto']:,}
    Requisitos técnicos:
    {licitacion['especificaciones']}

    EMPRESA:
    {perfil_empresa['descripcion']}
    Experiencia previa: {perfil_empresa['adjudicaciones_pasadas']}

    Genera una propuesta técnica profesional que:
    1. Demuestre comprensión de los requisitos
    2. Destaque nuestra experiencia relevante
    3. Proponga una solución concreta
    4. Incluya cronograma realista

    Formato: Carta formal para portal ChileCompra
    """

    propuesta = await gemini_ai.generar_texto(prompt)

    # Guardar borrador
    guardar_borrador(user_id, licitacion_id, propuesta)

    # Enviar como documento
    await context.bot.send_document(
        chat_id=user_id,
        document=generar_pdf(propuesta),
        filename=f"propuesta_{licitacion_id}.pdf",
        caption="✅ Propuesta generada. Revísala y personalízala antes de enviar."
    )
```

### 4.4 Scoring de Probabilidad de Ganar (Machine Learning)

Modelo de clasificación entrenado con histórico:

```python
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import joblib

def entrenar_modelo_win_probability():
    """
    Features:
    - Precio ofertado vs precio promedio histórico (ratio)
    - Experiencia previa del proveedor en categoría
    - Región match (local vs foráneo)
    - Tamaño del proveedor (PYME vs grande)
    - Día de la semana de cierre
    - Cantidad de competidores (estimado)

    Target: es_ganador (1/0)
    """

    query = """
        SELECT
            monto_total / promedio_categoria AS precio_ratio,
            COUNT(*) OVER (PARTITION BY rut_proveedor, categoria) AS experiencia,
            CASE WHEN region_proveedor = region_licitacion THEN 1 ELSE 0 END AS local,
            -- ... más features
            es_ganador
        FROM historico_licitaciones_features
    """

    df = pd.read_sql(query, conn)

    X = df.drop('es_ganador', axis=1)
    y = df['es_ganador']

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # Guardar modelo
    joblib.dump(model, 'models/win_probability_v1.pkl')

    return model

# Usar en comando /analizar
def predecir_probabilidad_ganar(licitacion, usuario):
    model = joblib.load('models/win_probability_v1.pkl')

    features = extraer_features(licitacion, usuario)
    probabilidad = model.predict_proba([features])[0][1]

    return {
        "probabilidad": round(probabilidad * 100, 1),
        "factores_clave": get_feature_importance(model, features),
        "recomendaciones": generar_recomendaciones(features, probabilidad)
    }
```

### Distribución de Features por Tier

| Feature | FREE | EMPRENDEDOR | PYME | PROFESIONAL |
|---------|------|-------------|------|-------------|
| Búsqueda básica | ✅ | ✅ | ✅ | ✅ |
| Alertas keyword | ❌ | ✅ (3) | ✅ (10) | ✅ (ilimitado) |
| **Alertas semánticas (IA)** | ❌ | ❌ | ✅ | ✅ |
| Análisis precio básico | ✅ (2/día) | ✅ (5/día) | ✅ (10/día) | ✅ (ilimitado) |
| **Análisis precio avanzado** | ❌ | ✅ | ✅ | ✅ |
| **Scoring probabilidad** | ❌ | ❌ | ✅ | ✅ |
| **Generador propuestas** | ❌ | ❌ | ✅ (5/mes) | ✅ (ilimitado) |
| **Análisis competencia** | ❌ | ❌ | ❌ | ✅ |
| API access | ❌ | ❌ | ❌ | ✅ |

---

## Integración con Stack de Monitoreo

### Infraestructura Existente

El servidor ya cuenta con:
- **Traefik** (reverse proxy)
- **Prometheus + Node Exporter + cAdvisor** (métricas)
- **Grafana** (dashboards)
- **Loki + Promtail** (logs centralizados)
- **Uptime Kuma** (uptime monitoring)
- **Portainer** (gestión de Docker)

### 5.1 Exponer Métricas de Prometheus

Agregar endpoint `/metrics` al bot:

```python
# src/metrics_server.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from aiohttp import web
import asyncio

# Métricas de negocio
command_counter = Counter(
    'compra_agil_commands_total',
    'Total comandos ejecutados',
    ['command', 'tier', 'status']
)

ml_latency = Histogram(
    'compra_agil_ml_duration_seconds',
    'Duración análisis ML',
    ['analysis_type']
)

active_subscriptions = Gauge(
    'compra_agil_subscriptions',
    'Suscripciones activas por tier',
    ['tier']
)

cache_hits = Counter(
    'compra_agil_cache_hits_total',
    'Cache hits/misses',
    ['result']
)

async def metrics_handler(request):
    return web.Response(body=generate_latest(REGISTRY), content_type='text/plain')

async def start_metrics_server():
    app = web.Application()
    app.router.add_get('/metrics', metrics_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    print("📊 Metrics server running on :8000/metrics")
```

### 5.2 Actualizar docker-compose.yml

```yaml
services:
  bot:
    image: ghcr.io/gerardbourguett/bot-compra-agil/bot:latest
    container_name: compra_agil_bot
    restart: unless-stopped
    networks:
      - default
      - traefik_default  # ← Conectar a red de Traefik
    labels:
      # Prometheus scraping
      - "prometheus.scrape=true"
      - "prometheus.port=8000"
      - "prometheus.path=/metrics"
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/metrics', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  traefik_default:
    external: true
```

### 5.3 Configurar Prometheus Scraping

Agregar a `/devops/monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'compra_agil_bot'
    static_configs:
      - targets: ['compra_agil_bot:8000']
        labels:
          app: 'compra_agil'
          service: 'telegram_bot'

  - job_name: 'compra_agil_scraper'
    static_configs:
      - targets: ['compra_agil_scraper:8000']
        labels:
          app: 'compra_agil'
          service: 'scraper'
```

### 5.4 Logging Estructurado para Loki

```python
# src/logger_config.py
import logging
import json
from datetime import datetime

class LokiFormatter(logging.Formatter):
    """Formato JSON para Promtail/Loki"""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "app": "compra_agil",
            "service": "telegram_bot",
            "message": record.getMessage(),
        }

        # Contexto adicional
        for attr in ['user_id', 'tier', 'command', 'duration_ms', 'error']:
            if hasattr(record, attr):
                log_obj[attr] = getattr(record, attr)

        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(LokiFormatter())

    logger = logging.getLogger('compra_agil')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger
```

### 5.5 Dashboard de Grafana

**Métricas clave a visualizar:**

1. **Panel: Usuarios Activos por Tier**
   ```promql
   compra_agil_subscriptions
   ```

2. **Panel: Comandos por Segundo**
   ```promql
   rate(compra_agil_commands_total[5m])
   ```

3. **Panel: Latencia ML (p95)**
   ```promql
   histogram_quantile(0.95, compra_agil_ml_duration_seconds_bucket)
   ```

4. **Panel: Cache Hit Rate**
   ```promql
   rate(compra_agil_cache_hits_total{result="hit"}[5m]) /
   rate(compra_agil_cache_hits_total[5m])
   ```

5. **Panel: Features Premium Bloqueadas (Conversión)**
   ```promql
   increase(compra_agil_commands_total{status="blocked"}[1h])
   ```

### 5.6 Uptime Kuma Monitors

Agregar en UI de Uptime Kuma:
- **Bot Health**: HTTP monitor a `http://compra_agil_bot:8000/metrics` cada 60s
- **Scraper Health**: TCP monitor a `compra_agil_scraper:8000` cada 120s
- **PostgreSQL**: PostgreSQL monitor directo a puerto 5433
- **Telegram API**: HTTP Keyword monitor a `https://api.telegram.org`

### 5.7 Alertas vía Telegram

```python
# src/monitoring/alerts.py
import os
from telegram import Bot

ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
alert_bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))

async def send_admin_alert(severity: str, message: str, metrics: dict = None):
    """Envía alerta al admin usando el mismo bot"""
    icons = {"critical": "🔴", "warning": "🟡", "info": "🟢", "success": "✅"}

    text = f"{icons[severity]} <b>{severity.upper()}</b>\n\n"
    text += f"{message}\n"

    if metrics:
        text += "\n📊 <b>Métricas:</b>\n"
        for key, value in metrics.items():
            text += f"  • {key}: {value}\n"

    await alert_bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=text,
        parse_mode='HTML'
    )

# Ejemplos de uso
if new_paid_subscriber:
    await send_admin_alert(
        "success",
        f"🎉 Nuevo suscriptor PYME!",
        {"Usuario": user_name, "Plan": tier, "Precio": "$9.990"}
    )

if celery_queue > 100:
    await send_admin_alert(
        "warning",
        "Queue de tareas alto",
        {"Pendientes": celery_queue, "Workers": worker_count}
    )
```

---

## Plan de Implementación por Fases

### Resumen de Prioridades

```
┌─────────────────────────────────────────────────┐
│  AHORA (crítico):                               │
│  • Fase 0: Estabilización                       │
│  • Fase 1: Persistencia bulletproof             │
│  • Fase 2: Optimización BD                      │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  SIGUIENTE (1-2 semanas):                       │
│  • Fase 3: Monitoreo                            │
│  • Fase 4: Workers/Queue                        │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  DESPUÉS (1 mes):                               │
│  • Fase 5: Features IA Premium                  │
│  • Fase 6: Monetización                         │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  FUTURO (cuando escales):                       │
│  • Fase 7: Escalabilidad horizontal             │
└─────────────────────────────────────────────────┘
```

---

### FASE 0: Estabilización (1-2 días) 🔧

**Objetivo:** Arreglar lo que está roto antes de construir cosas nuevas.

**Tareas:**
1. ✅ **Arreglar healthchecks** (bot y scraper están unhealthy)
   - Bot: endpoint `/health` o `/metrics`
   - Scraper: verificar conexión a BD

2. ✅ **Verificar preservación de volúmenes**
   - Test manual: deploy → verificar que datos persisten
   - Agregar step de validación post-deploy en CI/CD

3. ✅ **Configurar logging estructurado**
   - JSON formatter para Loki/Promtail
   - Logs centralizados visibles en Grafana

**Criterios de éxito:**
- [ ] `docker ps` muestra todos los servicios como `healthy`
- [ ] Logs JSON visibles en Grafana Loki
- [ ] Deploy manual exitoso sin pérdida de datos

**Entregable:** Sistema estable, servicios healthy, logs centralizados funcionando.

---

### FASE 1: Persistencia Bulletproof (2-3 días) 💾

**Objetivo:** Garantizar que NUNCA se pierdan los datos históricos.

**Tareas:**
1. ✅ **Backup automático mejorado**
   - Pre-deploy: backup obligatorio (ya existe parcialmente en línea 107 de ci-cd.yml)
   - Post-deploy: verificar que datos siguen ahí (línea 152-154)
   - Fallo del deploy si no hay backup exitoso

2. ✅ **Backup a almacenamiento externo**
   - Subir backups a GitHub Artifacts (gratis, 500MB)
   - Workflow semanal: backup completo comprimido
   - Retención: 4 backups mensuales

3. ✅ **Script de restauración**
   ```bash
   # scripts/restore_backup.sh
   # Uso: ./scripts/restore_backup.sh [backup_file.sql.gz]
   ```
   - Descargar desde GitHub Artifacts
   - Restaurar a PostgreSQL
   - Documentado en README

4. ✅ **Verificar workflow de importación histórica**
   - Confirmar que `.github/workflows/import-historico.yml` funciona con Docker
   - Test manual: importar 1 mes de datos (ej: COT_2024-12.zip)
   - Validar detección de duplicados

**Criterios de éxito:**
- [ ] Deploy exitoso con backup pre/post
- [ ] Backup subido a GitHub Artifacts automáticamente
- [ ] Script `restore_backup.sh` funcional y documentado
- [ ] Importación histórica mensual sin duplicados

**Archivos a crear/modificar:**
- `scripts/restore_backup.sh` (nuevo)
- `.github/workflows/ci-cd.yml` (mejorar backup steps)
- `.github/workflows/backup-to-artifacts.yml` (nuevo, semanal)
- `docs/DISASTER_RECOVERY.md` (nuevo)

**Entregable:** Deploys seguros, backups automáticos, capacidad de disaster recovery.

---

### FASE 2: Optimización de Base de Datos (3-4 días) 🚀

**Objetivo:** BD rápida para 10M+ registros, queries en <1s.

**Tareas:**
1. ✅ **Auditar índices existentes**
   - Revisar `scripts/create_indexes.py`
   - Ejecutar `EXPLAIN ANALYZE` en queries lentas
   - Identificar índices faltantes

2. ✅ **Particionamiento de `historico_licitaciones`**
   - Script de migración: `scripts/partition_historico.py`
   - Crear particiones mensuales desde 2020 hasta presente
   - Idempotente (detectar si ya está particionada)
   - Ejecutar en horario de baja actividad

3. ✅ **Optimizar queries lentas**
   - Habilitar `pg_stat_statements` en PostgreSQL
   - Identificar top 10 queries más lentas
   - Reescribir queries N+1 en `ml_precio_optimo.py` y `rag_historico.py`
   - Agregar logging de duración de queries (EXPLAIN ANALYZE en modo debug)

4. ✅ **Configurar Redis**
   - Agregar servicio Redis al docker-compose
   - Actualizar `redis_cache.py` para caché de ML
   - Cachear: resultados ML (TTL 1h), listados (TTL 15min), embeddings (TTL 24h)
   - Métricas de cache hit rate

**Criterios de éxito:**
- [ ] Queries de análisis ML <1s en p95
- [ ] Búsqueda RAG <2s en p95
- [ ] Particionamiento activo y funcional
- [ ] Redis operativo con hit rate >60%

**Archivos a crear/modificar:**
- `scripts/partition_historico.py` (nuevo)
- `scripts/create_indexes.py` (actualizar con índices nuevos)
- `docker-compose.yml` (agregar Redis)
- `src/redis_cache.py` (mejorar con TTL configurables)
- `src/ml_precio_optimo.py` (optimizar queries)
- `src/rag_historico.py` (optimizar queries)

**Entregable:** Queries <1s, experiencia de usuario fluida, BD lista para escalar.

---

### FASE 3: Monitoreo y Observabilidad (2 días) 📊

**Objetivo:** Visibilidad total de lo que pasa en producción.

**Tareas:**
1. ✅ **Instrumentar código con Prometheus**
   - Crear `src/metrics_server.py` con endpoint `/metrics`
   - Métricas de negocio: comandos, suscripciones, conversión
   - Métricas de performance: latencia ML, cache hit rate

2. ✅ **Configurar Prometheus scraping**
   - Actualizar `/devops/monitoring/prometheus/prometheus.yml`
   - Agregar jobs: compra_agil_bot, compra_agil_scraper
   - Labels para filtrar por servicio

3. ✅ **Crear dashboard en Grafana**
   - `grafana/dashboards/compra_agil.json`
   - Paneles: usuarios activos, comandos/s, latencia ML, cache hit rate
   - Panel de conversión: features bloqueadas vs upgrades

4. ✅ **Configurar alertas vía Telegram**
   - `src/monitoring/alerts.py`
   - Alertas: disco >90%, queue >100, nuevo suscriptor pago
   - Configurar `ADMIN_CHAT_ID` en `.env`

5. ✅ **Agregar healthchecks**
   - Bot: HTTP check a `/metrics`
   - Scraper: PostgreSQL connection check
   - Configurar en Uptime Kuma

**Criterios de éxito:**
- [ ] Métricas visibles en Prometheus
- [ ] Dashboard de Grafana funcional con datos reales
- [ ] Alertas de Telegram funcionando
- [ ] Todos los servicios `healthy` en `docker ps`

**Archivos a crear/modificar:**
- `src/metrics_server.py` (nuevo)
- `src/monitoring/alerts.py` (nuevo)
- `src/logger_config.py` (nuevo, JSON formatter)
- `docker-compose.yml` (healthchecks y labels Prometheus)
- `/devops/monitoring/prometheus/prometheus.yml` (actualizar)
- `/devops/grafana/dashboards/compra_agil.json` (nuevo)

**Entregable:** Dashboard en vivo, alertas automáticas, visibilidad de métricas de negocio.

---

### FASE 4: Workers y Queue (3-4 días) ⚙️

**Objetivo:** Bot siempre responsivo, tareas pesadas en background.

**Tareas:**
1. ✅ **Configurar Celery**
   - Crear `src/tasks.py` con configuración Celery
   - Definir queues: `ml`, `scraping`, `exports`
   - Configurar Redis como broker

2. ✅ **Migrar tareas pesadas a Celery**
   - `/precio` → `tasks.calcular_precio_optimo.delay()`
   - `/rag` → `tasks.buscar_rag_historico.delay()`
   - `/generar_excel` → `tasks.generar_excel_export.delay()`
   - Scraper → `tasks.ejecutar_scraper.delay()` con Celery Beat

3. ✅ **Actualizar docker-compose**
   - Agregar servicios: `celery-worker-ml`, `celery-worker-scraping`, `celery-beat`
   - Configurar concurrencia: ML (2 workers), scraping (1 worker)

4. ✅ **Implementar notificaciones asíncronas**
   - Cuando tarea termina, notificar al usuario via bot
   - Callbacks para tareas exitosas/fallidas
   - Retry automático con backoff exponencial

5. ✅ **Monitoreo de workers**
   - Métricas de Celery en Prometheus
   - Panel de Grafana: queue length, workers activos, latencia de tareas
   - Alerta si queue >100 tareas

**Criterios de éxito:**
- [ ] Bot responde instantáneamente (<200ms)
- [ ] Análisis ML se ejecutan en background
- [ ] Notificaciones asíncronas funcionando
- [ ] Scraper ejecuta cada 6h automáticamente vía Celery Beat

**Archivos a crear/modificar:**
- `src/tasks.py` (nuevo)
- `src/bot_ml_commands.py` (migrar a async con Celery)
- `src/scheduler.py` (migrar a Celery Beat)
- `docker-compose.yml` (agregar workers y beat)
- `requirements.txt` (agregar celery, redis)

**Entregable:** Bot súper responsivo, tareas pesadas no bloquean, mejor UX.

---

### FASE 5: Features de IA Premium (5-7 días) 🤖

**Objetivo:** Diferenciación competitiva, valor agregado real.

**Prioridad de implementación:**

**5.1 Análisis de Precios Mejorado (Quick Win - 1 día)**
- Mejorar `ml_precio_optimo.py` con insights específicos
- Añadir: precio por organismo, por región, competidores frecuentes
- Recomendaciones accionables basadas en histórico

**5.2 Scoring de Probabilidad de Ganar (Alto Valor - 2 días)**
- Entrenar modelo Random Forest con histórico
- Features: precio ratio, experiencia, región, tamaño proveedor
- Nuevo comando: `/scoring <licitacion_id>`
- Explicación de factores clave (feature importance)

**5.3 Matching Semántico con Embeddings (Diferenciador - 2 días)**
- Instalar extensión `pgvector` en PostgreSQL
- Generar embeddings de licitaciones con Gemini
- Tabla `licitacion_embeddings` con índice IVFFlat
- Migrar alertas a semantic search
- Comando: `/alertas_ia <descripcion_empresa>`

**5.4 Generador de Propuestas (Premium Killer Feature - 2 días)**
- Nuevo comando: `/generar_propuesta <licitacion_id>`
- Validar tier PYME/PROFESIONAL
- Prompt engineering con contexto de licitación + perfil empresa
- Exportar a PDF/DOCX
- Tracking de uso (5/mes para PYME, ilimitado para PROFESIONAL)

**Criterios de éxito:**
- [ ] Análisis de precios retorna 3 insights accionables
- [ ] Scoring predice con >70% accuracy
- [ ] Alertas semánticas encuentran >2x más matches relevantes
- [ ] Generador crea propuestas de calidad (validar manualmente)

**Archivos a crear/modificar:**
- `src/ml_precio_optimo_v2.py` (nuevo)
- `src/ml_win_probability.py` (nuevo, modelo scoring)
- `src/semantic_search.py` (nuevo, embeddings)
- `src/generador_propuestas.py` (nuevo)
- `scripts/train_win_model.py` (nuevo, entrenamiento)
- `scripts/generate_embeddings.py` (nuevo, batch embeddings)
- `migrations/add_pgvector.sql` (nuevo)

**Entregable:** Features premium implementadas, tier PYME/PROFESIONAL con valor real.

---

### FASE 6: Monetización y Pagos (4-5 días) 💰

**Objetivo:** Convertir usuarios gratis a pagos, revenue real.

**Tareas:**

**6.1 Integrar Pasarela de Pago (2 días)**
- Integrar Flow (recomendado para Chile) o Stripe
- Tabla `payments` para transacciones
- Webhook para confirmación de pago
- Comando: `/upgrade` con opciones de planes

**6.2 Sistema de Facturación (1 día)**
- Generar boleta/factura automática con datos chilenos
- Almacenar en tabla `invoices`
- Enviar por Telegram como PDF

**6.3 Gestión de Suscripciones (1 día)**
- Auto-renovación mensual
- Downgrade automático si falla pago
- Notificaciones: 3 días antes de vencimiento
- Comando: `/mis_suscripciones`

**6.4 Analytics de Conversión (1 día)**
- Funnel en Grafana: FREE → Bloqueado → Upgrade → Pago
- Métricas: tasa de conversión, MRR, churn rate
- A/B testing de precios (opcional)

**Criterios de éxito:**
- [ ] Pago exitoso actualiza tier del usuario
- [ ] Factura se genera automáticamente
- [ ] Auto-renovación funciona correctamente
- [ ] Dashboard de conversión operativo

**Archivos a crear/modificar:**
- `src/payments.py` (nuevo, integración Flow/Stripe)
- `src/invoicing.py` (nuevo, generación facturas)
- `src/bot_upgrade_commands.py` (nuevo)
- `migrations/add_payments_tables.sql` (nuevo)
- `.env.example` (agregar secrets de Flow/Stripe)

**Entregable:** Sistema de pagos funcionando, primeros clientes pagos.

---

### FASE 7: Escalabilidad Horizontal (Futuro) 📈

**Cuándo:** Cuando tengas >500 usuarios activos diarios o el VPS esté al 80% CPU constantemente.

**Tareas:**
1. ✅ **Migrar a multi-servidor**
   - Load balancer (Traefik ya lo tienes)
   - Múltiples workers Celery en servidores separados
   - Redis en modo cluster

2. ✅ **BD administrada**
   - PostgreSQL en servicio managed (DigitalOcean, AWS RDS)
   - Backups automáticos, réplicas read
   - Conexión pooling (PgBouncer)

3. ✅ **CDN para assets**
   - Si implementas dashboard web
   - CloudFlare (gratis) o AWS CloudFront

4. ✅ **Auto-scaling**
   - Docker Swarm (más simple que Kubernetes)
   - O Kubernetes si crece mucho más

**Criterios de éxito:**
- [ ] Sistema maneja 10,000+ usuarios concurrentes
- [ ] Latencia p95 <500ms bajo carga
- [ ] Uptime >99.9%

**Entregable:** Sistema listo para escalar masivamente.

---

## Anexos

### Métricas de Éxito del Proyecto

**Técnicas:**
- Uptime: >99.5%
- Queries de BD: p95 <1s
- Latencia de bot: p95 <200ms
- Cache hit rate: >60%

**Negocio:**
- Usuarios activos mensuales: meta 1,000 en 3 meses
- Tasa de conversión FREE → PAGO: meta 5%
- MRR (Monthly Recurring Revenue): meta $500,000 CLP en 6 meses
- Churn rate: <10% mensual

### Dependencias Técnicas

**Python packages nuevos:**
```
celery==5.3.4
redis==5.0.1
prometheus-client==0.19.0
pgvector==0.2.3
scikit-learn==1.3.2
joblib==1.3.2
```

**PostgreSQL extensions:**
- `pg_trgm` (ya instalada probablemente)
- `pgvector` (nueva)
- `pg_stat_statements` (para query profiling)

**Infraestructura:**
- Redis 7.x (nuevo servicio Docker)
- Espacio en disco: +20GB para backups
- RAM adicional: ~500MB (Celery workers + Redis)

### Riesgos y Mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|--------------|------------|
| Particionamiento corrompe datos | Alto | Baja | Backup completo antes, rollback plan |
| Celery workers colapsan servidor | Medio | Media | Monitoreo de recursos, límite de concurrencia |
| Integración de pagos falla | Alto | Baja | Testing exhaustivo en sandbox, validación manual |
| Embeddings consumen mucha API | Bajo | Alta | Cachear embeddings, batch processing |
| Modelo ML overfitting | Medio | Media | Validación cruzada, monitoreo de accuracy |

---

## Conclusión

Este plan transforma CompraAgil de un bot funcional a un SaaS escalable y monetizable con:

1. **Persistencia bulletproof**: Nunca perder datos históricos
2. **Performance optimizado**: Queries <1s, bot siempre responsivo
3. **Features premium**: Matching IA, scoring, generador de propuestas
4. **Observabilidad completa**: Métricas de negocio en tiempo real
5. **Monetización clara**: Sistema de pagos y facturación

**Próximo paso:** Comenzar con Fase 0 (Estabilización) y Fase 1 (Persistencia).

---

**Última actualización:** 2025-12-28
**Versión:** 1.0
