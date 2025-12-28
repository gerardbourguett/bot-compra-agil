#!/bin/bash
#
# restore_backup.sh - Script para restaurar backups de PostgreSQL
#
# Uso:
#   ./scripts/restore_backup.sh [archivo_backup.sql.gz]
#   ./scripts/restore_backup.sh --list
#   ./scripts/restore_backup.sh --from-artifacts
#

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detectar comando de docker-compose
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Funciones de utilidad
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Función para listar backups locales
list_local_backups() {
    print_header "📦 BACKUPS LOCALES DISPONIBLES"

    if [ -d "backups" ] && [ "$(ls -A backups/backup_*.sql* 2>/dev/null)" ]; then
        echo "Ubicación: $(pwd)/backups/"
        echo ""
        ls -lh backups/backup_*.sql* | awk '{printf "%s\t%s\t%s %s %s\n", NR, $5, $6, $7, $9}'
    else
        print_warning "No hay backups locales en $(pwd)/backups/"
    fi

    # Buscar también en ~/backups
    if [ -d "$HOME/backups" ] && [ "$(ls -A $HOME/backups/compra_agil_backup_*.sql* 2>/dev/null)" ]; then
        echo ""
        echo "Ubicación: $HOME/backups/"
        echo ""
        ls -lh $HOME/backups/compra_agil_backup_*.sql* | awk '{printf "%s\t%s\t%s %s %s\n", NR, $5, $6, $7, $9}'
    fi
}

# Función para listar backups en GitHub Artifacts
list_github_artifacts() {
    print_header "☁️  BACKUPS EN GITHUB ARTIFACTS"
    print_info "Para descargar desde GitHub Artifacts:"
    echo ""
    echo "1. Ve a: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[\/:]\(.*\)\.git/\1/')/actions/workflows/backup-to-artifacts.yml"
    echo "2. Haz clic en el workflow run más reciente"
    echo "3. Descarga el artifact 'database-backup-XXXXXXXX'"
    echo "4. Descomprime el archivo .gz"
    echo "5. Ejecuta: ./scripts/restore_backup.sh <archivo_descargado.sql>"
    echo ""
}

# Función para confirmar acción destructiva
confirm_restore() {
    local backup_file=$1

    print_warning "⚠️  ADVERTENCIA: Esta operación es DESTRUCTIVA"
    echo ""
    echo "Se va a:"
    echo "  1. Detener el servicio de PostgreSQL"
    echo "  2. ELIMINAR todos los datos actuales"
    echo "  3. Restaurar desde: $(basename $backup_file)"
    echo ""
    read -p "¿Estás SEGURO que deseas continuar? (escribe 'SI' en mayúsculas): " confirm

    if [ "$confirm" != "SI" ]; then
        print_error "Restauración cancelada por el usuario"
        exit 1
    fi
}

# Función para crear backup de seguridad antes de restaurar
create_safety_backup() {
    print_info "Creando backup de seguridad antes de restaurar..."

    mkdir -p backups

    local safety_backup="backups/safety_backup_before_restore_$(date +%Y%m%d_%H%M%S).sql"

    if $DOCKER_COMPOSE exec -T postgres pg_dump -U compra_agil_user compra_agil > "$safety_backup" 2>/dev/null; then
        print_success "Backup de seguridad creado: $safety_backup"
        echo "$safety_backup"
    else
        print_warning "No se pudo crear backup de seguridad (puede que la BD esté vacía)"
        echo ""
    fi
}

# Función principal de restauración
restore_backup() {
    local backup_file=$1

    # Validar que el archivo existe
    if [ ! -f "$backup_file" ]; then
        print_error "Archivo no encontrado: $backup_file"
        exit 1
    fi

    print_header "🔄 INICIANDO RESTAURACIÓN"
    echo "Archivo: $backup_file"
    echo "Tamaño: $(du -h "$backup_file" | cut -f1)"
    echo ""

    # Confirmar acción
    confirm_restore "$backup_file"

    # Crear backup de seguridad
    create_safety_backup

    # Descomprimir si es .gz
    local sql_file="$backup_file"
    if [[ "$backup_file" == *.gz ]]; then
        print_info "Descomprimiendo archivo..."
        sql_file="${backup_file%.gz}"
        gunzip -c "$backup_file" > "$sql_file"
        print_success "Archivo descomprimido"
    fi

    # Detener servicios que usan la BD
    print_info "Deteniendo servicios (bot y scraper)..."
    $DOCKER_COMPOSE stop bot scraper || true

    # Esperar a que las conexiones se cierren
    sleep 5

    # Eliminar BD y recrear
    print_info "Eliminando base de datos actual..."
    $DOCKER_COMPOSE exec -T postgres psql -U compra_agil_user -d postgres -c "DROP DATABASE IF EXISTS compra_agil;" || {
        print_error "No se pudo eliminar la BD. ¿Hay conexiones activas?"
        print_info "Intenta detener todos los servicios: $DOCKER_COMPOSE down"
        exit 1
    }

    print_info "Creando base de datos vacía..."
    $DOCKER_COMPOSE exec -T postgres psql -U compra_agil_user -d postgres -c "CREATE DATABASE compra_agil;"

    # Restaurar backup
    print_info "Restaurando backup... (esto puede tomar varios minutos)"
    if $DOCKER_COMPOSE exec -T postgres psql -U compra_agil_user -d compra_agil < "$sql_file"; then
        print_success "¡Backup restaurado exitosamente!"
    else
        print_error "Error al restaurar el backup"
        exit 1
    fi

    # Verificar datos
    print_info "Verificando datos restaurados..."
    $DOCKER_COMPOSE exec -T postgres psql -U compra_agil_user -d compra_agil -c "
        SELECT 'Licitaciones: ' || COUNT(*)::text FROM licitaciones
        UNION ALL
        SELECT 'Histórico: ' || COUNT(*)::text FROM historico_licitaciones
        UNION ALL
        SELECT 'Usuarios: ' || COUNT(*)::text FROM subscriptions;
    "

    # Reiniciar servicios
    print_info "Reiniciando servicios..."
    $DOCKER_COMPOSE up -d

    print_header "✅ RESTAURACIÓN COMPLETADA"
    print_success "Base de datos restaurada desde: $(basename $backup_file)"
    print_info "Los servicios están reiniciándose..."

    # Limpiar archivo temporal si se descomprimió
    if [[ "$backup_file" == *.gz ]]; then
        rm -f "$sql_file"
    fi
}

# Menú interactivo
interactive_menu() {
    print_header "🔧 RESTAURACIÓN DE BACKUP - CompraAgil"

    PS3=$'\n'"Selecciona una opción (1-4): "
    options=(
        "📋 Listar backups locales"
        "☁️  Ver backups en GitHub Artifacts"
        "♻️  Restaurar desde archivo específico"
        "❌ Salir"
    )

    select opt in "${options[@]}"; do
        case $REPLY in
            1)
                list_local_backups
                echo ""
                ;;
            2)
                list_github_artifacts
                echo ""
                ;;
            3)
                echo ""
                read -p "Ingresa la ruta completa del archivo de backup: " backup_path
                if [ -n "$backup_path" ]; then
                    restore_backup "$backup_path"
                    break
                fi
                ;;
            4)
                print_info "Saliendo..."
                exit 0
                ;;
            *)
                print_error "Opción inválida"
                ;;
        esac
    done
}

# Script principal
main() {
    # Verificar que estamos en el directorio correcto
    if [ ! -f "docker-compose.yml" ]; then
        print_error "Este script debe ejecutarse desde el directorio raíz del proyecto"
        print_info "Uso: ./scripts/restore_backup.sh"
        exit 1
    fi

    # Verificar que PostgreSQL está corriendo
    if ! docker ps --format '{{.Names}}' | grep -q compra_agil_db; then
        print_error "PostgreSQL no está corriendo"
        print_info "Inicia los servicios con: $DOCKER_COMPOSE up -d"
        exit 1
    fi

    # Parsear argumentos
    case "${1:-}" in
        --list)
            list_local_backups
            ;;
        --from-artifacts)
            list_github_artifacts
            ;;
        "")
            interactive_menu
            ;;
        *)
            restore_backup "$1"
            ;;
    esac
}

# Ejecutar script
main "$@"
