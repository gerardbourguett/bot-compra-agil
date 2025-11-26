#!/bin/bash

echo "=========================================="
echo "🚀 INICIANDO DESPLIEGUE AUTOMÁTICO"
echo "=========================================="

echo ""
echo "📦 1. Deteniendo contenedores actuales..."
docker-compose down

echo ""
echo "🔨 2. Construyendo nuevas imágenes..."
docker-compose build

echo ""
echo "🚀 3. Iniciando servicios..."
docker-compose up -d

echo ""
echo "🧹 4. Limpiando imágenes antiguas..."
docker image prune -f

echo ""
echo "=========================================="
echo "✅ DESPLIEGUE COMPLETADO EXITOSAMENTE"
echo "=========================================="
echo ""
echo "Los servicios están corriendo en segundo plano."
echo "Para ver los logs, ejecuta: docker-compose logs -f"
