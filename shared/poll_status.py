"""Shared polling helper for lychee async tasks."""

import time
from typing import Any, Callable, Dict, Optional, Tuple, Union

from http_client import LycheeApiError


ErrorField = Union[str, Tuple[str, ...]]


def _first_value(response: Dict[str, Any], fields: ErrorField) -> Optional[Any]:
    if isinstance(fields, str):
        return response.get(fields)
    for field in fields:
        value = response.get(field)
        if value:
            return value
    return None


def poll_status(
    poll_fn: Callable[[], Dict[str, Any]],
    *,
    interval: float = 5.0,
    timeout: float = 600.0,
    status_field: str = "status",
    success_states: Tuple[str, ...] = ("completed", "success"),
    error_states: Tuple[str, ...] = ("failed", "failure", "error"),
    error_field: ErrorField = "errorMessage",
    default_error: Optional[str] = None,
    timeout_error: str = "polling timeout",
    response_error: str = "poll response is not an object",
    request_id_field: str = "task_id",
    request_id: Optional[str] = None,
    pending_states: Optional[Tuple[str, ...]] = None,
) -> Dict[str, Any]:
    """Poll until the response status enters a success state or times out."""
    deadline = time.monotonic() + timeout
    last_request_id = request_id
    while time.monotonic() < deadline:
        response = poll_fn()
        if not isinstance(response, dict):
            raise LycheeApiError(500, response_error, last_request_id)
        last_request_id = response.get(request_id_field) or last_request_id
        status = response.get(status_field)
        if status in success_states:
            return response
        if status in error_states:
            error = _first_value(response, error_field)
            raise LycheeApiError(
                500,
                str(error or default_error or "{}={}".format(status_field, status)),
                last_request_id,
            )
        if pending_states is not None and status not in pending_states:
            raise LycheeApiError(
                500,
                "unknown {}: {}".format(status_field, status),
                last_request_id,
            )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(interval, remaining))
    raise LycheeApiError(504, timeout_error, last_request_id)
