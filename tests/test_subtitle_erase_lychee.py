"""subtitle-erase-lychee skill 的 smoke 测试。"""
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
    "scripts/erase.py",
]


@pytest.fixture
def skill_name():
    return "subtitle-erase-lychee"


def test_required_files_exist(skill_dir):
    assert_required_files(skill_dir, REQUIRED_FILES)


def test_skill_md_has_yaml_frontmatter(skill_dir):
    assert_skill_frontmatter(skill_dir, "subtitle-erase-lychee")


def test_script_help_runs(skill_dir):
    assert_script_help(skill_dir, "erase.py", ["--file"])


def test_doctor_runs_without_api_key(skill_dir, tmp_workspace_path, monkeypatch):
    assert_doctor_warns_without_api_key(skill_dir, tmp_workspace_path, monkeypatch)


def test_install_ps1_source_path_validation(skill_dir):
    assert_install_ps1_validates_source(skill_dir)
