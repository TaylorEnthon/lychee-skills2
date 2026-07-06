"""跨 skill workflow 文档与 slash command 的轻量测试。"""
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_workflow_docs_and_command_exist():
    for path in [
        "docs/workflows/README.md",
        "docs/workflows/short-drama-translate.md",
        "docs/workflows/multi-speaker-dub.md",
        "docs/workflows/voice-replicate.md",
        "commands/lychee-workflow.md",
    ]:
        assert (REPO_ROOT / path).is_file(), path


def test_recipe_docs_name_required_skills():
    expectations = {
        "docs/workflows/short-drama-translate.md": [
            "videots-lychee",
            "video-compose-lychee",
        ],
        "docs/workflows/multi-speaker-dub.md": ["speaker-classify-lychee"],
        "docs/workflows/voice-replicate.md": ["voice-clone-lychee", "tts-lychee"],
    }
    for path, keywords in expectations.items():
        text = (REPO_ROOT / path).read_text(encoding="utf-8")
        for keyword in keywords:
            assert keyword in text


def test_workflow_command_has_description_frontmatter():
    text = (REPO_ROOT / "commands/lychee-workflow.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "description:" in text.split("---", 2)[1]
