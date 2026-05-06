# Shared Shortcuts Manager

Reusable keyboard shortcuts configuration system for PySide6 applications with platform-specific defaults and TOML configuration.

## Quick Start

```python
# 1. Define shortcuts
from shared.shortcuts import ActionShortcut

DEFAULT_SHORTCUTS = (
    ActionShortcut("new_file", "New File", "Ctrl+N", "Ctrl+N", "Cmd+N"),
    ActionShortcut("save", "Save", "Ctrl+S", "Ctrl+S", "Cmd+S"),
    ActionShortcut("quit", "Quit", "Ctrl+Q", "Ctrl+Q", "Cmd+Q"),
)

# 2. Initialize manager
from shared.shortcuts import ShortcutManager
from pathlib import Path
import platformdirs

manager = ShortcutManager(
    config_dir=Path(platformdirs.user_config_dir("your_app")),
    app_name="your_app",
    default_shortcuts=DEFAULT_SHORTCUTS,
)

# 3. Use in Qt
shortcut = manager.get_shortcut("save")  # Returns "Ctrl+S"
```

## ActionShortcut

```python
ActionShortcut(
    action_id: str,           # Unique identifier (snake_case)
    display_name: str,        # Human-readable name for UI
    default_linux: str,       # Default for Linux
    default_windows: str = "",# Default for Windows (falls back to Linux)
    default_macos: str = "",  # Default for macOS (falls back to Linux)
)
```

Example:

```python
DEFAULT_SHORTCUTS = (
    ActionShortcut("new_file", "New File", "Ctrl+N", "Ctrl+N", "Cmd+N"),
    ActionShortcut("save", "Save", "Ctrl+S", "Ctrl+S", "Cmd+S"),
    ActionShortcut("save_as", "Save As", "Ctrl+Shift+S", "Ctrl+Shift+S", "Cmd+Shift+S"),
    ActionShortcut("undo", "Undo", "Ctrl+Z", "Ctrl+Z", "Cmd+Z"),
    ActionShortcut("quit", "Quit", "Ctrl+Q", "Ctrl+Q", "Cmd+Q"),
)
```

## Key Sequence Format

Qt's QKeySequence string format with `+` to combine modifiers:

- **Modifiers:** `Ctrl`, `Shift`, `Alt`, `Meta`
- **Special keys:** `Return` (NOT `Enter`), `Backspace`, `Delete`, `Tab`, `Escape`, `Space`, `F1`-`F35`
- **Navigation:** `Left`, `Right`, `Up`, `Down`, `Home`, `End`, `PageUp`, `PageDown`

**Important:** Always use `"Return"` for the main Enter key, NOT `"Enter"`.

## shortcuts.toml Format

Config location: `<config_dir>/<app_name>_shortcuts.toml`

```toml
# Edit keyboard shortcuts using Qt QKeySequence string format.
# MODIFIERS: Ctrl, Shift, Alt, Meta (use '+' to combine)
# SPECIAL KEYS: Return (Enter key), Backspace, Delete, Tab, Escape, Space, F1-F35
# EXAMPLES: "Ctrl+S", "Return", "Shift+Delete", "Alt+Left", "F5"

[shortcuts]
new_file = "Ctrl+N"
save = "Ctrl+S"
quit = "Ctrl+Q"
```

## Key API

### ActionShortcut (frozen dataclass)

```python
@dataclass(frozen=True)
class ActionShortcut:
    action_id: str
    display_name: str
    default_linux: str
    default_windows: str = ""
    default_macos: str = ""

    def get_default_for_platform(self) -> str:
        """Get the default shortcut for the current platform."""
```

### ShortcutConfig

```python
@dataclass
class ShortcutConfig:
    shortcuts: dict[str, str]

    def get_shortcut(self, action_id: str) -> str | None:
        """Get the configured shortcut for an action."""

    def set_shortcut(self, action_id: str, sequence: str) -> Result[None, str]:
        """Set a shortcut for an action."""

    def save(self, path: Path) -> Result[None, str]:
        """Save config to a TOML file."""
```

### ShortcutManager

```python
class ShortcutManager:
    def __init__(
        self,
        config_dir: Path,
        app_name: str = "app",
        default_shortcuts: tuple[ActionShortcut, ...] = (),
    ) -> None:
        """Initialize ShortcutManager."""

    def load(self) -> Result[ShortcutConfig, str]:
        """Load shortcuts from config file. Creates default if missing."""

    def get_shortcut(self, action_id: str) -> str:
        """Get the shortcut for an action, with default fallback."""

    def reload(self) -> Result[ShortcutConfig, str]:
        """Reload shortcuts from config file."""
```

## Usage in Qt

```python
from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QAction, QKeySequence

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.shortcut_manager = ShortcutManager(
            config_dir=Path(platformdirs.user_config_dir("your_app")),
            app_name="your_app",
            default_shortcuts=DEFAULT_SHORTCUTS,
        )
        self.shortcut_manager.load()
        self.setup_menu()

    def setup_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence(self.shortcut_manager.get_shortcut("save")))
        save_action.triggered.connect(self.save)
        file_menu.addAction(save_action)
```
