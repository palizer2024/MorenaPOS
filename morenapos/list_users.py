#!/usr/bin/env python
"""
Listar usuarios de la tabla 'usuario' con sus credenciales.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'morenapos.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db import connection

def list_users():
    """Listar usuarios con sus credenciales."""
    print("=== LISTA DE USUARIOS DISPONIBLES ===")
    print("Total de usuarios en tabla 'usuario':")
    
    with connection.cursor() as cursor:
        # Contar usuarios
        cursor.execute("SELECT COUNT(*) FROM usuario")
        total = cursor.fetchone()[0]
        print(f"Total: {total}")
        
        # Obtener usuarios activos
        cursor.execute("SELECT COUNT(*) FROM usuario WHERE estado = 1")
        activos = cursor.fetchone()[0]
        print(f"Activos (estado=1): {activos}")
        
        # Listar primeros 20 usuarios
        print("\n=== PRIMEROS 20 USUARIOS ===")
        cursor.execute("""
            SELECT TOP 20 
                id, 
                nombres, 
                nombreu, 
                clave,
                estado,
                Id_Rol
            FROM usuario 
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        for i, user in enumerate(users, 1):
            user_id, nombres, nombreu, clave, estado, id_rol = user
            print(f"\n{i}. ID: {user_id}")
            print(f"   Nombre: {nombres}")
            print(f"   Usuario (nombreu): '{nombreu}'")
            print(f"   Contraseña (clave): '{clave}'")
            print(f"   Estado: {estado} ({'Activo' if estado == 1 else 'Inactivo'})")
            print(f"   Rol ID: {id_rol}")
        
        # Verificar tabla rol para ver nombres de roles
        print("\n=== ROLES DISPONIBLES ===")
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'rol'")
        exists = cursor.fetchone()[0]
        
        if exists > 0:
            cursor.execute("SELECT id_rol, nombre_rol FROM rol ORDER BY id_rol")
            roles = cursor.fetchall()
            for rol in roles:
                print(f"   ID {rol[0]}: {rol[1]}")
        else:
            print("   Tabla 'rol' no encontrada")
        
        # Sugerencias para login
        print("\n=== SUGERENCIAS PARA LOGIN ===")
        print("1. Usa el campo 'nombreu' como nombre de usuario")
        print("2. Usa el campo 'clave' como contraseña")
        print("3. Asegúrate de seleccionar una sede activa")
        print("4. El usuario debe tener estado = 1 (activo)")
        
        # Mostrar algunos usuarios activos como sugerencia
        print("\n=== USUARIOS ACTIVOS SUGERIDOS ===")
        cursor.execute("""
            SELECT TOP 5 nombres, nombreu, clave 
            FROM usuario 
            WHERE estado = 1 
            ORDER BY id
        """)
        active_users = cursor.fetchall()
        for i, user in enumerate(active_users, 1):
            print(f"{i}. Usuario: '{user[1]}', Nombre: {user[0]}, Clave: '{user[2]}'")

if __name__ == '__main__':
    list_users()