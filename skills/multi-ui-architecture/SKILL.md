---
name: multi-ui-architecture
description: Use when building an application that needs multiple interfaces - GUI plus CLI, or planning to add API later
---

# Multi-UI Architecture

## Overview

UI is a plugin. Business logic lives in the domain layer. Adding a new interface (CLI, GUI, API) should not change business logic.

## Architecture

```
Presentation Layer (top)
├── Qt GUI (PySide6)    - consumes domain, handles display
├── CLI (typer)          - consumes domain, handles terminal I/O
└── API (FastAPI)        - consumes domain, handles HTTP (if needed)
        |
        v
Domain Layer (middle)
├── Managers             - orchestrate operations
├── Models               - dataclasses, TypedDicts
└── Services             - business rules, pure logic
        |
        v
Utility Layer (bottom)
├── Helpers              - stateless functions
├── Wrappers             - typed third-party interfaces
└── Platform             - OS-specific implementations
```

**Dependencies flow downward only.** Domain never imports from presentation.

## Entry Point Pattern

```python
# __main__.py
def main() -> int:
    if len(sys.argv) > 1:
        return cli_main()
    return gui_main()
```

## Shared Logic

Both GUI and CLI use the same manager:

```python
# CLI
def cmd_create(name: str) -> int:
    result = manager.create_profile(name)
    if result.is_err:
        print(f"Error: {result.unwrap_err()}", file=sys.stderr)
        return 1
    print(f"Created: {result.unwrap().name}")
    return 0

# GUI
def on_create_clicked(self) -> None:
    result = self._manager.create_profile(name)
    if result.is_err:
        self._show_error(result.unwrap_err())
        return
    self._refresh_list()
```

## FastAPI Note

FastAPI can be added as another presentation layer consuming the same domain:

```python
@router.post("/profiles")
async def create_profile(req: CreateProfileRequest) -> ProfileResponse:
    result = manager.create_profile(req.name)
    if result.is_err:
        raise HTTPException(400, result.unwrap_err())
    return ProfileResponse.from_domain(result.unwrap())
```

This is mentioned as a possibility. GUI + CLI are the primary focus.
