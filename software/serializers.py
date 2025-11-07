from rest_framework import serializers
from .models import SoftwareCatalog, Vulnerability, InstalledSoftware
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
