@echo off
title OptiGrid-AI - Plataforma de Optimizacion Energetica
color 0B
echo ===============================================================================
echo            OPTIGRID-AI: PLATAFORMA DE OPTIMIZACION ENERGETICA
echo            Universidad de La Guajira - Facultad de Ingenieria
echo ===============================================================================
echo.
echo Iniciando servidor backend Python y cargando modelos matematicos...
echo.

start "" "http://localhost:8000"
python app.py

pause
