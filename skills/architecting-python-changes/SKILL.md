---
name: architecting-python-changes
description: >-
  Python-specific extension to myai's `architecting-changes`. Load after myai's `architecting-changes` when a Python feature, fix, refactor, or structure change requires architecture decisions about layers, wrappers, composition roots, framework choices, reusable cores, or where code should live.
  Python architecture guide + skill router for boundary placement, reusable core design, composition vs inheritance, framework vs custom choices, backend/service layering, and follow-up docs/skills.
---

# Architecting Python Changes

## Prerequisites

This skill extends myai's `architecting-changes`. Load that first. `using-my-skills` and `engineering-principles` are assumed already loaded via myai bootstrap.

For the general architecture decision framework (boundaries, layers, wrappers, reusable cores, composition roots, framework choices), see myai's `architecting-changes`. This skill adds Python-specific routing: which Python skills and docs to consult for different architecture questions, Python-specific heuristics, and common Python architecture mistakes.

This skill is the first stop for non-trivial Python architecture decisions.
It is both a compact guide and a router to deeper project docs and domain skills.

---

## Default Approach

Follow the 6-step flow in myai's `architecting-changes` (classify → find change axis → identify question → choose boundary → route → continue). Then use the Python-specific router below to find the right Python skill for your domain.

---

## Core Heuristics

> **For the general architecture heuristics (boundaries, reuse vs custom, composition, reusable cores, transparency), see myai's `architecting-changes`.** Python-specific additions below.

### Boundaries and layers

- Enforce third-party wrapper usage via ruff `banned-api` in `pyproject.toml`. For the general boundary and layer philosophy, see myai's `architecting-changes`.

### Reuse versus custom code

- When selecting a library, analyze for typing support (basedpyright strict compatibility). For the general reuse philosophy, see myai's `architecting-changes`.

### Reusable cores

- For the Python-specific multi-UI pattern, see `building-multi-ui-apps`. For the general reusable core philosophy, see myai's `architecting-changes`.

---

## Where To Look

- `docs/PHILOSOPHY.md`
  - First source for the project's core architecture rules: dependency direction, reusable cores, composition, wrappers at dynamic boundaries, and transparency.

- `docs/coding_rules.md`
  - Code-facing rules that back the philosophy: wrapper enforcement, circular-import handling, architecture boundaries, error boundaries, and layout expectations.

- `setting-up-python-projects`
  - Use when the question is high-level repo/package structure, project shape, scaffolding level, framework choice, or generic architecture choices.

- `setting-up-python-backends`
  - Use when the repo is primarily a backend, API service, or worker-oriented system and you need backend-specific scaffolding, migrations, health endpoints, app factory choices, or service-first layout defaults.

- `building-backends` (myai)
  - Use when the architecture question is about backend/service layering, transport vs domain boundaries, transactions, auth/session edges, workers, or important operation flows. Has Python and TypeScript/Node ecosystem examples.

- `building-multi-ui-apps`
  - Use when CLI, GUI, API, or automation share business logic and you need adapters, a composition root, or interface separation.

- `building-qt-apps`
  - Use when the architecture question is specific to PySide6 or Qt: manager vs service vs wrapper, event-loop boundaries, signals, or platform integration.

- `writing-python-code`
  - Use after the structure is chosen, or when the decision is really about implementing typed wrappers, handling import cycles correctly, or encoding the boundary in code.

---

## Handoff

- After the architecture direction is clear, continue with `writing-python-code`.
- If the work is a brand-new project or major re-shape, also consult `setting-up-python-projects`.
- If the change needs a formal plan, write it in the project's normal planning flow before implementation.

---

## Related myai Skills

- **`architecting-changes`** — Parent skill. Language-agnostic architecture decision framework: boundaries, layers, wrappers, reusable cores, composition roots, framework choices.
- **`engineering-principles`** — Language-agnostic philosophy backing all architecture decisions.
- **`api-design`** — For stable API and protocol/interface design.
- **`brainstorming`** — For technical spec creation when requirements are clear but architecture needs design.
- **`doubt-early`** — For adversarial review before committing to architecture decisions.
- **`incremental-implementation`** — For implementing architecture changes in thin, verified slices.
