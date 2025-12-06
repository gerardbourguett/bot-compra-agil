# Guía de Backup y Restauración de Base de Datos

## Backups Automáticos

### Durante Despliegues

El workflow de GitHub Actions ahora crea **backups automáticos** antes de cada despliegue:

- **Ubicación:** `~/app/backups/backup_YYYYMMDD_HHMMSS.sql`
- **Retención:** Últimos 7 backups (los antiguos se eliminan automáticamente)
- **Formato:** SQL dump de PostgreSQL

## Comandos de Backup Manual

### Backup Completo

```bash
# Entrar al directorio del proyecto
cd ~/app

# Crear backup con timestamp
docker compose exec -T postgres pg_dump -U compra_agil_user compra_agil > backup_$(date +%Y%m%d_%H%M%S).sql

# Verificar el backup
ls -lh backup_*.sql
```

### Backup de Tablas Específicas

```bash
# Solo tabla de licitaciones
docker compose exec -T postgres pg_dump -U compra_agil_user -t licitaciones compra_agil > backup_licitaciones.sql

# Solo histórico
docker compose exec -T postgres pg_dump -U compra_agil_user -t historico_licitaciones compra_agil > backup_historico.sql
```

## Restauración desde Backup

### Restaurar Backup Completo

```bash
# Encontrar el backup más reciente
ls -t backup_*.sql | head -1

# Restaurar (reemplaza BACKUP_FILE con el nombre del archivo)
docker compose exec -T postgres psql -U compra_agil_user compra_agil < BACKUP_FILE.sql

# Verificar restauración
docker compose exec postgres psql -U compra_agil_user -d compra_agil -c "SELECT COUNT(*) FROM licitaciones;"
```

### Restaurar Solo una Tabla

```bash
# Restaurar licitaciones
docker compose exec -T postgres psql -U compra_agil_user compra_agil < backup_licitaciones.sql
```

## Verificación de Datos

### Contar Registros

```bash
docker compose exec postgres psql -U compra_agil_user -d compra_agil -c "
  SELECT 'Licitaciones: ' || COUNT(*) FROM licitaciones
  UNION ALL
  SELECT 'Histórico: ' || COUNT(*) FROM historico_licitaciones;
"
```

### Ver Últimas Licitaciones

```bash
docker compose exec postgres psql -U compra_agil_user -d compra_agil -c "
  SELECT codigo, nombre, fecha_publicacion 
  FROM licitaciones 
  ORDER BY fecha_publicacion DESC 
  LIMIT 5;
"
```

## Gestión de Volúmenes

### Ver Volumen de PostgreSQL

```bash
# Listar volúmenes
docker volume ls | grep postgres

# Inspeccionar volumen
docker volume inspect compra_agil_postgres_data
```

### Backup del Volumen Completo (nivel Docker)

```bash
# Crear backup del volumen como archivo tar
docker run --rm \
  -v compra_agil_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_volume_$(date +%Y%m%d).tar.gz -C /data .
```

### Restaurar Volumen desde Backup

```bash
# ADVERTENCIA: Esto elimina datos actuales
docker run --rm \
  -v compra_agil_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/postgres_volume_YYYYMMDD.tar.gz"
```

## Comandos Peligrosos (EVITAR)

> [!CAUTION]
> **NUNCA ejecutar estos comandos en producción:**

```bash
# ❌ ELIMINA TODOS LOS VOLÚMENES (incluye datos)
docker compose down -v

# ❌ ELIMINA EL VOLUMEN DE POSTGRES
docker volume rm compra_agil_postgres_data

# ❌ ELIMINA TODOS LOS VOLÚMENES NO USADOS
docker volume prune
```

## Comandos Seguros

> [!TIP]
> **Comandos seguros para usar:**

```bash
# ✅ Detiene contenedores pero PRESERVA datos
docker compose down

# ✅ Reinicia servicios
docker compose restart

# ✅ Ver logs
docker compose logs -f postgres
```

## Recuperación de Desastres

### Escenario: Se perdieron todos los datos

```bash
# 1. Verificar si existe backup
ls -lh backups/backup_*.sql

# 2. Restaurar el más reciente
LATEST=$(ls -t backups/backup_*.sql | head -1)
docker compose exec -T postgres psql -U compra_agil_user compra_agil < "$LATEST"

# 3. Ejecutar importación histórica
cd ~/app
gh workflow run "Importar Histórico Mensual"

# 4. Verificar datos
docker compose exec postgres psql -U compra_agil_user -d compra_agil -c "SELECT COUNT(*) FROM licitaciones;"
```

### Escenario: Despliegue falló y hay corrupción

```bash
# 1. Detener servicios
docker compose down

# 2. Eliminar volumen corrupto (cuidado!)
docker volume rm compra_agil_postgres_data

# 3. Reiniciar (creará volumen nuevo)
docker compose up -d

# 4. Esperar que PostgreSQL esté listo
sleep 15

# 5. Restaurar desde backup
LATEST=$(ls -t backups/backup_*.sql | head -1)
docker compose exec -T postgres psql -U compra_agil_user compra_agil < "$LATEST"
```

## Automatización Adicional

### Cron Job para Backups Diarios

Agregar al crontab del servidor:

```bash
# Editar crontab
crontab -e

# Agregar línea (backup diario a las 3 AM)
0 3 * * * cd ~/app && docker compose exec -T postgres pg_dump -U compra_agil_user compra_agil > backups/daily_backup_$(date +\%Y\%m\%d).sql
```

## Comandos de Monitoreo

### Ver Tamaño de la Base de Datos

```bash
docker compose exec postgres psql -U compra_agil_user -d compra_agil -c "
  SELECT pg_size_pretty(pg_database_size('compra_agil')) as db_size;
"
```

### Ver Tamaño por Tabla

```bash
docker compose exec postgres psql -U compra_agil_user -d compra_agil -c "
  SELECT 
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size
  FROM pg_catalog.pg_statio_user_tables
  ORDER BY pg_total_relation_size(relid) DESC;
"
```
