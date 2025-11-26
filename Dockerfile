# Dockerfile para el Bot de Compra Ágil
FROM python:3.11-slim

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

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación desde src/
COPY src/*.py ./
COPY .env.example .env.example

# Crear directorio para logs
RUN mkdir -p /app/logs

# Exponer puerto (si fuera necesario en el futuro)
EXPOSE 8000

# Comando por defecto (se puede sobrescribir en docker-compose)
CMD ["python", "bot_inteligente.py"]
