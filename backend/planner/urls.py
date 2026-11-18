from rest_framework.routers import DefaultRouter

from .views import TaskViewSet, TimerViewSet

router = DefaultRouter()
router.register("tasks", TaskViewSet, basename="task")
router.register("timers", TimerViewSet, basename="timer")
urlpatterns = router.urls
