# Script completo para activar entorno y ejecutar servidor MorenaPOS
# Ejecutar desde PowerShell en D:\MorenaPOS>

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "INICIANDO PROYECTO MORENAPOS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Paso 1: Verificar si el entorno virtual está activo
$venvActive = $env:VIRTUAL_ENV -ne $null
if (-not $venvActive) {
    Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
    if (Test-Path "morenapos\venv\Scripts\Activate.ps1") {
        & "morenapos\venv\Scripts\Activate.ps1"
        Write-Host "Entorno virtual activado." -ForegroundColor Green
    } else {
        Write-Host "ERROR: No se encontró el entorno virtual." -ForegroundColor Red
        Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
        & "morenapos\venv\Scripts\python.exe" -m venv "morenapos\venv"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "No se pudo crear el entorno virtual." -ForegroundColor Red
            exit 1
        }
        & "morenapos\venv\Scripts\Activate.ps1"
    }
} else {
    Write-Host "Entorno virtual ya activado." -ForegroundColor Green
}

# Paso 2: Cambiar al directorio del proyecto
Set-Location "morenapos"
Write-Host "Directorio actual: $PWD" -ForegroundColor Green

# Paso 3: Verificar que manage.py existe
if (-not (Test-Path "manage.py")) {
    Write-Host "ERROR: No se encuentra manage.py" -ForegroundColor Red
    exit 1
}

# Paso 4: Verificar que morenapos sea un paquete Python (tenga __init__.py)
if (-not (Test-Path "__init__.py")) {
    Write-Host "Creando __init__.py para hacer morenapos un paquete Python..." -ForegroundColor Yellow
    "# This file makes the morenapos directory a Python package" | Out-File "__init__.py" -Encoding UTF8
    Write-Host "__init__.py creado." -ForegroundColor Green
}

# Paso 5: Ejecutar el servidor
Write-Host ""
Write-Host "Iniciando servidor de desarrollo Django..." -ForegroundColor Green
Write-Host "Presiona Ctrl+C para detener." -ForegroundColor Yellow
Write-Host "URL: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host ""

# Usar el Python del entorno virtual
& "venv\Scripts\python.exe" manage.py runserver