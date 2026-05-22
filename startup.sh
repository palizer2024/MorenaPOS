#!/bin/bash

# startup.sh - Script de inicio para Azure App Service (Linux)
# MorenaPOS - Django + Gunicorn
# Configurar en Azure Portal como: bash /home/site/wwwroot/startup.sh

set -e

echo "=== INICIO STARTUP.SH ==="
echo "Fecha: $(date)"
echo "Directorio actual: $(pwd)"

APP_DIR="/home/site/wwwroot"

# ============================================================
# PASO 1: Verificar archivos
# ============================================================
echo ""
echo "=== Verificando archivos ==="
ls -la "$APP_DIR" 2>/dev/null
echo ""
ls -la "$APP_DIR/morenapos/" 2>/dev/null || echo "No existe morenapos/"

# ============================================================
# PASO 2: Crear y activar entorno virtual
# ============================================================
echo ""
echo "=== Configurando entorno virtual ==="

if [ ! -d "$APP_DIR/antenv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv "$APP_DIR/antenv"
fi
source "$APP_DIR/antenv/bin/activate"
echo "✓ Entorno virtual activado"
echo "Python: $(python3 --version)"
echo "Pip: $(pip3 --version)"

# ============================================================
# PASO 3: Instalar dependencias (solo si faltan)
# ============================================================
echo ""
echo "=== Verificando dependencias ==="

if ! python3 -c "import django" 2>/dev/null; then
    echo "Instalando dependencias..."
    REQ_FILE=""
    if [ -f "$APP_DIR/requirements.txt" ]; then
        REQ_FILE="$APP_DIR/requirements.txt"
    elif [ -f "$APP_DIR/morenapos/requirements.txt" ]; then
        REQ_FILE="$APP_DIR/morenapos/requirements.txt"
    fi
    if [ -n "$REQ_FILE" ]; then
        pip3 install --no-cache-dir -r "$REQ_FILE" 2>&1
        echo "✓ Dependencias instaladas"
    fi
else
    echo "✓ Django ya está instalado"
fi

python3 -c "import django; print(f'Django {django.get_version()}')" 2>&1

# ============================================================
# PASO 4: Iniciar Gunicorn directamente (sin collectstatic)
# ============================================================
echo ""
echo "=== Iniciando Gunicorn ==="
cd "$APP_DIR/morenapos"
echo "Directorio: $(pwd)"
echo "Contenido:"
ls -la

exec gunicorn --bind=0.0.0.0:8000 \
    --workers=2 \
    --timeout=120 \
    --access-logfile=- \
    --error-logfile=- \
    --log-level=info \
    wsgi:application
