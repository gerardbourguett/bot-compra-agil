@echo off
REM Script de Limpieza Segura - CompraÁgil (Windows)
REM Mueve archivos antiguos y elimina temporales

echo 🧹 Iniciando limpieza del proyecto...
echo.

REM Crear carpeta para versiones antiguas
echo 📁 Creando carpeta old_versions...
if not exist "old_versions" mkdir old_versions

REM Mover APIs antiguas
echo 📦 Moviendo APIs antiguas a old_versions\...
if exist "api_backend.py" (
    move api_backend.py old_versions\ >nul
    echo   ✅ Movido api_backend.py (v1)
)

if exist "api_backend_v2.py" (
    move api_backend_v2.py old_versions\ >nul
    echo   ✅ Movido api_backend_v2.py (v2)
)

REM Eliminar archivos temporales
echo.
echo 🗑️  Eliminando archivos temporales...

if exist "api_endpoints_complete.py" (
    del api_endpoints_complete.py
    echo   ✅ Eliminado api_endpoints_complete.py
)

if exist "temp_historico.zip" (
    del temp_historico.zip
    echo   ✅ Eliminado temp_historico.zip (~85MB)
)

REM Limpiar __pycache__
echo.
echo 🧹 Limpiando archivos Python compilados...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc >nul 2>&1
echo   ✅ Limpiado __pycache__ y *.pyc

REM Resumen
echo.
echo ============================================================
echo ✅ Limpieza Completada
echo ============================================================
echo 📦 Archivos en old_versions\:
dir /b old_versions 2>nul || echo   (ninguno)
echo.
echo 🗑️  Espacio liberado: ~90 MB
echo 📁 API actual: api_backend_v3.py
echo.
echo ✨ Proyecto limpio y organizado!
echo.
pause
