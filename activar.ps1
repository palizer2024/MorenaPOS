# Script para activar el entorno virtual de MorenaPOS
# Ejecutar desde PowerShell en la raíz del proyecto (D:\MorenaPOS)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "ACTIVANDO ENTORNO VIRTUAL MORENAPOS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (Test-Path "morenapos") {
    Write-Host "✓ Proyecto MorenaPOS encontrado" -ForegroundColor Green
} else {
    Write-Host "✗ ERROR: No se encuentra el directorio 'morenapos'" -ForegroundColor Red
    Write-Host "  Ejecuta este script desde D:\MorenaPOS\" -ForegroundColor Yellow
    exit 1
}

# Cambiar al directorio del proyecto
Set-Location "morenapos"
Write-Host "✓ Directorio cambiado a: $PWD" -ForegroundColor Green

# Verificar entorno virtual
Write-Host ""
Write-Host "1. Verificando entorno virtual..." -ForegroundColor Green
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "   ✓ Entorno virtual encontrado" -ForegroundColor Green
} else {
    Write-Host "   ⚠ No se encontró el entorno virtual" -ForegroundColor Yellow
    Write-Host "   Creando entorno virtual..." -ForegroundColor Yellow
    
    # Verificar Python
    $pythonCheck = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ✗ ERROR: Python no está instalado" -ForegroundColor Red
        Write-Host "   Instala Python desde https://python.org" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "   Usando: $pythonCheck" -ForegroundColor Gray
    python -m venv "venv"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ✗ ERROR: No se pudo crear el entorno virtual" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "   ✓ Entorno virtual creado" -ForegroundColor Green
}

# Activar entorno virtual
Write-Host ""
Write-Host "2. Activando entorno virtual..." -ForegroundColor Green
try {
    & "venv\Scripts\Activate.ps1"
    Write-Host "   ✓ Entorno virtual activado" -ForegroundColor Green
} catch {
    Write-Host "   ✗ ERROR: No se pudo activar" -ForegroundColor Red
    Write-Host "   Detalles: $_" -ForegroundColor Red
    exit 1
}

# Verificaciones
Write-Host ""
Write-Host "3. Verificando instalación..." -ForegroundColor Green
python --version
pip --version

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "¡ENTORNO ACTIVADO! (venv) debería aparecer en el prompt." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Comandos útiles:" -ForegroundColor Yellow
Write-Host "   pip install -r requirements.txt" -ForegroundColor White
Write-Host "   python manage.py runserver" -ForegroundColor White
Write-Host "   python manage.py migrate" -ForegroundColor White
Write-Host ""
Write-Host "Para desactivar: deactivate" -ForegroundColor Gray
Write-Host ""