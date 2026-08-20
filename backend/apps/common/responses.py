from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import exception_handler

SUCCESS_MESSAGE = "Operation completed successfully"
ERROR_MESSAGE = "Request failed"


def get_response_message(data, success):
    if isinstance(data, dict):
        for key in ("response_message", "message", "detail"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value
        if success:
            return SUCCESS_MESSAGE
        non_field_errors = data.get("non_field_errors")
        if isinstance(non_field_errors, list) and non_field_errors:
            return str(non_field_errors[0])
        for value in data.values():
            if isinstance(value, list) and value:
                return str(value[0])
            if isinstance(value, str) and value:
                return value
    if isinstance(data, list) and data:
        return str(data[0])
    return SUCCESS_MESSAGE if success else ERROR_MESSAGE


def is_enveloped(data):
    return isinstance(data, dict) and {"success", "response_code", "response_data"}.issubset(data)


def envelope_response(data, status_code):
    if is_enveloped(data):
        return data

    success = 200 <= status_code < 400
    message = get_response_message(data, success)
    pagination = None
    response_data = data

    if isinstance(data, dict) and {"count", "results"}.issubset(data):
        pagination = {
            key: value
            for key, value in data.items()
            if key not in {"results", "response_data"}
        }
        response_data = data.get("results")
    elif not success and isinstance(data, dict):
        response_data = data.get("errors", data)

    payload = {
        "success": success,
        "response_code": status_code,
        "response_message": message,
        "response_data": response_data,
    }

    if pagination is not None:
        payload["pagination"] = pagination

    return payload


class EnvelopedJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None
        request = renderer_context.get("request") if renderer_context else None

        if request and request.path.endswith("/schema/"):
            return super().render(data, accepted_media_type, renderer_context)

        status_code = response.status_code if response else 200
        if status_code == 204:
            return super().render(None, accepted_media_type, renderer_context)

        return super().render(
            envelope_response(data, status_code),
            accepted_media_type,
            renderer_context,
        )


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    message = get_response_message(response.data, False)
    response.data = {
        "message": message,
        "errors": response.data,
    }
    return response


def api_response(data=None, message=SUCCESS_MESSAGE, status_code=200):
    return Response(
        {
            "success": 200 <= status_code < 400,
            "response_code": status_code,
            "response_message": message,
            "response_data": data or {},
        },
        status=status_code,
    )
