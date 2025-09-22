from django.apps import AppConfig


class VerificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'verification'


class VerificationConfig(AppConfig):
    name = 'verification'

    def ready(self):
        import verification.signals