from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdminOrReadOnly
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
    permission_classes = [IsAuthenticated]


class InstalledSoftwareViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows softwares (installed) to be viewed or edited.
    """

    queryset = InstalledSoftware.objects.all()
    serializer_class = InstalledSoftwareSerializer
    permission_classes = [IsAuthenticated]


class LicenseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows licences to be viewed or edited.
    """

    queryset = License.objects.all()
    serializer_class = LicenseSerializer
    permission_classes = [IsAdminOrReadOnly]
