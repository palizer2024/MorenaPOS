#!/bin/bash

# startup.sh - Script de inicio para Azure App Service (Linux)
# MorenaPOS - Django + Gunicorn

set -e

echo "=== INICIO STARTUP.SH ==="
echo "Directorio actual: $(pwd)"
echo "HOME: $HOME"
echo "Contenido de /home/site/wwwroot:"
ls -la /home/site/wwwroot/ 2>&1 || echo "No existe /home/site/wwwroot"
echo ""

# Buscar el directorio de la aplicación
# Oryx extrae el build en /tmp/<build-id>/ y lo copia a /home/site/wwwroot/
# Pero a veces solo deja el manifest, no los archivos
if [ -f /home/site/wwwroot/morenapos/manage.py ]; then
    APP_DIR=/home/site/wwwroot
    echo "App encontrada en /home/site/wwwroot"
elif [ -f /home/site/wwwroot/oryx-manifest.toml ]; then
    # Intentar leer el manifest para encontrar el directorio de build
    echo "Oryx manifest encontrado, buscando directorio de build..."
    APP_DIR=/home/site/wwwroot
else
    # Fallback: buscar en el directorio actual
    APP_DIR=$(pwd)
    echo "Usando directorio actual: $APP_DIR"
fi

cd "$APP_DIR"
echo "Directorio de trabajo: $(pwd)"
echo "Contenido:"
ls -la
echo ""

# Activar el entorno virtual
# Oryx crea antenv en el directorio de build original (/tmp/<id>/antenv)
# Pero también puede estar en /opt/venv/ o en /home/site/wwwroot/antenv/
VENV_ACTIVATED=false

if [ -d /opt/venv ] && [ -f /opt/venv/bin/activate ]; then
    echo "Activando /opt/venv..."
    source /opt/venv/bin/activate
    VENV_ACTIVATED=true
elif [ -d antenv ] && [ -f antenv/bin/activate ]; then
    echo "Activando antenv (local)..."
    source antenv/bin/activate
    VENV_ACTIVATED=true
elif [ -d "$HOME/antenv" ] && [ -f "$HOME/antenv/bin/activate" ]; then
    echo "Activando antenv (home)..."
    source "$HOME/antenv/bin/activate"
    VENV_ACTIVATED=true
fi

if [ "$VENV_ACTIVATED" = false ]; then
    echo "ADVERTENCIA: No se encontró entorno virtual. Creando uno nuevo..."
    python -m venv antenv
    source antenv/bin/activate
fi

echo "Python: $(python --version 2>&1)"
echo "Pip: $(pip --version 2>&1)"
echo "VIRTUAL_ENV: $VIRTUAL_ENV"

# Verificar si Django está instalado
python -c "import django; print(f'Django {django.get_version()}')" 2>&1 || echo "Django NO instalado"

# Instalar dependencias si no están
if ! python -c "import django" 2>/dev/null; then
    echo "Instalando dependencias desde requirements.txt..."
    # Buscar requirements.txt
    if [ -f morenapos/requirements.txt ]; then
        pip install --no-cache-dir -r morenapos/requirements.txt 2>&1
    elif [ -f requirements.txt ]; then
        pip install --no-cache-dir -r requirements.txt 2>&1
    else
        echo "ERROR: No se encontró requirements.txt"
        ls -la
    fi
    echo "Verificando instalación de Django..."
    python -c "import django; print(f'Django {django.get_version()} instalado correctamente')"
fi

# Recopilar archivos estáticos
if [ -f morenapos/manage.py ]; then
    echo "Recopilando archivos estáticos..."
    cd morenapos
    python manage.py collectstatic --noinput 2>&1 || echo "collectstatic falló (no crítico)"
    cd "$APP_DIR"
fi

# Iniciar Gunicorn
echo "=== INICIANDO GUNICORN ==="
cd morenapos
echo "Directorio para gunicorn: $(pwd)"
echo "Contenido:"
ls -la

# El módulo WSGI es 'wsgi' porque estamos dentro de morenapos/
exec gunicorn --bind=0.0.0.0:8000 \
         --workers=2 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=debug \
         wsgi:application
