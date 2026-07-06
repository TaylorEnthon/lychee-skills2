"""tts-lychee preset 数据完整性测试。"""

import base64
import importlib.util
import sys
from pathlib import Path

import pytest

from helpers import SHARED_DIR


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNTHESIZE = REPO_ROOT / "skills" / "tts-lychee" / "scripts" / "synthesize.py"


@pytest.fixture(scope="module")
def synthesize_module():
    try:
        sys.path.insert(0, str(SHARED_DIR))
        spec = importlib.util.spec_from_file_location("tts_synthesize_for_test", SYNTHESIZE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.load_voice_data()
        return module
    except Exception as exc:
        pytest.skip("cannot load tts-lychee data: {}".format(exc))


@pytest.fixture(scope="module")
def voice_data(synthesize_module):
    return synthesize_module.load_voice_data()


def test_required_voices_and_aliases_resolve(synthesize_module, voice_data):
    alias_map, presets, _ = voice_data
    assert synthesize_module.REQUIRED_VOICES == [
        "默认女声",
        "默认男声",
        "性感女声",
        "小男孩声音",
        "云南话男声",
    ]
    for voice in synthesize_module.REQUIRED_VOICES:
        assert voice in presets
        assert alias_map[voice] in presets


def test_presets_have_valid_speaker_ref_category_and_match_mode(voice_data):
    _, presets, _ = voice_data
    for voice, preset in presets.items():
        speaker_ref = preset.get("speaker_ref")
        assert isinstance(speaker_ref, str) and speaker_ref, voice
        encoded = speaker_ref[4:] if speaker_ref.startswith("b64:") else speaker_ref
        assert base64.b64decode(encoded).decode("utf-8"), voice
        assert isinstance(preset.get("category"), str) and preset["category"], voice
        assert preset.get("match_mode") in {"normal", "exact"}, voice


def test_alias_map_values_exist_in_presets(voice_data):
    alias_map, presets, _ = voice_data
    for alias, voice in alias_map.items():
        assert voice in presets, alias


def test_run_doctor_keeps_core_voice_match(synthesize_module):
    result = synthesize_module.run_doctor()
    assert result["preview"]["voice"] == "性感女声"
