# 🌐 Setup en Vultr VPS - CompraÁgil API v3

## Información del Server

**Secrets Configurados en GitHub**:
- ✅ `VPS_HOST` - IP del servidor Vultr
- ✅ `VPS_USER` - Usuario SSH
- ✅ `VPS_PASSWORD` - Contraseña SSH
- ✅ `DATABASE_URL` - Conexión a PostgreSQL
- ✅ `GEMINI_API_KEY` - API Key de Google
- ✅ `POSTGRES_PASSWORD` - Password de PostgreSQL
- ✅ `TELEGRAM_TOKEN` - Token del bot

---

## 🚀 Setup Inicial del VPS

### 1. Conectarse al VPS

```bash
ssh VPS_USER@VPS_HOST
# Ingresa VPS_PASSWORD cuando te lo pida
```

### 2. Actualizar Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Instalar Dependencias Base

```bash
# Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip git -y

# Redis (para cache)
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Nginx (reverse proxy)
sudo apt install nginx -y
sudo systemctl enable nginx
```

### 4. Clonar Repositorio

```bash
cd ~
git clone https://github.com/TU-USUARIO/bot-compra-agil.git
cd bot-compra-agil
```

### 5. Crear Virtual Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 6. Configurar Variables de Entorno

```bash
nano .env
```

Pega:
```bash
# PostgreSQL ya está corriendo, usa el DATABASE_URL del secret
DATABASE_URL=postgresql://compra_agil_user:PASSWORD@64.176.19.51:5433/compra_agil

# Redis local
REDIS_URL=redis://localhost:6379/0

# Gemini AI
GEMINI_API_KEY=tu_key_aqui

# Telegram Bot
TELEGRAM_TOKEN=tu_token_aqui
```

---

## 📋 Crear Servicio Systemd

### 1. Crear archivo de servicio

```bash
sudo nano /etc/systemd/system/compraagil-api.service
```

### 2. Pegar configuración

```ini
[Unit]
Description=CompraÁgil API v3.0
After=network.target redis.service

[Service]
Type=simple
User=TU_VPS_USER
Group=TU_VPS_USER
WorkingDirectory=/home/TU_VPS_USER/bot-compra-agil

# Variables de entorno
EnvironmentFile=/home/TU_VPS_USER/bot-compra-agil/.env

# Comando para arrancar (usa gunicorn para producción)
ExecStart=/home/TU_VPS_USER/bot-compra-agil/.venv/bin/gunicorn \
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

**IMPORTANTE**: Reemplaza `TU_VPS_USER` con tu usuario real.

### 3. Crear directorio de logs

```bash
sudo mkdir -p /var/log/compraagil
sudo chown TU_VPS_USER:TU_VPS_USER /var/log/compraagil
```

### 4. Instalar Gunicorn

```bash
source .venv/bin/activate
pip install gunicorn
```

### 5. Habilitar y arrancar servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable compraagil-api
sudo systemctl start compraagil-api

# Verificar estado
sudo systemctl status compraagil-api
```

---

## 🌐 Configurar Nginx

### 1. Crear configuración

```bash
sudo nano /etc/nginx/sites-available/compraagil
```

### 2. Pegar configuración

```nginx
server {
    listen 80;
    server_name TU_DOMINIO_O_IP;  # Cambia esto

    # Tamaño máximo de upload
    client_max_body_size 10M;

    # Logs
    access_log /var/log/nginx/compraagil_access.log;
    error_log /var/log/nginx/compraagil_error.log;

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
}
```

### 3. Activar sitio

```bash
sudo ln -s /etc/nginx/sites-available/compraagil /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Configurar Firewall

```bash
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS (para después)
sudo ufw enable
```

---

## 🔒 SSL con Let's Encrypt (Opcional pero Recomendado)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d tu-dominio.com
```

---

## 🧪 Verificar que Todo Funciona

### 1. Check del servicio

```bash
sudo systemctl status compraagil-api
```

### 2. Ver logs

```bash
# Logs del servicio
sudo journalctl -u compraagil-api -f

# Logs de la aplicación
tail -f /var/log/compraagil/access.log
tail -f /var/log/compraagil/error.log
```

### 3. Test de health

```bash
curl http://localhost:8000/health
```

Debería responder:
```json
{
  "status": "healthy",
  "database": "connected",
  "historico_records": 10600000,
  "redis": "enabled"
}
```

### 4. Test desde fuera

```bash
curl http://TU_IP/health
```

---

## 🚀 GitHub Actions - Cómo Funciona

Cuando hagas `git push` a `main`:

1. GitHub Actions se activa automáticamente
2. Ejecuta tests en la nube
3. Si pasan → Se conecta a tu VPS por SSH
4. Hace `git pull` del código nuevo
5. Instala dependencias actualizadas
6. Reinicia el servicio `sudo systemctl restart compraagil-api`
7. Verifica health check
8. ✅ Deploy completo!

**Ver deploys**: GitHub → Tu repo → Actions

---

## 🔧 Comandos Útiles

### Reiniciar API

```bash
sudo systemctl restart compraagil-api
```

### Ver logs en tiempo real

```bash
sudo journalctl -u compraagil-api -f
```

### Ver estado de servicios

```bash
sudo systemctl status compraagil-api nginx redis-server
```

### Actualizar manualmente
```bash
cd ~/bot-compra-agil
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart compraagil-api
```

---

## 🐛 Troubleshooting

### API no arranca

```bash
# Ver logs detallados
sudo journalctl -u compraagil-api -n 100 --no-pager

# Verificar que el puerto 8000 está libre
sudo netstat -tulpn | grep :8000

# Restart manual
sudo systemctl stop compraagil-api
sudo systemctl start compraagil-api
```

### Database connection error

```bash
# Verificar DATABASE_URL en .env
cat .env | grep DATABASE_URL

# Test de conexión PostgreSQL
psql "postgresql://compra_agil_user:PASSWORD@64.176.19.51:5433/compra_agil"
```

### Redis error

```bash
# Verificar Redis
sudo systemctl status redis-server

# Reiniciar Redis
sudo systemctl restart redis-server
```

---

## 📊 Monitoreo

### Ver uso de recursos

```bash
# CPU y memoria
htop

# Espacio en disco
df -h

# Procesos de gunicorn
ps aux | grep gunicorn
```

### Ver requests en tiempo real

```bash
tail -f /var/log/nginx/compraagil_access.log
```

---

## ✅ Checklist de Deployment

Antes de tu primer deploy:

- [ ] VPS actualizado (`apt update && upgrade`)
- [ ] Python 3.11 instalado
- [ ] Redis instalado y corriendo
- [ ] Nginx instalado y configurado
- [ ] Repositorio clonado en `~/bot-compra-agil`
- [ ] Virtual environment creado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] `.env` configurado con todas las variables
- [ ] Systemd service creado y habilitado
- [ ] Logs directory creado (`/var/log/compraagil`)
- [ ] Firewall configurado (puertos 22, 80, 443)
- [ ] Health check responde (curl http://localhost:8000/health)
- [ ] Nginx proxy funcionando
- [ ] (Opcional) SSL configurado con Let's Encrypt

---

**Siguiente paso**: Hacer primer push a GitHub y ver el deploy automático! 🚀
