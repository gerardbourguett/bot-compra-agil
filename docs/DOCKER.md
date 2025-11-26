# Guía de Dockerización - Bot de Compra Ágil 🐳

## 📦 Componentes Docker

El proyecto incluye:
- **PostgreSQL 15**: Base de datos principal
- **Bot de Telegram**: Servicio principal del bot
- **Scraper**: Servicio que actualiza datos cada 24 horas

## 🚀 Inicio Rápido con Docker

### 1. Prerrequisitos

```bash
# Instalar Docker y Docker Compose
# Windows/Mac: Docker Desktop
# Linux: 
sudo apt-get install docker.io docker-compose
```

### 2. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Copiar ejemplo
cp .env.docker .env

# Editar con tus valores
nano .env  # o usa tu editor favorito
```

**Variables requeridas:**
```env
POSTGRES_PASSWORD=tu_password_seguro
TELEGRAM_TOKEN=tu_token_telegram
GEMINI_API_KEY=tu_api_key_gemini
```

### 3. Construir y Ejecutar

```bash
# Construir imágenes
docker-compose build

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### 4. Verificar Estado

```bash
# Ver servicios corriendo
docker-compose ps

# Ver logs del bot
docker-compose logs -f bot

# Ver logs del scraper
docker-compose logs -f scraper

# Ver logs de PostgreSQL
docker-compose logs -f postgres
```

## 🔧 Comandos Útiles

### Gestión de Servicios

```bash
# Detener todos los servicios
docker-compose stop

# Iniciar servicios detenidos
docker-compose start

# Reiniciar servicios
docker-compose restart

# Detener y eliminar contenedores
docker-compose down

# Detener y eliminar TODO (incluyendo volúmenes)
docker-compose down -v
```

### Ejecutar Comandos en Contenedores

```bash
# Ejecutar scraper manualmente
docker-compose exec scraper python scraper.py

# Obtener detalles manualmente
docker-compose exec scraper python obtener_detalles.py

# Acceder a shell del bot
docker-compose exec bot bash

# Acceder a PostgreSQL
docker-compose exec postgres psql -U compra_agil_user -d compra_agil
```

### Ver Logs

```bash
# Logs en tiempo real de todos los servicios
docker-compose logs -f

# Logs solo del bot
docker-compose logs -f bot

# Últimas 100 líneas
docker-compose logs --tail=100 bot

# Logs desde hace 1 hora
docker-compose logs --since 1h bot
```

## 🗄️ Gestión de Base de Datos

### Backup de PostgreSQL

```bash
# Crear backup
docker-compose exec postgres pg_dump -U compra_agil_user compra_agil > backup.sql

# Restaurar backup
docker-compose exec -T postgres psql -U compra_agil_user compra_agil < backup.sql
```

### Acceder a PostgreSQL

```bash
# Desde el contenedor
docker-compose exec postgres psql -U compra_agil_user -d compra_agil

# Desde tu máquina (si tienes psql instalado)
psql -h localhost -U compra_agil_user -d compra_agil
```

### Queries Útiles

```sql
-- Ver total de licitaciones
SELECT COUNT(*) FROM licitaciones;

-- Ver licitaciones recientes
SELECT codigo, nombre, fecha_publicacion 
FROM licitaciones 
ORDER BY fecha_publicacion DESC 
LIMIT 10;

-- Ver usuarios registrados
SELECT COUNT(*) FROM perfiles_empresas;

-- Ver licitaciones guardadas
SELECT COUNT(*) FROM licitaciones_guardadas;
```

## 📊 Monitoreo

### Ver Uso de Recursos

```bash
# Ver uso de CPU/RAM
docker stats

# Ver solo servicios de compra_agil
docker stats compra_agil_bot compra_agil_scraper compra_agil_db
```

### Healthchecks

```bash
# Ver estado de salud de PostgreSQL
docker-compose exec postgres pg_isready -U compra_agil_user

# Ver estado de todos los servicios
docker-compose ps
```

## 🔄 Actualizar el Código

```bash
# 1. Detener servicios
docker-compose stop bot scraper

# 2. Reconstruir imágenes
docker-compose build bot scraper

# 3. Reiniciar servicios
docker-compose up -d bot scraper

# O todo en uno:
docker-compose up -d --build
```

## 🐛 Troubleshooting

### El bot no inicia

```bash
# Ver logs detallados
docker-compose logs bot

# Verificar variables de entorno
docker-compose exec bot env | grep TELEGRAM

# Reiniciar bot
docker-compose restart bot
```

### PostgreSQL no conecta

```bash
# Ver logs de PostgreSQL
docker-compose logs postgres

# Verificar que esté corriendo
docker-compose ps postgres

# Verificar healthcheck
docker inspect compra_agil_db | grep -A 10 Health
```

### Scraper no actualiza datos

```bash
# Ver logs del scraper
docker-compose logs scraper

# Ejecutar manualmente
docker-compose exec scraper python scraper.py

# Ver última ejecución
docker-compose logs --tail=50 scraper
```

### Problemas de permisos

```bash
# Dar permisos a directorio de logs
chmod -R 777 logs/

# Recrear volúmenes
docker-compose down -v
docker-compose up -d
```

## 🔐 Seguridad

### Cambiar Contraseñas

1. Edita `.env` con nueva contraseña
2. Recrea el contenedor de PostgreSQL:
```bash
docker-compose down postgres
docker volume rm nueva_carpeta_postgres_data
docker-compose up -d postgres
```

### Backup Automático

Agrega a tu crontab:
```bash
# Backup diario a las 2 AM
0 2 * * * cd /ruta/al/proyecto && docker-compose exec -T postgres pg_dump -U compra_agil_user compra_agil > backups/backup_$(date +\%Y\%m\%d).sql
```

## 📈 Escalabilidad

### Aumentar Recursos

Edita `docker-compose.yml`:
```yaml
services:
  bot:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 512M
```

### Múltiples Instancias del Bot

```yaml
services:
  bot:
    deploy:
      replicas: 3
```

## 🌐 Despliegue en Producción

### Recomendaciones

1. **Usar Docker Swarm o Kubernetes** para orquestación
2. **Configurar reverse proxy** (nginx) si expones APIs
3. **Usar secrets** para variables sensibles
4. **Configurar logs externos** (ELK, Loki)
5. **Monitoreo** con Prometheus + Grafana
6. **Backups automáticos** de PostgreSQL

### Ejemplo con Docker Swarm

```bash
# Inicializar swarm
docker swarm init

# Desplegar stack
docker stack deploy -c docker-compose.yml compra_agil

# Ver servicios
docker service ls

# Escalar bot
docker service scale compra_agil_bot=3
```

## 📝 Notas Importantes

- Los datos de PostgreSQL se persisten en un volumen Docker
- El scraper se ejecuta automáticamente cada 24 horas
- Los logs se guardan en `./logs/`
- El bot se reinicia automáticamente si falla

## 🆘 Soporte

Si tienes problemas:
1. Revisa los logs: `docker-compose logs -f`
2. Verifica variables de entorno: `docker-compose config`
3. Revisa el estado: `docker-compose ps`
4. Consulta la documentación de Docker

---

**¡Tu bot está listo para producción con Docker! 🚀**
