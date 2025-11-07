from rest_framework import viewsets
from .models import SoftwareCatalog, InstalledSoftware
from .serializers import SoftwareCatalogSerializer, InstalledSoftwareSerializer


class SoftwareCatalogViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows softwares to be viewed or edited.
    """

    queryset = SoftwareCatalog.objects.all().order_by("name")
    serializer_class = SoftwareCatalogSerializer


class InstalledSoftwareViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows softwares (installed) to be viewed or edited.
    """

    queryset = InstalledSoftware.objects.all()
    serializer_class = InstalledSoftwareSerializer
