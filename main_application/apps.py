from django.apps import AppConfig


class MainApplicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main_application'

    def ready(self):
        """
        Import signals when the app is ready.
        This ensures all signal handlers are registered.
        """
        # Import signals to register them
        try:
            from . import middleware
            # The import alone is enough to register the signal handlers
        except ImportError:
            pass
