# Coding Rules (Short Version)

For single-file scripts and small projects. See [full version](https://github.com/quick-brown-foxxx/coding_rules_python/blob/master/rules/coding_rules.md) for details.

---

## Type Safety

- basedpyright strict mode, `reportAny=error`, `reportImportCycles=error`
- Type annotations on all functions
- No `Any`, no `typing.cast()`, no blanket `# type: ignore`
- `object` restricted to boundary positions (TypeIs guards, signal handlers, coroutine params)
- `msgspec.Struct` for external data (JSON, configs, APIs), `dataclass(frozen=True)` for domain objects
- `NewType` for domain identifiers (ProfileId, UserId) — prevent mixing
- Immutable by default: `frozen=True`, `tuple` over `list`, `Sequence` in params
- Max 5 function parameters; no boolean flag params

## Error Handling

- `Result[T, E]` from `rusty-results` for expected failures (IO, user input, network)
- Exceptions only for programming errors (bugs, impossible states)
- Catch third-party exceptions at the boundary, wrap in `Result`
- Early returns: handle error first, keep success path linear

## Style

- Line length: 120. Double quotes. 4-space indent.
- Naming: `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE` constants
- Google-style docstrings on public functions
- Comments explain "why", not "what"

## Tooling

- `uv` for deps and execution
- `ruff` for linting + formatting
- `basedpyright` for type checking
- `pytest` for testing
- Run `uv run poe lint_full` before committing

## Commits

Format: `<type>(<scope>): <subject>`
Types: feat, fix, docs, style, refactor, perf, test, chore
