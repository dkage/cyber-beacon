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


def document_error_code_header(result, **kwargs):
    header = {
        "description": "Stable code for the first error, when available.",
        "schema": {"type": "string"},
    }
    for path, operations in result["paths"].items():
        if not path.startswith("/api/v1/"):
            continue
        for operation in operations.values():
            responses = operation.get("responses", {})
            if "requestBody" in operation:
                responses.setdefault("400", {"description": "Invalid request."})
            for status, response in responses.items():
                if status.startswith(("4", "5")) and "$ref" not in response:
                    response.setdefault("headers", {})["X-Beacon-Error-Code"] = header
    return result
