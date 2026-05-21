#!/usr/bin/env python
"""
Script para iniciar el servidor de desarrollo MorenaPOS.
Ejecutar desde la raíz del proyecto (D:\MorenaPOS)
"""
import os
import sys
import subprocess

def main():
    # Agregar el directorio padre al sys.path
    project_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_dir)
    
    # Cambiar al directorio morenapos
    os.chdir(os.path.join(project_dir, 'morenapos'))
    
    # Activar entorno virtual (no necesario si ya está activo)
    # Ejecutar manage.py runserver
    cmd = [sys.executable, 'manage.py', 'runserver']
    print("Iniciando servidor de desarrollo MorenaPOS...")
    print("Presiona Ctrl+C para detener.")
    subprocess.run(cmd)

if __name__ == '__main__':
    main()