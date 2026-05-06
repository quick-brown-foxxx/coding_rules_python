---
name: architecting-python-changes
description: >
  ALWAYS LOAD THIS SKILL WHEN PLANNING OR SHAPING A NEW FEATURE, NON-TRIVIAL FIX, OR REFACTOR THAT MAY CHANGE STRUCTURE, LAYERS, WRAPPERS, OR LIBRARY CHOICES, OR WHEN ASKING WHERE CODE SHOULD LIVE. Do not make architecture decisions in Python projects blindly — use this skill first.
  Small routing skill for architecture-related work: points to the right existing project docs and skills for layering, wrappers, UI separation, Qt structure, and implementation follow-up.
---

# Architecting Python Changes

This skill is a **routing layer**, not a replacement for the existing architecture docs and domain skills.

Use it to decide **which guidance to consult before coding or plan writing**.

---

## Default Approach

1. Classify the change:
   - small local fix
   - feature adding new behavior or a new caller
   - refactor moving responsibilities or dependencies
2. Identify the real architecture question:
   - layering and extraction
   - wrapper or platform boundary
   - multi-interface separation
   - Qt manager/service/wrapper split
   - library vs custom code
3. Load the matching source below, then continue with implementation skills.

---

## Where To Look

- `docs/PHILOSOPHY.md`
  - First source for the project's core architecture rules: dependency direction, UI as plugin, wrappers at dynamic boundaries, and scale-appropriate separation.

- `docs/coding_rules.md`
  - Most of project rules that back the philosophy: wrapper enforcement, circular-import handling, error boundaries, and layout expectations.

- `setting-up-python-projects`
  - Use when the question is high level repo/package structure, directory layout, code quality enforcement, or generic architecture choices.

- `building-multi-ui-apps`
  - Use when CLI, GUI, or API share business logic and you need routing, composition root, or interface separation.

- `building-qt-apps`
  - Use when the architecture question is specific to PySide6 or Qt: manager vs service vs wrapper, event-loop boundaries, signals, or platform integration.

- `writing-python-code`
  - Use after the structure is chosen, or when the decision is really about implementing typed wrappers, handling import cycles correctly, or encoding the boundary in code.

---

## Brief Heuristics

- Small fix: keep it local unless the wrong boundary caused the bug.
- New shared behavior: extract downward instead of duplicating across UI entry points.
- Third-party or OS-specific dependency: consider a wrapper when typing, portability, exception isolation, or future replacement matters.
- Commodity problem: prefer a boring maintained library over custom infrastructure.
- Domain rule or thin orchestration: prefer simple custom code over premature abstraction.

---

## Handoff

- After the architecture direction is clear, continue with `writing-python-code`.
- If the change needs a formal plan, write it in the project’s normal planning flow before implementation.
