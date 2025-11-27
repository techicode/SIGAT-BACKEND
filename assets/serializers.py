from rest_framework import serializers
from .models import Asset
from users.serializers import DepartmentBasicSerializer, EmployeeBasicSerializer
from users.models import Department, Employee


class AssetListSerializer(serializers.ModelSerializer):

    department = DepartmentBasicSerializer(read_only=True)
    employee = EmployeeBasicSerializer(read_only=True)

    class Meta:
        model = Asset
        fields = [
            "inventory_code",
            "asset_type",
            "brand",
            "model",
            "status",
            "department",
            "employee",
        ]


class AssetDetailSerializer(serializers.ModelSerializer):

    department = DepartmentBasicSerializer(read_only=True)
    employee = EmployeeBasicSerializer(read_only=True)

    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source="department",
        write_only=True,
        allow_null=True,
        required=False,
    )
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        source="employee",
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Asset
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]
