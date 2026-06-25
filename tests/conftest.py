"""pytest 配置 + 路径常量。"""
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
    "voice-clone-lychee",
    "voice-infer-lychee",
    "timbre-design-lychee",
    "speaker-classify-lychee",
    "voice-separate-lychee",
    "subtitle-erase-lychee",
    "videots-lychee",
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
