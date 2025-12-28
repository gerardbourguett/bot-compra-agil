# 🚨 Disaster Recovery - CompraAgil

Guía completa para recuperación ante desastres y pérdida de datos.

---

## 📋 Tabla de Contenidos

1. [Estrategia de Backups](#estrategia-de-backups)
2. [Niveles de Protección](#niveles-de-protección)
3. [Procedimientos de Restauración](#procedimientos-de-restauración)
4. [Escenarios Comunes](#escenarios-comunes)
5. [Testing de Backups](#testing-de-backups)
6. [Checklist de Recuperación](#checklist-de-recuperación)

---

## 🛡️ Estrategia de Backups

CompraAgil utiliza una **estrategia de 3 capas** para máxima protección:

```
┌─────────────────────────────────────────────────────┐
│ Capa 1: Docker Volume (persistencia)               │
│ • compra_agil_postgres_data                         │
│ • Persiste entre deploys                            │
│ • NO se elimina con 'docker compose down'           │
└─────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────┐
│ Capa 2: Backups Locales                            │
│ • ~/app/backups/ (10 últimos backups)               │
│ • ~/backups/ (backups de >7 días)                   │
│ • Creados automáticamente en cada deploy            │
│ • Fail-safe: deploy se detiene si backup falla      │
└─────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────┐
│ Capa 3: GitHub Artifacts (backup externo)          │
│ • Subidos a GitHub después de cada deploy           │
│ • Backup diario automático (3 AM UTC)               │
│ • Retención: 30 días                                 │
│ • Accesibles desde cualquier lugar                  │
└─────────────────────────────────────────────────────┘
```

---

## 🔐 Niveles de Protección

### ✅ Nivel 1: Protección contra deploys
**Problema:** Deploy elimina datos accidentalmente
**Solución:** `docker compose down` NO elimina volúmenes
**Verificación:** Ver CI/CD workflow línea 122

### ✅ Nivel 2: Protección contra errores humanos
**Problema:** `docker compose down -v` ejecutado por error
**Solución:** Backups locales automáticos antes de cada deploy
**Verificación:** Ver CI/CD workflow líneas 94-131

### ✅ Nivel 3: Protección contra pérdida del servidor
**Problema:** Servidor muere, disco se corrompe
**Solución:** Backups en GitHub Artifacts (externo al servidor)
**Verificación:** Ver workflow `backup-to-artifacts.yml`

---

## 🔧 Procedimientos de Restauración

### Método 1: Script Automático (Recomendado)

```bash
cd ~/app  # o donde esté el proyecto

# Ver backups disponibles
./scripts/restore_backup.sh --list

# Restaurar de forma interactiva
./scripts/restore_backup.sh

# Restaurar desde archivo específico
./scripts/restore_backup.sh backups/backup_20250128_120000.sql.gz
```

El script realiza automáticamente:
1. ✅ Backup de seguridad antes de restaurar
2. ✅ Detiene servicios
3. ✅ Elimina BD actual
4. ✅ Restaura desde backup
5. ✅ Verifica datos
6. ✅ Reinicia servicios

---

### Método 2: Manual (Avanzado)

#### Desde backup local:

```bash
# 1. Detener servicios
docker compose stop bot scraper

# 2. Crear backup de seguridad
docker compose exec -T postgres pg_dump -U compra_agil_user compra_agil > safety_backup.sql

# 3. Eliminar BD
docker compose exec -T postgres psql -U compra_agil_user -d postgres \
  -c "DROP DATABASE IF EXISTS compra_agil;"

# 4. Recrear BD
docker compose exec -T postgres psql -U compra_agil_user -d postgres \
  -c "CREATE DATABASE compra_agil;"

# 5. Restaurar (si está comprimido, descomprimir primero)
gunzip -c backups/backup_20250128_120000.sql.gz | \
  docker compose exec -T postgres psql -U compra_agil_user -d compra_agil

# 6. Verificar
docker compose exec -T postgres psql -U compra_agil_user -d compra_agil \
  -c "SELECT COUNT(*) FROM historico_licitaciones;"

# 7. Reiniciar servicios
docker compose up -d
```

#### Desde GitHub Artifacts:

```bash
# 1. Descargar desde GitHub
# Ve a: https://github.com/<tu-usuario>/bot-compra-agil/actions/workflows/backup-to-artifacts.yml
# Descarga el artifact más reciente

# 2. Descomprimir
gunzip compra_agil_backup_*.sql.gz

# 3. Usar el script de restauración
./scripts/restore_backup.sh compra_agil_backup_*.sql
```

---

## 🚨 Escenarios Comunes

### Escenario 1: Deploy Accidental con `-v`

**Síntomas:**
```bash
$ docker compose down -v
$ docker compose up -d
# Base de datos vacía!
```

**Solución:**
```bash
# 1. Listar backups locales
ls -lh ~/app/backups/backup_*.sql.gz

# 2. Restaurar el más reciente
./scripts/restore_backup.sh ~/app/backups/backup_<timestamp>.sql.gz
```

**Tiempo estimado:** 5-15 minutos (dependiendo del tamaño de la BD)

---

### Escenario 2: Servidor Comprometido/Perdido

**Síntomas:**
- Servidor VPS no responde
- Disco corrupto
- Ataque ransomware

**Solución:**
```bash
# 1. Provisionar nuevo servidor VPS

# 2. Instalar Docker + Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 3. Clonar repositorio
git clone https://github.com/<tu-usuario>/bot-compra-agil.git
cd bot-compra-agil

# 4. Configurar .env
cp .env.example .env
# Editar .env con tus credenciales

# 5. Iniciar servicios
docker compose up -d
sleep 30  # Esperar a que PostgreSQL esté listo

# 6. Descargar backup de GitHub Artifacts
# (desde el navegador o usando gh CLI)
gh run download -n database-backup-<timestamp>

# 7. Restaurar
gunzip compra_agil_backup_*.sql.gz
./scripts/restore_backup.sh compra_agil_backup_*.sql

# 8. Configurar self-hosted runner
# Ver: https://github.com/<tu-usuario>/bot-compra-agil/settings/actions/runners
```

**Tiempo estimado:** 30-60 minutos

---

### Escenario 3: Corrupción de Datos (Error de Aplicación)

**Síntomas:**
- Datos inconsistentes
- Foreign key violations
- Tablas vacías sin razón

**Solución:**
```bash
# 1. Identificar cuándo ocurrió la corrupción
# Ver logs del bot/scraper

# 2. Buscar backup ANTES del problema
ls -lht ~/app/backups/

# 3. Restaurar backup anterior al problema
./scripts/restore_backup.sh backups/backup_<antes_del_problema>.sql.gz

# 4. Si no hay backup local suficientemente antiguo,
#    descargar de GitHub Artifacts (30 días de retención)
```

---

### Escenario 4: Testing de Nueva Migración

**Síntomas:**
- Quieres testear una migración sin riesgo

**Solución:**
```bash
# 1. Crear backup manual ANTES de la migración
docker compose exec -T postgres pg_dump -U compra_agil_user compra_agil > \
  backups/before_migration_$(date +%Y%m%d_%H%M%S).sql

# 2. Ejecutar migración
python scripts/migrate_<nueva_feature>.py

# 3. Si falla o hay problemas, restaurar
./scripts/restore_backup.sh backups/before_migration_*.sql
```

---

## 🧪 Testing de Backups

### Test 1: Verificar Backup Automático en Deploy

```bash
# 1. Hacer un cambio mínimo
echo "# test" >> README.md
git add README.md
git commit -m "test: verificar backup automático"
git push

# 2. Ver logs del workflow
# GitHub Actions debe mostrar:
# ✅ Backup creado exitosamente

# 3. Verificar en servidor
ssh usuario@servidor
ls -lh ~/app/backups/
# Debe aparecer un backup reciente
```

### Test 2: Verificar Backup a GitHub Artifacts

```bash
# 1. Ir a GitHub Actions
# https://github.com/<tu-usuario>/bot-compra-agil/actions/workflows/backup-to-artifacts.yml

# 2. Hacer clic en "Run workflow" (manual trigger)

# 3. Esperar 2-3 minutos

# 4. Verificar que el artifact aparece en el workflow run
# Debe mostrar: database-backup-<timestamp> con tamaño > 0 MB
```

### Test 3: Test Completo de Restauración (STAGING ONLY)

⚠️ **NO ejecutar en producción sin crear backup primero**

```bash
# 1. Crear backup de seguridad
docker compose exec -T postgres pg_dump -U compra_agil_user compra_agil > \
  test_restore_backup.sql

# 2. Contar filas ANTES
docker compose exec -T postgres psql -U compra_agil_user -d compra_agil \
  -c "SELECT COUNT(*) FROM historico_licitaciones;" > before_count.txt

# 3. Restaurar desde backup
./scripts/restore_backup.sh backups/backup_*.sql.gz

# 4. Contar filas DESPUÉS
docker compose exec -T postgres psql -U compra_agil_user -d compra_agil \
  -c "SELECT COUNT(*) FROM historico_licitaciones;" > after_count.txt

# 5. Comparar
diff before_count.txt after_count.txt
# Debe ser IDÉNTICO

# 6. Limpiar archivos de test
rm before_count.txt after_count.txt test_restore_backup.sql
```

---

## ✅ Checklist de Recuperación

### Pre-Desastre (Prevención)
- [ ] Backups automáticos funcionando (verificar GitHub Actions)
- [ ] Workflow `backup-to-artifacts.yml` ejecutándose diariamente
- [ ] Backup local creado en cada deploy (ver CI/CD logs)
- [ ] Al menos 3 backups en GitHub Artifacts
- [ ] Script `restore_backup.sh` con permisos de ejecución
- [ ] Documentación actualizada (este archivo)

### Durante Desastre
- [ ] **NO PÁNICO** - Tienes 3 capas de protección
- [ ] Identificar tipo de desastre (ver Escenarios arriba)
- [ ] Verificar disponibilidad de backups (`--list`)
- [ ] Crear backup de seguridad del estado actual (si es posible)
- [ ] Seleccionar backup a restaurar (más reciente = mejor)

### Restauración
- [ ] Ejecutar `./scripts/restore_backup.sh`
- [ ] Verificar datos restaurados (COUNT de tablas principales)
- [ ] Reiniciar servicios
- [ ] Verificar que bot responde
- [ ] Verificar que scraper funciona
- [ ] Verificar métricas en Prometheus

### Post-Recuperación
- [ ] Documentar el incidente (qué pasó, cómo se recuperó)
- [ ] Crear GitHub Issue con post-mortem
- [ ] Actualizar procedimientos si es necesario
- [ ] Agregar tests/validaciones para prevenir recurrencia
- [ ] Notificar a usuarios si hubo pérdida de datos

---

## 🆘 Contactos de Emergencia

- **GitHub Issues:** https://github.com/<tu-usuario>/bot-compra-agil/issues
- **Documentación:** `/docs/`
- **Logs del servidor:** `~/app/logs/`

---

## 📊 Métricas de Recuperación (SLA)

| Escenario | RTO (Recovery Time) | RPO (Recovery Point) |
|-----------|---------------------|----------------------|
| Deploy con `-v` | < 15 minutos | 0 minutos (último backup antes del deploy) |
| Servidor perdido | < 60 minutos | < 24 horas (backup diario) |
| Corrupción de datos | < 30 minutos | Variable (depende del backup) |

**RTO (Recovery Time Objective):** Tiempo máximo aceptable de downtime
**RPO (Recovery Point Objective):** Máxima cantidad de datos que se pueden perder

---

## 🔄 Actualizaciones de este Documento

Este documento debe actualizarse cuando:
- Se agregue un nuevo tipo de backup
- Se cambie la estrategia de retención
- Se descubra un nuevo escenario de desastre
- Se mejore el proceso de restauración

**Última actualización:** 2025-12-28
**Versión:** 1.0.0
