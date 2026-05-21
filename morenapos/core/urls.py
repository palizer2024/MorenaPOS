"""
URLs para la aplicación core.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('seleccionar-sede/', views.seleccionar_sede, name='seleccionar_sede'),
]