#!/bin/bash

# startup.sh - Script de inicio para Azure App Service (Linux)
# MorenaPOS - Django + Gunicorn

set -e

echo "=== INICIO STARTUP.SH ==="
echo "Directorio actual: $(pwd)"
echo "HOME: $HOME"

# Buscar el directorio de la aplicación
# Oryx extrae el build en /tmp/<build-id>/ y desde ahí ejecuta
APP_DIR="/home/site/wwwroot"

if [ -f "$APP_DIR/morenapos/manage.py" ]; then
    echo "App encontrada en $APP_DIR"
elif [ -f "$APP_DIR/oryx-manifest.toml" ]; then
    echo "Manifest encontrado en $APP_DIR"
    # Leer el manifest para encontrar el directorio de build
    if command -v python3 &> /dev/null; then
        BUILD_DIR=$(python3 -c "import tomllib; m=tomllib.load(open('$APP_DIR/oryx-manifest.toml','rb')); print(m.get('source','').get('dir',''))" 2>/dev/null || echo "")
        if [ -n "$BUILD_DIR" ] && [ -d "$BUILD_DIR/antenv" ]; then
            echo "Usando directorio de build: $BUILD_DIR"
            APP_DIR="$BUILD_DIR"
        fi
    fi
else
    echo "ADVERTENCIA: No se encontró manage.py ni manifest. Buscando..."
    # Buscar en /tmp/
    for dir in /tmp/*/; do
        if [ -f "${dir}morenapos/manage.py" ]; then
            echo "App encontrada en $dir"
            APP_DIR="$dir"
            break
        fi
    done
fi

cd "$APP_DIR"
echo "Directorio de trabajo: $(pwd)"
echo "Contenido:"
ls -la
echo ""

# Activar el entorno virtual
VENV_ACTIVATED=false

# Buscar antenv en varias ubicaciones
for VENV_PATH in "/tmp/"*"/antenv" "$APP_DIR/antenv" "/opt/venv" "$HOME/antenv"; do
    if [ -d "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/activate" ]; then
        # Expandir wildcard si es necesario
        for f in $VENV_PATH; do
            if [ -f "$f/bin/activate" ]; then
                echo "Activando entorno: $f"
                source "$f/bin/activate"
                VENV_ACTIVATED=true
                break
            fi
        done
        if [ "$VENV_ACTIVATED" = true ]; then
            break
        fi
    fi
done

if [ "$VENV_ACTIVATED" = false ]; then
    echo "ADVERTENCIA: No se encontró entorno virtual. Creando uno nuevo..."
    python3 -m venv antenv
    source antenv/bin/activate
fi

echo "Python: $(python3 --version 2>&1)"
echo "Pip: $(pip3 --version 2>&1)"
echo "VIRTUAL_ENV: $VIRTUAL_ENV"

# Verificar e instalar dependencias
echo "Verificando dependencias..."
if ! python3 -c "import django" 2>/dev/null; then
    echo "Instalando dependencias..."
    # Buscar requirements.txt
    for REQ_FILE in "$APP_DIR/requirements.txt" "$APP_DIR/morenapos/requirements.txt"; do
        if [ -f "$REQ_FILE" ]; then
            echo "Instalando desde $REQ_FILE"
            pip3 install --no-cache-dir -r "$REQ_FILE" 2>&1
            break
        fi
    done
    echo "Verificando instalación..."
    python3 -c "import django; print(f'Django {django.get_version()} instalado')"
fi

# Recopilar archivos estáticos
if [ -f "$APP_DIR/morenapos/manage.py" ]; then
    echo "Recopilando archivos estáticos..."
    cd "$APP_DIR/morenapos"
    python3 manage.py collectstatic --noinput 2>&1 || echo "collectstatic falló (no crítico)"
    cd "$APP_DIR"
fi

# Iniciar Gunicorn
echo "=== INICIANDO GUNICORN ==="
cd "$APP_DIR/morenapos"
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
