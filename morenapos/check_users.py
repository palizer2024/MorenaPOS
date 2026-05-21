#!/usr/bin/env python
"""
Script para verificar usuarios en la base de datos.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'morenapos.settings')
django.setup()

from django.db import connection

def check_users():
    """Verificar usuarios en la base de datos."""
    print("=== Verificación de usuarios en la base de datos ===")
    
    with connection.cursor() as cursor:
        # Verificar tabla usuario
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'usuario'")
        exists = cursor.fetchone()[0]
        print(f"1. Tabla 'usuario' existe: {'Sí' if exists > 0 else 'No'}")
        
        if exists > 0:
            # Primero obtener los nombres de las columnas
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'usuario'
                ORDER BY ORDINAL_POSITION
            """)
            columns = [row[0] for row in cursor.fetchall()]
            print(f"2. Columnas de la tabla 'usuario': {', '.join(columns)}")
            
            cursor.execute('SELECT COUNT(*) FROM usuario')
            count = cursor.fetchone()[0]
            print(f"3. Total de registros en tabla 'usuario': {count}")
            
            if count > 0:
                # Construir consulta con las columnas disponibles
                select_cols = ['id', 'nombres', 'nombreu', 'clave', 'estado', 'Id_Rol']
                available_cols = [col for col in select_cols if col in columns]
                
                if available_cols:
                    query = f'SELECT TOP 10 {", ".join(available_cols)} FROM usuario'
                    cursor.execute(query)
                    users = cursor.fetchall()
                    print(f"4. Primeros {len(users)} usuarios (con credenciales):")
                    for i, user in enumerate(users, 1):
                        user_info = []
                        for j, col in enumerate(available_cols):
                            # Ocultar contraseña completa por seguridad
                            if col == 'clave' and user[j]:
                                masked = user[j][:3] + '***' if len(user[j]) > 3 else '***'
                                user_info.append(f"{col}: {masked}")
                            else:
                                user_info.append(f"{col}: {user[j]}")
                        print(f"   {i}. {', '.join(user_info)}")
                    
                    # Contar usuarios activos
                    if 'estado' in columns:
                        cursor.execute("SELECT COUNT(*) FROM usuario WHERE estado = 1")
                        active_count = cursor.fetchone()[0]
                        print(f"5. Usuarios activos (estado=1): {active_count} de {count}")
                else:
                    print("4. No se encontraron columnas conocidas para mostrar")
            else:
                print("4. La tabla 'usuario' está vacía")
        else:
            print("2. La tabla 'usuario' no existe en la base de datos")
        
        # Verificar tabla auth_user (usuarios de Django por defecto)
        print("\n=== Verificación de tabla auth_user (Django) ===")
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'auth_user'")
        exists_auth = cursor.fetchone()[0]
        print(f"1. Tabla 'auth_user' existe: {'Sí' if exists_auth > 0 else 'No'}")
        
        if exists_auth > 0:
            cursor.execute('SELECT COUNT(*) FROM auth_user')
            count_auth = cursor.fetchone()[0]
            print(f"2. Total de registros en tabla 'auth_user': {count_auth}")
            
            if count_auth > 0:
                cursor.execute('SELECT TOP 5 id, username, email, first_name, last_name, is_active FROM auth_user')
                auth_users = cursor.fetchall()
                print(f"3. Primeros {len(auth_users)} usuarios auth_user:")
                for i, user in enumerate(auth_users, 1):
                    print(f"   {i}. ID: {user[0]}, Usuario: {user[1]}, "
                          f"Email: {user[2]}, Nombre: {user[3]} {user[4]}, Activo: {user[5]}")
        
        # Verificar tabla usuariosede (relación usuario-sede)
        print("\n=== Verificación de tabla usuariosede ===")
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'usuariosede'")
        exists_us = cursor.fetchone()[0]
        print(f"1. Tabla 'usuariosede' existe: {'Sí' if exists_us > 0 else 'No'}")
        
        if exists_us > 0:
            cursor.execute('SELECT COUNT(*) FROM usuariosede')
            count_us = cursor.fetchone()[0]
            print(f"2. Total de registros en tabla 'usuariosede': {count_us}")
            
            if count_us > 0:
                cursor.execute('SELECT TOP 5 id_usuario_sede, id_usuario, id_sede, activo FROM usuariosede')
                user_sedes = cursor.fetchall()
                print(f"3. Primeros {len(user_sedes)} relaciones usuario-sede:")
                for i, us in enumerate(user_sedes, 1):
                    print(f"   {i}. ID: {us[0]}, Usuario ID: {us[1]}, Sede ID: {us[2]}, Activo: {us[3]}")

if __name__ == '__main__':
    check_users()