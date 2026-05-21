from django.urls import path
from . import views

app_name = 'core_api'

urlpatterns = [
    path('ticket-detalle/<int:ticket_id>/', views.api_ticket_detalle, name='ticket_detalle'),
]