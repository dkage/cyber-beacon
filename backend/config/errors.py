from rest_framework.exceptions import ErrorDetail
from rest_framework.views import exception_handler


def first_error_code(value):
    if isinstance(value, ErrorDetail):
        return value.code
    if isinstance(value, dict):
        value = value.values()
    elif not isinstance(value, list):
        return None
    return next((code for item in value if (code := first_error_code(item))), None)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None and (code := first_error_code(response.data)):
        response["X-Beacon-Error-Code"] = code
    return response
