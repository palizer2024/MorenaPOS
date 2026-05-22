from django.urls import path
from . import views

urlpatterns = [
    path('emision/', views.emitir_factura, name='emision_factura'),  # Changed from 'emiti_factura' to 'emitir_factura'
    path('factura-exitosa/<int:pk>/', views.factura_exitosa, name='factura_exitosa'),
]