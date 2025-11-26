@echo off
echo ==========================================
echo 🧪 PROBANDO CI/CD LOCALMENTE (DRY RUN)
echo ==========================================
echo.
echo Este script simula los pasos de construcción de GitHub Actions.
echo Si esto falla aqui, fallara en GitHub.
echo.

echo 🔨 1. Probando construcción de imagen BOT...
docker build --target bot -t test-bot:latest .
if %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Falló la construcción del BOT.
    exit /b %ERRORLEVEL%
)
echo ✅ Construcción del BOT exitosa.

echo.
echo 🔨 2. Probando construcción de imagen SCRAPER...
docker build --target scraper -t test-scraper:latest .
if %ERRORLEVEL% NEQ 0 (
    echo ❌ ERROR: Falló la construcción del SCRAPER.
    exit /b %ERRORLEVEL%
)
echo ✅ Construcción del SCRAPER exitosa.

echo.
echo ==========================================
echo ✅ PRUEBA EXITOSA: Tu código está listo para PUSH
echo ==========================================
echo.
echo Nota: Esto solo prueba la construcción. El despliegue
echo depende de que tus secretos en GitHub estén bien configurados.
pause
