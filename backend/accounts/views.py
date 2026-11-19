from django.db import transaction
from rest_framework.generics import RetrieveUpdateAPIView

from planner.services import lock_user

from .serializers import SettingsSerializer


class SettingsView(RetrieveUpdateAPIView):
    serializer_class = SettingsSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        request.user = lock_user(request.user)
        return super().patch(request, *args, **kwargs)
