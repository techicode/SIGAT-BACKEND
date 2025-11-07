from rest_framework import viewsets
from .models import Department, Employee
from .serializers import DepartmentSerializer, EmployeeSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows departments to be viewed or edited.
    """

    queryset = Department.objects.all().order_by("name")
    serializer_class = DepartmentSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employees to be viewed or edited.
    """

    queryset = Employee.objects.all().order_by("last_name", "first_name")
    serializer_class = EmployeeSerializer
