from typing import Any


def success_response(data: Any, *, message: str | None = None) -> dict[str, Any]:
    response = {"data": data}
    if message is not None:
        response["message"] = message
    return response
