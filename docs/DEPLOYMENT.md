# 🚀 Guía de Deployment - API v3.0

## Opciones de Deployment

### Opción 1: Servidor VPS/Dedicated (Recomendado)
**Plataformas**: DigitalOcean, AWS EC2, Linode, Vultr

### Opción 2: Platform-as-a-Service
**Plataformas**: Railway, Render, Fly.io, Heroku

### Opción 3: Serverless
**Plataformas**: AWS Lambda, Google Cloud Run

---

## 🎯 Configuración Recomendada: VPS con GitHub Actions

### Arquitectura:
```
GitHub (push) → GitHub Actions → SSH a VPS → Deploy API
```

---

## 📋 Paso 1: Preparar el Servidor

### 1.1 Instalar Dependencias en el Servidor

```bash
# SSH a tu servidor
ssh user@tu-servidor.com

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip -y

# Instalar PostgreSQL (si no está)
sudo apt install postgresql postgresql-contrib -y

# Instalar Redis
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Instalar Nginx (reverse proxy)
sudo apt install nginx -y
```

### 1.2 Crear Usuario para la App

```bash
sudo useradd -m -s /bin/bash compraagil
sudo su - compraagil

# Crear directorio para la app
mkdir -p ~/app
cd ~/app
```

---

## 📋 Paso 2: Configurar Systemd Service

Crea: `/etc/systemd/system/compraagil-api.service`

```ini
[Unit]
Description=CompraÁgil API v3.0
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=compraagil
Group=compraagil
WorkingDirectory=/home/compraagil/app
Environment="PATH=/home/compraagil/app/.venv/bin"
Environment="DATABASE_URL=postgresql://user:pass@localhost:5432/compra_agil"
Environment="REDIS_URL=redis://localhost:6379/0"
Environment="GEMINI_API_KEY=your_key_here"

# Comando para arrancar
ExecStart=/home/compraagil/app/.venv/bin/gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile /var/log/compraagil/access.log \
    --error-logfile /var/log/compraagil/error.log \
    api_backend_v3:app

# Reinicio automático
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Crear logs directory
```bash
sudo mkdir -p /var/log/compraagil
sudo chown compraagil:compraagil /var/log/compraagil
```

### Habilitar y arrancar servicio
```bash
sudo systemctl daemon-reload
sudo systemctl enable compraagil-api
sudo systemctl start compraagil-api
sudo systemctl status compraagil-api
```

---

## 📋 Paso 3: Configurar Nginx (Reverse Proxy)

Crea: `/etc/nginx/sites-available/compraagil`

```nginx
server {
    listen 80;
    server_name api.tudominio.com;  # Cambia esto

    # Logs
    access_log /var/log/nginx/compraagil_access.log;
    error_log /var/log/nginx/compraagil_error.log;

    # Tamaño máximo de upload
    client_max_body_size 10M;

    # Proxy a la API
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (si los tienes)
    location /static/ {
        alias /home/compraagil/app/static/;
        expires 30d;
    }
}
```

### Activar sitio
```bash
sudo ln -s /etc/nginx/sites-available/compraagil /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL con Let's Encrypt (HTTPS)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d api.tudominio.com
```

---

## 📋 Paso 4: GitHub Actions Workflow

Crea: `.github/workflows/deploy.yml`

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main  # Deploy solo en push a main
    paths:
      - 'api_backend_v3.py'
      - 'src/**'
      - 'requirements.txt'
      - '.github/workflows/deploy.yml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: 🚀 Deploy via SSH
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          port: 22
          script: |
            cd /home/compraagil/app
            
            # Pull latest code
            git pull origin main
            
            # Activate venv
            source .venv/bin/activate
            
            # Install dependencies
            pip install -r requirements.txt
            
            # Run migrations (si las tienes)
            # alembic upgrade head
            
            # Restart service
            sudo systemctl restart compraagil-api
            
            # Check status
            sudo systemctl status compraagil-api --no-pager
            
            # Test health endpoint
            sleep 5
            curl -f http://localhost:8000/health || exit 1
            
            echo "✅ Deployment successful!"
```

---

## 📋 Paso 5: Configurar Secrets en GitHub

Ve a tu repo → Settings → Secrets and variables → Actions → New repository secret

Añade:
- `SERVER_HOST`: IP o dominio de tu servidor
- `SERVER_USER`: `compraagil`
- `SSH_PRIVATE_KEY`: Tu llave SSH privada

### Generar SSH Key
```bash
# En tu máquina local
ssh-keygen -t ed25519 -C "github-actions"
# Guarda en: ~/.ssh/github_actions

# Copia la clave pública al servidor
ssh-copy-id -i ~/.ssh/github_actions.pub compraagil@tu-servidor.com

# Copia la clave PRIVADA a GitHub Secrets
cat ~/.ssh/github_actions
```

---

## 📋 Paso 6: Script de Deployment Manual

Crea: `deploy.sh`

```bash
#!/bin/bash
set -e

echo "🚀 Deploying CompraÁgil API v3.0..."

# Variables
APP_DIR="/home/compraagil/app"
SERVICE_NAME="compraagil-api"

# Pull latest code
echo "📥 Pulling latest code..."
cd $APP_DIR
git pull origin main

# Activate venv
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet

# Run database migrations (opcional)
# echo "🗄️  Running migrations..."
# alembic upgrade head

# Restart service
echo "🔄 Restarting service..."
sudo systemctl restart $SERVICE_NAME

# Wait for startup
echo "⏳ Waiting for service to start..."
sleep 5

# Check health
echo "🏥 Checking health..."
curl -f http://localhost:8000/health || {
    echo "❌ Health check failed!"
    sudo systemctl status $SERVICE_NAME
    exit 1
}

echo "✅ Deployment successful!"
echo "📊 Service status:"
sudo systemctl status $SERVICE_NAME --no-pager
```

---

## 🔧 Comandos Útiles en Producción

### Ver logs en tiempo real
```bash
# API logs
sudo journalctl -u compraagil-api -f

# Nginx logs
sudo tail -f /var/log/nginx/compraagil_access.log
```

### Reiniciar servicios
```bash
# API
sudo systemctl restart compraagil-api

# Nginx
sudo systemctl restart nginx

# Redis
sudo systemctl restart redis-server
```

### Verificar estado
```bash
# Todos los servicios
sudo systemctl status compraagil-api nginx redis-server postgresql

# Solo API
curl http://localhost:8000/health
```

### Ver procesos
```bash
# Gunicorn workers
ps aux | grep gunicorn

# Conexiones
netstat -tulpn | grep :8000
```

---

## 🐳 Opción Alternativa: Docker

Si prefieres usar Docker (más portable):

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port
EXPOSE 8000

# Run
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "api_backend_v3:app"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - redis
      - postgres
    restart: always

  redis:
    image: redis:7-alpine
    restart: always

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=compra_agil
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - api
    restart: always

volumes:
  pgdata:
```

### GitHub Actions con Docker
```yaml
- name: Build and Deploy
  run: |
    ssh ${{ secrets.SERVER_USER }}@${{ secrets.SERVER_HOST }} << 'EOF'
      cd /home/compraagil/app
      git pull origin main
      docker-compose down
      docker-compose build
      docker-compose up -d
      docker-compose ps
    EOF
```

---

## ✅ Checklist de Deployment

Antes de hacer deploy:

- [ ] Variables de entorno configuradas (`.env`)
- [ ] Base de datos creada y migrada
- [ ] Redis corriendo
- [ ] Nginx configurado
- [ ] SSL (HTTPS) configurado
- [ ] Logs directory creado
- [ ] Systemd service creado
- [ ] GitHub Secrets configurados
- [ ] Health endpoint responde
- [ ] Tests pasan localmente

---

## 🎯 Recomendación Para CompraÁgil

**Setup Ideal:**
1. VPS (DigitalOcean Droplet $12/mes)
2. Systemd + Gunicorn + Uvicorn workers
3. Nginx como reverse proxy
4. GitHub Actions para CI/CD
5. Let's Encrypt para SSL

**Ventajas:**
- Control total
- Costo predecible
- Fácil debugging
- Escalable

---

**Siguiente paso**: ¿Configuro el workflow de GitHub Actions completo?
