# Guía Rápida: Migración a PostgreSQL y Docker 🐳

## 🎯 Resumen

Tu proyecto ahora soporta:
- ✅ **SQLite** (desarrollo local)
- ✅ **PostgreSQL** (producción con Docker)
- ✅ **Detección automática** según `DATABASE_URL`

## 🚀 Opción 1: Docker (Recomendado para Producción)

### Paso 1: Configurar Variables

```bash
# Copiar ejemplo
cp .env.docker .env

# Editar con tus valores
nano .env
```

Contenido del `.env`:
```env
POSTGRES_PASSWORD=tu_password_seguro
TELEGRAM_TOKEN=tu_token_telegram
GEMINI_API_KEY=tu_api_key_gemini
```

### Paso 2: Iniciar con Docker

```bash
# Construir e iniciar todo
docker-compose up -d

# Ver logs
docker-compose logs -f
```

¡Listo! El sistema completo está corriendo:
- 🗄️ PostgreSQL en puerto 5432
- 🤖 Bot de Telegram activo
- 🕷️ Scraper automático (cada 24 horas)

### Comandos Útiles

```bash
# Ver estado
docker-compose ps

# Ver logs del bot
docker-compose logs -f bot

# Ejecutar scraper manualmente
docker-compose exec scraper python scraper.py

# Detener todo
docker-compose stop

# Eliminar todo (incluyendo datos)
docker-compose down -v
```

## 💻 Opción 2: Local con SQLite (Desarrollo)

### Funciona igual que antes:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar scraper
python scraper.py

# Ejecutar bot
python bot_inteligente.py
```

**No necesitas configurar nada extra** - usa SQLite automáticamente.

## 🔄 Migrar de SQLite a PostgreSQL

### Opción A: Exportar/Importar Datos

```bash
# 1. Exportar de SQLite
sqlite3 compra_agil.db .dump > export.sql

# 2. Iniciar PostgreSQL con Docker
docker-compose up -d postgres

# 3. Adaptar SQL (cambiar sintaxis si es necesario)
# 4. Importar a PostgreSQL
docker-compose exec -T postgres psql -U compra_agil_user compra_agil < export_adapted.sql
```

### Opción B: Empezar de Cero

```bash
# Simplemente inicia Docker y ejecuta el scraper
docker-compose up -d
docker-compose exec scraper python scraper.py
```

## 📊 Comparación

| Característica | SQLite | PostgreSQL |
|----------------|--------|------------|
| **Instalación** | ✅ Incluida | ⚠️ Requiere Docker |
| **Rendimiento** | 🟡 Bueno para <100k registros | 🟢 Excelente para millones |
| **Concurrencia** | 🔴 Limitada | 🟢 Excelente |
| **Backups** | 🟡 Copiar archivo | 🟢 pg_dump |
| **Producción** | ⚠️ No recomendado | ✅ Recomendado |
| **Desarrollo** | ✅ Perfecto | 🟡 Overhead |

## 🔧 Configuración Avanzada

### Cambiar Puerto de PostgreSQL

Edita `docker-compose.yml`:
```yaml
postgres:
  ports:
    - "5433:5432"  # Cambiar 5432 a otro puerto
```

### Configurar Scraper para Ejecutar Cada 12 Horas

Edita `docker-compose.yml`:
```yaml
scraper:
  command: >
    sh -c "
      while true; do
        python scraper.py
        sleep 43200  # 12 horas = 43200 segundos
      done
    "
```

### Acceder a PostgreSQL desde tu Máquina

```bash
# Instalar cliente PostgreSQL
# Ubuntu/Debian:
sudo apt-get install postgresql-client

# Mac:
brew install postgresql

# Conectar
psql -h localhost -U compra_agil_user -d compra_agil
```

## 🐛 Solución de Problemas

### "DATABASE_URL not found"

**Solución**: Asegúrate de que `.env` existe y tiene `DATABASE_URL` o déjalo vacío para usar SQLite.

### "Connection refused" en PostgreSQL

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps postgres

# Ver logs
docker-compose logs postgres

# Reiniciar
docker-compose restart postgres
```

### El bot no se conecta a PostgreSQL

```bash
# Verificar variables de entorno
docker-compose exec bot env | grep DATABASE

# Verificar conectividad
docker-compose exec bot ping postgres
```

## 📝 Archivos Creados

- `Dockerfile` - Imagen del bot
- `docker-compose.yml` - Orquestación de servicios
- `db_adapter.py` - Adaptador dual SQLite/PostgreSQL
- `init.sql` - Inicialización de PostgreSQL
- `.dockerignore` - Archivos a ignorar en build
- `.env.docker` - Ejemplo de variables para Docker
- `DOCKER.md` - Guía completa de Docker

## ✅ Checklist de Despliegue

### Desarrollo Local
- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Ejecutar bot: `python bot_inteligente.py`

### Producción con Docker
- [ ] Instalar Docker y Docker Compose
- [ ] Crear archivo `.env` con tus credenciales
- [ ] Ejecutar: `docker-compose up -d`
- [ ] Verificar logs: `docker-compose logs -f`
- [ ] Configurar backups automáticos

## 🎓 Próximos Pasos

1. **Prueba local** con SQLite para verificar que todo funciona
2. **Despliega con Docker** cuando estés listo para producción
3. **Configura backups** automáticos de PostgreSQL
4. **Monitorea** con `docker stats` y logs

## 📞 Ayuda

- Ver `DOCKER.md` para guía completa de Docker
- Ver `GUIA_BOT.md` para uso del bot
- Ver `README.md` para documentación general

---

**¡Tu proyecto ahora está listo para escalar! 🚀**
