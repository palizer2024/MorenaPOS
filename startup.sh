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
ls -la "$APP_DIR"
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
# PASO 3: Instalar dependencias
# ============================================================
echo ""
echo "=== Instalando dependencias ==="

# Buscar requirements.txt
REQ_FILE=""
if [ -f "$APP_DIR/requirements.txt" ]; then
    REQ_FILE="$APP_DIR/requirements.txt"
elif [ -f "$APP_DIR/morenapos/requirements.txt" ]; then
    REQ_FILE="$APP_DIR/morenapos/requirements.txt"
fi

if [ -n "$REQ_FILE" ]; then
    echo "Requirements: $REQ_FILE"
    pip3 install --no-cache-dir -r "$REQ_FILE" 2>&1
    echo "✓ Dependencias instaladas"
fi

# Verificar
python3 -c "import django; print(f'✓ Django {django.get_version()}')" 2>&1

# ============================================================
# PASO 4: Recopilar estáticos
# ============================================================
echo ""
echo "=== Recopilando estáticos ==="
cd "$APP_DIR/morenapos"
python3 manage.py collectstatic --noinput 2>&1 || echo "⚠ collectstatic falló"

# ============================================================
# PASO 5: Iniciar Gunicorn
# ============================================================
echo ""
echo "=== Iniciando Gunicorn ==="
cd "$APP_DIR/morenapos"
exec gunicorn --bind=0.0.0.0:8000 \
    --workers=2 \
    --timeout=120 \
    --access-logfile=- \
    --error-logfile=- \
    --log-level=info \
    wsgi:application
