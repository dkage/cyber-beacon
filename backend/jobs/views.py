from rest_framework import generics, serializers

from .models import JobRun


class JobRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRun
        fields = ["id", "kind", "started_at", "ended_at", "outcome", "message", "counts"]


class JobRunList(generics.ListAPIView):
    serializer_class = JobRunSerializer

    def get_queryset(self):
        return JobRun.objects.filter(user=self.request.user).order_by("-started_at", "-pk")
