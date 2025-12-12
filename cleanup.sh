#!/bin/bash
# Script de Limpieza Segura - CompraÁgil
# Mueve archivos antiguos y elimina temporales

echo "🧹 Iniciando limpieza del proyecto..."
echo ""

# Crear carpeta para versiones antiguas
echo "📁 Creando carpeta old_versions..."
mkdir -p old_versions

# Mover APIs antiguas
echo "📦 Moviendo APIs antiguas a old_versions/..."
if [ -f "api_backend.py" ]; then
    mv api_backend.py old_versions/
    echo "  ✅ Movido api_backend.py (v1)"
fi

if [ -f "api_backend_v2.py" ]; then
    mv api_backend_v2.py old_versions/
    echo "  ✅ Movido api_backend_v2.py (v2)"
fi

# Eliminar archivos temporales
echo ""
echo "🗑️  Eliminando archivos temporales..."

if [ -f "api_endpoints_complete.py" ]; then
    rm api_endpoints_complete.py
    echo "  ✅ Eliminado api_endpoints_complete.py"
fi

if [ -f "temp_historico.zip" ]; then
    rm temp_historico.zip
    echo "  ✅ Eliminado temp_historico.zip (~85MB)"
fi

# Limpiar __pycache__
echo ""
echo "🧹 Limpiando archivos Python compilados..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
echo "  ✅ Limpiado __pycache__ y *.pyc"

# Resumen
echo ""
echo "=" * 60
echo "✅ Limpieza Completada"
echo "=" * 60
echo "📦 Archivos movidos a old_versions/:"
ls -lh old_versions/ 2>/dev/null || echo "  (ninguno)"
echo ""
echo "🗑️  Espacio liberado: ~90 MB"
echo "📁 API actual: api_backend_v3.py"
echo ""
echo "✨ Proyecto limpio y organizado!"
