from django.db import models
from assets.models import Asset


class Vulnerability(models.Model):
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
        verbose_name = "Software en Catálogo"
        verbose_name_plural = "Software en Catálogo"

    def __str__(self):
        return f"{self.name} ({self.developer})"


class InstalledSoftware(models.Model):
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="installed_software"
    )
    software = models.ForeignKey(
        SoftwareCatalog, on_delete=models.PROTECT, related_name="installations"
    )
    version = models.CharField(max_length=50, blank=True)
    install_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("asset", "software")
        verbose_name = "Software Instalado"
        verbose_name_plural = "Software Instalado"

    def __str__(self):
        return f"{self.software.name} en {self.asset.inventory_code}"


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
