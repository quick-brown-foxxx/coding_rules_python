# Python Coding Standards

Personal Python development standards, templates, and AI skills.

Not intended for any third-party use but I will be glad if someone will find it at least inspirational.

## Structure

```
PHILOSOPHY.md          Core beliefs — every other doc inherits from this
pyproject.toml         Project config (deps, tooling)
uv.lock                Locked dependency versions

shared/                Copy-paste reusable code for new projects
  logging/               Logging setup + colored non-log output
  shortcuts/             Keyboard shortcuts manager (PySide6 + TOML)
  linting/               Custom lint checks (AST-based)
    lint_utils.py          Shared utilities (file collection, ignore handling)
    check_frozen_dataclasses.py  Enforce frozen=True on all dataclasses
    check_ignored_results.py     Catch common ignored Result-returning calls
    check_module_mutables.py     Ban module-level mutable state
    check_object_annotations.py  Restrict object to boundary positions
    check_type_ignore.py         Require rationale on type:ignore comments
    check_raw_dicts.py           Ban raw dict annotations in business code

shared_tests/          Tests for shared/ code
  test_shortcuts_base.py   Generic shortcut config tests
  test_shortcuts_manager.py  ShortcutManager tests
  test_linting/            Tests for custom lint checks
    test_check_frozen_dataclasses.py
    test_check_module_mutables.py
    test_check_object_annotations.py
    test_check_raw_dicts.py
    test_check_type_ignore.py

rules/                 Copy-paste rule files for projects
  coding_rules.md        Full coding standards.
  coding_rules_short.md  Condensed version for scripts

templates/             Copy into new projects, fill TODOs
  AGENTS.md              AI agent guide template
  pyproject.toml         Full tooling config
  pre-commit-config.yaml Git hooks
  gitignore              Python .gitignore
  vscode_settings.json   Editor config
  vscode_extensions.json Recommended extensions

skills/                Claude Code skills (deploy to ~/.claude/skills/)
  writing-python-code/          Core Python: typing, errors, async, style, security
  writing-python-scripts/       PEP 723 single-file scripts
  setting-up-python-projects/   New project bootstrap
  building-qt-apps/             PySide6 desktop apps
  testing-python/               Pytest setup, fixtures, containerized testing
  building-multi-ui-apps/       GUI + CLI + API architecture
  setting-up-logging/           Colored logging with colorlog
  setting-up-shortcuts/         PySide6 keyboard shortcuts

notes/                Project-specific personal notes
  other-patterns.md      Localization, config merging + msgspec validation
```

## How to Use

### Install

`npx -y skills add quick-brown-foxxx/coding_rules_python`

Note: `skills` updates detection has bugs, more reliable is to do force add from time to time. Eg for all skills in current project for specified agents:

`npx -y skills add quick-brown-foxxx/coding_rules_python -s "*" -a claude-code universal kilo codex opencode -y`

### Shared building blocks

The `shared/` folder contains copy-paste building blocks for new projects, not an installable library. Copy the directories you need into the new repo's top-level `shared/` and `shared_tests/` directories and update imports if the package name changes. The template `pyproject.toml` includes the dependencies needed for a full `shared/` + `shared_tests/` copy; trim unused modules and deps afterward if you do not need them.

### Starting a new project

1. Read `PHILOSOPHY.md` for the mindset
2. Decide: single script or full project? (see `writing-python-scripts` or `setting-up-python-projects` skills)
3. Promote template files into place: `AGENTS.md`, `pyproject.toml`, `.pre-commit-config.yaml`, `.gitignore`, and `.vscode/`
   Shortcut: `skills/setting-up-python-projects/bootstrap_downstream_repo.sh SOURCE_REPO TARGET_REPO`
4. Copy `shared/` and `shared_tests/` into the new project root
5. Copy `rules/coding_rules.md` (or `_short`) into `docs/` and copy `PHILOSOPHY.md` to `docs/PHILOSOPHY.md`
6. Create `CLAUDE.md` symlink → `AGENTS.md` (Claude Code reads CLAUDE.md; the `@docs/PHILOSOPHY.md` import in AGENTS.md auto-loads philosophy into context)
7. Fill in TODO sections in `AGENTS.md` and `pyproject.toml`
8. Run `uv sync --all-extras --group dev`, then verify with `uv run poe lint_full` and `uv run poe test`

From this point on, prefer project-local commands through `uv` rather than system-installed tools: `uv run pytest`, `uv run ruff`, `uv run basedpyright`, `uv run poe`, `uv run python`, `uv run pre-commit`. In practice, the baseline verification flow is `uv run poe lint_full` (basedpyright + Ruff check/format + custom linters) followed by `uv run poe test`.

### For AI agents

Deploy skills from `skills/` to `~/.claude/skills/`. The top-level `writing-python-code` skill covers core standards; other skills cover specific domains.

### Quick reference

- **What tools?** uv, basedpyright (strict), Ruff with the stricter profile (`PLR`, `FBT`, plus the core rules), pytest, poethepoet, msgspec
- **How to run them?** Through `uv` (`uv run ...`), not global/system binaries.
- **Error handling?** `Result[T, E]` from rusty-results. Rusty-results is nice for our use case and we will use it, but it is not maintained and may require replacement in future. Exceptions = bugs only.
- **Data validation?** `msgspec.Struct` for external data (JSON, configs, APIs). Validates at decode time.
- **CLI?** typer (argparse only for stdlib-only scripts)
- **GUI?** PySide6 + qasync (not QtAsyncio — still in technical preview)
- **Text output?** Jinja2
- **Tests?** E2e > unit. Real > mocked. Trustworthiness > coverage.
