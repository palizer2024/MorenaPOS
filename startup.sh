#!/bin/bash

# startup.sh - Script de inicio para Azure App Service (Linux)
# MorenaPOS - Django + Gunicorn

# Salir ante cualquier error
set -e

# Activar el entorno virtual si existe (Azure lo crea automáticamente)
if [ -d /opt/venv ]; then
    source /opt/venv/bin/activate
fi

# Instalar dependencias
pip install --no-cache-dir -r morenapos/requirements.txt

# Recopilar archivos estáticos
python morenapos/manage.py collectstatic --noinput --settings=morenapos.settings

# Iniciar Gunicorn
# - workers: 2-4 recomendado para App Service (2 * CPUs + 1)
# - timeout: 120s para conexiones lentas
# - access-logfile: envía logs a stdout para Azure Monitor
gunicorn --bind=0.0.0.0:8000 \
         --workers=2 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=info \
         morenapos.wsgi:application
