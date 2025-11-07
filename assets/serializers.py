from rest_framework import serializers
from .models import Asset


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            "inventory_code",
            "serial_number",
            "asset_type",
            "status",
            "brand",
            "model",
            "acquisition_date",
            "employee",
            "department",
            "created_at",
            "updated_at",
        ]

        read_only_fields = ["created_at", "updated_at"]
