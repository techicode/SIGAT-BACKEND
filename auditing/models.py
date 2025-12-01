from django.conf import settings
from django.db import models
from django.utils import timezone
from assets.models import Asset
from users.models import Employee
import secrets


class AuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    system_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField(max_length=50)
    target_table = models.CharField(max_length=100)
    target_id = models.PositiveIntegerField()
    details = models.JSONField(null=True, blank=True)

    def __str__(self):
        username = self.system_user.username if self.system_user else "deleted_user"
        return f"{self.timestamp} - {username} - {self.action}"


class AssetCheckin(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "PENDIENTE", "Pendiente"
        COMPLETED = "COMPLETADO", "Completado"
        EXPIRED = "EXPIRADO", "Expirado"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="checkins")
    employee = models.ForeignKey(
        Employee, on_delete=models.PROTECT, related_name="checkins"
    )
    unique_token = models.CharField(max_length=64, unique=True, db_index=True, default='')
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    requested_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Original fields (completed by employee)
    checkin_date = models.DateTimeField(null=True, blank=True)
    physical_state = models.CharField(max_length=50, blank=True)
    performance_satisfaction = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Check-in de {self.asset.inventory_code} por {self.employee} - {self.get_status_display()}"

    @staticmethod
    def generate_unique_token():
        """Generate a cryptographically secure unique token"""
        return secrets.token_urlsafe(32)

    def save(self, *args, **kwargs):
        """Override save to generate token if not present"""
        if not self.unique_token:
            self.unique_token = self.generate_unique_token()
        super().save(*args, **kwargs)


class ComplianceWarning(models.Model):
    class StatusChoices(models.TextChoices):
        NEW = "NUEVA", "Nueva"
        IN_REVIEW = "EN_REVISION", "En Revisión"
        RESOLVED = "RESUELTA", "Resuelta"
        FALSE_POSITIVE = "FALSO_POSITIVO", "Falso Positivo"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="warnings")
    detection_date = models.DateTimeField(default=timezone.now)
    category = models.CharField(max_length=100)
    description = models.TextField()
    evidence = models.JSONField(
        null=True, blank=True, verbose_name="Evidencia (ej. rutas)"
    )
    status = models.CharField(
        max_length=50, choices=StatusChoices.choices, default=StatusChoices.NEW
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_warnings",
    )
    resolution_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Alerta de {self.category} en {self.asset.inventory_code}"


class HardwareObsolescenceRules(models.Model):
    """
    Singleton model to store hardware obsolescence rules.
    Defines thresholds for what is considered obsolete hardware.
    """
    # Windows versions (build numbers)
    windows_min_version = models.CharField(
        max_length=50,
        default="10.0.19041",  # Windows 10 20H1
        verbose_name="Versión mínima de Windows",
        help_text="Build number (ej: 10.0.19041 para Win10, 10.0.22000 para Win11)"
    )

    # RAM minimum (GB)
    ram_min_gb = models.FloatField(
        default=4.0,
        verbose_name="RAM mínima (GB)",
        help_text="Equipos con menos RAM se consideran obsoletos"
    )

    # Disk space minimum (percentage)
    disk_min_free_percent = models.FloatField(
        default=10.0,
        verbose_name="Espacio libre mínimo en disco (%)",
        help_text="Equipos con menos espacio disponible se consideran en riesgo"
    )

    # CPU generation/age rules could be added here
    # For now, we'll focus on the above three

    enabled = models.BooleanField(
        default=True,
        verbose_name="Reglas activas",
        help_text="Desactivar para pausar la detección de hardware obsoleto"
    )

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="obsolescence_rules_updates"
    )

    class Meta:
        verbose_name = "Reglas de Obsolescencia de Hardware"
        verbose_name_plural = "Reglas de Obsolescencia de Hardware"

    def __str__(self):
        return f"Reglas de Obsolescencia (actualizado: {self.updated_at})"

    @classmethod
    def get_rules(cls):
        """Get the singleton instance, creating it if it doesn't exist."""
        rules, created = cls.objects.get_or_create(pk=1)
        return rules
