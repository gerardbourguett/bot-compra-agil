# Etapa base con dependencias comunes
FROM python:3.11-slim AS base

# Establecer directorio de trabajo
WORKDIR /app

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/*.py ./
COPY .env.example .env.example

# Crear directorio para logs
RUN mkdir -p /app/logs

# Etapa para el Bot
FROM base AS bot
CMD ["python", "bot_inteligente.py"]

# Etapa para el Scraper
FROM base AS scraper
CMD ["python", "scraper.py"]
