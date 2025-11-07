from rest_framework import viewsets
from .models import Asset
from .serializers import AssetSerializer


class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows departments to be viewed or edited.
    """

    queryset = Asset.objects.all().order_by("inventory_code")
    serializer_class = AssetSerializer
