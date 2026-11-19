from django.conf import settings
from django.db import connection
from django.http import FileResponse, Http404, JsonResponse
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


@require_GET
def frontend(request, route=""):
    """Only client routes receive a shell; missing assets and API paths stay 404."""
    root = settings.FRONTEND_DIR.resolve()
    if route in {"", "today", "connections", "settings", "kiosk", "login"}:
        target = root / "index.html"
    else:
        target = (root / route).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            raise Http404()
    if not target.is_file():
        raise Http404()
    response = FileResponse(target.open("rb"))
    response["Cache-Control"] = "no-cache" if target.suffix == ".html" else "public, max-age=3600"
    return response
