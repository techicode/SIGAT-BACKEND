from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count
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

    Supports:
    - Search: ?search=Adobe (searches name and developer)
    - Ordering: ?ordering=name or ?ordering=-installed_count
    """

    queryset = SoftwareCatalog.objects.annotate(
        installed_count=Count('installations', distinct=True),
        license_count=Count('licenses', distinct=True)
    ).order_by('name')
    serializer_class = SoftwareCatalogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'developer']
    ordering_fields = ['name', 'developer', 'installed_count', 'license_count']


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
