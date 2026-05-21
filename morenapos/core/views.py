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
from functools import wraps
import base64
from django.db import connection

from .models import Sede, UsuarioSede, Usuario


def login_required(view_func):
    """
    Decorador personalizado que reemplaza @login_required de Django.
    Verifica tanto la autenticación de Django como la sesión manual (usuario_id).
    Esto evita el bucle de redirección infinita entre /dashboard/ y /login/.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated or request.session.get('usuario_id'):
            return view_func(request, *args, **kwargs)
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path(), login_url=reverse('login'))
    return _wrapped_view


@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    """
    Vista de inicio de sesión SIMPLE - verifica directamente en tabla usuario.
    """
    # Si ya hay sesión activa (por sesión personalizada o autenticación Django), redirigir a dashboard
    if request.session.get('usuario_id') or request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        sede_id = request.POST.get('sede')
        
        # Validar campos requeridos
        if not username or not password or not sede_id:
            messages.error(request, 'Todos los campos son requeridos.')
            sedes = Sede.objects.filter(estado=True)
            return render(request, 'core/login.html', {'sedes': sedes})
        
        # Verificar usuario en la tabla usuario directamente
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, nombres, nombreu, clave, estado, Id_Rol
                FROM usuario
                WHERE nombreu = %s AND estado = 1
            """, [username])
            row = cursor.fetchone()
        
        if row:
            user_id, nombres, nombreu, clave_db, estado, id_rol = row
            
            # Verificar contraseña (codificar a base64 para comparar)
            password_base64 = base64.b64encode(password.encode()).decode()
            if password_base64 == clave_db:
                # Verificar acceso a la sede (tabla usuariosede si existe)
                try:
                    # Primero verificar si la tabla usuariosede existe
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
                            WHERE TABLE_NAME = 'usuariosede'
                        """)
                        existe_tabla = cursor.fetchone()[0] > 0
                    
                    if existe_tabla:
                        # Verificar acceso en usuariosede
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT COUNT(*) FROM usuariosede
                                WHERE id_usuario = %s AND id_sede = %s AND activo = 1
                            """, [user_id, sede_id])
                            tiene_acceso = cursor.fetchone()[0] > 0
                        
                        if not tiene_acceso:
                            messages.error(request, 'No tiene acceso a esta sede o la sede está inactiva.')
                            sedes = Sede.objects.filter(estado=True)
                            return render(request, 'core/login.html', {'sedes': sedes})
                    else:
                        # Si no existe tabla usuariosede, solo verificar que la sede exista y esté activa
                        try:
                            sede = Sede.objects.get(id=sede_id, estado=True)
                        except Sede.DoesNotExist:
                            messages.error(request, 'Sede no encontrada o inactiva.')
                            sedes = Sede.objects.filter(estado=True)
                            return render(request, 'core/login.html', {'sedes': sedes})
                    
                    # Obtener información de la sede
                    try:
                        sede = Sede.objects.get(id=sede_id, estado=True)
                    except Sede.DoesNotExist:
                        messages.error(request, 'Sede no encontrada o inactiva.')
                        sedes = Sede.objects.filter(estado=True)
                        return render(request, 'core/login.html', {'sedes': sedes})
                    
                    # Login exitoso - crear sesión manual
                    request.session['usuario_id'] = user_id
                    request.session['usuario_nombre'] = nombres
                    request.session['usuario_login'] = nombreu
                    request.session['usuario_rol'] = id_rol
                    request.session['sede_id'] = sede.id
                    request.session['sede_nombre'] = sede.nombre
                    
                    messages.success(request, f'Bienvenido, {nombres}')
                    return redirect('ventas:caja')
                    
                except Exception as e:
                    messages.error(request, f'Error al verificar acceso: {str(e)}')
            else:
                messages.error(request, 'Contraseña incorrecta.')
        else:
            messages.error(request, 'Usuario no encontrado o inactivo.')
    
    # GET request: mostrar formulario de login
    sedes = Sede.objects.filter(estado=True)
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