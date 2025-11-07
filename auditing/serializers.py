from rest_framework import serializers
from .models import AssetCheckin
from assets.models import Asset
from users.models import Employee

from users.serializers import EmployeeBasicSerializer
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
