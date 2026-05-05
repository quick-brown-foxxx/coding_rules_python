# Project Audit — Issue Tracker

## CRITICAL

- [x] **C1.** ~~`except` clause syntax bug (`reusable/linting/lint_utils.py:48`).~~ **Fixed.**
- [x] **C2.** ~~Own code uses `Any` and `cast()` in shortcuts.~~ **Fixed** — removed `Any`/`cast` imports, use isinstance narrowing.
- [x] **C3.** ~~Wrong PEP number everywhere.~~ **Fixed** — PEP 722 → PEP 723 in all docs.
- [ ] **C4.** `rusty-results` is a critical architectural risk — tiny library (3 releases), minimal adoption, no maintenance signal. Entire error-handling philosophy depends on it. No wrapping guidance. **Confirmed bad decision.** Need to evaluate alternatives: `result` library, hand-rolled Result type, or other. **HIGH effort — needs design decision, affects all docs/skills/rules/examples.**
- [x] **C5.** ~~No tests for `lint_utils.py`.~~ **Fixed** — 24 unit tests added.
- [x] **C6.** ~~Unsound `TypeIs` guard examples.~~ **Fixed** — added "simplified for brevity" caveat noting msgspec.convert() for production.

## IMPORTANT — Code Fixes

- [x] **I1.** ~~`_is_final_annotation` doesn't handle `typing.Final` attribute form.~~ **Fixed** — also moved to `lint_utils.py` (I4).
- [x] **I2.** ~~`_is_mutable_value` misses qualified constructor calls.~~ **Fixed.**
- [x] **I3.** ~~`_is_dataclass_decorator` misses bare `@dataclasses.dataclass`.~~ **Fixed.**
- [x] **I4.** ~~Duplicated `_is_final_annotation`.~~ **Fixed** — deduplicated into `lint_utils.py`.
- [x] **I5.** ~~`write_error` color detection uses wrong stream.~~ **Fixed** — stream param now configurable.
- [x] **I6.** ~~`ColoredFormatter` created on every call.~~ **Fixed** — cached per stream.
- [x] **I7.** ~~`tomli` dependency redundant.~~ **Fixed** — replaced with stdlib `tomllib`.
- [x] **I8.** ~~`_validate_key_sequence` exported with type: ignore.~~ **Fixed** — renamed to `validate_key_sequence`.

## IMPORTANT — Test Fixes

- [x] **T1.** ~~Tautological assertions.~~ **Fixed** — now assert `result.is_err`.
- [x] **T2.** ~~Linting assertions use `>=`.~~ **Fixed** — exact `==` counts.
- [x] **T3.** ~~Relative `FIXTURES` path fragile.~~ **Fixed** — uses `Path(__file__).resolve()`.
- [x] **T4.** ~~No tests for `reusable/logging/` — zero coverage.~~ **Fixed** — added focused regression coverage in `reusable_tests/test_logging_reusable.py` for stdout/file handler level behavior.
- [x] **T5.** ~~`ShortcutManager.load()` caching untested.~~ **Fixed** — caching + reload test added.
- [x] **T6.** ~~No edge case fixtures for linters.~~ **Fixed** — 5 edge case fixtures + tests added.
- [x] **T7.** ~~Tests never verify reported line numbers.~~ **Fixed** — line number assertions added to all fail tests.
- [x] **T8.** ~~`_run` helper duplicated across 5 test files.~~ **Fixed** — extracted to `conftest.py`.

## IMPORTANT — Docs Consistency

- [x] **D1.** ~~Domain object example missing `frozen=True`.~~ **Fixed.**
- [x] **D2.** ~~`reportImportCycles=error` missing from full rules and skill.~~ **Fixed.**
- [x] **D3.** ~~Template `pre-commit-config.yaml` missing 2 hooks.~~ **Fixed.**
- [x] **D4.** ~~Template `pyproject.toml` missing `msgspec` dependency.~~ **Fixed** — added as commented-out.
- [x] **D5.** ~~README structure listing outdated.~~ **Fixed** — added `docs/`, `pyproject.toml`, `uv.lock`.
- [x] **D6.** ~~`asyncio.get_event_loop()` deprecated.~~ **Fixed** — `get_running_loop()`.
- [x] **D7.** ~~`Path("~/.config/app")` examples missing `.expanduser()`.~~ **Fixed.**

## CONCERNING — Needs Design Thinking

- [ ] **X1.** Result pattern verbosity — no `map`/`and_then` chaining shown. More verbose than try/except for multi-step operations. Tied to C4. **Needs design decision.**
- [ ] **X2.** "All I/O should be async" is overly broad — Python asyncio has no true async file I/O. Docs never mention aiofiles. **Needs guidance rewrite.**
- [ ] **X3.** `frozen=True` friction undocumented — ORMs, incremental construction, state machines. **Needs "when to opt out" section.**
- [ ] **X4.** `Any`/`cast()` ban pragmatism — numpy/pandas/SQLAlchemy stubs return Any. **Needs "ecosystem exceptions" guidance.**
- [x] **X5.** ~~`requires-python >= 3.14` aggressive for reusable repo.~~ **Decided: 3.14 is fine.**
- [ ] **X6.** `sys.argv` length heuristic for GUI vs CLI (building-multi-ui-apps skill) — fragile. **Needs better pattern.**
- [ ] **X7.** Testing skill recommends `subprocess.run()` but async rules ban it. **Needs explicit carve-out for test code.**

## LOW / NITPICK

- [ ] **L1.** `ShortcutConfig._TOML_HEADER` missing `ClassVar` annotation
- [ ] **L2.** `ShortcutManager` could be a dataclass per philosophy
- [ ] **L3.** `find | xargs` in poe tasks breaks on filenames with spaces
- [ ] **L4.** `lint_full` poe task `&&` chaining hides subsequent failures
- [ ] **L5.** `LockManager` in Qt skill has TOCTOU race on lock file
- [ ] **L6.** Missing ruff rules (`PLR`, `FBT`) in script template
- [ ] **L7.** `setting-up-python-projects` skill puts linters under `scripts/` not `shared/linting/`
- [ ] **L8.** `check_raw_dicts.py` doesn't inspect nested classes
- [ ] **L9.** Inconsistent docstring `Usage:` format in check_frozen_dataclasses.py
- [ ] **L10.** Skills examples use bare `@dataclass` without frozen/slots (acceptable for brevity)
- [ ] **L11.** Short rules omit Qt camelCase naming exception
- [ ] **L12.** `writing-python-code` TYPE_CHECKING section wording could confuse
- [ ] **L13.** `templates/AGENTS.md` omits 2 skills from list
- [ ] **L14.** Template linter paths reference `reusable/` instead of project-local path
- [ ] **L15.** `check_object_annotations.py` doesn't handle qualified container names
- [ ] **L16.** No test for `ShortcutConfig.save()` failure path
- [ ] **L17.** No test for `ShortcutManager` with empty `default_shortcuts`
- [ ] **L18.** `msgspec` YAML config workflow never shown end-to-end
- [ ] **L19.** No lockfile/reproducible builds guidance despite mandating `uv`

---

## Fix Plan

### Phase 1: Quick Fixes ✅ COMPLETE

All 21 items fixed: C1, C3, I1–I8, T1–T3, T8, D1–D7. Tests pass (54/54), ruff clean, custom linters clean.

### Phase 2: Medium Fixes ✅ COMPLETE

All 6 items fixed: C2, C5, C6, T5, T6, T7. Tests pass (84/84), ruff clean.

Follow-up verification pass also fixed two latent linter logic bugs discovered during independent review:
- narrowed the `Coroutine[...]` exemption in `check_object_annotations.py` to only `Coroutine[object, None, T]`
- fixed `check_module_mutables.py` so `if TYPE_CHECKING:` only exempts the `if` body, not the runtime `else:` branch

Manual/runtime validation pass additionally:
- fixed `setup_stdout_logging()` so the configured level is applied to the stdout handler
- added regression coverage for reusable logging
- validated custom linters with temporary mock files and real repo task execution
- confirmed `lint_full` passes end-to-end

Final verification after follow-up:
- 96/96 tests pass
- `poe lint_full` passes
- ruff passes
- basedpyright passes
- custom linters pass
- manual validation of shortcuts, logging, and linting completed
- independent read-only review found no remaining must-fix issues before commit

### Phase 3: Design Decisions (need brainstorming before implementation)

- [ ] C4 — `rusty-results` replacement strategy: evaluate `result` lib, hand-rolled type, or other
- [ ] X1 — Result pattern ergonomics: `map`/`and_then` chaining, conciseness guidance (tied to C4)
- [ ] X2 — Rewrite async guidance: acknowledge no true async file I/O, mention aiofiles, be more nuanced
- [ ] X3 — Add "when to opt out of `frozen=True`" section (ORMs, incremental construction, state machines)
- [ ] X4 — Add "ecosystem exceptions" for `Any`/`cast()` ban (numpy, pandas, SQLAlchemy)
- [ ] X6 — Replace `sys.argv` length heuristic with better GUI/CLI detection
- [ ] X7 — Add explicit carve-out allowing `subprocess.run()` in test code

### Phase 4: Low Priority (fix opportunistically)

- [ ] L1 through L19 — address when touching related code
