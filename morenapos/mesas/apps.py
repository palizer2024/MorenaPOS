from django.apps import AppConfig


class MesasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mesas'
    verbose_name = 'Gestión de Mesas'
    
    def ready(self):
        # Importar señales y configuración inicial
        import mesas.signals  # noqa