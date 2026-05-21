"""
Context processors para la aplicación core.
"""
from .models import Sede


def sede_context(request):
    """
    Agrega información de sede al contexto de las plantillas.
    """
    context = {}
    
    # Obtener la sede activa de la sesión si existe
    sede_id = request.session.get('sede_id')
    if sede_id:
        try:
            sede = Sede.objects.get(id=sede_id, estado=True)
            context['sede_actual'] = sede
        except Sede.DoesNotExist:
            pass
    
    # Obtener todas las sedes activas para menús de selección
    context['sedes_activas'] = Sede.objects.filter(estado=True)
    
    return context