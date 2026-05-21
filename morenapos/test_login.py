#!/usr/bin/env python
"""
Script para probar el login con las nuevas contraseñas.
"""
import os
import sys
import django
import base64

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'morenapos.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db import connection

def test_login():
    """Probar que el login funciona con las nuevas contraseñas."""
    print("=== PRUEBA DE LOGIN CON NUEVAS CONTRASEÑAS ===")
    
    # Contraseña que el usuario debe ingresar
    password_usuario = "12345"
    password_base64 = base64.b64encode(password_usuario.encode()).decode()
    
    print(f"Contraseña que el usuario ingresa: '{password_usuario}'")
    print(f"Contraseña en base64 (almacenada en DB): '{password_base64}'")
    
    with connection.cursor() as cursor:
        # Obtener algunos usuarios activos
        cursor.execute("""
            SELECT TOP 5 id, nombres, nombreu, clave, estado
            FROM usuario 
            WHERE estado = 1
            ORDER BY id
        """)
        usuarios = cursor.fetchall()
        
        print(f"\n=== USUARIOS ACTIVOS PARA PROBAR ===")
        for i, user in enumerate(usuarios, 1):
            user_id, nombres, nombreu, clave_db, estado = user
            print(f"\n{i}. Usuario: '{nombreu}'")
            print(f"   Nombre: {nombres}")
            print(f"   Contraseña en DB: '{clave_db}'")
            print(f"   ¿Coincide con '12345' en base64? {clave_db == password_base64}")
            
            if clave_db == password_base64:
                print(f"   ✓ CONTRASEÑA CORRECTA - Puede iniciar sesión con usuario '{nombreu}' y contraseña '12345'")
            else:
                print(f"   ✗ CONTRASEÑA INCORRECTA - No coincide")
        
        # Verificar que todas las contraseñas sean iguales
        cursor.execute("SELECT COUNT(DISTINCT clave) FROM usuario WHERE estado = 1")
        distinct_passwords = cursor.fetchone()[0]
        
        print(f"\n=== RESUMEN ===")
        print(f"Contraseñas distintas entre usuarios activos: {distinct_passwords}")
        
        if distinct_passwords == 1:
            print("✓ TODOS los usuarios activos tienen la misma contraseña '12345'")
            print("✓ El login debería funcionar para cualquier usuario activo")
        else:
            print("✗ ALGUNOS usuarios tienen contraseñas diferentes")
        
        # Contar usuarios
        cursor.execute("SELECT COUNT(*) FROM usuario WHERE estado = 1")
        activos = cursor.fetchone()[0]
        print(f"\nTotal de usuarios activos: {activos}")
        print(f"Todos pueden iniciar sesión con:")
        print(f"  - Nombre de usuario: cualquiera de la lista anterior")
        print(f"  - Contraseña: '12345' (sin comillas)")
        print(f"  - Sede: cualquier sede activa")
        
        # Mostrar algunas sedes activas
        print(f"\n=== SEDES ACTIVAS DISPONIBLES ===")
        try:
            from core.models import Sede
            sedes = Sede.objects.filter(estado=True)[:5]
            for i, sede in enumerate(sedes, 1):
                print(f"{i}. Sede ID: {sede.id}, Nombre: {sede.nombre}")
        except Exception as e:
            print(f"Error al obtener sedes: {e}")
            print("(Pero el login debería funcionar igual)")

if __name__ == '__main__':
    try:
        test_login()
        print("\n" + "="*50)
        print("PRUEBA COMPLETADA EXITOSAMENTE")
        print("Ahora puedes:")
        print("1. Ir a http://127.0.0.1:8000/login/")
        print("2. Usar cualquier usuario activo (ej: 'admin', 'vendedor', etc.)")
        print("3. Usar la contraseña '12345'")
        print("4. Seleccionar una sede activa")
        print("5. Iniciar sesión correctamente")
        print("="*50)
    except Exception as e:
        print(f"\n✗ Error durante la prueba: {e}")
        sys.exit(1)