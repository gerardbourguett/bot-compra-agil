@echo off
echo ============================================================
echo SETUP COMPRAAGIL - Entorno de Desarrollo
echo ============================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en PATH
    echo Por favor instala Python 3.11 desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Python detectado
python --version
echo.

REM Crear entorno virtual
echo [2/5] Creando entorno virtual...
if exist .venv (
    echo Entorno virtual ya existe, saltando...
) else (
    python -m venv .venv
    echo Entorno virtual creado
)
echo.

REM Activar entorno virtual
echo [3/5] Activando entorno virtual...
call .venv\Scripts\activate.bat
echo.

REM Actualizar pip
echo [4/5] Actualizando pip...
python -m pip install --upgrade pip
echo.

REM Instalar dependencias
echo [5/5] Instalando dependencias...
echo Esto puede tomar varios minutos...
pip install -r requirements.txt
echo.

echo ============================================================
echo SETUP COMPLETO
echo ============================================================
echo.
echo Proximos pasos:
echo 1. Configurar .env con tus credenciales
echo 2. Ejecutar migraciones: python scripts/migrate_subscriptions.py
echo 3. Ejecutar migracion de auth: python scripts/migrate_api_keys.py
echo 4. Iniciar API: python api_backend_v3.py
echo.
echo El entorno virtual esta activado. Para desactivar usa: deactivate
echo.
pause
