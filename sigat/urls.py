from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView as OriginalTokenObtainPairView,
)
from rest_framework.response import Response
from rest_framework import status
from users.serializers import MyTokenObtainPairSerializer


class MyTokenObtainPairView(OriginalTokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the tokens
        tokens = serializer.validated_data

        # Get the user from the serializer
        user = serializer.user

        # Add user info to the response
        response_data = {
            'refresh': str(tokens['refresh']),
            'access': str(tokens['access']),
            'username': user.username,
            'role': user.role,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }

        return Response(response_data, status=status.HTTP_200_OK)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include("users.urls")),
    path("api/", include("assets.urls")),
    path("api/", include("software.urls")),
    path("api/", include("auditing.urls")),
]
