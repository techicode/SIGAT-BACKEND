from rest_framework import serializers
from .models import AssetCheckin, ComplianceWarning, AuditLog, HardwareObsolescenceRules
from assets.models import Asset
from users.models import Employee, CustomUser

from users.serializers import EmployeeBasicSerializer, SystemUserBasicSerializer
from software.serializers import AssetBasicSerializer


class AssetCheckinSerializer(serializers.ModelSerializer):
    asset = AssetBasicSerializer(read_only=True)
    employee = EmployeeBasicSerializer(read_only=True)

    asset_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(), source="asset", write_only=True
    )
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source="employee", write_only=True
    )

    class Meta:
        model = AssetCheckin
        fields = [
            "id",
            "asset",
            "asset_id",
            "employee",
            "employee_id",
            "unique_token",
            "status",
            "requested_at",
            "completed_at",
            "checkin_date",
            "physical_state",
            "performance_satisfaction",
            "notes",
        ]
        read_only_fields = ["unique_token", "requested_at"]


class AssetCheckinPublicSerializer(serializers.ModelSerializer):
    """
    Serializer for public checkin form (via unique token, no auth required)
    Only shows necessary asset/employee information
    """
    asset = AssetBasicSerializer(read_only=True)
    employee = EmployeeBasicSerializer(read_only=True)

    class Meta:
        model = AssetCheckin
        fields = [
            "id",
            "asset",
            "employee",
            "status",
            "requested_at",
            "physical_state",
            "performance_satisfaction",
            "notes",
        ]
        read_only_fields = ["id", "asset", "employee", "status", "requested_at"]


class ComplianceWarningSerializer(serializers.ModelSerializer):

    asset = AssetBasicSerializer(read_only=True)
    resolved_by = SystemUserBasicSerializer(read_only=True)

    asset_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(), source="asset", write_only=True
    )

    resolved_by_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source="resolved_by",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ComplianceWarning
        fields = [
            "id",
            "asset",
            "asset_id",
            "detection_date",
            "category",
            "description",
            "evidence",
            "status",
            "resolved_by",
            "resolved_by_id",
            "resolution_notes",
        ]
        read_only_fields = ["detection_date"]


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog model.
    Shows complete audit trail with user information.
    """
    system_user = SystemUserBasicSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "timestamp",
            "system_user",
            "action",
            "target_table",
            "target_id",
            "details",
        ]
        read_only_fields = ["timestamp"]


class HardwareObsolescenceRulesSerializer(serializers.ModelSerializer):
    """
    Serializer for hardware obsolescence rules configuration.
    """
    updated_by = SystemUserBasicSerializer(read_only=True)

    class Meta:
        model = HardwareObsolescenceRules
        fields = [
            "id",
            "windows_min_version",
            "ram_min_gb",
            "disk_min_free_percent",
            "enabled",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = ["updated_at", "updated_by"]


class ObsoleteAssetSerializer(serializers.Serializer):
    """
    Serializer for obsolete asset information.
    This is not a model serializer - data comes from hardware_checker.
    """
    inventory_code = serializers.CharField()
    asset_type = serializers.CharField()
    brand = serializers.CharField()
    model = serializers.CharField()
    department = serializers.CharField(allow_null=True)
    employee = serializers.CharField(allow_null=True)
    reasons = serializers.ListField(child=serializers.CharField())
    details = serializers.JSONField()


# ==================== AGENT HARDWARE REPORT SERIALIZERS ====================

class AgentOSSerializer(serializers.Serializer):
    """Serializer for operating system information from agent"""
    nombre = serializers.CharField(max_length=255)
    version = serializers.CharField(max_length=100)
    arquitectura = serializers.CharField(max_length=50)


class AgentMotherboardSerializer(serializers.Serializer):
    """Serializer for motherboard information from agent"""
    fabricante = serializers.CharField(max_length=255)
    modelo = serializers.CharField(max_length=255)


class AgentStorageDeviceSerializer(serializers.Serializer):
    """Serializer for storage device information from agent"""
    modelo = serializers.CharField(max_length=255)
    numero_serie = serializers.CharField(max_length=255)
    capacidad_gb = serializers.FloatField()
    espacio_libre_gb = serializers.FloatField()


class AgentSoftwareSerializer(serializers.Serializer):
    """Serializer for installed software information from agent"""
    nombre = serializers.CharField(max_length=255)
    desarrollador = serializers.CharField(max_length=255, required=False, allow_blank=True)
    version = serializers.CharField(max_length=100, required=False, allow_blank=True)


class AgentSuspiciousSoftwareSerializer(serializers.Serializer):
    """Serializer for suspicious/illegal software detected by agent"""
    nombre = serializers.CharField(max_length=255, help_text="Software name")
    ruta_instalacion = serializers.CharField(max_length=500, help_text="Installation path")
    razon_sospecha = serializers.CharField(
        max_length=500,
        help_text="Reason for suspicion (e.g., 'crack', 'keygen', 'no license')"
    )
    desarrollador = serializers.CharField(max_length=255, required=False, allow_blank=True)
    version = serializers.CharField(max_length=100, required=False, allow_blank=True)
    evidencia = serializers.JSONField(
        required=False,
        help_text="Additional evidence (files found, registry keys, etc.)"
    )


class AgentHardwareSerializer(serializers.Serializer):
    """Serializer for hardware information from agent"""
    identificador_unico = serializers.CharField(max_length=255, help_text="BIOS/UEFI UUID")
    cpu = serializers.CharField(max_length=255)
    memoria_ram_gb = serializers.FloatField()
    placa_base = AgentMotherboardSerializer()
    tipo_chassis = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Chassis type from Win32_SystemEnclosure (8-14=Laptop, 3-7=Desktop)"
    )
    almacenamiento = serializers.ListField(
        child=AgentStorageDeviceSerializer(),
        allow_empty=True
    )
    gpus = serializers.ListField(
        child=serializers.CharField(max_length=255),
        allow_empty=True
    )


class AgentHardwareReportSerializer(serializers.Serializer):
    """
    Main serializer for hardware reports sent by the SIGAT agent.

    Expected payload structure:
    {
        "sistema_operativo": {...},
        "hardware": {...},
        "software_instalado": [...],      # Optional
        "software_sospechoso": [...]      # Optional but IMPORTANT
    }
    """
    sistema_operativo = AgentOSSerializer()
    hardware = AgentHardwareSerializer()
    software_instalado = serializers.ListField(
        child=AgentSoftwareSerializer(),
        required=False,
        allow_empty=True
    )
    software_sospechoso = serializers.ListField(
        child=AgentSuspiciousSoftwareSerializer(),
        required=False,
        allow_empty=True,
        help_text="List of suspicious/illegal software detected (cracks, keygens, pirated software)"
    )


class AgentReportResponseSerializer(serializers.Serializer):
    """Serializer for agent report API response"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    asset_created = serializers.BooleanField()
    asset_id = serializers.IntegerField(required=False)
    inventory_code = serializers.CharField(required=False)
    warnings_generated = serializers.IntegerField()
    changes_detected = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
