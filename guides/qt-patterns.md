# Qt Patterns Guide

PySide6 patterns for desktop applications. See [PHILOSOPHY.md](../PHILOSOPHY.md) sections 6, 8.

---

## Why PySide6

- LGPL license (no additional restrictions)
- No extra system dependencies (ships with wheels)
- Same API as PyQt6, but freely redistributable

---

## Architecture: Manager -> Service -> Wrapper

```
UI Layer (MainWindow, Dialogs, TrayIcon)
    |  Qt signals/slots
    v
Manager Layer (AudioManager, TranscriptionManager)
    |  orchestrates, emits signals
    v
Service Layer (TranscriptionService, RecordingService)
    |  async operations
    v
Wrapper Layer (WhisperWrapper, SoundcardWrapper)
    |  typed interfaces to third-party libs
    v
Third-Party Libraries
```

### Manager Pattern

Managers coordinate operations and emit Qt signals:

```python
class TranscriptionManager(QObject):
    transcription_finished = Signal(str)
    transcription_error = Signal(str)
    model_changed = Signal(str)

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._service: TranscriptionService | None = None
        self._bridge = QAsyncSignalBridge()

    def transcribe(self, audio_data: np.ndarray) -> bool:
        if not self._service:
            self.transcription_error.emit("Service not initialized")
            return False

        self._bridge.run_async(
            self._service.transcribe(audio_data),
            on_success=self._on_finished,
            on_error=self._on_error,
        )
        return True

    def _on_finished(self, text: str) -> None:
        self.transcription_finished.emit(text)

    def _on_error(self, error: str) -> None:
        self.transcription_error.emit(error)
```

### Wrapper Pattern

Typed wrappers isolate untyped third-party APIs:

```python
class WhisperModelWrapper:
    """Typed wrapper for faster-whisper."""

    def __init__(self, model_size: str, device: str = "auto") -> None:
        from faster_whisper import WhisperModel as _WhisperModel
        self._model = _WhisperModel(model_size, device=device)

    def transcribe(self, audio: np.ndarray, language: str | None = None) -> TranscriptionResult:
        segments_gen, info = self._model.transcribe(audio, language=language)
        return TranscriptionResult(
            text="".join(s.text for s in segments_gen),
            language=str(info.language),
        )
```

---

## Async Integration with qasync

### Setup

```python
import asyncio
import qasync

def main() -> int:
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        window = MainWindow()
        window.show()
        loop.run_forever()
    return 0
```

### QAsyncSignalBridge

See [async-patterns.md](async-patterns.md) for full implementation.

### ThreadPoolExecutor for Blocking Libraries

```python
class AsyncRecorder(QObject):
    recording_completed = Signal(np.ndarray)

    def __init__(self) -> None:
        super().__init__()
        self._executor = ThreadPoolExecutor(max_workers=1)

    async def start_recording(self) -> None:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, self._sync_record)
        self.recording_completed.emit(result)
```

---

## Signal/Slot Conventions

- Define signals at class level (not in `__init__`)
- Connect signals in the component that owns the relationship
- Use typed signals: `Signal(str)`, `Signal(float)`, `Signal(object)`

```python
class AudioManager(QObject):
    volume_changed = Signal(float)
    recording_completed = Signal(np.ndarray)
    recording_failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._recorder = AsyncRecorder()
        self._recorder.recording_completed.connect(self.recording_completed)
```

---

## Naming Convention Exception

Qt event handlers use `camelCase` per Qt convention. Ignore ruff `N802` for these:

```toml
[tool.ruff.lint]
ignore = ["N802"]  # Qt event handlers use camelCase
```

```python
class CustomWidget(QWidget):
    def mousePressEvent(self, event: QMouseEvent) -> None:  # Qt convention
        ...

    def on_button_clicked(self) -> None:  # Our slots use snake_case
        ...
```

---

## System Tray Pattern

```python
class ApplicationTrayIcon(QSystemTrayIcon):
    def __init__(self) -> None:
        super().__init__()
        self.setIcon(QIcon("icon.png"))
        self._setup_menu()

    def _setup_menu(self) -> None:
        menu = QMenu()
        menu.addAction("Settings", self._open_settings)
        menu.addSeparator()
        menu.addAction("Quit", QApplication.quit)
        self.setContextMenu(menu)
```

---

## Single Instance Enforcement

```python
class LockManager:
    def __init__(self, lock_path: Path) -> None:
        self._lock_path = lock_path

    def acquire(self) -> Result[None, str]:
        if self._lock_path.exists():
            pid = int(self._lock_path.read_text())
            if self._is_process_running(pid):
                return Err(f"Another instance running (PID {pid})")
            # Stale lock file
        self._lock_path.write_text(str(os.getpid()))
        return Ok(None)

    def release(self) -> None:
        self._lock_path.unlink(missing_ok=True)
```

---

## Keyboard Shortcuts

Customizable via TOML config:

```python
# constants.py
class ActionID(enum.Enum):
    NEW_PROFILE = "new_profile"
    START_PROFILE = "start_profile"

@dataclass
class ActionShortcut:
    id: str
    label: str
    default_key: str

DEFAULT_SHORTCUTS = (
    ActionShortcut(ActionID.NEW_PROFILE.value, "New Profile", "Ctrl+N"),
    ActionShortcut(ActionID.START_PROFILE.value, "Start Profile", "Return"),
)
```

User overrides stored in `~/.config/appname/shortcuts.toml`.

---

## Testing Qt Components

Use `pytest-qt`:

```python
def test_main_window_creates(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.isVisible() is False  # Not shown until .show()

def test_button_click(qtbot: QtBot) -> None:
    widget = MyWidget()
    qtbot.addWidget(widget)
    with qtbot.waitSignal(widget.action_triggered, timeout=1000):
        qtbot.mouseClick(widget.button, Qt.LeftButton)
```
