from django.db import connection
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})


@require_GET
def csrf(request):
    return JsonResponse({"csrf_token": get_token(request)})
