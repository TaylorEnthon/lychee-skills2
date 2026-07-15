"""voice-lychee 音色与任务列表脚本契约。"""

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "voice-lychee" / "scripts"


def load(name):
    path = SCRIPTS / "{}.py".format(name)
    assert path.is_file(), "{} is missing".format(path.name)
    spec = importlib.util.spec_from_file_location("voice_lychee_{}".format(name), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_list_voices_fetches_normalizes_and_caches(monkeypatch, tmp_path):
    module = load("list_voices")
    cache = tmp_path / "voices-cache.json"
    get_json = MagicMock(return_value=[{
        "id": "1", "name": "Vivi 2.0", "description": "通用", "type": "builtin",
        "gender": "female", "lang_code": None,
    }])
    monkeypatch.setattr(module, "get_json", get_json)

    voices = module.list_voices(cache, refresh=False, no_cache=False, timeout=10)

    assert voices[0]["id"] == "1"
    assert json.loads(cache.read_text(encoding="utf-8"))["voices"] == voices


def test_list_voices_uses_fresh_cache(monkeypatch, tmp_path):
    module = load("list_voices")
    cache = tmp_path / "voices-cache.json"
    cache.write_text(json.dumps({
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "voices": [{"id": "2", "name": "cached"}],
    }), encoding="utf-8")
    get_json = MagicMock()
    monkeypatch.setattr(module, "get_json", get_json)

    assert module.list_voices(cache, refresh=False, no_cache=False, timeout=10)[0]["name"] == "cached"
    get_json.assert_not_called()


def test_list_tasks_normalizes_page(monkeypatch):
    module = load("list_tasks")
    get_json = MagicMock(return_value={"list": [{"id": 7}], "total": 1, "page": 2, "page_size": 10})
    monkeypatch.setattr(module, "get_json", get_json)

    result = module.list_tasks(page=2, page_size=10, status="success", timeout=20)

    assert result == {"success": True, "total": 1, "page": 2, "page_size": 10, "tasks": [{"id": 7}]}
    assert get_json.call_args.kwargs["params"] == {"page": 2, "page_size": 10, "status": "success"}

