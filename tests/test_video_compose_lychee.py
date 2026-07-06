"""video-compose-lychee skill 的 smoke 测试。"""
import importlib.util
import sys
from types import SimpleNamespace

import pytest

from helpers import (
    SHARED_DIR,
    assert_doctor_warns_without_api_key,
    assert_install_ps1_validates_source,
    assert_required_files,
    assert_script_help,
    assert_skill_frontmatter,
)

REQUIRED_FILES = [
    "SKILL.md",
    "install.sh",
    "install.ps1",
    "doctor.sh",
    "doctor.ps1",
    "scripts/compose.py",
]


@pytest.fixture
def skill_name():
    return "video-compose-lychee"


def test_required_files_exist(skill_dir):
    assert_required_files(skill_dir, REQUIRED_FILES)


def test_skill_md_has_yaml_frontmatter(skill_dir):
    assert_skill_frontmatter(skill_dir, "video-compose-lychee")


def test_script_help_runs(skill_dir):
    assert_script_help(skill_dir, "compose.py", ["--video-file", "--subtitle-file"])


def test_doctor_runs_without_api_key(skill_dir, tmp_workspace_path, monkeypatch):
    assert_doctor_warns_without_api_key(skill_dir, tmp_workspace_path, monkeypatch)


def test_install_ps1_source_path_validation(skill_dir):
    assert_install_ps1_validates_source(skill_dir)


def test_subtitle_file_requires_target_language(skill_dir, tmp_path):
    sys.path.insert(0, str(SHARED_DIR))
    spec = importlib.util.spec_from_file_location(
        "video_compose", skill_dir / "scripts" / "compose.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    video = tmp_path / "demo.mp4"
    subtitle = tmp_path / "demo.srt"
    video.write_bytes(b"0")
    subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n", encoding="utf-8")
    args = SimpleNamespace(
        video_file=video,
        audio_file=None,
        subtitle_file=subtitle,
        target_language=None,
        subtitle_x=None,
        subtitle_y=None,
        subtitle_font_size=None,
        coordinate_width=None,
        coordinate_height=None,
        interval=5.0,
        timeout=600.0,
    )

    with pytest.raises(ValueError, match="target-language"):
        module.validate_args(args)
