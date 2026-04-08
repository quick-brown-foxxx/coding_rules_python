---
name: building-multi-ui-apps
description: >
  ALWAYS LOAD THIS SKILL WHEN APP HAS BOTH CLI AND GUI, OR MULTIPLE INTERFACES SHARING LOGIC. Do not architect multi-interface apps directly — use this skill first.
  Multi-interface Python apps: layered architecture for GUI + CLI + API sharing business logic.
---

# Building Multi-UI Apps

UI is a plugin. Business logic lives in the domain layer. Adding a new interface (CLI, GUI, API) should not change business logic.

---

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

---

## Entry Point Pattern

```python
# __main__.py
def main() -> int:
    if len(sys.argv) > 1:
        return cli_main()
    return gui_main()
```

---

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

---

## Platform Abstraction

For apps that must run on multiple platforms:

```python
from abc import ABC, abstractmethod

class PlatformBackend(ABC):
    @abstractmethod
    async def start_instance(self, profile: Profile, binary: Path) -> Result[int, str]: ...

    @abstractmethod
    def get_data_dir(self) -> Path: ...

    @abstractmethod
    def get_config_dir(self) -> Path: ...

class LinuxBackend(PlatformBackend):
    async def start_instance(self, profile: Profile, binary: Path) -> Result[int, str]:
        env = {
            "XDG_CONFIG_HOME": str(profile.path / "config"),
            "XDG_DATA_HOME": str(profile.path / "data"),
        }
        process = await asyncio.create_subprocess_exec(
            str(binary), "-many", "-workdir", str(profile.path),
            env={**os.environ, **env},
        )
        return Ok(process.pid) if process.pid else Err("Failed to start")
```

**DO NOT DO** — platform abstraction layer directly calling platform-specific code with conditionals:

```python
# ❌ WRONG: NotificationsManager directly branches on platform
class NotificationsManager:
    def send(self, message: str) -> None:
        if sys.platform == "linux":
            linux_backend.run(message)          # direct call, no interface
        elif sys.platform == "darwin":
            macos_backend.notify(message)       # direct call, no interface
        else:
            windows_backend.toast(message)      # direct call, no interface
```

The manager now knows about every platform. Adding a new OS means editing business logic. Platform code **must** be hidden behind an interface/protocol/abstract class; the manager only calls the abstraction.

Select backend at startup:

```python
def get_backend() -> PlatformBackend:
    match sys.platform:
        case "linux":
            return LinuxBackend()
        case _:
            raise NotImplementedError(f"Unsupported platform: {sys.platform}")
```

---

## Dependency Injection — Composition Root

Pass dependencies via constructor parameters. Wire everything in a single composition root function. No DI libraries — they break basedpyright strict or add unnecessary indirection.

### Pattern

```python
# app/bootstrap.py
def create_domain(config: AppConfig) -> SessionManager:
    """Composition root — the ONLY place dependencies are wired."""
    db = DatabaseWrapper(config.db_path)
    api = ApiClientWrapper(config.api_url, config.api_key)
    auth = AuthService(api_client=api)
    sync = SyncService(db=db, api_client=api)
    return SessionManager(auth=auth, sync=sync)

# GUI entry point
def main_gui() -> None:
    config = load_config()
    session = create_domain(config)
    window = MainWindow(session=session)
    ...

# CLI entry point
def main_cli() -> None:
    config = load_config()
    session = create_domain(config)
    cli_app = build_typer_app(session=session)
    cli_app()
```

### Rules

- **Domain classes never instantiate their own infrastructure.** Dependencies come through the constructor.
- **One composition root per app.** This is the single place to understand the object graph.
- **Protocol-typed interfaces** for dependencies that may have test doubles.
- **Testing:** construct with fakes directly — no container setup needed:

```python
def test_sync_handles_conflict() -> None:
    db = FakeDatabaseWrapper()
    api = FakeApiClient(responses=[CONFLICT_RESPONSE])
    sync = SyncService(db=db, api_client=api)
    result = sync.pull_changes()
    assert result.is_err
```

---

## Other Presentation Layers

FastAPI can be added as another presentation layer consuming the same domain:

```python
@router.post("/profiles")
async def create_profile(req: CreateProfileRequest) -> ProfileResponse:
    result = manager.create_profile(req.name)
    if result.is_err:
        raise HTTPException(400, result.unwrap_err())
    return ProfileResponse.from_domain(result.unwrap())
```

Other presentation layers also possible in specific cases: TUI, python exportable API
