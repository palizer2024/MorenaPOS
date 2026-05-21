@echo off
echo ============================================
echo VERIFICADOR DE ENTORNO VIRTUAL MORENAPOS
echo ============================================
echo.
echo 1. Directorio actual: %CD%
echo.
echo 2. Verificando entorno virtual...
if exist "venv\Scripts\activate.bat" (
    echo   - Entorno virtual encontrado en: %CD%\venv
) else (
    echo   - ERROR: No se encontró el entorno virtual
    goto :error
)
echo.
echo 3. Activando entorno virtual...
call venv\Scripts\activate.bat
echo.
echo 4. Verificando Python...
python --version
echo.
echo 5. Verificando pip...
pip --version
echo.
echo 6. Verificando Django...
python -c "import django; print(f'Django version: {django.__version__}')" 2>nul || echo Django no instalado
echo.
echo ============================================
echo Si ves (venv) al inicio de la línea, el entorno está activo
echo ============================================
pause
exit /b 0

:error
echo.
echo ERROR: No se pudo encontrar el entorno virtual.
echo Ejecuta: py -m venv venv
pause
exit /b 1