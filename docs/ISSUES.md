# Project Issues and Planning

## Release validation status

Current HEAD has been validated with:
- `poe lint_full`
- `pytest reusable_tests/`
- `ruff check .`
- `basedpyright`
- direct runs of all custom linters on repo code
- manual temp-file validation for custom linter edge cases
- manual temp-app validation for logging and shortcuts
- disposable-worktree release smoke:
  - import smoke
  - copy-paste consumer smoke for reusable modules
  - Qt shortcut integration smoke
  - poe-task smoke with filenames containing spaces

At the time this file was last updated, these checks were green.

## Open critical design issue

- **C4 — Replace `rusty-results`**
  - Current state: the repo’s error-handling philosophy depends on `rusty-results`.
  - Risk: tiny ecosystem footprint and low confidence as a long-term foundation.
  - Needed next step: choose a replacement strategy before further philosophy/docs work.
  - Options to evaluate:
    - adopt a more established library
    - hand-roll a minimal internal `Result` type
    - partially retreat from Result-first guidance where Python ergonomics are poor

## Open design / guidance work

- **X1 — Result ergonomics after C4**
  - Define the recommended style for multi-step flows.
  - Need guidance on verbosity, chaining, and when `try/except` is still better.

- **X2 — Async guidance is too broad**
  - Current docs overstate “all I/O should be async”.
  - Need a more accurate rule for file I/O, subprocesses, and practical app structure.

- **X3 — `frozen=True` opt-out guidance**
  - Keep immutable-by-default stance, but document when mutable dataclasses are acceptable.
  - Examples to cover: builders, explicit accumulation, stateful lifecycle objects, framework constraints.

- **X4 — Practical exceptions for `Any` / `cast()`**
  - Core stance should stay strict, but docs need a realistic policy for weakly typed third-party ecosystems.
  - Especially relevant for scientific / ORM / legacy library boundaries.

- **X6 — Better GUI/CLI entry selection pattern**
  - Replace the fragile `len(sys.argv) > 1` heuristic in multi-UI guidance.

- **X7 — Explicit sync carve-out for test code**
  - Document that `subprocess.run()` and similar sync patterns are acceptable in tests/harness code.

## Low-priority backlog

- **L1** — Add `ClassVar` annotation for `ShortcutConfig._TOML_HEADER`
- **L2** — Re-evaluate whether `ShortcutManager` should remain a normal class or become a dataclass
- **L4** — Reconsider whether `lint_full` should continue stopping on first failing stage via `&&`
- **L5** — Improve `LockManager` race-safety in Qt skill examples
- **L6** — Revisit missing `PLR` / `FBT` in the script template if those rules remain part of the standard
- **L7** — Re-check project-layout guidance for where copied linters should live
- **L8** — Consider nested-class support in `check_raw_dicts.py`
- **L9** — Normalize `Usage:` formatting across linter module docstrings
- **L10** — Decide whether any skill examples should be expanded for stronger dataclass consistency, or remain intentionally brief
- **L11** — Decide whether the short rules need the Qt camelCase exception
- **L12** — Reword the `TYPE_CHECKING` guidance in `writing-python-code` if it still feels ambiguous
- **L13** — Revisit omitted skills in `templates/AGENTS.md`
- **L14** — Revisit template path guidance for copied linter locations
- **L15** — Consider qualified-container support in `check_object_annotations.py`
- **L16** — Add save-failure coverage for `ShortcutConfig`
- **L17** — Add explicit empty-default-shortcuts coverage for `ShortcutManager`
- **L18** — Add a concrete YAML + `msgspec` end-to-end example
- **L19** — Add lockfile / reproducible-build guidance for `uv`

## Suggested next planning order

1. **C4 + X1 together** — choose the future of Result-style guidance first
2. **X2 + X7 together** — rewrite async/subprocess guidance coherently
3. **X3 + X4 together** — add pragmatic exceptions without weakening the core philosophy too much
4. **X6** — clean up multi-UI app entry guidance
5. Low-priority backlog opportunistically
