---
name: building-python-backends
description: >-
  ALWAYS LOAD THIS SKILL WHEN DESIGNING OR CHANGING PYTHON BACKEND, SERVICE, WORKER, OR API ARCHITECTURE: ROUTES, USE-CASE LAYERS, AUTH BOUNDARIES, PERSISTENCE, TRANSACTIONS, OR BACKGROUND JOBS. Do not shape Python backends directly — use this skill first.
  Python backend architecture: thin transport, reusable core, Result-to-HTTP mapping, transaction ownership, auth/session boundaries, workers, idempotency, and infrastructure separation.
---

# Building Python Backends

Backends are just another adapter around business logic.
Keep transport thin, core reusable, infrastructure explicit, and operationally important flows traceable.

---

## Default Architecture

```text
Transport / Adapters
  - HTTP routes
  - workers and schedulers
  - CLI/admin scripts
        |
        v
Application / Use Cases
  - one service or command per business operation
        |
        v
Domain
  - models, policies, domain errors
        |
        v
Infrastructure
  - DB, cache, external clients, auth adapters
```

In small backends, application and domain code may live close together. Add more layers only when responsibilities or change axes differ.

---

## Core Rules

- Routes and workers decode input, call one core operation, then map the result outward.
- `pydantic` request/response DTOs should live at the FastAPI edge, but they are not domain models.
- Convert auth/session/request state immediately at the edge into framework-free typed inputs and actor/principal values.
- Expected failures stay `Result[T, E]` through core layers. HTTP status mapping happens at the transport boundary.
- Exceptions are bugs or infrastructure escapes. Catch them at the global boundary.

---

## Persistence and Transactions

- A use-case owns the transaction boundary.
- Repositories are optional, not mandatory. Use them when they express a real persistence boundary, not because the pattern exists.
- Do not let routes open, commit, and orchestrate business transactions inline.
- Do not let repositories silently commit their own work for multi-step flows.

---

## Workers and Background Work

- Workers are another adapter calling the same core services as HTTP or CLI.
- Important background work should have an explicit job payload and handler.
- Do not hide important work inside fire-and-forget tasks started from request handlers.
- If work needs retries, durability, or traceability, treat it as a real backend workflow, not a convenience callback.

---

## Auth and Operation Context

- Keep framework auth/session objects at the edge.
- Pass a typed actor/principal into core operations.
- Important write operations should expose execution context clearly: actor, request ID, idempotency key, and mode when needed.
- Prefer typed mode values over a naked `dry_run: bool` when behavior meaningfully changes.

---

## Framework and Library Heuristics

- **FastAPI** is the default boring HTTP adapter.
- **Django** is justified when backend complexity, admin, auth/session behavior, and CRUD surface are obviously large from day 1.
- **SQLAlchemy 2** + **Alembic** is the default relational stack when the service owns its DB.
- **httpx** wrappers own outbound HTTP boundaries.
- Add Redis, queues, and extra infrastructure only when the product actually needs them.

---

## Common Mistakes

- business logic and DB commits inline in routes
- request DTOs or ORM rows used as domain models
- framework request/auth/session objects leaking into core code
- generic repository layers everywhere
- separate worker logic duplicating route logic
- important writes without idempotency, dry-run, or traceability where they matter
- CLI or admin scripts bypassing the real core services

---

## Handoff

- Use `setting-up-python-backends` for new backend repos and initial scaffolding.
- Use `building-multi-ui-apps` if API, CLI, and automation share one core.
- Use `writing-python-code` for implementation details.
- Use `testing-python` for API/service/worker testing strategy.
