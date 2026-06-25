"""pre-commit hook source smoke tests."""
import os
import stat


def test_precommit_hook_exists_and_is_executable():
    hook = os.path.join(os.path.dirname(__file__), "..", ".githooks", "pre-commit")
    assert os.path.isfile(hook)
    if os.name == "nt":
        with open(hook, encoding="utf-8") as f:
            assert f.readline().strip() == "#!/usr/bin/env bash"
        install_sh = os.path.join(os.path.dirname(__file__), "..", "install.sh")
        with open(install_sh, encoding="utf-8") as f:
            assert 'chmod +x "$HERE/.git/hooks/pre-commit"' in f.read()
    else:
        mode = os.stat(hook).st_mode
        assert mode & stat.S_IXUSR


def test_precommit_hook_contains_core_checks():
    hook = os.path.join(os.path.dirname(__file__), "..", ".githooks", "pre-commit")
    content = open(hook, encoding="utf-8").read()
    for keyword in [
        "skills-lock.json",
        ".codex-prompts/",
        "CRLF line endings",
        "> 10MB",
        "SKIP_PRECOMMIT_TESTS",
        "tests/run_tests.sh",
    ]:
        assert keyword in content
