---
name: repair-opencode-kilo-python-lsp-diagnostics
description: >-
  Use this skill if you see library resolution errors when doing Python file reads or writes via the edit tool. This may mean that your built-in LSP is misbehaving.
  Note: this is ONLY for Kilo/opencode. Repair the Kilo/opencode LSP (pyright) so Python third-party imports resolve correctly.
---

# Repair Opencode/Kilo Python LSP Diagnostics

## Scope

This skill is **only for Kilo and opencode** (which share the same core). It does not apply to Claude Code, Codex, or other agents.

## Symptom

While reading or editing Python files through the edit tool, the built-in LSP reports failed third-party library resolution:

    Import "fastapi" could not be resolved from source
    Import "pytest" could not be resolved
    ...

These come from the agent harness's LSP, not from your own verification. The code may be fine — the LSP is just misconfigured.

## Root Cause

Kilo/opencode sends the venv interpreter as a **top-level** `initialization.pythonPath`, but pyright only reads the venv from `python.pythonPath` or from the `[tool.pyright]` config section. So pyright falls back to the system Python and cannot resolve third-party imports that live only in the project venv. Builtins and local imports still resolve.

## Config Section Rule

Both pyright and basedpyright read `[tool.pyright]`; basedpyright additionally reads `[tool.basedpyright]`. A single config file must contain only one of the two sections — having both is not supported. `[tool.pyright]` is therefore the canonical section: it serves both tools without conflicts.

## Repair Procedure

When you encounter failed resolution errors on a project and it does NOT yet have the fix:

1. **Install dependencies** so the venv exists and has the third-party packages:
   ```bash
   uv sync --all-groups
   ```

2. **Verify a clean CLI check passes** (this isolates the problem to the LSP, not the code):
   ```bash
   uv run basedpyright   # or: uv run pyright
   ```
   If the CLI check is clean but the edit-tool LSP still reports unresolved imports, the LSP config is the problem.

3. **Apply the fix** in `pyproject.toml`. The end state is a single `[tool.pyright]` section:
   - If `[tool.basedpyright]` is present, rename that section to `[tool.pyright]` and keep all its keys and values unchanged.
   - If neither section is present, add:
     ```toml
     [tool.pyright]
     venvPath = "."
     venv = ".venv"
     ```
     Relative paths resolve against the config file (project root), so this is shared across devs.

4. **Do NOT block on a session reload.** Finish your task normally. The fix only takes effect in the LSP after the session is restarted, so in your final message just report that you fixed the LSP config and recommend the user restart the session/chat.

## Important

- Never leave `[tool.pyright]` and `[tool.basedpyright]` in the same config file — that combination is not supported. Rename the section; do not add a second one.
- If the project already has the correct single `[tool.pyright]` section and you are in a fresh session, the "failed resolution" reports from the edit-tool LSP are known false positives — **ignore them**.
- The fix is in-repo and machine-independent (`venvPath`/`venv` relative to the config file). Do not put absolute machine-specific paths into the repo.

## Verification

- Correct diagnosis: clean `uv run basedpyright` CLI result + unresolved imports in the edit-tool LSP = LSP config issue, apply the fix.
- After applying the fix, re-run `uv run basedpyright` and confirm it stays clean — both tools read the `[tool.pyright]` section. The LSP will be clean only after the user restarts the session — state this in your final message.
