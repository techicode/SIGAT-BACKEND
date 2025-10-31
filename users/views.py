from rest_framework import viewsets
from .models import Department
from .serializers import DepartmentSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows departments to be viewed or edited.
    """

    queryset = Department.objects.all().order_by("name")
    serializer_class = DepartmentSerializer
