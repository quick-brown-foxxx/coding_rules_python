---
name: architecting-python-changes
description: >-
  ALWAYS LOAD THIS SKILL WHEN A NEW FEATURE, NON-TRIVIAL FIX, REFACTOR, OR PYTHON STRUCTURE CHANGE REQUIRES AN ARCHITECTURE DECISION ABOUT LAYERS, WRAPPERS, COMPOSITION ROOTS, FRAMEWORK CHOICES, REUSABLE CORES, OR WHERE CODE SHOULD LIVE. Do not make Python architecture decisions blindly — use this skill first.
  Python architecture guide + skill router for boundary placement, reusable core design, composition vs inheritance, framework vs custom choices, backend/service layering, and follow-up docs/skills.
---

# Architecting Python Changes

This skill is the first stop for non-trivial Python architecture decisions.
It is both a compact guide and a router to deeper project docs and domain skills.

---

## Default Approach

1. Classify the change:
   - small local fix
   - feature adding new behavior or a new caller
   - refactor moving responsibilities or dependencies
   - project setup or framework choice
2. Ask yourself what is actually expected to change later:
   - business rules
   - validation or transport
   - UI or API surface
   - infrastructure or third-party dependency
   - platform support
   - workflow observability or operational controls
3. Identify the real architecture question:
   - where should this code live?
   - what deserves a boundary or wrapper?
   - should this be reusable from CLI, GUI, API, or automation?
   - is a boring framework or library better than custom code here?
   - is inheritance being used where composition would be clearer?
4. Apply the heuristics below.
5. Load the matching deeper source, then continue with implementation skills.

---

## Core Heuristics

### Boundaries and layers

- Keep a small fix local unless the bug was caused by the wrong boundary.
- Extract shared behavior downward into domain/utilities instead of duplicating across entry points or logic/flow branches.
- Keep business rules separate from validation plumbing, transport shapes, auth/session concerns, and raw infrastructure.
- Wrap third-party or OS-specific boundaries when typing, exception isolation, portability, or replacement matters.

### Reuse versus custom code

- Prefer boring popular maintained libraries and frameworks for commodity infrastructure: auth, packaging, builds, queues, caching, deployment, migrations, or orchestration.
- Do not build ad hoc systems on top of a tiny framework when the domain already implies substantial backend concerns.
- For tiny one-off helpers or stable details, simple custom code is often better than heavyweight scaffolding.
- When selecting a library, do web research and compare multiple options, consider how each one fits philosophy and architecture, remember to analyze for typing support.

### Composition and state

- Prefer composition, explicit data flow, and small protocol-shaped interfaces over deep class hierarchies.
- Add stateful classes for lifecycle or orchestration, not to manufacture abstractions.
- Hidden mutable state is a smell. Important state changes should be visible in code.

### Reusable cores

- If CLI, GUI, API, or automation may share logic, build a reusable core plus thin adapters.
- Start with one useful implementation, but do not trap business logic inside the first interface.
- Prefer composable pieces over one giant super-tool.

### Transparency and operations

- Important workflows should be inspectable: clear validation, explicit errors, logs at operation boundaries, and dry-run behavior where practical.
- For risky multi-step actions, prefer explicit step/state models and machines over opaque helper chains.
- If a failure would be costly or hard to debug for user, design for traceability early instead of bolting it on later.

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

- `building-python-backends`
  - Use when the architecture question is about backend/service layering, transport vs domain boundaries, transactions, auth/session edges, workers, or important operation flows.

- `building-multi-ui-apps`
  - Use when CLI, GUI, API, or automation share business logic and you need adapters, a composition root, or interface separation.

- `building-qt-apps`
  - Use when the architecture question is specific to PySide6 or Qt: manager vs service vs wrapper, event-loop boundaries, signals, or platform integration.

- `writing-python-code`
  - Use after the structure is chosen, or when the decision is really about implementing typed wrappers, handling import cycles correctly, or encoding the boundary in code.

---

## Common Mistakes

- Extracting layers because the pattern exists, not because responsibilities or change axes differ.
- Mixing domain rules with request/response models, validation glue, or infrastructure calls.
- Letting the first UI own logic that later needs to be shared.
- Introducing inheritance where a couple of collaborating objects would be clearer.
- Building custom infrastructure in a domain that already has strong boring solutions.

---

## Handoff

- After the architecture direction is clear, continue with `writing-python-code`.
- If the work is a brand-new project or major re-shape, also consult `setting-up-python-projects`.
- If the change needs a formal plan, write it in the project's normal planning flow before implementation.
