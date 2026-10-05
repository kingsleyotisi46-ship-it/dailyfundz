from django.apps import AppConfig


class SocialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'social'
    
    def ready(self):
        """Import signals when Django starts"""
        import social.signals  # noqa
