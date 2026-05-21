Write-Host "============================================" -ForegroundColor Cyan
Write-Host "ACTIVADOR DE ENTORNO VIRTUAL (PowerShell)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Cambiar al directorio del proyecto si es necesario
if ($PWD.Path -notlike "*morenapos*") {
    Set-Location "morenapos"
    Write-Host "Cambiado a directorio: $PWD" -ForegroundColor Yellow
}

Write-Host "1. Verificando entorno virtual..." -ForegroundColor Green
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "   - Entorno virtual encontrado en: $PWD\venv" -ForegroundColor Green
} else {
    Write-Host "   - ERROR: No se encontró el entorno virtual" -ForegroundColor Red
    Write-Host "   - Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   - ERROR: No se pudo crear el entorno virtual" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "2. Activando entorno virtual..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "3. Verificando Python..." -ForegroundColor Green
python --version

Write-Host ""
Write-Host "4. Verificando pip..." -ForegroundColor Green
pip --version

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "¡ENTORNO ACTIVADO! Deberías ver (venv) en el prompt." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para instalar dependencias, ejecuta:" -ForegroundColor Yellow
Write-Host "   pip install -r requirements-basic.txt" -ForegroundColor White
Write-Host ""
Write-Host "Para ejecutar el servidor:" -ForegroundColor Yellow
Write-Host "   python manage.py runserver" -ForegroundColor White