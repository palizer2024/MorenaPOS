from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import connection, transaction
from .models import ComprobanteClonado, ComprobanteDetClonado
from .forms import InvoceForm


# Create your views here.

def emitir_factura(request):
    if request.method == 'POST':
        form = InvoceForm(request.POST)
        if form.is_valid():
            cliente_id = form.cleaned_data['cliente_id']
            sede_id = form.cleaned_data['sede_id']
            serie = form.cleaned_data['serie']

            # Obtener la sede usando SQL directo para evitar datetimeoffset (ODBC -155)
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, correlativo_boleta, correlativo_factura, "
                    "correlativo_nota_credito_boleta, correlativo_nota_credito_factura "
                    "FROM sedeclonada WHERE id = %s",
                    [sede_id]
                )
                sede_row = cursor.fetchone()

            if not sede_row:
                form.add_error(None, 'Sede no encontrada.')
                return render(request, 'facturacion/emision_factura.html', {'form': form})

            (sede_pk, corr_boleta, corr_factura,
             corr_nc_boleta, corr_nc_factura) = sede_row

            # Calcular próximo correlativo y actualizar en BD
            if serie == 'FA':
                nuevo_correlativo = corr_factura + 1
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE sedeclonada SET correlativo_factura = %s WHERE id = %s",
                        [nuevo_correlativo, sede_id]
                    )
            elif serie == 'BO':
                nuevo_correlativo = corr_boleta + 1
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE sedeclonada SET correlativo_boleta = %s WHERE id = %s",
                        [nuevo_correlativo, sede_id]
                    )
            elif serie == 'NC-BO':
                nuevo_correlativo = corr_nc_boleta + 1
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE sedeclonada SET correlativo_nota_credito_boleta = %s WHERE id = %s",
                        [nuevo_correlativo, sede_id]
                    )
            elif serie == 'NC-FA':
                nuevo_correlativo = corr_nc_factura + 1
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE sedeclonada SET correlativo_nota_credito_factura = %s WHERE id = %s",
                        [nuevo_correlativo, sede_id]
                    )
            else:
                nuevo_correlativo = 0

            # Crear comprobante clonado
            with transaction.atomic():
                comprobante = ComprobanteClonado.objects.create(
                    id_cliente=cliente_id,
                    id_sede=sede_id,
                    serie=serie,
                    correlativo=nuevo_correlativo,
                    tipocomprobante='FACTURA',
                    total=0,
                    estado=True
                )

                # Crear detalles de ejemplo (en producción usar el JSON de productos)
                # ComprobanteDetClonado.objects.create(...)

            return redirect('facturacion:factura_exitosa', pk=comprobante.id)
    else:
        form = InvoceForm()
    return render(request, 'facturacion/emision_factura.html', {'form': form})


def factura_exitosa(request, pk):
    return render(request, 'facturacion/factura_exitosa.html', {'comprobante_id': pk})