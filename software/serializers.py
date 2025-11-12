from rest_framework import serializers
from .models import SoftwareCatalog, InstalledSoftware, License
from assets.models import Asset


class AssetBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ["inventory_code"]


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
            "created_at",
        ]
        read_only_fields = ["created_at"]
        extra_kwargs = {"license_key": {"write_only": True}}

    def get_license_key_display(self, obj):
        user = self.context["request"].user
        if user.is_authenticated and user.role == "ADMIN":
            return obj.license_key
        if obj.license_key and len(obj.license_key) > 4:
            return f"****-****-****-{obj.license_key[-4:]}"
        return "Hidden"
