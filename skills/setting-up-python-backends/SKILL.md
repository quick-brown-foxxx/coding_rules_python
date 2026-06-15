---
name: setting-up-python-backends
description: >-
  Python-specific extension to myai's `setting-up-backends`.
  ALWAYS LOAD `setting-up-backends` FIRST, AND THAN THIS skill for Python backend tooling.
  Backend/API bootstrap for Python: FastAPI/Django choice, backend repo layout,
  app factory, SQLAlchemy+Alembic, pydantic at edge, migrations, and service-first conventions.
---

# Setting Up Python Backends

## Prerequisites

This is a Python-specific extension to myai's `setting-up-backends`.
**Load `setting-up-backends` first** for the backend architecture philosophy,
directory layout patterns, wiring rules, defer-by-default guidance, and
migrations/operations strategy. This skill provides only Python-specific
framework choices, library selections, and code patterns.

Also requires `engineering-principles` and `architecting-changes` (via myai bootstrap).

This skill is a backend-specialized extension of `setting-up-python-projects`.
Start here for backend repos, then pull generic Python bootstrap pieces from
`setting-up-python-projects` as needed.

## Python Framework Choice

- **FastAPI** is the default boring choice for most service APIs.
- **Django** is justified when auth, admin, sessions, and CRUD-heavy backend surface are obviously large from the start.
- **Starlette** is for deliberate thin-edge builds, not as a default.

## Python Default Stack

- `FastAPI` + `uvicorn`
- `pydantic` models at the FastAPI HTTP edge; `msgspec.Struct` for config and non-framework external payload decoding
- `dataclass(frozen=True, slots=True)` + `Result[T, E]` in the core
- `SQLAlchemy 2` + `Alembic` when the service owns relational persistence
- `httpx` for outbound HTTP
- existing repo logging setup via `shared/logging`
- `pytest`, `pytest-asyncio`, and integration tests through real app wiring
- `uv`, `poethepoet`, `basedpyright`, and `ruff`

Keep `pydantic` request/response DTOs at the HTTP boundary and convert immediately into framework-free typed structures.

## Python Backend Layout

See `setting-up-backends` for the philosophy behind this layout.

```text
src/appname/
  api/
    app.py
    routes/
    schemas/
    errors.py
  domain/
    models.py
    services.py
    errors.py
  infrastructure/
    config.py
    logging.py
    db/
      models.py
      session.py
      queries.py
    clients/
  workers/
    __main__.py
  bootstrap.py
tests/
  integration/
  unit/
  fixtures/
migrations/
```

Omit what you do not need. No DB, no `db/` or `migrations/`. No workers, no `workers/`.

## First Files

- `api/app.py` with `create_app()`
- `api/routes/health.py` with `/healthz`
- `bootstrap.py` with `create_services()` and app wiring
- `domain/models.py` and one small service/use-case module
- `infrastructure/config.py` to parse env into typed settings
- DB files and migrations only if persistence exists
- one smoke API test and one domain test

## Wiring Rules

- `create_app()` assembles only the HTTP layer.
- `bootstrap.py` wires settings, DB/session factories, external clients, and services.
- No DI framework by default. Use constructor injection and one composition root.
- Keep `__main__.py` or ASGI entrypoints thin.

---

## Boundary Rules

- Request/response schemas are not domain models.
- No `Request`, `Response`, `Depends`, ORM session, or framework auth objects in domain services.
- Convert request data and auth/session state at the edge.
- Workers are another adapter, not a separate business-logic stack.
- CLI/admin scripts should call the same core services when they touch the same workflows.
## Python Migrations and Operations

- If the service owns a relational DB, initialize `Alembic` early.
- Add health and readiness endpoints early.
- Keep dev run, lint, test, and migrate commands in Poe tasks.
- Containerize when needed, but keep v1 Linux-first and boring.

## Defer by Default

See `setting-up-backends` for the full defer-by-default philosophy. The list below is the Python ecosystem application:

- queues and background-job stacks
- caching layers
- metrics/tracing vendors
- event buses or CQRS
- multitenancy
- API versioning strategy beyond basic room for growth
- generated SDKs and OpenAPI customization
- Kubernetes-specific guidance

Add those only when the project actually needs them.

## Handoff

- Use `building-backends` (myai) for day-2 backend architecture and service/API/worker shaping.
- Use `building-multi-ui-apps` if API, CLI, and automation share one core.
- Use `writing-python-code` for implementation rules.

## Related Skills

- **`setting-up-backends`** (myai) — Parent skill. Load first for backend architecture philosophy.
- **`engineering-principles`** (myai) — Foundation.
- **`architecting-changes`** (myai) — Architecture decisions.
- **`api-design`** (myai) — Stable API and protocol design.
- **`security-and-hardening`** (myai) — Auth, secrets, boundary hardening.
- **`setting-up-python-projects`** — Generic Python bootstrap pieces (templates, shared code).
- **`building-backends`** (myai) — Day-2 backend architecture.
- **`testing-python`** — Python API/service test setup.
