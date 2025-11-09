from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from .permissions import IsAdminOrReadOnly
from .models import Department, Employee, CustomUser
from .serializers import (
    DepartmentSerializer,
    EmployeeSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = CustomUser.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows departments to be viewed or edited.
    """

    queryset = Department.objects.all().order_by("name")
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnly]


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employees to be viewed or edited.
    """

    queryset = Employee.objects.all().order_by("last_name", "first_name")
    serializer_class = EmployeeSerializer
