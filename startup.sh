#!/bin/bash

# startup.sh - Script de inicio para Azure App Service (Linux)
# MorenaPOS - Django + Gunicorn
# Este script se ejecuta cuando se configura en Azure Portal como:
#   bash /home/site/wwwroot/startup.sh
# O cuando Oryx no puede detectar Django automáticamente.

set -e

echo "=== INICIO STARTUP.SH ==="
echo "Fecha: $(date)"
echo "Directorio actual: $(pwd)"
echo "HOME: $HOME"
echo "USER: $(whoami)"

APP_DIR="/home/site/wwwroot"

# ============================================================
# PASO 1: Verificar que los archivos de la app existen
# ============================================================
echo ""
echo "=== PASO 1: Verificando archivos de la app ==="
if [ -f "$APP_DIR/morenapos/manage.py" ]; then
    echo "✓ manage.py encontrado en $APP_DIR/morenapos/"
elif [ -f "$APP_DIR/manage.py" ]; then
    echo "✓ manage.py encontrado en $APP_DIR/"
    # La app está en la raíz, no en morenapos/
    APP_IS_ROOT=true
else
    echo "✗ No se encontró manage.py en $APP_DIR"
    echo "Contenido de $APP_DIR:"
    ls -la "$APP_DIR"
    echo ""
    echo "Buscando manage.py en todo /home/site/wwwroot..."
    find "$APP_DIR" -name "manage.py" 2>/dev/null || echo "No encontrado"
fi

# ============================================================
# PASO 2: Configurar el entorno virtual
# ============================================================
echo ""
echo "=== PASO 2: Configurando entorno virtual ==="

VENV_ACTIVATED=false

# Buscar antenv en orden de prioridad
for VENV_PATH in \
    "/tmp/"*"/antenv" \
    "$APP_DIR/antenv" \
    "/opt/venv" \
    "$HOME/antenv" \
    "/antenv"; do
    # Expandir wildcards
    for f in $VENV_PATH; do
        if [ -d "$f" ] && [ -f "$f/bin/activate" ]; then
            echo "✓ Activando entorno virtual: $f"
            source "$f/bin/activate"
            VENV_ACTIVATED=true
            break
        fi
    done
    if [ "$VENV_ACTIVATED" = true ]; then
        break
    fi
done

if [ "$VENV_ACTIVATED" = false ]; then
    echo "⚠ No se encontró entorno virtual. Creando uno nuevo en $APP_DIR/antenv..."
    python3 -m venv "$APP_DIR/antenv"
    source "$APP_DIR/antenv/bin/activate"
    echo "✓ Entorno virtual creado y activado"
fi

echo "Python: $(python3 --version 2>&1)"
echo "Pip: $(pip3 --version 2>&1)"
echo "VIRTUAL_ENV: $VIRTUAL_ENV"

# ============================================================
# PASO 3: Instalar dependencias
# ============================================================
echo ""
echo "=== PASO 3: Instalando dependencias ==="

# Buscar requirements.txt
REQ_FILE=""
if [ -f "$APP_DIR/requirements.txt" ]; then
    REQ_FILE="$APP_DIR/requirements.txt"
elif [ -f "$APP_DIR/morenapos/requirements.txt" ]; then
    REQ_FILE="$APP_DIR/morenapos/requirements.txt"
fi

if [ -n "$REQ_FILE" ]; then
    echo "Requirements encontrado: $REQ_FILE"
    echo "Contenido:"
    cat "$REQ_FILE"
    echo ""
    
    # Verificar si Django ya está instalado
    if python3 -c "import django" 2>/dev/null; then
        DJANGO_VER=$(python3 -c "import django; print(django.get_version())")
        echo "✓ Django $DJANGO_VER ya está instalado"
    else
        echo "Instalando dependencias desde $REQ_FILE..."
        pip3 install --no-cache-dir -r "$REQ_FILE" 2>&1
        echo "✓ Dependencias instaladas"
    fi
    
    # Verificar instalación
    echo ""
    echo "Verificando paquetes instalados:"
    python3 -c "import django; print(f'✓ Django {django.get_version()}')" 2>&1 || echo "✗ Django NO instalado"
    python3 -c "import mssql; print(f'✓ mssql-django {mssql.__version__}')" 2>&1 || echo "⚠ mssql-django no encontrado"
    python3 -c "import django_htmx; print(f'✓ django-htmx')" 2>&1 || echo "⚠ django-htmx no encontrado"
else
    echo "✗ No se encontró requirements.txt"
fi

# ============================================================
# PASO 4: Verificar ODBC Driver para SQL Server
# ============================================================
echo ""
echo "=== PASO 4: Verificando ODBC Driver ==="
if command -v odbcinst &> /dev/null; then
    echo "Drivers ODBC instalados:"
    odbcinst -q -d 2>/dev/null || echo "  No se pudieron listar drivers"
fi

python3 -c "
try:
    import pyodbc
    print(f'✓ pyodbc {pyodbc.version}')
    print(f'  Drivers: {pyodbc.drivers()}')
except ImportError:
    print('⚠ pyodbc no instalado')
except Exception as e:
    print(f'⚠ Error con pyodbc: {e}')
" 2>&1

# ============================================================
# PASO 5: Recopilar archivos estáticos
# ============================================================
echo ""
echo "=== PASO 5: Recopilando archivos estáticos ==="

if [ -f "$APP_DIR/morenapos/manage.py" ]; then
    cd "$APP_DIR/morenapos"
    echo "Ejecutando collectstatic desde $(pwd)..."
    python3 manage.py collectstatic --noinput 2>&1 || echo "⚠ collectstatic falló (no crítico)"
    cd "$APP_DIR"
elif [ -f "$APP_DIR/manage.py" ]; then
    echo "Ejecutando collectstatic desde $APP_DIR..."
    python3 manage.py collectstatic --noinput 2>&1 || echo "⚠ collectstatic falló (no crítico)"
fi

# ============================================================
# PASO 6: Iniciar Gunicorn
# ============================================================
echo ""
echo "=== PASO 6: Iniciando Gunicorn ==="

# Determinar desde dónde ejecutar gunicorn
if [ -f "$APP_DIR/morenapos/manage.py" ]; then
    # La app está en morenapos/
    cd "$APP_DIR/morenapos"
    echo "Directorio de trabajo: $(pwd)"
    echo "Contenido:"
    ls -la
    echo ""
    echo "Ejecutando: gunicorn --bind=0.0.0.0:8000 --workers=2 --timeout=120 wsgi:application"
    exec gunicorn --bind=0.0.0.0:8000 \
         --workers=2 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=info \
         wsgi:application
elif [ -f "$APP_DIR/manage.py" ]; then
    # La app está en la raíz
    cd "$APP_DIR"
    echo "Directorio de trabajo: $(pwd)"
    echo "Ejecutando: gunicorn --bind=0.0.0.0:8000 --workers=2 --timeout=120 wsgi:application"
    exec gunicorn --bind=0.0.0.0:8000 \
         --workers=2 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=info \
         wsgi:application
else
    echo "✗ No se encontró manage.py. No se puede iniciar Gunicorn."
    echo "Contenido de $APP_DIR:"
    ls -la "$APP_DIR"
    exit 1
fi
