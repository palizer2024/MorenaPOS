from django.urls import path
from . import views

app_name = 'core_api'

urlpatterns = [
    path('ticket-detalle/<int:ticket_id>/', views.api_ticket_detalle, name='ticket_detalle'),
    path('consultar-documento/<str:numero>/', views.api_consultar_documento, name='consultar_documento'),
    path('buscar-cliente/<str:query>/', views.api_buscar_cliente, name='buscar_cliente'),
    path('previsualizar-comprobante/', views.api_previsualizar_comprobante, name='previsualizar_comprobante'),
    path('proxy-pdf/', views.api_proxy_pdf, name='proxy_pdf'),
]