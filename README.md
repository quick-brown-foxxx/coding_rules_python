# Python Coding Standards

Personal Python development standards, templates, and AI skills.

## Structure

```
PHILOSOPHY.md          Core beliefs — every other doc inherits from this

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
  writing-python-code/          High-level routing skill
  write-single-python-script/   PEP 722 single-file scripts
  setup-python-project/         New project bootstrap
  working-with-qt/              PySide6 desktop apps
  python-error-handling/        Result pattern
  python-testing-lightweight/   Standard pytest setup
  python-testing-heavyweight/   Containerized testing
  multi-ui-architecture/        GUI + CLI + API

guides/                Detailed reference docs
  type-system.md         Type safety patterns
  async-patterns.md      Async + Qt integration
  testing-lightweight.md Pytest setup & fixtures
  testing-heavyweight.md Containers & mock servers
  qt-patterns.md         Signals, wrappers, managers
  project-layout.md      Full project vs single script
  other-patterns.md      J2, platform abstraction, security, logging
```

## How to Use

### Starting a new project

1. Read `PHILOSOPHY.md` for the mindset
2. Decide: single script or full project? (see `guides/project-layout.md`)
3. Copy relevant files from `templates/` into your project
4. Copy `rules/coding_rules.md` (or `_short`) into `docs/`
5. Fill in TODO sections in `AGENTS.md` and `pyproject.toml`
6. Run `uv sync && uv run pre-commit install`

### For AI agents

Deploy skills from `skills/` to `~/.claude/skills/`. The top-level `writing-python-code` skill routes to specific skills based on task type.

### Quick reference

- **What tools?** uv, basedpyright (strict), ruff, pytest, poethepoet
- **Error handling?** `Result[T, E]` from rusty-results. Exceptions = bugs only.
- **CLI?** typer (argparse only for stdlib-only scripts)
- **GUI?** PySide6 + qasync
- **Text output?** Jinja2
- **Tests?** E2e > unit. Real > mocked. Trustworthiness > coverage.
