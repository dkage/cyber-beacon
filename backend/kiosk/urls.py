from django.urls import path

from .views import Devices, KioskSummary, PairApprove, PairPoll, PairStart, RevokeDevice

urlpatterns = [
    path("pair/", PairStart.as_view(), name="pair-start"),
    path("pair/approve/", PairApprove.as_view(), name="pair-approve"),
    path("pair/poll/", PairPoll.as_view(), name="pair-poll"),
    path("devices/", Devices.as_view(), name="devices"),
    path("devices/<uuid:device_id>/revoke/", RevokeDevice.as_view(), name="device-revoke"),
    path("summary/", KioskSummary.as_view(), name="kiosk-summary"),
]
