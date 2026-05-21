"""
Vistas para la aplicación core (autenticación, sedes, usuarios).
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required as django_login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.core.cache import cache
from django.urls import reverse
from django.http import JsonResponse
from functools import wraps
import base64
from django.db import connection

from .models import Sede, UsuarioSede, Usuario


def login_required(view_func):
    """
    Decorador personalizado que reemplaza @login_required de Django.
    Verifica si existe 'usuario_id' en la sesión (aunque sea 0).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated or 'usuario_id' in request.session:
            return view_func(request, *args, **kwargs)
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path(), login_url=reverse('login'))
    return _wrapped_view


@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    """
    Vista de inicio de sesión simplificada - solo pide sede.
    """
    # Si ya hay sesión activa, redirigir a caja
    if request.session.get('usuario_id'):
        return redirect('ventas:caja')
    
    # Obtener sedes activas con SQL directo
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, nombre FROM sede WHERE estado = 1 ORDER BY nombre")
        sedes = [{'id': row[0], 'nombre': row[1]} for row in cursor.fetchall()]
    
    if request.method == 'POST':
        sede_id = request.POST.get('sede')
        
        if not sede_id:
            messages.error(request, 'Debe seleccionar una sede.')
            return render(request, 'core/login.html', {'sedes': sedes})
        
        # Verificar que la sede existe y está activa
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, nombre FROM sede WHERE id = %s AND estado = 1", [sede_id])
            sede_row = cursor.fetchone()
        
        if not sede_row:
            messages.error(request, 'Sede no encontrada o inactiva.')
            return render(request, 'core/login.html', {'sedes': sedes})
        
        sede_id_db, sede_nombre = sede_row
        
        # Crear sesión con datos básicos
        request.session['usuario_id'] = 0
        request.session['usuario_nombre'] = 'Usuario'
        request.session['usuario_login'] = 'usuario'
        request.session['usuario_rol'] = 0
        request.session['sede_id'] = sede_id_db
        request.session['sede_nombre'] = sede_nombre
        request.session['turno'] = ''
        
        messages.success(request, f'Bienvenido a {sede_nombre}')
        return redirect('ventas:caja')
    
    return render(request, 'core/login.html', {'sedes': sedes})


@login_required
def logout_view(request):
    """
    Cerrar sesión y limpiar datos de sesión.
    """
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('login')


@login_required
def seleccionar_sede(request):
    """
    Permite al usuario seleccionar una sede si tiene acceso a múltiples.
    """
    if request.method == 'POST':
        sede_id = request.POST.get('sede')
        try:
            usuario_sede = UsuarioSede.objects.get(
                usuario=request.user, 
                sede_id=sede_id, 
                activo=True
            )
            request.session['sede_id'] = usuario_sede.sede.id
            request.session['sede_nombre'] = usuario_sede.sede.nombre
            messages.success(request, f'Sede {usuario_sede.sede.nombre} seleccionada.')
            return redirect('ventas:caja')
        except UsuarioSede.DoesNotExist:
            messages.error(request, 'No tiene acceso a esta sede.')
    
    # Obtener sedes disponibles para el usuario
    sedes = Sede.objects.filter(
        usuariosede__usuario=request.user,
        usuariosede__activo=True,
        estado=True
    ).distinct()
    
    return render(request, 'core/seleccionar_sede.html', {'sedes': sedes})


@login_required
def dashboard(request):
    """
    Dashboard principal después del login.
    """
    sede_id = request.session.get('sede_id')
    if not sede_id:
        return redirect('seleccionar_sede')
    
    try:
        sede = Sede.objects.get(id=sede_id)
    except Sede.DoesNotExist:
        messages.error(request, 'Sede no encontrada.')
        return redirect('seleccionar_sede')
    
    context = {
        'sede': sede,
        'usuario': request.user,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def api_ticket_detalle(request, ticket_id):
    """
    API que retorna el detalle de un ticket (productos, cantidades, precios).
    Tabla: ticketdet con JOIN a productogeneral para el nombre del producto.
    """
    import json
    from django.utils.timezone import now as tz_now
    
    sede_id = request.session.get('sede_id')
    if not sede_id:
        return JsonResponse({'error': 'Sin sede'}, status=400)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                td.Id,
                td.Id_Producto,
                ISNULL(pg.Nombre, 'Producto #' + CAST(td.Id_Producto AS VARCHAR)) AS ProductoNombre,
                td.Cantidad,
                td.PrecioUnitario,
                td.Total,
                td.Id_Ticket
            FROM ticketdet td
            LEFT JOIN producto p ON p.Id = td.Id_Producto
            LEFT JOIN productogeneral pg ON pg.Id = p.Id_ProductoGeneral
            WHERE td.Id_Ticket = %s
            ORDER BY td.Id
        """, [ticket_id])
        rows = cursor.fetchall()
    
    detalles = []
    for row in rows:
        detalles.append({
            'id': row[0],
            'id_producto': row[1],
            'producto': row[2],
            'cantidad': float(row[3]) if row[3] else 0,
            'precio_unitario': float(row[4]) if row[4] else 0,
            'total': float(row[5]) if row[5] else 0,
        })
    
    return JsonResponse({'detalles': detalles})