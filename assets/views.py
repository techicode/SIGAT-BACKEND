from rest_framework import viewsets
from .models import Asset
from .serializers import AssetListSerializer, AssetDetailSerializer


class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows departments to be viewed or edited.
    """

    queryset = Asset.objects.all().order_by("inventory_code")

    lookup_field = "inventory_code"

    def get_serializer_class(self):

        if self.action == "list":
            return AssetListSerializer

        return AssetDetailSerializer
