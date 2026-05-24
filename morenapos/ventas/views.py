from django.shortcuts import render
from django.db import connection
from django.utils.timezone import now, localtime
from datetime import datetime
from core.views import login_required


@login_required
def caja(request):
    """
    Vista principal del módulo de caja.
    Muestra tickets de la sede logueada con filtro por fecha.
    Solo lectura, no modifica ninguna tabla.
    """
    sede_id = request.session.get('sede_id')
    sede_nombre = request.session.get('sede_nombre', '')
    
    # Fecha seleccionada (hoy por defecto, en hora local)
    fecha_str = request.GET.get('fecha', '')
    try:
        fecha_filtro = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else localtime(now()).date()
    except ValueError:
        fecha_filtro = localtime(now()).date()
    
    # Obtener tickets de la sede y fecha seleccionada
    tickets = []
    if sede_id:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT t.Id, t.Serie, t.Correlativo, t.NombreCliente,
                       t.Total, t.Turno, t.Created, t.UserCreated, t.Duplicado
                FROM ticket t
                WHERE t.Id_Sede = %s AND CAST(t.Created AS DATE) = %s AND t.Estado = 1
                ORDER BY t.Created ASC
            """, [sede_id, fecha_filtro])
            rows = cursor.fetchall()
            for row in rows:
                tickets.append({
                    'id': row[0],
                    'serie': (row[1] or '').strip(),
                    'correlativo': row[2],
                    'cliente': (row[3] or '').strip(),
                    'total': float(row[4]) if row[4] else 0,
                    'turno': (row[5] or '').strip(),
                    'created': row[6],
                    'user': (row[7] or '').strip(),
                    'duplicado': row[8],
                })
    
    context = {
        'usuario_nombre': request.session.get('usuario_nombre', ''),
        'usuario_login': request.session.get('usuario_login', ''),
        'sede_id': sede_id,
        'sede_nombre': sede_nombre,
        'turno': request.session.get('turno', ''),
        'rol': request.session.get('usuario_rol', ''),
        'tickets': tickets,
        'fecha_actual': fecha_filtro.isoformat(),
        'fecha_actual_str': fecha_filtro.strftime('%Y-%m-%d'),
        'today_str': localtime(now()).date().strftime('%Y-%m-%d'),
    }
    return render(request, 'ventas/caja.html', context)
