"""pytest 配置 + 路径常量。"""
import os
from pathlib import Path
import re
import shutil

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = REPO_ROOT / "shared"
SKILLS_DIR = REPO_ROOT / "skills"
SKILLS = [
    "asr-lychee",
    "tts-lychee",
    "voice-lychee",
    "voice-clone-lychee",
    "voice-infer-lychee",
    "timbre-design-lychee",
    "speaker-classify-lychee",
    "voice-separate-lychee",
    "subtitle-erase-lychee",
    "videots-lychee",
    "video-compose-lychee",
]


@pytest.fixture(params=SKILLS)
def skill_name(request):
    return request.param


@pytest.fixture
def skill_dir(skill_name):
    return SKILLS_DIR / skill_name


@pytest.fixture
def shared_dir():
    return SHARED_DIR


def _ensure_test_api_key():
    """保证单元测试有占位 API key；真实请求由 mock 拦截。"""
    os.environ.setdefault("LYCHEE_API_KEY", "test-fixture-key")


@pytest.fixture(autouse=True)
def _api_key_fixture():
    _ensure_test_api_key()


@pytest.fixture
def tmp_workspace_path(request):
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", request.node.name)
    path = REPO_ROOT / ".pytest-tmp" / safe_name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
