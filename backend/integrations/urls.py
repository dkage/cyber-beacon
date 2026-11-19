from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ConnectionViewSet, MountViewSet, OAuthCallback, OAuthStart

router = DefaultRouter()
router.register("connections", ConnectionViewSet, basename="connection")
router.register("mounts", MountViewSet, basename="mount")
urlpatterns = [
    path("oauth/start/", OAuthStart.as_view(), name="oauth-start"),
    path("oauth/<str:provider>/callback/", OAuthCallback.as_view(), name="oauth-callback"),
    *router.urls,
]
