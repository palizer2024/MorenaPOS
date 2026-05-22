#!/bin/bash

# startup.sh - Script de inicio para Azure App Service (Linux)
# MorenaPOS - Django + Gunicorn

# Salir ante cualquier error
set -e

# Mostrar información de depuración
echo "=== INICIO STARTUP.SH ==="
echo "Directorio actual: $(pwd)"
echo "Contenido del directorio:"
ls -la
echo ""

# Activar el entorno virtual si existe (Azure lo crea automáticamente)
if [ -d /opt/venv ]; then
    echo "Activando entorno virtual /opt/venv..."
    source /opt/venv/bin/activate
elif [ -d antenv ]; then
    echo "Activando entorno virtual antenv..."
    source antenv/bin/activate
elif [ -d env ]; then
    echo "Activando entorno virtual env..."
    source env/bin/activate
else
    echo "ADVERTENCIA: No se encontró entorno virtual"
fi

# Verificar Python
echo "Python: $(python --version 2>&1)"
echo "Pip: $(pip --version 2>&1)"

# Ir al directorio de la aplicación
cd /home/site/wwwroot

# Instalar dependencias
echo "Instalando dependencias..."
pip install --no-cache-dir -r morenapos/requirements.txt 2>&1

# Recopilar archivos estáticos
echo "Recopilando archivos estáticos..."
cd morenapos
python manage.py collectstatic --noinput --settings=morenapos.settings 2>&1
cd ..

# Iniciar Gunicorn
echo "Iniciando Gunicorn..."
cd morenapos
gunicorn --bind=0.0.0.0:8000 \
         --workers=2 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=debug \
         morenapos.wsgi:application
