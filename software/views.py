from rest_framework import viewsets
from .models import SoftwareCatalog, InstalledSoftware, License
from .serializers import (
    SoftwareCatalogSerializer,
    InstalledSoftwareSerializer,
    LicenseSerializer,
)


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


class LicenseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows licences to be viewed or edited.
    """

    queryset = License.objects.all()
    serializer_class = LicenseSerializer
