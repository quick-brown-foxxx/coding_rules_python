from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "setting-up-python-projects"
TEMPLATE_ROOT = REPO_ROOT / "templates"


def resolve_bootstrap_script() -> Path:
    candidates = sorted(path for path in SKILL_DIR.glob("*.sh") if path.is_file())

    assert candidates, f"Expected a shell bootstrap script next to {SKILL_DIR / 'SKILL.md'}"
    assert len(candidates) == 1, f"Expected exactly one shell bootstrap script in {SKILL_DIR}, found: {candidates}"
    return candidates[0]


def assert_bootstrapped_layout(target_root: Path) -> None:
    assert not (target_root / "templates").exists()
    assert (target_root / "AGENTS.md").is_file()
    assert (target_root / "pyproject.toml").is_file()
    assert (target_root / ".pre-commit-config.yaml").is_file()
    assert (target_root / ".gitignore").is_file()
    assert (target_root / ".vscode" / "settings.json").is_file()
    assert (target_root / ".vscode" / "extensions.json").is_file()
    assert (target_root / "docs" / "coding_rules.md").is_file()
    assert (target_root / "docs" / "PHILOSOPHY.md").is_file()
    assert (target_root / "CLAUDE.md").is_symlink()
    assert (target_root / "CLAUDE.md").resolve() == (target_root / "AGENTS.md").resolve()
    assert (target_root / "src" / "todo_package_name" / "__init__.py").is_file()
    assert (target_root / "src" / "todo_package_name" / "__main__.py").is_file()
    assert (target_root / "tests" / "test_main.py").is_file()
    assert (target_root / "shared" / "__init__.py").is_file()
    assert (target_root / "shared_tests" / "__init__.py").is_file()


def test_bootstrap_shell_script_bootstraps_real_repo_layout(tmp_path: Path) -> None:
    bootstrap_script = resolve_bootstrap_script()
    target_root = tmp_path / "downstream_repo"

    result = subprocess.run(
        [
            "bash",
            str(bootstrap_script),
            str(REPO_ROOT),
            str(target_root),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert f"Bootstrapped downstream repo in {target_root.resolve()}" in result.stdout
    assert_bootstrapped_layout(target_root)


def test_bootstrap_shell_script_supports_stdin_copy_paste_flow(tmp_path: Path) -> None:
    bootstrap_script = resolve_bootstrap_script()
    source_root = tmp_path / "source_repo"
    target_root = tmp_path / "pasted_bootstrap_repo"
    fake_bin = tmp_path / "bin"
    uv_log = tmp_path / "uv.log"

    (source_root / "templates").mkdir(parents=True)
    (source_root / "shared").mkdir()
    (source_root / "shared_tests").mkdir()
    (source_root / "rules").mkdir()
    fake_bin.mkdir()

    (source_root / "templates" / "AGENTS.md").write_text("@docs/PHILOSOPHY.md\n", encoding="utf-8")
    (source_root / "templates" / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (source_root / "templates" / "pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    (source_root / "templates" / "src" / "todo_package_name").mkdir(parents=True)
    (source_root / "templates" / "src" / "todo_package_name" / "__init__.py").write_text(
        '__version__ = "0.1.0"\n',
        encoding="utf-8",
    )
    (source_root / "templates" / "src" / "todo_package_name" / "__main__.py").write_text(
        "def main() -> int:\n    return 0\n",
        encoding="utf-8",
    )
    (source_root / "templates" / "tests").mkdir()
    (source_root / "templates" / "tests" / "test_main.py").write_text(
        "def test_main() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    (source_root / "templates" / "gitignore").write_text(".venv/\n", encoding="utf-8")
    (source_root / "templates" / "vscode_settings.json").write_text("{}\n", encoding="utf-8")
    (source_root / "templates" / "vscode_extensions.json").write_text("{}\n", encoding="utf-8")
    (source_root / "shared" / "__init__.py").write_text("", encoding="utf-8")
    (source_root / "shared_tests" / "__init__.py").write_text("", encoding="utf-8")
    (source_root / "PHILOSOPHY.md").write_text("# Philosophy\n", encoding="utf-8")
    (source_root / "rules" / "coding_rules.md").write_text("# Rules\n", encoding="utf-8")

    (fake_bin / "uv").write_text(
        f"#!/usr/bin/env bash\nset -euo pipefail\nprintf '%s\\n' \"$*\" >> {uv_log}\n",
        encoding="utf-8",
    )
    os.chmod(fake_bin / "uv", 0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = subprocess.run(
        ["bash", "-s", "--", str(source_root), str(target_root)],
        input=bootstrap_script.read_text(encoding="utf-8"),
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert f"Bootstrapped downstream repo in {target_root.resolve()}" in result.stdout
    assert_bootstrapped_layout(target_root)
    assert uv_log.read_text(encoding="utf-8").splitlines() == [
        "sync --all-extras --group dev",
        "run poe lint_full",
        "run poe test",
    ]
