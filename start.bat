@echo off
echo Iniciando MorenaPOS...
cd morenapos
call venv\Scripts\activate.bat
echo Ejecutando servidor de desarrollo...
venv\Scripts\python.exe manage.py runserver
pause