from rest_framework import serializers
from .models import AssetCheckin, ComplianceWarning
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
