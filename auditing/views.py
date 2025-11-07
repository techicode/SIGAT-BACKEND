from rest_framework import viewsets
from .models import AssetCheckin
from .serializers import AssetCheckinSerializer


class AssetCheckinViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows checkins to be viewed or edited.
    """

    queryset = AssetCheckin.objects.all().order_by("-checkin_date")
    serializer_class = AssetCheckinSerializer
