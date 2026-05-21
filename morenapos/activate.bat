@echo off
echo Activando entorno virtual MorenaPOS...
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo Entorno virtual activado.
echo.
echo Comandos disponibles:
echo   python manage.py runserver  - Iniciar servidor de desarrollo
echo   python manage.py migrate    - Aplicar migraciones
echo   python manage.py createsuperuser - Crear superusuario
echo.
cmd /k