@echo off
echo ========================================
echo  Instalando Dependencias ML/IA
echo ========================================
echo.

echo [1/4] Instalando dependencias ML...
pip install xgboost lightgbm shap fuzzywuzzy python-Levenshtein

echo.
echo [2/4] Instalando dependencias Dashboard...
pip install streamlit plotly altair

echo.
echo [3/4] Instalando dependencias SaaS Backend...
pip install stripe passlib[bcrypt] python-multipart email-validator alembic

echo.
echo [4/4] Verificando instalacion...
python -c "import pandas, xgboost, fuzzywuzzy; print('✅ Todas las dependencias ML instaladas correctamente')"

echo.
echo ========================================
echo  Instalación Completada
echo ========================================
pause
