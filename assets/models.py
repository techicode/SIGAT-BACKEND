from django.db import models
from users.models import Employee, Department  # Importamos desde la app 'users'


class Asset(models.Model):
    class AssetTypeChoices(models.TextChoices):
        NOTEBOOK = "NOTEBOOK", "Notebook"
        DESKTOP = "DESKTOP", "Desktop"
        MONITOR = "MONITOR", "Monitor"
        PRINTER = "PRINTER", "Impresora"
        OTHER = "OTHER", "Otro"

    class StatusChoices(models.TextChoices):
        IN_STORAGE = "BODEGA", "En Bodega"
        ASSIGNED = "ASIGNADO", "Asignado"
        IN_REPAIR = "REPARACION", "En Reparación"
        DISPOSED = "DE_BAJA", "De Baja"

    inventory_code = models.CharField(
        max_length=100, unique=True, verbose_name="Código de Inventario"
    )
    serial_number = models.CharField(
        max_length=100, unique=True, verbose_name="Número de Serie"
    )
    asset_type = models.CharField(
        max_length=50, choices=AssetTypeChoices.choices, verbose_name="Tipo de Activo"
    )
    status = models.CharField(
        max_length=50,
        choices=StatusChoices.choices,
        default=StatusChoices.IN_STORAGE,
        verbose_name="Estado",
    )
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    acquisition_date = models.DateField(
        null=True, blank=True, verbose_name="Fecha de Adquisición"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
        verbose_name="Empleado Asignado",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
        verbose_name="Departamento (Centro de Costo)",
    )

    def __str__(self):
        return f"{self.inventory_code} ({self.get_asset_type_display()})"


class ComputerDetail(models.Model):
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    unique_identifier = models.CharField(
        max_length=255, blank=True, verbose_name="UUID de BIOS/UEFI"
    )
    os_name = models.CharField(max_length=100, blank=True, verbose_name="Nombre SO")
    os_version = models.CharField(max_length=50, blank=True, verbose_name="Versión SO")
    os_arch = models.CharField(
        max_length=10, blank=True, verbose_name="Arquitectura SO"
    )
    cpu_model = models.CharField(
        max_length=255, blank=True, verbose_name="Modelo de CPU"
    )
    ram_gb = models.FloatField(null=True, blank=True, verbose_name="RAM (GB)")
    motherboard_manufacturer = models.CharField(
        max_length=100, blank=True, verbose_name="Fabricante Placa Base"
    )
    motherboard_model = models.CharField(
        max_length=100, blank=True, verbose_name="Modelo Placa Base"
    )
    last_updated_by_agent = models.DateTimeField(
        null=True, blank=True, verbose_name="Última Actualización por Agente"
    )

    def __str__(self):
        return f"Detalles de {self.asset.inventory_code}"


class StorageDevice(models.Model):
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="storage_devices"
    )
    model = models.CharField(max_length=255, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    capacity_gb = models.FloatField(
        null=True, blank=True, verbose_name="Capacidad (GB)"
    )
    free_space_gb = models.FloatField(
        null=True, blank=True, verbose_name="Espacio Libre (GB)"
    )

    def __str__(self):
        return f"Disco {self.model} para {self.asset.inventory_code}"


class GraphicsCard(models.Model):
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="graphics_cards"
    )
    model_name = models.CharField(max_length=255)

    def __str__(self):
        return f"GPU {self.model_name} para {self.asset.inventory_code}"
