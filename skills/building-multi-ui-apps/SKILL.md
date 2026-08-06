---
name: building-multi-ui-apps
description: >-
  Python-specific extension to myai's `architecting-changes`. Load after myai's `architecting-changes` when a Python app has multiple interfaces sharing logic, such as CLI, GUI, API, or automation entry points.
  Multi-interface Python apps: reusable core, thin adapters, composition root, and layered architecture for GUI + CLI + API sharing business logic.
---

# Building Multi-UI Apps

## Prerequisites

This skill extends myai's `architecting-changes`. Load that first. `using-my-skills` and `engineering-principles` are assumed already loaded via myai bootstrap.

For the general architecture principles (reusable cores, thin adapters, composition roots, dependency injection), see myai's `architecting-changes`. This skill covers only Python-specific multi-interface patterns: PySide6 GUI + typer CLI + FastAPI sharing a domain core, entry point routing, platform abstraction, and composition root wiring.

UI is a plugin. Build a reusable core first, then keep each interface as a thin adapter around it. Adding a new interface (CLI, GUI, API) should not change business logic.

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

## Reusable Core First

- Build one composable domain API first, then add CLI/GUI/API adapters around it.
- The first shipped interface may be the only one today; still keep business rules out of commands, routes, and widgets.
- Presentation layers parse input, call the core, and format output.
- Framework-specific request objects, CLI contexts, and widgets stay at the edge.

---

## Entry Point Pattern

Keep it simple: one Typer multi-command app where **every invocation names a command**. GUI-launching commands are just ordinary Typer commands mixed into the same list as the CLI commands. There is no root/default command and no mode-detection logic to maintain.

This gives:
- `myapp -h` / `myapp --help` -> help listing every command
- `myapp gui FILE [--debug]` -> a GUI command (shows the window)
- `myapp run foo` / `myapp config get key` -> CLI commands

Deliberately no default/root command: making bare `myapp` do something special (e.g. open the GUI) forces mode-detection heuristics or Typer/Click default-command hacks (`typer.core.TyperGroup` subclassing, `sys.argv` mutation), which are brittle and version-fragile. If you want a GUI shortcut, register an explicit `gui` command and document it — the cost of naming a command is that bare `myapp` shows help instead of launching a GUI.

```python
# __main__.py
from __future__ import annotations

import typer

from myapp.bootstrap import create_services
from myapp.version import VERSION

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command()
def gui(path: str, debug: bool = False) -> None:
    """Open the GUI with this file."""
    services = create_services(debug=debug)

    from myapp.gui import run_gui  # noqa: PLC0415 - lazy so CLI runs stay Qt-free

    run_gui(services=services, path=path, debug=debug)


@app.command()
def run(item: str) -> None:
    """A plain CLI command."""
    services = create_services(debug=False)
    typer.echo(f"run {item}")


@app.command()
def version() -> None:
    """Print the version — a normal command, no --version magic needed."""
    typer.echo(VERSION)


if __name__ == "__main__":
    app()
```

Notes:
- **Lazy-import the GUI** inside the GUI command's body so `run`/`config`/`version` never import Qt. The `open` command parses args, builds the core, then `from myapp.gui import run_gui` at call time.
- **Keep dependency wiring elsewhere**: commands parse input and call the core / `run_gui(...)`; the composition root (`create_services`) still builds the object graph and is injected. Never wire objects inside `__main__.py`.
- **GUI subcommands** (`myapp show-print-dialog FILE`) are just more `@app.command`s that route into GUI callables; nested groups via `app.add_typer(...)` work exactly as in any Typer app.
- Help/version are regular commands, so there is no `--version` flag handling to get wrong (and no `Missing command` edge case).

### Tip: also export a bare GUI binary

Export a second console script that opens the GUI directly (`myapp-gui`), so users and the desktop don't have to type `myapp open`:

```python
# __main__.py (add alongside `main`)
def main() -> None:
    app()  # full CLI, including the `open` GUI command


def main_gui() -> None:
    """Bare GUI entry point: `myapp-gui` just opens the window."""
    services = create_services(debug=False)

    from myapp.gui import run_gui  # noqa: PLC0415 - lazy: only this binary needs Qt

    run_gui(services=services, path=None, debug=False)
```

```toml
# pyproject.toml
[project.scripts]
myapp = "myapp.__main__:main"        # full CLI (contains the `open` GUI command)
myapp-gui = "myapp.__main__:main_gui"  # dedicated GUI entry, for launchers/desktop
```

Use `myapp-gui` in `.desktop` files, file-manager "Open with" handlers, launchpad/Spotlight-style launchers, and packaging desktop entries — a bare binary that opens the GUI is what those integrations expect. The CLI `myapp` (with the `open`/`show-print-dialog` commands) stays for scripted/terminal use.

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

## Interactive / Long-Running Operations

The `Shared Logic` example above is a **one-shot command**: `() -> Result[T, E]` — call the core, get a result, done. Both CLI and GUI treat it trivially (CLI: `print(result)`; GUI: refresh a view).

Interactive operations are different. They run for a while, **emit progress/errors as they go**, and may **ask the user a question mid-run** (e.g. "this vacancy wants an answer before we submit — what do you say?"). A GUI (Qt MVVM) handles this naturally with signals out and dialogs in. A CLI can too, but only if we do not shape the core around signals.

**Key principle:** MVVM (signals, `@Slot`s, bindings) is *how the Qt adapter implements the operation* — it is never the *shape of the core*. The core must not import Qt, must not know about signals, and must not know about `typer`. Express the operation against a tiny **interaction interface** — an out-channel for events/errors and an in-channel for questions — and let each adapter map that to its own idiom.

### The interaction interface (core, framework-free)

```python
# core/interaction.py  — no Qt, no typer imports
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class ProgressEvent:
    vacancy_id: str
    message: str

@dataclass(frozen=True)
class Question:
    vacancy_id: str
    text: str

class ReplyFlowIO(Protocol):
    """The only thing the core knows about its user."""
    async def progress(self, event: ProgressEvent) -> None: ...
    async def error(self, error: str) -> None: ...
    async def ask(self, question: Question) -> str: ...  # returns the user's answer

async def run_reply_flow(vacancies: list[Vacancy], io: ReplyFlowIO) -> ReplyResult:
    """The interactive flow. UI-agnostic: only negotiates through `io`."""
    for v in vacancies:
        await io.progress(ProgressEvent(v.id, f"checking {v.title}"))
        answer: str | None = None
        if v.requires_answer:
            answer = await io.ask(Question(v.id, v.text))
            if not answer:
                await io.progress(ProgressEvent(v.id, "skipped"))
                continue
        result = await submit_reply(v, answer)
        if result.is_err:
            await io.error(result.unwrap_err())
            continue
        await io.progress(ProgressEvent(v.id, "replied"))
    return finalize_reply(vacancies)
```

The flow is a plain `async` function over the protocol. The core decides *what* to do, never *how* events are shown or *how* questions are answered.

### CLI adapter — prints and prompts as it runs

```python
# cli.py
import asyncio
import typer

class CliReplyIO:
    async def progress(self, event: ProgressEvent) -> None:
        typer.echo(f"[{event.vacancy_id}] {event.message}")

    async def error(self, error: str) -> None:
        typer.echo(f"error: {error}", err=True)

    async def ask(self, question: Question) -> str:
        return typer.prompt(question.text)

@app.command()
def reply(vacancies: list[Path]) -> int:
    """One command that happens to be interactive underneath."""
    result = asyncio.run(run_reply_flow(load_vacancies(vacancies), CliReplyIO()))
    typer.echo(f"done: {result}")
    return 0
```

From the shell's perspective `myapp reply ...` is still a single blocking command: it prints progress lines to a terminal, blocks on a prompt when a vacancy needs an answer, then exits. This is exactly the CLI's "way of life" — the interaction interface makes it possible without polluting the core.

### Qt MVVM adapter — the ViewModel implements the interface

The Qt adapter is where MVVM earns its keep. The **ViewModel implements the same `ReplyFlowIO`**; it is the single bridge between the core and QML. Progress/errors become VM state + signals that QML binds to; `ask()` hands control to a QML dialog and awaits the answer via a pending `asyncio.Future`.

```python
# gui/reply_viewmodel.py
from __future__ import annotations

import asyncio
from PySide6.QtCore import QObject, Signal, Slot

from core.interaction import ProgressEvent, Question, ReplyFlowIO

class ReplyViewModel(QObject, ReplyFlowIO):
    progress_message = Signal(str)     # -> QML updates a status line / list row
    error_message = Signal(str)        # -> QML shows an error block
    question_requested = Signal(str)   # -> QML opens a prompt dialog with `text`
    reply_finished = Signal(object)    # -> QML knows the flow ended

    def __init__(self) -> None:
        super().__init__()
        self._pending: asyncio.Future[str] | None = None

    # --- ReplyFlowIO: turn core events into VM state + signals ---
    async def progress(self, event: ProgressEvent) -> None:
        self.progress_message.emit(f"[{event.vacancy_id}] {event.message}")

    async def error(self, error: str) -> None:
        self.error_message.emit(error)

    async def ask(self, question: Question) -> str:
        # Defer to the view: emit, present a dialog in QML,
        # and sleep until QML calls back with the answer.
        self._pending = asyncio.get_running_loop().create_future()
        self.question_requested.emit(question.text)
        return await self._pending

    # --- Called by QML when the prompt dialog is answered ---
    @Slot(str)
    def submit_answer(self, text: str) -> None:
        if self._pending is not None and not self._pending.done():
            self._pending.set_result(text)
```

In QML the `question_requested` signal opens a dialog and `submit_answer` is invoked on accept — the dialog is pure view, and the async flow simply resumes with the returned string. Threading note: these callbacks run on the GUI thread (where the qasync loop lives), so `set_result` resumes the coroutine safely. If the flow were doing real blocking I/O it should run on a worker/`ThreadPoolExecutor` and marshal results back via signals — but the core interface shape is unaffected.

### Async-by-contract

The interaction interface is `async` deliberately. The GUI *must* `await` a dialog, so it needs coroutines. The CLI implements the same async protocol and just runs it with `asyncio.run(...)` — CLI's blocking behaviour is preserved, GUI's non-blocking event loop is preserved, and they share one core function. Synchronous one-shot commands stick with `Result`; interactive operations go through an `…IO` interface.

**Summary:** basic commands return `Result`. Interactive operations negotiate through an injected `…IO` interface (events out, questions in). MVVM is only how the Qt adapter implements that interface — it is never the shape of the core.

### Scaling the pattern

The examples above are a **starting shape, not the ceiling**. For real Qt interoperation three gaps appear, and all of them concentrate on the `ask()`/control bridge — the core boundary stays stable.

**1. User-initiated cancellation (the user → core direction).** The flow as drawn is one-directional: the user only answers when asked. A real GUI user wants to stop mid-run. Prefer built-in primitives where they fit, fall back to ad-hoc flags only when they don't:

- **Built-in async cancellation** — run the flow as an `asyncio.Task` and let the VM's "Stop" button call `task.cancel()`; `CancelledError` fires at the next `await` and unwinds through any cleanup. Ideal when the operation is genuinely async (every blocking step is an await) and you want an immediate hard stop. It is abrupt — the core can't intercept at a safety boundary — so it suits "stop the whole job now", not "finish this item then pause".
- **Cooperative flag / `asyncio.Event`** — the core checks `await should_abort()` (or `evt.is_set()`) between steps and returns a clean `aborted` result. Good for graceful/checkpointed stops (finish the current vacancy, then halt) or when an instant interrupt would be unsafe.

The choice is coupled to how the work runs: `Task.cancel()` only works where there are `await` points in the same event loop. If blocking work runs on a `ThreadPoolExecutor`, a running thread cannot be cancelled — use a cooperative flag checked between blocking calls, or cancel at the process level.

**2. Concurrent / dynamic questions — key the futures.** The example keeps one `self._pending: Future[str]`, which is overwritten if a second `ask` fires before the first resolves. Real apps process tasks concurrently or run a wizard where the next question depends on the last answer. Key futures by question id (or queue them) so each `ask` awaits its own future, and hand the whole `Question` to QML rather than a bare string:

```python
self._pending: dict[str, asyncio.Future[str]] = {}

async def ask(self, question: Question) -> str:
    fut = asyncio.get_running_loop().create_future()
    self._pending[question.id] = fut
    self.question_requested.emit(question)
    return await fut

@Slot(str, str)
def submit_answer(self, question_id: str, text: str) -> None:
    fut = self._pending.pop(question_id, None)
    if fut is not None and not fut.done():
        fut.set_result(text)
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

---

## Related myai Skills

- **`architecting-changes`** — Parent skill. Language-agnostic architecture decision framework: reusable cores, thin adapters, composition roots.
- **`engineering-principles`** — Language-agnostic philosophy: architecture separation, UI as plugin.
- **`architecting-python-changes`** — Python-specific architecture router.
- **`building-qt-apps`** — Python-specific PySide6 GUI patterns.
- **`building-backends`** (myai) — Backend architecture patterns when adding an API layer.
- **`writing-python-code`** — Python-specific coding rules for the shared domain core.
