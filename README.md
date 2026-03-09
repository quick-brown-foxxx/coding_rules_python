# Python Coding Standards

Personal Python development standards, templates, and AI skills.

## Structure

```
PHILOSOPHY.md          Core beliefs — every other doc inherits from this

reusable/              Copy-paste reusable code (shadcn-ui style)
  logging/               Logging setup + colored non-log output
  shortcuts/             Keyboard shortcuts manager (PySide6 + TOML)

reusable_tests/        Tests for reusable/ code
  test_shortcuts_base.py   Generic shortcut config tests
  test_shortcuts_manager.py  ShortcutManager tests

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
  writing-python-scripts/       PEP 722 single-file scripts
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

### Reusable code (shadcn-ui style)

The `reusable/` folder contains copy-paste components — not an installable library. Copy what you need into your project's `shared/` directory and update import paths. Each module is self-contained and documented.

### Starting a new project

1. Read `PHILOSOPHY.md` for the mindset
2. Decide: single script or full project? (see `writing-python-scripts` or `setting-up-python-projects` skills)
3. Copy relevant files from `templates/` into your project
4. Copy `rules/coding_rules.md` (or `_short`) into `docs/`
5. Copy `PHILOSOPHY.md` into `docs/` (referenced by AGENTS.md)
6. Create `CLAUDE.md` symlink → `AGENTS.md` (Claude Code reads CLAUDE.md; the `@docs/PHILOSOPHY.md` import in AGENTS.md auto-loads philosophy into context)
7. Fill in TODO sections in `AGENTS.md` and `pyproject.toml`
8. Run `uv sync && uv run pre-commit install`

### For AI agents

Deploy skills from `skills/` to `~/.claude/skills/`. The top-level `writing-python-code` skill covers core standards; other skills cover specific domains.

### Quick reference

- **What tools?** uv, basedpyright (strict), ruff, pytest, poethepoet, msgspec
- **Error handling?** `Result[T, E]` from rusty-results. Exceptions = bugs only.
- **Data validation?** `msgspec.Struct` for external data (JSON, configs, APIs). Validates at decode time.
- **CLI?** typer (argparse only for stdlib-only scripts)
- **GUI?** PySide6 + qasync (not QtAsyncio — still in technical preview)
- **Text output?** Jinja2
- **Tests?** E2e > unit. Real > mocked. Trustworthiness > coverage.
