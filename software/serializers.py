from rest_framework import serializers
from .models import SoftwareCatalog, Vulnerability, InstalledSoftware, License
from assets.models import Asset


class AssetBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ["inventory_code"]


class SoftwareCatalogSerializer(serializers.ModelSerializer):

    vulnerabilities = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = SoftwareCatalog
        fields = ["id", "name", "developer", "vulnerabilities"]


class InstalledSoftwareSerializer(serializers.ModelSerializer):

    asset = AssetBasicSerializer(read_only=True)
    software = SoftwareCatalogSerializer(read_only=True)

    asset_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(), source="asset", write_only=True
    )
    software_id = serializers.PrimaryKeyRelatedField(
        queryset=SoftwareCatalog.objects.all(), source="software", write_only=True
    )

    class Meta:
        model = InstalledSoftware
        fields = [
            "id",
            "asset",
            "asset_id",
            "software",
            "software_id",
            "version",
            "install_date",
        ]


class SoftwareCatalogBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoftwareCatalog
        fields = ["id", "name", "developer"]


class LicenseSerializer(serializers.ModelSerializer):
    software = SoftwareCatalogBasicSerializer(read_only=True)

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
            "purchase_date",
            "expiration_date",
            "quantity",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class LicenseBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = ["id", "license_key", "expiration_date"]


class InstalledSoftwareSerializer(serializers.ModelSerializer):
    asset = AssetBasicSerializer(read_only=True)
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
        allow_null=True,
        required=False,
    )

    class Meta:
        model = InstalledSoftware
        fields = [
            "id",
            "asset",
            "asset_id",
            "software",
            "software_id",
            "license",
            "license_id",
            "version",
            "install_date",
        ]
