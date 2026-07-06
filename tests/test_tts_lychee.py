"""tts-lychee skill 的 smoke 测试。"""
import json

import pytest

from helpers import (
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
    "scripts/synthesize.py",
]
REQUIRED_VOICES = ["默认女声", "默认男声", "性感女声", "小男孩声音", "云南话男声"]


@pytest.fixture
def skill_name():
    return "tts-lychee"


def test_required_files_exist(skill_dir):
    assert_required_files(skill_dir, REQUIRED_FILES)


def test_skill_md_has_yaml_frontmatter(skill_dir):
    assert_skill_frontmatter(skill_dir, "tts-lychee")


def test_script_help_runs(skill_dir):
    assert_script_help(skill_dir, "synthesize.py", ["--text", "--voice"])


def test_doctor_runs_without_api_key(skill_dir, tmp_workspace_path, monkeypatch):
    assert_doctor_warns_without_api_key(skill_dir, tmp_workspace_path, monkeypatch)


def test_install_ps1_source_path_validation(skill_dir):
    assert_install_ps1_validates_source(skill_dir)


def test_data_files_exist(skill_dir):
    for file_name in ["alias_map.json", "presets.json", "voice_aliases.json"]:
        assert (skill_dir / "data" / file_name).is_file()


def test_required_voices_in_presets(skill_dir):
    presets = json.loads((skill_dir / "data" / "presets.json").read_text(encoding="utf-8"))
    for voice in REQUIRED_VOICES:
        assert voice in presets, f"missing voice: {voice}"


def test_required_aliases_in_alias_map(skill_dir):
    alias_map = json.loads(
        (skill_dir / "data" / "alias_map.json").read_text(encoding="utf-8")
    )
    for voice in REQUIRED_VOICES:
        assert voice in alias_map, f"missing alias: {voice}"
