from rest_framework import serializers
from .models import SoftwareCatalog, InstalledSoftware, License, SoftwareVulnerability
from assets.models import Asset


class AssetBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ["inventory_code", "brand", "model", "asset_type"]


class SoftwareCatalogBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoftwareCatalog
        fields = ["id", "name", "developer"]


class LicenseBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = ["id", "license_key", "expiration_date"]


class SoftwareCatalogSerializer(serializers.ModelSerializer):
    vulnerabilities = serializers.StringRelatedField(many=True, read_only=True)
    installed_count = serializers.IntegerField(read_only=True, default=0)
    license_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = SoftwareCatalog
        fields = ["id", "name", "developer", "vulnerabilities", "installed_count", "license_count"]


class InstalledSoftwareSerializer(serializers.ModelSerializer):
    asset = AssetBasicSerializer(read_only=True)
    software = SoftwareCatalogSerializer(read_only=True)
    license = LicenseBasicSerializer(read_only=True)

    asset_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(), source="asset", write_only=True
    )
    software_id = serializers.PrimaryKeyRelatedField(
        queryset=SoftwareCatalog.objects.all(), source="software", write_only=True
    )
    license_id = serializers.PrimaryKeyRelatedField(
        queryset=License.objects.all(),
        source="license",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = InstalledSoftware

        fields = [
            "id",
            "asset",
            "software",
            "license",
            "version",
            "install_date",
            "asset_id",
            "software_id",
            "license_id",
        ]


class LicenseSerializer(serializers.ModelSerializer):
    software = SoftwareCatalogBasicSerializer(read_only=True)
    license_key_display = serializers.SerializerMethodField()
    in_use_count = serializers.SerializerMethodField()

    software_id = serializers.PrimaryKeyRelatedField(
        queryset=SoftwareCatalog.objects.all(), source="software", write_only=True
    )

    class Meta:
        model = License
        fields = [
            "id",
            "software",
            "software_id",
            "license_key",
            "license_key_display",
            "purchase_date",
            "expiration_date",
            "quantity",
            "in_use_count",
            "created_at",
        ]
        read_only_fields = ["created_at"]
        extra_kwargs = {"license_key": {"write_only": True}}

    def get_license_key_display(self, obj):
        """Always return masked key in lists. Full key only returned via license_key field when writing."""
        if obj.license_key and len(obj.license_key) > 4:
            return f"****-****-****-{obj.license_key[-4:]}"
        return "Sin clave"

    def get_in_use_count(self, obj):
        """Return count of assets using this license."""
        return obj.installations.count()


class SoftwareVulnerabilitySerializer(serializers.ModelSerializer):
    """
    Serializer for SoftwareVulnerability.
    Used to manage vulnerability information for software catalog entries.
    """
    software_name = serializers.CharField(source='software.name', read_only=True)

    class Meta:
        model = SoftwareVulnerability
        fields = [
            'id',
            'software',
            'software_name',
            'cve_id',
            'title',
            'description',
            'severity',
            'affected_versions',
            'safe_version_from',
            'link_to_details',
            'discovered_date',
            'created_at',
        ]
        read_only_fields = ['created_at']


class SoftwareCatalogDetailSerializer(serializers.ModelSerializer):
    """
    Extended serializer for software catalog with vulnerability information.
    Used for detail views.
    """
    vulnerabilities = serializers.StringRelatedField(many=True, read_only=True)
    software_vulnerabilities = SoftwareVulnerabilitySerializer(many=True, read_only=True)
    installed_count = serializers.IntegerField(read_only=True, default=0)
    license_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = SoftwareCatalog
        fields = [
            'id',
            'name',
            'developer',
            'vulnerabilities',  # Legacy M2M field
            'software_vulnerabilities',  # New vulnerability tracking
            'installed_count',
            'license_count'
        ]


class LicenseInstallationSerializer(serializers.ModelSerializer):
    """Serializer for showing which assets have a license assigned."""
    asset = AssetBasicSerializer(read_only=True)

    class Meta:
        model = InstalledSoftware
        fields = ['id', 'asset', 'version', 'install_date']


class AssetWithLicenseStatusSerializer(serializers.Serializer):
    """Serializer for assets eligible for a license with their license status."""
    id = serializers.IntegerField()
    inventory_code = serializers.CharField()
    brand = serializers.CharField()
    model = serializers.CharField()
    asset_type = serializers.CharField()
    version = serializers.CharField()
    install_date = serializers.DateField()
    has_license = serializers.BooleanField()
    license_assigned = serializers.CharField(allow_null=True)
    installed_software_id = serializers.IntegerField()
    employee_name = serializers.CharField()
    employee_rut = serializers.CharField()
