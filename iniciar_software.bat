@echo off
title OptiGrid Enterprise - Sistema de Optimizacion Energetica
color 0B
echo ===============================================================================
echo            OPTIGRID ENTERPRISE: PLATAFORMA DE OPTIMIZACION ENERGETICA
echo            Universidad de La Guajira - Facultad de Ingenieria
echo ===============================================================================
echo.
echo Liberando puerto 8000 e iniciando servidor backend...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    if not "%%a"=="0" taskkill /f /pid %%a >nul 2>&1
)

echo Iniciando OptiGrid Enterprise en http://localhost:8000 ...
start "" "http://localhost:8000"
python app.py

pause
