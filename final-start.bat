@echo off
echo Iniciando MorenaPOS...
cd morenapos
call venv\Scripts\activate.bat
set PYTHONPATH=..;%PYTHONPATH%
venv\Scripts\python.exe manage.py runserver
pause