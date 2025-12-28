# Multi-stage Dockerfile para Bot, Scraper y API
FROM python:3.11-slim AS base

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar wget para healthchecks y limpiar cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/logs /app/src && \
    chown -R appuser:appuser /app

# Directorio de trabajo
WORKDIR /app

# Copiar requirements primero (cache de Docker)
COPY --chown=appuser:appuser requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

# Cambiar a usuario no-root
USER appuser

# ============================================
# Target: Bot de Telegram
# ============================================
FROM base AS bot

WORKDIR /app

# Health check para el bot
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "bot_inteligente.py" || exit 1

# Comando de inicio
CMD ["python", "src/bot_inteligente.py"]

# ============================================
# Target: Scraper
# ============================================
FROM base AS scraper

WORKDIR /app

# Health check para el scraper
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "scheduler.py" || exit 1

# Comando de inicio
CMD ["python", "src/scheduler.py"]

# ============================================
# Target: API (default)
# ============================================
FROM base AS api

WORKDIR /app

# Instalar gunicorn para API
RUN pip install --no-cache-dir gunicorn uvicorn[standard]

# Health check para API
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["gunicorn", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "/app/logs/access.log", \
     "--error-logfile", "/app/logs/error.log", \
     "--log-level", "info", \
     "api_backend_v3:app"]
