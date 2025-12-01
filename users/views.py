import logging
from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count

logger = logging.getLogger(__name__)

from .permissions import IsAdminOrReadOnly
from .models import Department, Employee, CustomUser
from .serializers import (
    DepartmentSerializer,
    EmployeeSerializer,
    UserSerializer,
    ChangePasswordSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000


class ChangePasswordView(APIView):
    """
    An endpoint for changing password.
    """

    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        return self.request.user

    def put(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()

            return Response({"status": "password set"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.

    Supports:
    - Search: ?search=username (searches username and email)
    - Filter: ?role=ADMIN or ?role=TECHNICIAN
    """

    queryset = CustomUser.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    filterset_fields = {
        'role': ['exact'],
        'is_active': ['exact'],
    }


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows departments to be viewed or edited.

    Includes employee_count and asset_count annotations.
    """

    queryset = Department.objects.annotate(
        employee_count=Count('employees', distinct=True),
        asset_count=Count('assets', distinct=True)
    ).order_by("name")
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def create(self, request, *args, **kwargs):
        """Override create to add detailed logging for validation errors"""
        logger.info(f"Creating department with data: {request.data}")
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            logger.error(f"Department creation failed. Validation errors: {serializer.errors}")
            logger.error(f"Request data was: {request.data}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        logger.info(f"Department created successfully: {serializer.data}")
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employees to be viewed or edited.

    Supports:
    - Search: ?search=name (searches first_name, last_name, email, rut)
    - Filter: ?department=1
    """

    queryset = Employee.objects.select_related('department').all().order_by("last_name", "first_name")
    serializer_class = EmployeeSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'rut', 'position']
    filterset_fields = {
        'department': ['exact'],
    }
