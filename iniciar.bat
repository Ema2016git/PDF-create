@echo off
echo Iniciando servidor...
echo NO cierres esta ventana.
echo.
start msedge http://localhost:8000
python server.py
pause
