"""shared.poll_status 的最小行为测试。"""

import pytest

from helpers import SHARED_DIR

import sys

sys.path.insert(0, str(SHARED_DIR))
from http_client import LycheeApiError
from poll_status import poll_status


def test_poll_status_returns_after_success(monkeypatch):
    responses = iter([
        {"status": "pending", "task_id": "t1"},
        {"status": "pending", "task_id": "t1"},
        {"status": "completed", "task_id": "t1", "result": "ok"},
    ])
    calls = []
    monkeypatch.setattr("poll_status.time.sleep", lambda seconds: calls.append(seconds))

    result = poll_status(lambda: next(responses), interval=1, timeout=10)

    assert result["result"] == "ok"
    assert len(calls) == 2


def test_poll_status_failed_raises():
    with pytest.raises(LycheeApiError, match="x"):
        poll_status(lambda: {"status": "failed", "errorMessage": "x", "task_id": "t1"})


def test_poll_status_timeout_raises(monkeypatch):
    monkeypatch.setattr("poll_status.time.sleep", lambda seconds: None)

    with pytest.raises(LycheeApiError, match="polling timeout"):
        poll_status(lambda: {"status": "pending", "task_id": "t1"}, timeout=0.001)
