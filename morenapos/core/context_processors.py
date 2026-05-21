"""
Context processors para la aplicación core.
"""
from django.db import connection


def sede_context(request):
    """
    Agrega información de sede al contexto de las plantillas.
    Usa SQL directo para evitar errores por columnas que no existen en la DB.
    """
    context = {}
    
    # Obtener la sede activa de la sesión si existe
    sede_id = request.session.get('sede_id')
    if sede_id:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, nombre FROM sede WHERE id = %s AND estado = 1", [sede_id])
            row = cursor.fetchone()
            if row:
                context['sede_actual'] = {'id': row[0], 'nombre': row[1]}
    
    # Obtener todas las sedes activas para menús de selección
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, nombre FROM sede WHERE estado = 1 ORDER BY nombre")
        context['sedes_activas'] = [{'id': row[0], 'nombre': row[1]} for row in cursor.fetchall()]
    
    return context