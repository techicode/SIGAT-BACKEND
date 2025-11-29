from rest_framework import serializers
from .models import Asset, ComputerDetail, StorageDevice, GraphicsCard
from users.serializers import DepartmentBasicSerializer, EmployeeBasicSerializer
from users.models import Department, Employee


class InstalledSoftwareBasicSerializer(serializers.Serializer):
    """Basic serializer for installed software on an asset."""
    id = serializers.IntegerField()
    software_name = serializers.CharField(source='software.name')
    software_developer = serializers.CharField(source='software.developer')
    version = serializers.CharField()
    install_date = serializers.DateField()


class StorageDeviceSerializer(serializers.ModelSerializer):
    """Serializer for storage devices (disks)."""
    class Meta:
        model = StorageDevice
        fields = ['id', 'model', 'serial_number', 'capacity_gb', 'free_space_gb']


class GraphicsCardSerializer(serializers.ModelSerializer):
    """Serializer for graphics cards (GPUs)."""
    class Meta:
        model = GraphicsCard
        fields = ['id', 'model_name']


class ComputerDetailSerializer(serializers.ModelSerializer):
    """Serializer for computer hardware details."""
    class Meta:
        model = ComputerDetail
        fields = [
            'unique_identifier',
            'os_name',
            'os_version',
            'os_arch',
            'cpu_model',
            'ram_gb',
            'motherboard_manufacturer',
            'motherboard_model',
            'last_updated_by_agent',
        ]


class AssetListSerializer(serializers.ModelSerializer):

    department = DepartmentBasicSerializer(read_only=True)
    employee = EmployeeBasicSerializer(read_only=True)

    class Meta:
        model = Asset
        fields = [
            "inventory_code",
            "serial_number",
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

    # Hardware details (only for NOTEBOOK and DESKTOP)
    computerdetail = ComputerDetailSerializer(read_only=True)
    storage_devices = StorageDeviceSerializer(many=True, read_only=True)
    graphics_cards = GraphicsCardSerializer(many=True, read_only=True)

    # Installed software
    installed_software = InstalledSoftwareBasicSerializer(many=True, read_only=True)

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
