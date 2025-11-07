from rest_framework import viewsets
from .models import SoftwareCatalog
from .serializers import SoftwareCatalogSerializer


class SoftwareCatalogViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows softwares to be viewed or edited.
    """

    queryset = SoftwareCatalog.objects.all().order_by("name")
    serializer_class = SoftwareCatalogSerializer
