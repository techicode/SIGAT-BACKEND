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
            "checkin_date",
            "physical_state",
            "performance_satisfaction",
            "notes",
        ]
        read_only_fields = ["checkin_date"]


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
