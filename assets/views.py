from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Asset
from .serializers import AssetListSerializer, AssetDetailSerializer


class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows assets to be viewed or edited.
    """

    queryset = Asset.objects.all().order_by("inventory_code")
    permission_classes = [IsAuthenticated]

    lookup_field = "inventory_code"

    def get_serializer_class(self):
        if self.action == "list":
            return AssetListSerializer

        return AssetDetailSerializer
