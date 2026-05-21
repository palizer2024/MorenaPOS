from django.shortcuts import render
from core.views import login_required


@login_required
def caja(request):
    """
    Vista principal del módulo de caja - template vacío con datos de sesión.
    Solo lectura, no modifica ninguna tabla.
    """
    context = {
        'usuario_nombre': request.session.get('usuario_nombre', ''),
        'usuario_login': request.session.get('usuario_login', ''),
        'sede_id': request.session.get('sede_id', ''),
        'sede_nombre': request.session.get('sede_nombre', ''),
        'turno': request.session.get('turno', ''),
        'rol': request.session.get('usuario_rol', ''),
    }
    return render(request, 'ventas/caja.html', context)
