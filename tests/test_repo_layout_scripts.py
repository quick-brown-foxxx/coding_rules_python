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


def assert_bootstrapped_layout(target_root: Path, package_name: str = "todo_package_name") -> None:
    package_root = target_root / "src" / package_name

    assert not (target_root / "templates").exists()
    assert not (target_root / "shared").exists(), "top-level shared/ must not be rendered into downstream repos"
    assert (target_root / "AGENTS.md").is_file()
    assert (target_root / "pyproject.toml").is_file()
    assert (target_root / ".pre-commit-config.yaml").is_file()
    assert (target_root / ".gitignore").is_file()
    assert (target_root / ".vscode" / "settings.json").is_file()
    assert (target_root / ".vscode" / "extensions.json").is_file()
    assert (target_root / ".github" / "workflows" / "ci.yml").is_file()
    assert (target_root / "docs" / "coding_rules.md").is_file()
    assert (target_root / "CLAUDE.md").is_symlink()
    assert (target_root / "CLAUDE.md").resolve() == (target_root / "AGENTS.md").resolve()

    assert (package_root / "__init__.py").is_file()
    assert (package_root / "__main__.py").is_file()
    assert (package_root / "shared" / "__init__.py").is_file()
    assert (package_root / "shared" / "logging" / "__init__.py").is_file()
    assert (package_root / "shared" / "shortcuts" / "__init__.py").is_file()
    assert (package_root / "shared" / "subprocess.py").is_file()

    assert (target_root / "tools" / "__init__.py").is_file()
    assert (target_root / "tools" / "linting" / "__init__.py").is_file()
    assert (target_root / "shared_tests" / "__init__.py").is_file()
    assert (target_root / "tests" / "test_main.py").is_file()

    pyproject = (target_root / "pyproject.toml").read_text(encoding="utf-8")
    assert f'packages = ["src/{package_name}"]' in pyproject


def write_fake_source(source_root: Path) -> None:
    (source_root / "templates" / "src" / "todo_package_name").mkdir(parents=True)
    (source_root / "templates" / "tests").mkdir(parents=True)
    (source_root / "templates" / ".github" / "workflows").mkdir(parents=True)
    (source_root / "shared" / "logging").mkdir(parents=True)
    (source_root / "shared" / "shortcuts").mkdir(parents=True)
    (source_root / "tools" / "linting").mkdir(parents=True)
    (source_root / "shared_tests").mkdir(parents=True)
    (source_root / "rules").mkdir()

    (source_root / "templates" / "AGENTS.md").write_text("# Agent Guide\n", encoding="utf-8")
    (source_root / "templates" / "pyproject.toml").write_text(
        '[project]\nname = "TODO_PROJECT_NAME"\n\n'
        '[tool.hatch.build.targets.wheel]\npackages = ["src/todo_package_name"]\n\n'
        '[tool.poe.tasks]\napp = "python -m todo_package_name"\n',
        encoding="utf-8",
    )
    (source_root / "templates" / "pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    (source_root / "templates" / "src" / "todo_package_name" / "__init__.py").write_text(
        '__version__ = "0.1.0"\n',
        encoding="utf-8",
    )
    (source_root / "templates" / "src" / "todo_package_name" / "__main__.py").write_text(
        "def main() -> int:\n    return 0\n",
        encoding="utf-8",
    )
    (source_root / "templates" / "tests" / "test_main.py").write_text(
        "from todo_package_name.__main__ import main\n\n\ndef test_main() -> None:\n    assert main() == 0\n",
        encoding="utf-8",
    )
    (source_root / "templates" / "gitignore").write_text(".venv/\n", encoding="utf-8")
    (source_root / "templates" / "vscode_settings.json").write_text("{}\n", encoding="utf-8")
    (source_root / "templates" / "vscode_extensions.json").write_text("{}\n", encoding="utf-8")
    (source_root / "templates" / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")

    (source_root / "shared" / "__init__.py").write_text("", encoding="utf-8")
    (source_root / "shared" / "logging" / "__init__.py").write_text("", encoding="utf-8")
    (source_root / "shared" / "shortcuts" / "__init__.py").write_text("", encoding="utf-8")
    (source_root / "shared" / "subprocess.py").write_text(
        "def run_subprocess_with_capture() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (source_root / "tools" / "__init__.py").write_text("", encoding="utf-8")
    (source_root / "tools" / "linting" / "__init__.py").write_text("", encoding="utf-8")
    (source_root / "shared_tests" / "__init__.py").write_text(
        "from shared.logging import setup_file_logging\n"
        "from shared.shortcuts import ShortcutManager\n"
        "from shared.subprocess import run_subprocess_with_capture\n"
        "from your_app.shared.shortcuts import keep_as_is\n",
        encoding="utf-8",
    )
    (source_root / "rules" / "coding_rules.md").write_text("# Rules\n", encoding="utf-8")


def write_fake_uv(fake_bin: Path, uv_log: Path) -> None:
    fake_bin.mkdir()
    (fake_bin / "uv").write_text(
        f'#!/usr/bin/env bash\nset -euo pipefail\nprintf \'%s\\n\' "$*" >> "{uv_log}"\n',
        encoding="utf-8",
    )
    os.chmod(fake_bin / "uv", 0o755)


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

    write_fake_source(source_root)
    write_fake_uv(fake_bin, uv_log)

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

    shared_tests_init = (target_root / "shared_tests" / "__init__.py").read_text(encoding="utf-8")
    assert "from todo_package_name.shared.logging import setup_file_logging" in shared_tests_init
    assert "from todo_package_name.shared.shortcuts import ShortcutManager" in shared_tests_init
    assert "from todo_package_name.shared.subprocess import run_subprocess_with_capture" in shared_tests_init

    assert uv_log.read_text(encoding="utf-8").splitlines() == [
        "sync",
        "run poe lint_full",
        "run poe test",
    ]


def test_bootstrap_shell_script_renders_package_name_override(tmp_path: Path) -> None:
    bootstrap_script = resolve_bootstrap_script()
    source_root = tmp_path / "source_repo"
    target_root = tmp_path / "renamed_repo"
    fake_bin = tmp_path / "bin"
    uv_log = tmp_path / "uv.log"

    write_fake_source(source_root)
    write_fake_uv(fake_bin, uv_log)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = subprocess.run(
        ["bash", "-s", "--", "--package-name", "acme", str(source_root), str(target_root)],
        input=bootstrap_script.read_text(encoding="utf-8"),
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert_bootstrapped_layout(target_root, package_name="acme")
    assert not (target_root / "src" / "todo_package_name").exists()

    test_main = (target_root / "tests" / "test_main.py").read_text(encoding="utf-8")
    assert "from acme.__main__ import main" in test_main
    assert "todo_package_name" not in test_main

    pyproject = (target_root / "pyproject.toml").read_text(encoding="utf-8")
    assert "python -m acme" in pyproject
    assert "todo_package_name" not in pyproject

    shared_tests_init = (target_root / "shared_tests" / "__init__.py").read_text(encoding="utf-8")
    assert "from acme.shared.logging import setup_file_logging" in shared_tests_init
    assert "from acme.shared.shortcuts import ShortcutManager" in shared_tests_init
    assert "from acme.shared.subprocess import run_subprocess_with_capture" in shared_tests_init
    assert "from your_app.shared.shortcuts import keep_as_is" in shared_tests_init
    assert "from shared.logging" not in shared_tests_init


def test_bootstrap_shell_script_rejects_invalid_package_name(tmp_path: Path) -> None:
    bootstrap_script = resolve_bootstrap_script()
    source_root = tmp_path / "source_repo"
    target_root = tmp_path / "bad_repo"

    write_fake_source(source_root)

    result = subprocess.run(
        ["bash", str(bootstrap_script), "--package-name", "not-valid!", str(source_root), str(target_root)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Invalid package name" in result.stderr
    assert not target_root.exists()


def test_bootstrap_shell_script_rejects_python_keyword(tmp_path: Path) -> None:
    bootstrap_script = resolve_bootstrap_script()
    source_root = tmp_path / "source_repo"
    target_root = tmp_path / "keyword_repo"

    write_fake_source(source_root)

    result = subprocess.run(
        ["bash", str(bootstrap_script), "--package-name", "class", str(source_root), str(target_root)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Python keyword" in result.stderr
    assert not target_root.exists()


def test_bootstrap_shell_script_help_exits_zero() -> None:
    bootstrap_script = resolve_bootstrap_script()

    result = subprocess.run(["bash", str(bootstrap_script), "--help"], capture_output=True, text=True)

    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "--package-name" in result.stdout
