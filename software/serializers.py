from rest_framework import serializers
from .models import SoftwareCatalog, Vulnerability


class SoftwareCatalogSerializer(serializers.ModelSerializer):

    vulnerabilities = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = SoftwareCatalog
        fields = ["id", "name", "developer", "vulnerabilities"]
