# Script simple para MorenaPOS
# Ejecutar desde D:\MorenaPOS>

Write-Host "Activando entorno virtual..." -ForegroundColor Yellow

# Si no está activo, activar
if (Test-Path "morenapos\venv\Scripts\Activate.ps1") {
    & "morenapos\venv\Scripts\Activate.ps1"
} else {
    Write-Host "No hay entorno virtual. Creando..." -ForegroundColor Red
    python -m venv "morenapos\venv"
    & "morenapos\venv\Scripts\Activate.ps1"
}

Write-Host "Entorno activado." -ForegroundColor Green

# Cambiar al directorio del proyecto
cd "morenapos"

Write-Host "Ejecutando servidor..." -ForegroundColor Green
python manage.py runserver