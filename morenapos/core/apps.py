from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Núcleo del Sistema'
    
    def ready(self):
        # Importar señales y configuración inicial
        import core.signals  # noqa