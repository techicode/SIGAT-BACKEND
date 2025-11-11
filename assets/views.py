from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Asset
from .serializers import AssetListSerializer, AssetDetailSerializer


class AssetPagination(PageNumberPagination):
    """
    Custom pagination class for assets.
    Allows clients to request custom page sizes up to max_page_size.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows assets to be viewed or edited.

    Supports:
    - Pagination: ?page=2&page_size=50
    - Search: ?search=Dell (searches inventory_code, serial_number, brand, model, department, employee)
    - Ordering: ?ordering=brand or ?ordering=-inventory_code
    """

    queryset = Asset.objects.select_related('department', 'employee').order_by("inventory_code")
    permission_classes = [IsAuthenticated]
    lookup_field = "inventory_code"

    # Pagination
    pagination_class = AssetPagination

    # Filtering and search
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        'inventory_code',
        'serial_number',
        'brand',
        'model',
        'department__name',
        'employee__first_name',
        'employee__last_name',
    ]
    ordering_fields = ['inventory_code', 'brand', 'model', 'status', 'asset_type']

    def get_serializer_class(self):
        if self.action == "list":
            return AssetListSerializer

        return AssetDetailSerializer
