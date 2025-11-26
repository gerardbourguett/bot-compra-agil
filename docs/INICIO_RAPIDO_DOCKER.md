# Inicio Rápido con Docker 🐳

## 📋 Pasos para Iniciar

### 1. Configurar Variables de Entorno

```bash
# Copiar plantilla
cp .env.docker .env

# Editar con tus valores (IMPORTANTE)
notepad .env  # Windows
# o
nano .env     # Linux/Mac
```

**Configura estos valores en `.env`:**
```env
POSTGRES_PASSWORD=tu_password_seguro_aqui
TELEGRAM_TOKEN=tu_token_de_telegram
GEMINI_API_KEY=tu_api_key_de_gemini
```

### 2. Construir Imágenes

```bash
docker-compose build
```

### 3. Iniciar Servicios

```bash
docker-compose up -d
```

### 4. Verificar que Todo Funciona

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver solo el bot
docker-compose logs -f bot

# Ver solo el scraper
docker-compose logs -f scraper

# Ver estado de servicios
docker-compose ps
```

## 🔧 Configuración del Sistema

### Servicios Incluidos

1. **PostgreSQL** (puerto 5433)
   - Base de datos principal
   - Datos persistentes en volumen Docker

2. **Bot de Telegram**
   - Siempre activo
   - Se reinicia automáticamente si falla

3. **Scraper Automático**
   - Ejecuta cada 6 horas
   - Obtiene nuevas licitaciones
   - Obtiene detalles automáticamente

### Frecuencia del Scraper

Por defecto: **cada 6 horas**

Para cambiar la frecuencia, edita `docker-compose.yml`:

```yaml
# Cada 12 horas (43200 segundos)
sleep 43200

# Cada 24 horas (86400 segundos)
sleep 86400

# Cada 3 horas (10800 segundos)
sleep 10800
```

## 🚨 Solución de Problemas

### Error: "port is already allocated"

**Problema**: El puerto 5432 ya está en uso (PostgreSQL local)

**Solución**: Ya está configurado para usar puerto 5433. Si aún falla:

```bash
# Opción 1: Detener PostgreSQL local
# Windows:
net stop postgresql-x64-15

# Linux:
sudo systemctl stop postgresql

# Opción 2: Cambiar puerto en docker-compose.yml
ports:
  - "5434:5432"  # Usar otro puerto
```

### Error: "GEMINI_API_KEY variable is not set"

**Solución**: Configura el archivo `.env`:

```bash
cp .env.docker .env
# Edita .env y agrega tu GEMINI_API_KEY
```

### El scraper no ejecuta

```bash
# Ver logs del scraper
docker-compose logs scraper

# Ejecutar manualmente
docker-compose exec scraper python scraper.py
```

### El bot no responde

```bash
# Ver logs del bot
docker-compose logs bot

# Verificar que TELEGRAM_TOKEN esté configurado
docker-compose exec bot env | grep TELEGRAM

# Reiniciar bot
docker-compose restart bot
```

## 📊 Comandos Útiles

### Gestión de Servicios

```bash
# Detener todo
docker-compose stop

# Iniciar todo
docker-compose start

# Reiniciar todo
docker-compose restart

# Ver logs
docker-compose logs -f

# Ver estado
docker-compose ps

# Eliminar todo (CUIDADO: borra datos)
docker-compose down -v
```

### Ejecutar Comandos

```bash
# Ejecutar scraper manualmente
docker-compose exec scraper python scraper.py

# Obtener detalles manualmente
docker-compose exec scraper python obtener_detalles.py

# Acceder a PostgreSQL
docker-compose exec postgres psql -U compra_agil_user -d compra_agil

# Ver estadísticas
docker-compose exec postgres psql -U compra_agil_user -d compra_agil -c "SELECT COUNT(*) FROM licitaciones;"
```

### Backup de Base de Datos

```bash
# Crear backup
docker-compose exec postgres pg_dump -U compra_agil_user compra_agil > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker-compose exec -T postgres psql -U compra_agil_user compra_agil < backup_20251126.sql
```

## 🔄 Actualizar el Código

```bash
# 1. Detener servicios
docker-compose stop

# 2. Reconstruir imágenes
docker-compose build

# 3. Reiniciar
docker-compose up -d
```

## 📈 Monitoreo

### Ver Uso de Recursos

```bash
docker stats compra_agil_bot compra_agil_scraper compra_agil_db
```

### Ver Logs Históricos

```bash
# Últimas 100 líneas
docker-compose logs --tail=100 bot

# Desde hace 1 hora
docker-compose logs --since 1h scraper
```

## ✅ Checklist de Despliegue

- [ ] Archivo `.env` configurado con tus credenciales
- [ ] Docker y Docker Compose instalados
- [ ] Puerto 5433 disponible (o cambiado en docker-compose.yml)
- [ ] Ejecutado `docker-compose build`
- [ ] Ejecutado `docker-compose up -d`
- [ ] Verificado logs: `docker-compose logs -f`
- [ ] Bot responde en Telegram
- [ ] Scraper ejecutando correctamente

## 🎯 Resumen

**El sistema está configurado para:**
- ✅ Bot siempre activo
- ✅ Scraper ejecuta cada 6 horas
- ✅ Base de datos PostgreSQL persistente
- ✅ Reinicio automático si falla
- ✅ Logs accesibles

**Para cambiar frecuencia del scraper:**
Edita `docker-compose.yml` línea con `sleep 21600` (6 horas en segundos)

---

**¿Necesitas ayuda?** Revisa `DOCKER.md` para guía completa.
