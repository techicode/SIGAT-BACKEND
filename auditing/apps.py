from django.apps import AppConfig


class AuditingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "auditing"

    def ready(self):
        """Import signals when the app is ready."""
        import auditing.signals  # noqa: F401
