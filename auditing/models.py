from django.conf import settings
from django.db import models
from assets.models import Asset
from users.models import Employee


class AuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    system_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=50)
    target_table = models.CharField(max_length=100)
    target_id = models.PositiveIntegerField()
    details = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.timestamp} - {self.system_user.username} - {self.action}"


class AssetCheckin(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="checkins")
    employee = models.ForeignKey(
        Employee, on_delete=models.PROTECT, related_name="checkins"
    )
    checkin_date = models.DateTimeField(auto_now_add=True)
    physical_state = models.CharField(max_length=50)
    performance_satisfaction = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Check-in de {self.asset.inventory_code} por {self.employee}"


class ComplianceWarning(models.Model):
    class StatusChoices(models.TextChoices):
        NEW = "NUEVA", "Nueva"
        IN_REVIEW = "EN_REVISION", "En Revisión"
        RESOLVED = "RESUELTA", "Resuelta"
        FALSE_POSITIVE = "FALSO_POSITIVO", "Falso Positivo"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="warnings")
    detection_date = models.DateTimeField(auto_now_add=True)
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
