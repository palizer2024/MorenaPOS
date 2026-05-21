from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def caja(request):
    """
    Vista principal del módulo de caja (punto de venta).
    """
    context = {
        'sede_id': request.session.get('sede_id'),
        'sede_nombre': request.session.get('sede_nombre'),
    }
    return render(request, 'ventas/caja.html', context)
