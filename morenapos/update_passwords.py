#!/usr/bin/env python
"""
Script para actualizar todas las contraseñas de usuarios a '12345'.
"""
import os
import sys
import base64
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'morenapos.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db import connection

def update_passwords():
    """Actualizar todas las contraseñas a '12345'."""
    print("=== ACTUALIZACIÓN DE CONTRASEÑAS ===")
    
    # Contraseña nueva: '12345' en base64 (igual que las actuales)
    nueva_contrasena = "12345"
    nueva_contrasena_base64 = base64.b64encode(nueva_contrasena.encode()).decode()
    
    print(f"Contraseña nueva: '{nueva_contrasena}'")
    print(f"Contraseña en base64: '{nueva_contrasena_base64}'")
    
    with connection.cursor() as cursor:
        # Contar usuarios antes de actualizar
        cursor.execute("SELECT COUNT(*) FROM usuario")
        total_antes = cursor.fetchone()[0]
        print(f"\nTotal de usuarios antes de actualizar: {total_antes}")
        
        # Contar usuarios activos
        cursor.execute("SELECT COUNT(*) FROM usuario WHERE estado = 1")
        activos_antes = cursor.fetchone()[0]
        print(f"Usuarios activos (estado=1): {activos_antes}")
        
        # Mostrar algunos usuarios antes de actualizar
        print("\n=== ALGUNOS USUARIOS ANTES DE ACTUALIZAR ===")
        cursor.execute("""
            SELECT TOP 5 id, nombres, nombreu, clave, estado
            FROM usuario 
            ORDER BY id
        """)
        usuarios_antes = cursor.fetchall()
        for i, user in enumerate(usuarios_antes, 1):
            print(f"{i}. ID: {user[0]}, Usuario: '{user[2]}', Contraseña actual: '{user[3]}'")
        
        # Actualizar TODAS las contraseñas
        print(f"\nActualizando todas las contraseñas a '{nueva_contrasena_base64}'...")
        cursor.execute("""
            UPDATE usuario 
            SET clave = %s
        """, [nueva_contrasena_base64])
        
        filas_afectadas = cursor.rowcount
        print(f"Filas actualizadas: {filas_afectadas}")
        
        # Mostrar algunos usuarios después de actualizar
        print("\n=== ALGUNOS USUARIOS DESPUÉS DE ACTUALIZAR ===")
        cursor.execute("""
            SELECT TOP 5 id, nombres, nombreu, clave, estado
            FROM usuario 
            ORDER BY id
        """)
        usuarios_despues = cursor.fetchall()
        for i, user in enumerate(usuarios_despues, 1):
            print(f"{i}. ID: {user[0]}, Usuario: '{user[2]}', Contraseña nueva: '{user[3]}'")
        
        # Verificar que todas las contraseñas sean iguales
        cursor.execute("SELECT COUNT(DISTINCT clave) FROM usuario")
        distinct_passwords = cursor.fetchone()[0]
        print(f"\nContraseñas distintas en la base de datos: {distinct_passwords}")
        
        if distinct_passwords == 1:
            print("✓ Todas las contraseñas han sido actualizadas correctamente")
        else:
            print("✗ Algunas contraseñas no se actualizaron correctamente")
        
        # Mostrar instrucciones para login
        print("\n=== INSTRUCCIONES PARA LOGIN ===")
        print(f"1. Nombre de usuario: cualquier usuario de la lista")
        print(f"2. Contraseña: '{nueva_contrasena}' (sin comillas)")
        print(f"3. Asegúrate de que el usuario tenga estado = 1 (activo)")
        print(f"4. Selecciona una sede activa")
        
        # Listar algunos usuarios activos para probar
        print("\n=== USUARIOS ACTIVOS PARA PROBAR ===")
        cursor.execute("""
            SELECT TOP 10 nombres, nombreu, estado
            FROM usuario 
            WHERE estado = 1
            ORDER BY id
        """)
        usuarios_activos = cursor.fetchall()
        for i, user in enumerate(usuarios_activos, 1):
            print(f"{i}. Usuario: '{user[1]}', Nombre: {user[0]}")
        
        return filas_afectadas

if __name__ == '__main__':
    try:
        filas = update_passwords()
        print(f"\n✓ Actualización completada. {filas} usuarios actualizados.")
        print("Ahora puedes iniciar sesión con cualquier usuario usando la contraseña '12345'")
    except Exception as e:
        print(f"\n✗ Error durante la actualización: {e}")
        sys.exit(1)