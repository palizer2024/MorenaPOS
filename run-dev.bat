@echo off
echo Configurando entorno de desarrollo MorenaPOS...
cd morenapos
call venv\Scripts\activate.bat
set DJANGO_SETTINGS_MODULE=morenapos.settings
set DEBUG=True
echo Ejecutando servidor...
venv\Scripts\python.exe manage.py runserver
pause