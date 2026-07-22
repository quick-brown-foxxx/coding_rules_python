# Python Auxiliary Skills for myai

**Prerequisite: [myai](https://github.com/quick-brown-foxxx/myai) must be installed first.**

This repo is an **auxiliary skill pack** for the myai agent skill system. myai provides 40+ language-agnostic skills covering the full SDLC (engineering principles, planning, implementation, testing, debugging, review, CI/CD, security, performance, agent orchestration). This repo adds the Python-specific layer: tooling choices, library patterns, and Python conventions.

Think of it as: **myai = the engine and chassis; this repo = the Python body kit.** The generic philosophy lives in myai's `engineering-principles` skill. The skills here keep only Python-specific content and reference myai for everything else.

Not intended for any third-party use but I will be glad if someone will find it at least inspirational.

## The Auxiliary Model

Each Python skill here extends one or more myai parent skills. The load order is:

1. `using-my-skills` (myai bootstrap, auto-injected)
2. `engineering-principles` (myai — language-agnostic philosophy)
3. Relevant myai workflow skill (e.g., `architecting-changes`, `test-driven-development`)
4. Python-specific extension from this repo (e.g., `writing-python-code`, `testing-python`)

The 9 Python skills and their myai parents

| Python Skill | myai Parent(s) |
|---|---|
| `writing-python-code` | `engineering-principles` |
| `testing-python` | `high-level-testing-strategy`, `test-driven-development`, `manual-testing` |
| `architecting-python-changes` | `architecting-changes` |
| `setting-up-python-projects` | `engineering-principles`, `setting-up-projects` |
| `setting-up-python-backends` | `engineering-principles`, `architecting-changes`, `setting-up-backends` |
| `setting-up-logging` | `engineering-principles` |
| `setting-up-shortcuts` | `engineering-principles` |
| `building-multi-ui-apps` | `architecting-changes` |
| `building-qt-apps` | `architecting-changes`, `engineering-principles` |

## Most important stuff

```
shared/                Copy-paste reusable code for new projects
  logging/               Logging setup + colored non-log output
  shortcuts/             Keyboard shortcuts manager (PySide6 + TOML)
  linting/               Custom lint checks (AST-based)

shared_tests/          Tests for shared/ code
 ...

rules/                 Copy-paste rule files for projects
  coding_rules.md        Full coding standards.
  coding_rules_short.md  Condensed version for scripts

templates/             Copy into new projects, fill TODOs
  AGENTS.md              AI agent guide template
  pyproject.toml         Full tooling config
  pre-commit-config.yaml Git hooks
  ...

skills/                Claude Code skills (deploy to ~/.claude/skills/)
 ...
```

## How to Use

### Install

`npx -y skills add quick-brown-foxxx/coding_rules_python`

Note: `skills` updates detection has bugs, more reliable is to do force add from time to time. Eg for all skills in current project for specified agents:

`npx -y skills add quick-brown-foxxx/coding_rules_python -s "*" -a claude-code universal kilo codex opencode -y`

### Shared building blocks

The `shared/` folder contains copy-paste building blocks for new projects, not an installable library. Copy the directories you need into the new repo's top-level `shared/` and `shared_tests/` directories and update imports if the package name changes. The template `pyproject.toml` includes the dependencies needed for a full `shared/` + `shared_tests/` copy; trim unused modules and deps afterward if you do not need them.

### Starting a new project

1. Read myai's canonical `engineering-principles` skill for the mindset
2. Decide: single script, general Python project, or backend/service repo? (use `writing-scripts` (myai) for scripts, `setting-up-python-projects` for general packages/apps, and `setting-up-python-backends` for service/API repos)
3. Promote template files into place: `AGENTS.md`, `pyproject.toml`, `.pre-commit-config.yaml`, `.gitignore`, and `.vscode/`
   Shortcut: `skills/setting-up-python-projects/bootstrap_downstream_repo.sh SOURCE_REPO TARGET_REPO`
4. Copy `shared/` and `shared_tests/` into the new project root
5. Copy `rules/coding_rules.md` (or `_short`) into `docs/`
6. Create `CLAUDE.md` symlink → `AGENTS.md` (Claude Code reads `CLAUDE.md`)
7. Fill in TODO sections in `AGENTS.md` and `pyproject.toml`
8. Run `uv sync --all-extras --group dev`, then verify with `uv run poe lint_full` and `uv run poe test`

From this point on, prefer project-local commands through `uv` rather than system-installed tools: `uv run pytest`, `uv run ruff`, `uv run basedpyright`, `uv run poe`, `uv run python`, `uv run pre-commit`. In practice, the baseline verification flow is `uv run poe lint_full` (basedpyright + Ruff check/format + custom linters) followed by `uv run poe test`.

### For AI agents

Deploy skills from `skills/` to `~/.claude/skills/`. Load `architecting-python-changes` when a feature, fix, or refactor may require architecture decisions, then follow it to the right existing docs and domain skills. For new backend repos, start with `setting-up-python-backends`, then use `setting-up-python-projects` for generic bootstrap pieces as needed. Load `building-backends` (myai) for backend structure decisions and `writing-python-code` for the actual Python editing rules.

### Quick reference

- **What tools?** uv, basedpyright (strict), Ruff with strict profile, pytest, poethepoet, msgspec
- **How to run them?** Through `uv` (`uv run ...`), not global/system binaries.
- **Error handling?** `Result[T, E]` from rusty-results. Rusty-results is nice for our use case and we will use it, but it is not maintained and may require replacement in future. Exceptions = bugs only.
- **Data validation?** `msgspec.Struct` for configs and non-framework external data. In FastAPI apps, use `pydantic` at the HTTP edge and convert immediately into framework-free typed structures.
- **CLI?** typer (argparse only for stdlib-only scripts)
- **GUI?** PySide6 + qasync (not QtAsyncio — still in technical preview)
- **Text output?** Jinja2
- **Tests?** E2e > unit. Real > mocked. Trustworthiness > coverage.
