from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from accounts.views import SettingsView

from .views import csrf, frontend, health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("_allauth/", include("allauth.headless.urls")),
    path("api/v1/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="api-docs"),
    path("api/v1/", include("planner.urls")),
    path("api/v1/settings/", SettingsView.as_view(), name="settings"),
    path("api/v1/csrf/", csrf, name="csrf"),
    path("health/", health, name="health"),
    path("", frontend, name="frontend"),
    path("<path:route>", frontend, name="frontend-route"),
]
