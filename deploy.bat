@echo off
echo ==========================================
echo 🚀 INICIANDO DESPLIEGUE AUTOMATICO
echo ==========================================

echo.
echo 📦 1. Deteniendo contenedores actuales...
docker-compose down

echo.
echo 🔨 2. Construyendo nuevas imagenes...
docker-compose build

echo.
echo 🚀 3. Iniciando servicios...
docker-compose up -d

echo.
echo 🧹 4. Limpiando imagenes antiguas (ahorrando espacio)...
docker image prune -f

echo.
echo ==========================================
echo ✅ DESPLIEGUE COMPLETADO EXITOSAMENTE
echo ==========================================
echo.
echo Los servicios estan corriendo en segundo plano.
echo Para ver los logs, ejecuta: docker-compose logs -f
echo.
pause
