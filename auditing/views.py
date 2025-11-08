from rest_framework import viewsets
from .models import AssetCheckin, ComplianceWarning
from .serializers import AssetCheckinSerializer, ComplianceWarningSerializer


class AssetCheckinViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows checkins to be viewed or edited.
    """

    queryset = AssetCheckin.objects.all().order_by("-checkin_date")
    serializer_class = AssetCheckinSerializer


class ComplianceWarningViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows compliances warning to be viewed or edited.
    """

    queryset = ComplianceWarning.objects.all().order_by("-detection_date")
    serializer_class = ComplianceWarningSerializer
    
    def perform_update(self, serializer):
        serializer.save(resolved_by=self.request.user)
