import logging
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Asset
from .serializers import AssetListSerializer, AssetDetailSerializer

logger = logging.getLogger(__name__)


class AssetPagination(PageNumberPagination):
    """
    Custom pagination class for assets.
    Allows clients to request custom page sizes up to max_page_size.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows assets to be viewed or edited.

    Supports:
    - Pagination: ?page=2&page_size=50
    - Search: ?search=Dell (searches inventory_code, serial_number, brand, model, department, employee)
    - Ordering: ?ordering=brand or ?ordering=-inventory_code
    - Filters: ?asset_type=NOTEBOOK&status=ASIGNADO&department=1
    """

    queryset = Asset.objects.select_related('department', 'employee').order_by("-created_at")
    permission_classes = [IsAuthenticated]
    lookup_field = "inventory_code"

    # Pagination
    pagination_class = AssetPagination

    # Filtering and search
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = [
        'inventory_code',
        'serial_number',
        'brand',
        'model',
        'department__name',
        'employee__first_name',
        'employee__last_name',
    ]
    ordering_fields = ['inventory_code', 'brand', 'model', 'status', 'asset_type', 'created_at', 'updated_at']
    filterset_fields = {
        'asset_type': ['exact'],
        'status': ['exact'],
        'department': ['exact'],
        'employee': ['exact'],
        'inventory_code': ['exact', 'istartswith'],
    }

    def get_serializer_class(self):
        if self.action == "list":
            return AssetListSerializer

        return AssetDetailSerializer

    def create(self, request, *args, **kwargs):
        """Override create to add detailed logging for validation errors"""
        logger.info(f"Creating asset with data: {request.data}")
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            logger.error(f"Asset creation failed. Validation errors: {serializer.errors}")
            logger.error(f"Request data was: {request.data}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        logger.info(f"Asset created successfully: {serializer.data}")
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
