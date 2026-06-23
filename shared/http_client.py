"""lychee OpenAPI 共享 HTTP 客户端。"""

import time
from typing import Any, Dict, Optional, Tuple

import requests

from auth import API_KEY_HEADER, get_api_key

BASE_URL = "https://shanhaistudio.lycheeai.com.cn/openapi"


class LycheeApiError(Exception):
    """lychee OpenAPI 返回业务或 HTTP 错误。"""

    def __init__(self, code: Any, info: str, request_id: Optional[str] = None):
        message = "[{}] {}".format(code, info)
        if request_id:
            message += " (request_id={})".format(request_id)
        super().__init__(message)
        self.code = code
        self.info = info
        self.request_id = request_id


_SESSION = requests.Session()


def _headers() -> Dict[str, str]:
    return {API_KEY_HEADER: get_api_key()}


def _url(path: str) -> str:
    return BASE_URL.rstrip("/") + "/" + path.lstrip("/")


def _response_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return None


def _request_id(body: Any) -> Optional[str]:
    if not isinstance(body, dict):
        return None
    return body.get("request_id") or body.get("requestId")


def _raise_http_error(response: requests.Response, body: Any) -> None:
    if isinstance(body, dict):
        code = body.get("code", response.status_code)
        info = body.get("info") or body.get("message") or response.reason
    else:
        code = response.status_code
        info = response.text.strip() or response.reason
    raise LycheeApiError(code, str(info), _request_id(body))


def _unwrap(body: Any) -> Any:
    """解开 ApiResponse 包装，裸 JSON 保持原样。"""
    if isinstance(body, dict) and all(key in body for key in ("code", "info", "data")):
        if body.get("code") not in (200, "200"):
            raise LycheeApiError(body.get("code"), body.get("info"), _request_id(body))
        data = body.get("data")
        return {} if data is None else data

    if isinstance(body, dict) and "code" in body and body.get("code") not in (200, "200"):
        info = body.get("info") or body.get("message") or "API request failed"
        raise LycheeApiError(body.get("code"), str(info), _request_id(body))
    return body


def _handle_response(response: requests.Response) -> Any:
    body = _response_json(response)
    if not 200 <= response.status_code < 300:
        _raise_http_error(response, body)
    if body is None:
        raise LycheeApiError(response.status_code, "response is not valid JSON")
    return _unwrap(body)


def post_multipart(
    path: str,
    files: Dict[str, Any],
    data: Optional[Dict[str, Any]] = None,
    timeout: float = 60,
) -> Any:
    """POST multipart，返回解包后的 data 或裸 JSON。"""
    response = _SESSION.post(
        _url(path), headers=_headers(), files=files, data=data, timeout=timeout
    )
    return _handle_response(response)


def post_json(path: str, body: Dict[str, Any], timeout: float = 60) -> Any:
    """POST JSON，返回解包后的 data 或裸 JSON。"""
    response = _SESSION.post(
        _url(path), headers=_headers(), json=body, timeout=timeout
    )
    return _handle_response(response)


def get_json(
    path: str, params: Optional[Dict[str, Any]] = None, timeout: float = 60
) -> Any:
    """GET JSON，返回解包后的 data 或裸 JSON。"""
    response = _SESSION.get(
        _url(path), headers=_headers(), params=params, timeout=timeout
    )
    return _handle_response(response)


def poll_status(
    path_template: str,
    request_id: str,
    interval: float = 3.0,
    timeout: float = 300.0,
    terminal: Tuple[str, ...] = ("success", "failed", "completed"),
) -> Dict[str, Any]:
    """轮询状态接口，命中 terminal 时返回最后一次响应。"""
    deadline = time.monotonic() + timeout
    path = path_template.format(request_id=request_id)

    while True:
        result = get_json(path)
        if not isinstance(result, dict):
            raise LycheeApiError(500, "polling response is not an object", request_id)
        if result.get("status") in terminal:
            return result

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise LycheeApiError(504, "polling timeout", request_id)
        time.sleep(min(interval, remaining))
