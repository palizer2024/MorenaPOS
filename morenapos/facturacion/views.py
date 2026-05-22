from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import ComprobanteClonado, ComprobanteDetClonado, SedeClonada
from .forms import InvoceForm
from django.db import transaction

# Create your views here.

def emitir_factura(request):
    if request.method == 'POST':
        form = InvoceForm(request.POST)
        if form.is_valid():
            cliente_id = form.cleaned_data['cliente_id']
            sede_id = form.cleaned_data['sede_id']
            serie = form.cleaned_data['serie']
            
            # Obtener la sede
            sede = SedeClonada.objects.get(id=sede_id)
            
            # Obtener el próximo correlativo
            correlativo = sede.get_next_correlativo(serie)
            
            # Crear comprobante clonado
            with transaction.atomic():
                comprobante = ComprobanteClonado.objects.create(
                    id_cliente=cliente_id,
                    id_sede=sede_id,
                    serie=serie,
                    correlativo=correlativo,
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