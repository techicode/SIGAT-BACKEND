from django.db import models
from assets.models import Asset


class Vulnerability(models.Model):
    """
    DEPRECATED: This model is being replaced by SoftwareVulnerability.
    Kept for backwards compatibility.
    """
    cve_id = models.CharField(max_length=50, unique=True, verbose_name="ID de CVE")
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=20)
    link_to_details = models.URLField(max_length=512, blank=True)

    def __str__(self):
        return self.cve_id


class SoftwareCatalog(models.Model):
    name = models.CharField(max_length=255)
    developer = models.CharField(max_length=255, blank=True)

    vulnerabilities = models.ManyToManyField(
        Vulnerability, blank=True, related_name="software"
    )

    class Meta:
        unique_together = ("name", "developer")
        verbose_name = "Software catalog"
        verbose_name_plural = "software catalogs"

    def __str__(self):
        return f"{self.name} ({self.developer})"


class License(models.Model):
    software = models.ForeignKey(
        SoftwareCatalog, on_delete=models.CASCADE, related_name="licenses"
    )
    license_key = models.TextField(blank=True, verbose_name="Clave de Licencia")
    purchase_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Licencia para {self.software.name} (Qty: {self.quantity})"


class InstalledSoftware(models.Model):
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="installed_software"
    )
    software = models.ForeignKey(
        SoftwareCatalog, on_delete=models.PROTECT, related_name="installations"
    )
    version = models.CharField(max_length=50, blank=True)
    install_date = models.DateField(null=True, blank=True)

    license = models.ForeignKey(
        License,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="installations",
    )

    class Meta:
        unique_together = ("asset", "software")
        verbose_name = "Installed Software"
        verbose_name_plural = "Installed Softwares"

    def __str__(self):
        return f"{self.software.name} en {self.asset.inventory_code}"


class SoftwareVulnerability(models.Model):
    """
    Tracks vulnerabilities for specific software with version information.
    This allows detecting if installed software versions are vulnerable.
    """
    class SeverityChoices(models.TextChoices):
        CRITICAL = "CRITICAL", "Crítica"
        HIGH = "HIGH", "Alta"
        MEDIUM = "MEDIUM", "Media"
        LOW = "LOW", "Baja"

    software = models.ForeignKey(
        SoftwareCatalog,
        on_delete=models.CASCADE,
        related_name="software_vulnerabilities"
    )
    cve_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="ID de CVE",
        help_text="Ej: CVE-2024-1234"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Título de la Vulnerabilidad"
    )
    description = models.TextField(blank=True)
    severity = models.CharField(
        max_length=20,
        choices=SeverityChoices.choices,
        default=SeverityChoices.MEDIUM
    )

    # Version information
    affected_versions = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Versiones Afectadas",
        help_text="Ej: < 2.5.0, >= 1.0 < 2.0"
    )
    safe_version_from = models.CharField(
        max_length=50,
        verbose_name="Versión Segura Desde",
        help_text="Primera versión sin esta vulnerabilidad. Ej: 2.5.0"
    )

    link_to_details = models.URLField(max_length=512, blank=True)
    discovered_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vulnerabilidad de Software"
        verbose_name_plural = "Vulnerabilidades de Software"
        ordering = ['-severity', '-created_at']

    def __str__(self):
        cve = f"{self.cve_id} - " if self.cve_id else ""
        return f"{cve}{self.software.name} < {self.safe_version_from}"
