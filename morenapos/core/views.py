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


@login_required
def api_consultar_documento(request, numero):
    """
    API que consulta RUC o DNI en APIPERU y devuelve los datos.
    - Si numero tiene 8 dígitos → consulta DNI
    - Si numero tiene 11 dígitos → consulta RUC
    Usa el token configurado en settings.APIPERU_TOKEN.
    """
    import requests
    from django.conf import settings
    
    numero = numero.strip()
    
    if len(numero) == 8:
        tipo = 'dni'
        endpoint = 'https://apiperu.dev/api/dni'
    elif len(numero) == 11:
        tipo = 'ruc'
        endpoint = 'https://apiperu.dev/api/ruc'
    else:
        return JsonResponse({'error': 'Número inválido. DNI = 8 dígitos, RUC = 11 dígitos'}, status=400)
    
    api_token = getattr(settings, 'APIPERU_TOKEN', '')
    if not api_token:
        return JsonResponse({'error': 'APIPERU_TOKEN no configurado en settings'}, status=500)
    
    try:
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
        }
        payload = {tipo: numero}
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return JsonResponse({'error': f'APIPERU error: {response.status_code}', 'detalle': response.text}, status=502)
        
        data = response.json()
        
        # APIPERU devuelve: {"success":true,"data":{...}}
        inner = data.get('data') or {}
        success = data.get('success', False)
        
        if tipo == 'dni':
            return JsonResponse({
                'tipo': 'dni',
                'numero': numero,
                'nombre': inner.get('nombre_completo', ''),
                'direccion': inner.get('direccion_completa', ''),
                'success': success,
            })
        else:
            return JsonResponse({
                'tipo': 'ruc',
                'numero': numero,
                'nombre': inner.get('nombre_o_razon_social', ''),
                'direccion': inner.get('direccion_completa', ''),
                'success': success,
            })
            
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'Tiempo de espera agotado al consultar APIPERU'}, status=504)
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'No se pudo conectar con APIPERU'}, status=502)
    except Exception as e:
        return JsonResponse({'error': f'Error al consultar: {str(e)}'}, status=500)


@login_required
def api_buscar_cliente(request, query):
    """
    Busca clientes en la tabla local Cliente por NroDocumento.
    Devuelve hasta 10 coincidencias para autocomplete.
    """
    query = query.strip()
    if len(query) < 2:
        return JsonResponse({'clientes': []})
    
    with connection.cursor() as cursor:
        # Usamos ROW_NUMBER para evitar duplicados por NroDocumento,
        # priorizando el registro que tenga Domicilio no vacío
        cursor.execute("""
            SELECT Id, NombreCompleto, TipoDocumento, NroDocumento, Domicilio
            FROM (
                SELECT Id, NombreCompleto, TipoDocumento, NroDocumento, Domicilio,
                    ROW_NUMBER() OVER (
                        PARTITION BY NroDocumento
                        ORDER BY CASE WHEN Domicilio IS NOT NULL AND Domicilio != '' THEN 0 ELSE 1 END, Id
                    ) AS rn
                FROM Cliente
                WHERE Estado = 1 AND NroDocumento LIKE %s
            ) AS sub
            WHERE rn = 1
            ORDER BY Id
        """, [query + '%'])
        rows = cursor.fetchall()
    
    clientes = []
    for row in rows:
        clientes.append({
            'id': row[0],
            'nombre': row[1],
            'tipo_documento': row[2],
            'nro_documento': row[3],
            'domicilio': row[4] or '',
        })
    
    return JsonResponse({'clientes': clientes})


@login_required
@require_http_methods(["POST"])
def api_previsualizar_comprobante(request):
    """
    API que genera y emite una Boleta/Factura real usando Nubefact.
    Usa los datos de sedeclonada para ruta, token, series y correlativos.
    Guarda el comprobante en comprobanteclonada y su detalle en comprobantedetclonada.
    Auto-incrementa el correlativo en sedeclonada.
    
    NOTA: Usa SQL directo (no ORM) para sedeclonada/comprobanteclonada/comprobantedetclonada
    porque el driver ODBC en Linux no soporta datetimeoffset (tipo SQL -155).
    """
    import json
    import requests
    from datetime import datetime, timedelta

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    ticket_id = data.get('ticket_id')
    tipo = data.get('tipo', 'boleta')  # 'boleta' o 'factura'
    cliente_documento = data.get('documento', '').strip()
    cliente_nombre = data.get('nombre', '').strip()
    cliente_direccion = data.get('direccion', '').strip()
    sin_dni = data.get('sin_dni', False)

    if not ticket_id:
        return JsonResponse({'error': 'ticket_id es requerido'}, status=400)

    sede_id = request.session.get('sede_id')
    if not sede_id:
        return JsonResponse({'error': 'Sin sede seleccionada'}, status=400)

    # Obtener datos de sedeclonada usando SQL directo (evita datetimeoffset del ORM)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                id_sede_original, nombre, valor_igv, identificador,
                serie_factura, serie_boleta, correlativo_boleta, correlativo_factura,
                serie_nota_credito_boleta, correlativo_nota_credito_boleta,
                serie_nota_credito_factura, correlativo_nota_credito_factura,
                ruta, token, serie_ticket, correlativo_ticket, nombre_impresora,
                created, modified, user_created, user_modified, estado, fecha_clonacion
            FROM sedeclonada
            WHERE id_sede_original = %s
        """, [sede_id])
        sede_row = cursor.fetchone()
    
    if not sede_row:
        return JsonResponse({'error': 'Sede no encontrada en sedeclonada. Ejecute: python manage.py clonar_tablas --solo-sedes'}, status=400)

    # Mapear columnas por índice
    nubefact_ruta = (sede_row[12] or '').strip()   # ruta
    nubefact_token = (sede_row[13] or '').strip()   # token
    valor_igv = float(sede_row[2]) if sede_row[2] else 10.5  # valor_igv
    serie_boleta = sede_row[5] or ''   # serie_boleta
    serie_factura = sede_row[4] or ''  # serie_factura
    correlativo_boleta = int(sede_row[6]) if sede_row[6] else 0   # correlativo_boleta
    correlativo_factura = int(sede_row[7]) if sede_row[7] else 0  # correlativo_factura

    if not nubefact_ruta:
        return JsonResponse({'error': 'La sede no tiene configurada la ruta de Nubefact en sedeclonada'}, status=400)
    if not nubefact_token:
        return JsonResponse({'error': 'La sede no tiene configurado el token de Nubefact en sedeclonada'}, status=400)

    # Obtener serie y auto-incrementar correlativo desde sedeclonada (SQL directo)
    if tipo == 'boleta':
        serie = serie_boleta
        nuevo_correlativo = correlativo_boleta + 1
        with connection.cursor() as cursor:
            cursor.execute("UPDATE sedeclonada SET correlativo_boleta = %s WHERE id_sede_original = %s", [nuevo_correlativo, sede_id])
        correlativo = nuevo_correlativo
    else:
        serie = serie_factura
        nuevo_correlativo = correlativo_factura + 1
        with connection.cursor() as cursor:
            cursor.execute("UPDATE sedeclonada SET correlativo_factura = %s WHERE id_sede_original = %s", [nuevo_correlativo, sede_id])
        correlativo = nuevo_correlativo
    
    # Obtener detalle del ticket
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                td.Id,
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
        det_rows = cursor.fetchall()
    
    if not det_rows:
        return JsonResponse({'error': 'El ticket no tiene productos'}, status=400)
    
    # Obtener datos del ticket (fecha, etc.)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT Created FROM ticket WHERE Id = %s
        """, [ticket_id])
        ticket_row = cursor.fetchone()
    
    fecha_emision = ticket_row[0] if ticket_row else datetime.now()
    if isinstance(fecha_emision, str):
        from datetime import datetime as dt
        fecha_emision = dt.strptime(fecha_emision, '%Y-%m-%d %H:%M:%S')
    
    # Determinar tipo de comprobante Nubefact
    # 1 = Factura, 2 = Boleta
    tipo_comprobante = 2 if tipo == 'boleta' else 1
    
    # Tipo de documento del cliente
    # 1: DNI, 6: RUC, 0: Sin Documento / Doc. identidad de país de origen
    if sin_dni:
        cliente_tipo_doc = 0  # Sin Documento (Consumidor Final)
    elif len(cliente_documento) == 8:
        cliente_tipo_doc = 1  # DNI
    elif len(cliente_documento) == 11:
        cliente_tipo_doc = 6  # RUC
    else:
        cliente_tipo_doc = -1  # Otros
    
    # Calcular totales
    total_general = sum(float(row[4]) for row in det_rows)
    igv_rate = valor_igv / 100.0
    subtotal = total_general / (1 + igv_rate)
    total_igv = total_general - subtotal
    
    # Construir items para Nubefact
    items = []
    for i, row in enumerate(det_rows):
        cant = float(row[2]) if row[2] else 1
        pu = float(row[3]) if row[3] else 0
        total_item = float(row[4]) if row[4] else 0
        valor_unitario = pu / (1 + igv_rate)
        subtotal_item = total_item / (1 + igv_rate)
        igv_item = total_item - subtotal_item
        
        items.append({
            "unidad_de_medida": "NIU",
            "codigo": str(i + 1).zfill(3),
            "descripcion": row[1],
            "cantidad": round(cant, 2),
            "valor_unitario": round(valor_unitario, 2),
            "precio_unitario": round(pu, 2),
            "descuento": "",
            "subtotal": round(subtotal_item, 2),
            "tipo_de_igv": 1,
            "igv": round(igv_item, 2),
            "total": round(total_item, 2),
            "anticipo_regularizacion": False,
            "anticipo_comprobante_serie": "",
            "anticipo_comprobante_numero": ""
        })
    
    # Construir JSON para Nubefact
    invoice = {
        "operacion": "generar_comprobante",
        "tipo_de_comprobante": tipo_comprobante,
        "serie": serie,
        "numero": str(correlativo),
        "sunat_transaction": 1,
        "cliente_tipo_de_documento": str(cliente_tipo_doc),
        "cliente_numero_de_documento": cliente_documento,
        "cliente_denominacion": cliente_nombre,
        "cliente_direccion": cliente_direccion,
        "cliente_email": "",
        "cliente_email_1": "",
        "cliente_email_2": "",
        "fecha_de_emision": fecha_emision.strftime('%d-%m-%Y'),
        "fecha_de_vencimiento": "",
        "moneda": 1,
        "tipo_de_cambio": "",
        "porcentaje_de_igv": valor_igv,
        "descuento_global": "",
        "total_descuento": "",
        "total_anticipo": "",
        "total_gravada": round(subtotal, 2),
        "total_inafecta": "",
        "total_exonerada": "",
        "total_igv": round(total_igv, 2),
        "total_gratuita": "",
        "total_otros_cargos": "",
        "total": round(total_general, 2),
        "percepcion_tipo": "",
        "percepcion_base_imponible": "",
        "total_percepcion": "",
        "total_incluido_percepcion": "",
        "retencion_tipo": "",
        "retencion_base_imponible": "",
        "total_retencion": "",
        "total_impuestos_bolsas": "",
        "detraccion": False,
        "observaciones": "",
        "documento_que_se_modifica_tipo": "",
        "documento_que_se_modifica_serie": "",
        "documento_que_se_modifica_numero": "",
        "tipo_de_nota_de_credito": "",
        "tipo_de_nota_de_debito": "",
        "enviar_automaticamente_a_la_sunat": True,
        "enviar_automaticamente_al_cliente": False,
        "condiciones_de_pago": "",
        "medio_de_pago": "",
        "placa_vehiculo": "",
        "orden_compra_servicio": "",
        "formato_de_pdf": "TICKET",
        "items": items
    }
    
    # Enviar a Nubefact
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token token={nubefact_token}"
        }
        
        response = requests.post(
            nubefact_ruta,
            json=invoice,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            try:
                detalle_json = response.json()
            except:
                detalle_json = response.text
            return JsonResponse({
                'success': False,
                'error': f'Nubefact error: {response.status_code}',
                'detalle': detalle_json
            })
        
        nubefact_resp = response.json()
        
        # Verificar si hay errores
        if nubefact_resp.get('errors'):
            return JsonResponse({
                'error': 'Nubefact devolvió errores',
                'detalle': nubefact_resp['errors']
            }, status=400)
        
        # === GUARDAR EN comprobanteclonada y comprobantedetclonada (SQL directo) ===
        from django.db import transaction as db_transaction
        
        with db_transaction.atomic():
            # Generar un ID negativo único para comprobantes emitidos desde Nubefact
            with connection.cursor() as cursor:
                cursor.execute("SELECT MIN(id_comprobante_original) FROM comprobanteclonada")
                min_id_row = cursor.fetchone()
                min_id = min_id_row[0] if min_id_row and min_id_row[0] is not None else 0
            next_negative_id = min(min_id - 1, -1)
            
            # Insertar en comprobanteclonada (SQL directo)
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fecha_emision_str = fecha_emision.strftime('%Y-%m-%d %H:%M:%S')
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO comprobanteclonada
                        (id_comprobante_original, id_cliente, id_sede, turno, referenciaticket,
                         serie, correlativo, tipocomprobante, total, enviosunat, identificador,
                         usercreated, created, estado, enviado_sunat, respuesta_sunat, fecha_envio_sunat)
                    OUTPUT INSERTED.id
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    next_negative_id, 0, sede_id, request.session.get('turno', ''),
                    str(ticket_id), serie, correlativo,
                    'BOLETA' if tipo == 'boleta' else 'FACTURA',
                    round(total_general, 2),
                    1 if nubefact_resp.get('aceptada_por_sunat', False) else 0,
                    0, request.session.get('usuario_login', ''),
                    fecha_emision_str, 1, 1,
                    json.dumps(nubefact_resp), now_str
                ])
                comprobante_clonado_id = cursor.fetchone()[0]
            
            # Generar ID negativo único para detalles
            with connection.cursor() as cursor:
                cursor.execute("SELECT MIN(id_detalle_original) FROM comprobantedetclonada")
                min_det_row = cursor.fetchone()
                min_det_id = min_det_row[0] if min_det_row and min_det_row[0] is not None else 0
            next_det_negative_id = min(min_det_id - 1, -1)
            
            # Insertar detalles en comprobantedetclonada (SQL directo)
            for i, row in enumerate(det_rows):
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO comprobantedetclonada
                            (id_detalle_original, id_comprobante_clonado, id_producto, descripcion,
                             tipoventa, codproductosunat, cantidad, preciounitario, total)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        next_det_negative_id - i,
                        comprobante_clonado_id,
                        int(row[0]) if row[0] else 0,
                        row[1], '', '',
                        float(row[2]) if row[2] else 1,
                        float(row[3]) if row[3] else 0,
                        float(row[4]) if row[4] else 0,
                    ])
        
        # Devolver datos al frontend
        return JsonResponse({
            'success': True,
            'tipo': nubefact_resp.get('tipo'),
            'serie': nubefact_resp.get('serie'),
            'numero': nubefact_resp.get('numero'),
            'url': nubefact_resp.get('url', ''),
            'enlace_del_pdf': nubefact_resp.get('enlace_del_pdf', ''),
            'aceptada_por_sunat': nubefact_resp.get('aceptada_por_sunat', False),
            'pdf_zip_base64': nubefact_resp.get('pdf_zip_base64', ''),
            'xml_zip_base64': nubefact_resp.get('xml_zip_base64', ''),
            'cdr_zip_base64': nubefact_resp.get('cdr_zip_base64', ''),
            'cadena_para_codigo_qr': nubefact_resp.get('cadena_para_codigo_qr', ''),
            'codigo_hash': nubefact_resp.get('codigo_hash', ''),
            'sunat_description': nubefact_resp.get('sunat_description', ''),
            'comprobante_id': comprobante_clonado_id,
        })
        
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'Tiempo de espera agotado al conectar con Nubefact'}, status=504)
    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': 'No se pudo conectar con Nubefact. Verifique su conexión a internet.'}, status=502)
    except Exception as e:
        return JsonResponse({'error': f'Error al generar comprobante: {str(e)}'}, status=500)


@login_required
@require_http_methods(["GET"])
def api_proxy_pdf(request):
    """
    Proxy endpoint para descargar el PDF de Nubefact y servirlo desde el backend.
    Esto evita problemas de CORS/mixed content que ocurren al cargar el PDF
    directamente desde el enlace de Nubefact en un iframe.
    """
    import requests as req_lib
    
    pdf_url = request.GET.get('url', '')
    if not pdf_url:
        return JsonResponse({'error': 'URL del PDF es requerida'}, status=400)
    
    try:
        pdf_resp = req_lib.get(pdf_url, timeout=30)
        pdf_resp.raise_for_status()
        
        # Devolver el PDF como respuesta binaria
        from django.http import HttpResponse
        response = HttpResponse(pdf_resp.content, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="comprobante.pdf"'
        # Permitir que sea cargado en iframe del mismo origen
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response
    except req_lib.exceptions.RequestException as e:
        return JsonResponse({'error': f'Error al descargar PDF: {str(e)}'}, status=502)


@login_required
@require_http_methods(["GET"])
def api_impresora_info(request):
    """
    API que devuelve el nombre de la impresora configurada en sedeclonada
    para la sede actual.
    Usa SQL directo para evitar problemas con datetimeoffset del ORM en Linux.
    """
    sede_id = request.session.get('sede_id')
    if not sede_id:
        return JsonResponse({'error': 'Sin sede seleccionada'}, status=400)
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT nombre_impresora FROM sedeclonada WHERE id_sede_original = %s", [sede_id])
        row = cursor.fetchone()
    
    if not row:
        return JsonResponse({'error': 'Sede no encontrada en sedeclonada'}, status=400)
    
    nombre_impresora = (row[0] or '').strip()
    return JsonResponse({
        'success': True,
        'nombre_impresora': nombre_impresora,
    })


@login_required
@require_http_methods(["POST"])
def api_imprimir_comprobante(request):
    """
    API que imprime un comprobante usando la impresora configurada en sedeclonada.
    Envía el PDF a la impresora usando QZ Tray (socket) o impresión nativa de Windows.
    """
    import json
    import tempfile
    import os
    import subprocess
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    
    pdf_url = data.get('pdf_url', '')
    comprobante_id = data.get('comprobante_id')
    
    if not pdf_url and not comprobante_id:
        return JsonResponse({'error': 'Se requiere pdf_url o comprobante_id'}, status=400)
    
    sede_id = request.session.get('sede_id')
    if not sede_id:
        return JsonResponse({'error': 'Sin sede seleccionada'}, status=400)
    
    # SQL directo para evitar datetimeoffset del ORM en Linux
    with connection.cursor() as cursor:
        cursor.execute("SELECT nombre_impresora FROM sedeclonada WHERE id_sede_original = %s", [sede_id])
        imp_row = cursor.fetchone()
    
    if not imp_row:
        return JsonResponse({'error': 'Sede no encontrada en sedeclonada'}, status=400)
    
    nombre_impresora = (imp_row[0] or '').strip()
    
    if not nombre_impresora:
        return JsonResponse({'error': 'La sede no tiene impresora configurada en sedeclonada'}, status=400)
    
    # Descargar el PDF
    import requests as req_lib
    try:
        pdf_resp = req_lib.get(pdf_url, timeout=30)
        pdf_resp.raise_for_status()
    except req_lib.exceptions.RequestException as e:
        return JsonResponse({'error': f'Error al descargar PDF para imprimir: {str(e)}'}, status=502)
    
    # Guardar PDF temporal y enviar a impresora
    try:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(pdf_resp.content)
            tmp_path = tmp.name
        
        # Buscar SumatraPDF (mejor para imprimir PDFs en ticketeras de rollo)
        sumatra_paths = [
            r'C:\Program Files\SumatraPDF\SumatraPDF.exe',
            r'C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe',
        ]
        sumatra_exe = None
        for sp in sumatra_paths:
            if os.path.exists(sp):
                sumatra_exe = sp
                break
        
        if sumatra_exe:
            # SumatraPDF respeta la configuración de papel de la impresora
            # Si la impresora térmica está configurada con papel de 80mm,
            # SumatraPDF escalará el PDF automáticamente a ese tamaño
            subprocess.run(
                [sumatra_exe, '-print-to', nombre_impresora, '-exit-on-print', tmp_path],
                capture_output=True,
                timeout=60
            )
        else:
            # Intentar con PowerShell usando Start-Process con print verb
            # Esto usa la configuración predeterminada de la impresora
            ps_print = f'''
            Start-Process -FilePath "{tmp_path}" -Verb Print -PassThru |
            ForEach-Object {{ $_ | Wait-Process -Timeout 60 }}
            '''
            try:
                subprocess.run(
                    ['powershell', '-Command', ps_print],
                    capture_output=True,
                    timeout=60
                )
            except Exception:
                # Último recurso: comando nativo de Windows
                subprocess.run(
                    ['cmd.exe', '/c', 'start', '/min', '/wait', tmp_path, '/print', nombre_impresora],
                    capture_output=True,
                    timeout=60
                )
        
        # Limpiar archivo temporal
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Comprobante enviado a la impresora: {nombre_impresora}',
            'nombre_impresora': nombre_impresora,
        })
        
    except subprocess.TimeoutExpired:
        return JsonResponse({'error': 'Tiempo de espera agotado al imprimir'}, status=504)
    except Exception as e:
        return JsonResponse({'error': f'Error al imprimir: {str(e)}'}, status=500)