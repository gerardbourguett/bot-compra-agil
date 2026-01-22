# 🚀 Guía de DevOps - Bot Compra Ágil

Esta guía explica cómo configurar el servidor y el pipeline de CI/CD para desplegar automáticamente la aplicación.

---

## 📋 Requisitos Previos

### En el Servidor
1. **Docker** y **Docker Compose** instalados
2. **Git** instalado
3. **Usuario SSH** con permisos para ejecutar Docker

### En GitHub
Configurar los siguientes **Secrets** en `Settings > Secrets and variables > Actions`:

| Secret | Descripción |
|--------|-------------|
| `SSH_HOST` | IP o dominio del servidor |
| `SSH_USERNAME` | Usuario SSH para conectar |
| `SSH_KEY` | Clave privada SSH (todo el contenido) |
| `GH_PAT` | Personal Access Token con permisos `read:packages` |
| `APP_DIR` | Directorio de la app en el servidor (ej: `/opt/compra-agil`) |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL |
| `TELEGRAM_TOKEN` | Token del bot de Telegram |
| `GEMINI_API_KEY` | API Key de Gemini |

---

## 🗄️ Base de Datos Independiente

Para levantar **solo** PostgreSQL y Redis (sin la aplicación):

```bash
docker compose -f docker-compose.db.yml up -d
```

Esto es útil para:
- Desarrollo local
- Mantener las bases de datos corriendo mientras actualizas la app
- Debugging de problemas de conectividad

### Verificar que están corriendo:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Variables de conexión:
- **PostgreSQL**: `postgresql://compra_agil_user:PASSWORD@localhost:5433/compra_agil`
- **Redis**: `redis://localhost:6379/0`

---

## 🔄 Pipeline de CI/CD

El workflow `.github/workflows/simple_deploy.yml` se ejecuta automáticamente al hacer push a `main`.

### Qué hace:
1. **Build**: Construye las imágenes Docker (bot y scraper)
2. **Push**: Sube las imágenes a GitHub Container Registry (GHCR)
3. **Deploy**: Conecta por SSH al servidor y:
   - Descarga las nuevas imágenes
   - Actualiza el código
   - Reinicia los contenedores

### Ejecutar manualmente:
Ve a `Actions > Build and Deploy > Run workflow`

---

## 🛠️ Configuración Inicial del Servidor

### 1. Instalar Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Cerrar sesión y volver a entrar para aplicar cambios
```

### 2. Crear directorio de la aplicación
```bash
sudo mkdir -p /opt/compra-agil
sudo chown $USER:$USER /opt/compra-agil
```

### 3. Configurar SSH Key
```bash
# En tu máquina local, generar una clave si no tienes una
ssh-keygen -t ed25519 -C "deploy-key"

# Copiar la clave pública al servidor
ssh-copy-id -i ~/.ssh/id_ed25519.pub usuario@servidor

# El contenido de ~/.ssh/id_ed25519 (privada) va en el secret SSH_KEY
```

### 4. Primer despliegue (opcional, se hará automático)
```bash
cd /opt/compra-agil
git clone https://github.com/gerardbourguett/bot-compra-agil.git .

# Crear archivo .env
cp .env.example .env
nano .env  # Editar con los valores reales

# Levantar bases de datos primero
docker compose -f docker-compose.db.yml up -d

# Luego la app completa
docker compose up -d
```

---

## 🔍 Comandos Útiles

### Ver logs de los contenedores
```bash
docker compose logs -f bot
docker compose logs -f scraper
docker compose logs -f postgres
```

### Reiniciar un servicio específico
```bash
docker compose restart bot
```

### Ver estado de la base de datos
```bash
docker compose exec postgres psql -U compra_agil_user -d compra_agil -c "SELECT COUNT(*) FROM licitaciones;"
```

### Backup de la base de datos
```bash
docker compose exec postgres pg_dump -U compra_agil_user compra_agil > backup_$(date +%Y%m%d).sql
```

---

## ⚠️ Troubleshooting

### Los contenedores no inician
```bash
# Ver logs detallados
docker compose logs --tail=100

# Verificar que las imágenes existen
docker images | grep compra
```

### Error de conexión SSH en el workflow
1. Verificar que `SSH_KEY` está completa (incluyendo `-----BEGIN/END-----`)
2. Verificar que el usuario puede ejecutar Docker sin sudo
3. Verificar firewall: `sudo ufw status`

### Base de datos sin datos
```bash
# Verificar que el volumen existe
docker volume ls | grep postgres

# Si perdiste datos, restaurar backup:
cat backup.sql | docker compose exec -T postgres psql -U compra_agil_user -d compra_agil
```
