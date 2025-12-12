# Dockerfile optimizado para producción con Kubernetes
FROM python:3.11-slim

# Metadata
LABEL maintainer="Gerard Bourguett"
LABEL description="CompraÁgil API v3.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 apiuser && \
    mkdir -p /app /app/logs && \
    chown -R apiuser:apiuser /app

# Directorio de trabajo
WORKDIR /app

# Copiar requirements primero (cache de Docker)
COPY --chown=apiuser:apiuser requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn uvicorn[standard]

# Copiar código de la aplicación
COPY --chown=apiuser:apiuser . .

# Cambiar a usuario no-root
USER apiuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

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
