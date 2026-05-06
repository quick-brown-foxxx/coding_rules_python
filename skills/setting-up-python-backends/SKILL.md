---
name: setting-up-python-backends
description: >-
  ALWAYS LOAD THIS SKILL WHEN BOOTSTRAPPING A NEW PYTHON BACKEND, API SERVICE, OR WEB/WORKER REPO, OR WHEN CHOOSING ITS INITIAL SERVICE-ORIENTED PROJECT SHAPE. Do not scaffold Python backends directly — use this skill first.
  Backend/API bootstrap for Python: framework choice, backend repo layout, app factory/composition root, config, migrations, workers, API test setup, and service-first project conventions.
---

# Setting Up Python Backends

This skill is a backend-specialized extension of `setting-up-python-projects`.
Use it when the repo is primarily a service, API, or worker-oriented backend. Start here for backend repos, then pull generic bootstrap pieces from `setting-up-python-projects` as needed.

---

## Default Approach

1. Choose framework weight:
   - **FastAPI** is the default boring choice for most service APIs.
   - **Django** is justified when auth, admin, sessions, and CRUD-heavy backend surface are obviously large from the start.
   - **Starlette** is for deliberate thin-edge builds, not as a default.
2. Start with a reusable core and thin transport:
   - routes, workers, schedulers, CLI hooks, and automation call the same core services
3. Add infrastructure only when needed:
   - relational DB -> `SQLAlchemy 2` + `Alembic`
   - auth/OIDC/JWT -> `Authlib`
   - outbound HTTP -> `httpx`
   - cache/jobs -> `Redis`, and optionally `Dramatiq` when durable background work actually exists
4. Keep one composition root and one app factory.

---

## Default Stack

- `FastAPI` + `uvicorn`
- `pydantic` models at the FastAPI HTTP edge; `msgspec.Struct` for config and non-framework external payload decoding
- `dataclass(frozen=True, slots=True)` + `Result[T, E]` in the core
- `SQLAlchemy 2` + `Alembic` when the service owns relational persistence
- `httpx` for outbound HTTP
- existing repo logging setup via `shared/logging`
- `pytest`, `pytest-asyncio`, and integration tests through real app wiring
- `uv`, `poethepoet`, `basedpyright`, and `ruff`

Keep `pydantic` request/response DTOs at the HTTP boundary and convert immediately into framework-free typed structures.

---

## Default Layout

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

---

## First Files

- `api/app.py` with `create_app()`
- `api/routes/health.py` with `/healthz`
- `bootstrap.py` with `create_services()` and app wiring
- `domain/models.py` and one small service/use-case module
- `infrastructure/config.py` to parse env into typed settings
- DB files and migrations only if persistence exists
- one smoke API test and one domain test

---

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

---

## Migrations and Operations

- If the service owns a relational DB, initialize `Alembic` early.
- Add health and readiness endpoints early.
- Keep dev run, lint, test, and migrate commands in Poe tasks.
- Containerize when needed, but keep v1 Linux-first and boring.

---

## Defer by Default

- queues and background-job stacks
- caching layers
- metrics/tracing vendors
- event buses or CQRS
- multitenancy
- API versioning strategy beyond basic room for growth
- generated SDKs and OpenAPI customization
- Kubernetes-specific guidance

Add those only when the project actually needs them.

---

## Handoff

- Use `building-python-backends` for day-2 backend architecture and service/API/worker shaping.
- Use `building-multi-ui-apps` if API, CLI, and automation share one core.
- Use `writing-python-code` for implementation rules.
