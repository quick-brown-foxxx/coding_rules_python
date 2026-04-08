"""Generic keyboard shortcuts manager for PySide6 apps.

This is a reusable shortcuts manager that can be copied to any PySide6 application.
It provides platform-specific default shortcuts and the ability to load custom
shortcuts from a TOML configuration file.

To use in another app:
------------------------
1. Copy the shared/shortcuts/ directory to your app
2. Define your DEFAULT_SHORTCUTS in your app's config.py:

    from your_app.shared.shortcuts.shortcuts import ActionShortcut

    DEFAULT_SHORTCUTS = (
        ActionShortcut("new_file", "New File", "Ctrl+N", "Ctrl+N", "Cmd+N"),
        ActionShortcut("save", "Save", "Ctrl+S", "Ctrl+S", "Cmd+S"),
        # ... add your shortcuts
    )

3. Initialize with your app's config directory and defaults:

    from your_app.shared.shortcuts.shortcuts import ShortcutManager
    from pathlib import Path

    config_dir = Path("~/.config/your_app").expanduser()
    manager = ShortcutManager(
        config_dir=config_dir,
        app_name="your_app",
        default_shortcuts=DEFAULT_SHORTCUTS,
    )

4. Use the manager to get shortcuts:

    shortcut = manager.get_shortcut("new_file")  # Returns "Ctrl+N"

5. For Qt integration, use QShortcut:

    from PySide6.QtGui import QKeySequence, QShortcut
    from PySide6.QtWidgets import QWidget

    widget = QWidget()
    key_seq = QKeySequence(manager.get_shortcut("save"))
    QShortcut(key_seq, widget, widget.save)

Configuration File:
--------------------
Shortcuts are stored in: <config_dir>/<app_name>_shortcuts.toml

The file is automatically created with defaults on first load.

Dependencies:
-------------
- PySide6 (Qt6)
- tomli, tomli-w (TOML parsing)
- rusty-results (Result types)
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, cast

import tomli
import tomli_w
from PySide6.QtGui import QKeySequence
from rusty_results.prelude import Err, Ok, Result

logger = logging.getLogger(__name__)

# Platform detection
IS_WINDOWS: Final[bool] = sys.platform == "win32"
IS_MACOS: Final[bool] = sys.platform == "darwin"
IS_LINUX: Final[bool] = not IS_WINDOWS and not IS_MACOS


@dataclass(slots=True, frozen=True)
class ActionShortcut:
    """Immutable definition of a keyboard shortcut for an action.

    Attributes:
        action_id: Unique identifier for the action (snake_case)
        display_name: Human-readable name for UI display
        default_linux: Default key sequence for Linux (e.g., "Ctrl+N")
        default_windows: Default key sequence for Windows (e.g., "Ctrl+N")
        default_macos: Default key sequence for macOS (e.g., "Cmd+N")

    Note:
        Use "Return" for the main Enter key, not "Enter". "Enter" maps to the
        numpad Enter key on some platforms, while "Return" is the standard
        keyboard Enter key that works consistently across all platforms.
    """

    action_id: str
    display_name: str
    default_linux: str
    default_windows: str = ""
    default_macos: str = ""

    def __post_init__(self) -> None:
        # If platform-specific defaults not provided, use Linux as fallback
        if not self.default_windows:
            object.__setattr__(self, "default_windows", self.default_linux)
        if not self.default_macos:
            object.__setattr__(self, "default_macos", self.default_linux)

    def get_default_for_platform(self) -> str:
        """Get the default shortcut for the current platform."""
        if IS_WINDOWS:
            return self.default_windows
        if IS_MACOS:
            return self.default_macos
        return self.default_linux


def _validate_key_sequence(sequence: str) -> Result[QKeySequence, str]:
    """Validate a key sequence string.

    Args:
        sequence: Key sequence string (e.g., "Ctrl+N")

    Returns:
        Ok(QKeySequence) if valid, Err(message) if invalid
    """
    if not sequence:
        # Empty sequence is valid (no shortcut)
        return Ok(QKeySequence())

    key_seq = QKeySequence(sequence)
    if key_seq.isEmpty():
        return Err(f"Invalid key sequence: '{sequence}'")

    # Also check if the sequence has a valid string representation.
    # Some invalid sequences like "Invalid+++" don't return isEmpty()=True
    # but produce an empty toString(), which indicates invalid parsing.
    if key_seq.toString() == "":
        return Err(f"Invalid key sequence: '{sequence}'")

    return Ok(key_seq)


@dataclass(slots=True)  # lint-ignore[unfrozen-dataclass]: mutable config loaded from TOML, updated at runtime
class ShortcutConfig:
    """Loaded shortcut configuration.

    Attributes:
        shortcuts: Dict mapping action_id to key sequence string
    """

    shortcuts: dict[str, str] = field(default_factory=dict)  # lint-ignore[raw-dict]: TOML key sequences

    _TOML_HEADER = """# Edit keyboard shortcuts using Qt QKeySequence string format.
#
# MODIFIERS: Ctrl, Shift, Alt, Meta (use '+' to combine, e.g. 'Ctrl+S')
# SPECIAL KEYS: Return (Enter key), Backspace, Delete, Tab, Escape, Space, F1-F35
# NAVIGATION: Left, Right, Up, Down, Home, End, PageUp, PageDown
#
# EXAMPLES:
#   "Ctrl+S"         - Control+S
#   "Return"         - Enter key (use 'Return' not 'Enter')
#   "Shift+Delete"   - Shift+Delete
#   "Alt+Left"       - Alt+Left arrow
#   "F5"             - F5 key
#   ""               - Empty string disables the shortcut
"""

    def to_toml(self) -> str:
        """Serialize to TOML string with header comment."""
        # Build the shortcuts section
        toml_data: dict[str, dict[str, str]] = {"shortcuts": self.shortcuts}
        body = tomli_w.dumps(toml_data)
        return self._TOML_HEADER + "\n" + body

    @staticmethod
    def from_toml(
        data: dict[str, object],  # lint-ignore[restricted-object]: TOML dict  # lint-ignore[raw-dict]: TOML data
    ) -> Result[ShortcutConfig, str]:
        """Deserialize from TOML dict, with validation.

        Invalid shortcuts are logged as warnings and skipped rather than
        causing the entire config to fail.

        Args:
            data: Dictionary with "shortcuts" key mapping action_id to key sequence

        Returns:
            Ok(ShortcutConfig) if valid structure, Err(message) if structure invalid
        """
        if not isinstance(data, dict):
            return Err("Shortcut config must be a dictionary")

        shortcuts_obj = data.get("shortcuts", {})
        if not isinstance(shortcuts_obj, dict):
            return Err("'shortcuts' must be a dictionary")

        shortcuts: dict[str, str] = {}
        # Cast to dict[str, Any] to allow iteration with type checking
        shortcuts_dict: dict[str, Any] = cast(dict[str, Any], shortcuts_obj)
        for action_id, sequence in shortcuts_dict.items():  # type: ignore[assignment]  # cast to dict[str, Any] above handles typing, but items() still infers wrong types
            if not isinstance(action_id, str):
                logger.warning(f"Action ID must be a string, got {type(action_id).__name__}")
                continue

            # Allow empty string to disable shortcut
            if sequence == "" or sequence is None:
                shortcuts[action_id] = ""
                continue

            if not isinstance(sequence, str):
                logger.warning(f"Shortcut for '{action_id}' must be a string or null")
                continue

            # Validate the key sequence (sequence is str after isinstance check above)
            validation = _validate_key_sequence(sequence)
            if validation.is_err:
                logger.warning(f"Invalid shortcut for '{action_id}': {validation.unwrap_err()}")
                continue  # Skip this invalid shortcut but continue processing

            shortcuts[action_id] = sequence

        return Ok(ShortcutConfig(shortcuts=shortcuts))

    # Keep old from_dict method for backward compatibility with tests
    @staticmethod
    def from_dict(
        data: dict[str, object],  # lint-ignore[restricted-object]: TOML dict  # lint-ignore[raw-dict]: TOML data
    ) -> Result[ShortcutConfig, str]:
        """Deserialize from dict, with validation.

        This is an alias for from_toml for backward compatibility.

        Args:
            data: Dictionary with "shortcuts" key mapping action_id to key sequence

        Returns:
            Ok(ShortcutConfig) if valid structure, Err(message) if structure invalid
        """
        return ShortcutConfig.from_toml(data)

    def get_shortcut(self, action_id: str) -> str | None:
        """Get the configured shortcut for an action.

        Args:
            action_id: The action identifier

        Returns:
            The key sequence string, or None if not configured
        """
        return self.shortcuts.get(action_id)

    def set_shortcut(self, action_id: str, sequence: str) -> Result[None, str]:
        """Set a shortcut for an action.

        Args:
            action_id: The action identifier
            sequence: The key sequence string

        Returns:
            Ok(None) if valid, Err(message) if invalid
        """
        if sequence:
            validation = _validate_key_sequence(sequence)
            if validation.is_err:
                return Err(validation.unwrap_err())

        self.shortcuts[action_id] = sequence
        return Ok(None)

    def save(self, path: Path) -> Result[None, str]:
        """Save config to a TOML file.

        Args:
            path: Path to save the config file

        Returns:
            Ok(None) if successful, Err(message) if failed
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self.to_toml(), encoding="utf-8")
            return Ok(None)
        except OSError as exc:
            return Err(f"Failed to save shortcuts config: {exc}")


class ShortcutManager:
    """Manages keyboard shortcuts configuration.

    This class handles loading shortcuts from the config file and
    providing defaults for all supported actions.

    The manager is parameterized to work with any app:
    - config_dir: Directory where config files are stored
    - app_name: Name used for the config file (<app_name>_shortcuts.toml)
    - default_shortcuts: Tuple of ActionShortcut definitions
    """

    def __init__(
        self,
        config_dir: Path,
        app_name: str = "app",
        default_shortcuts: tuple[ActionShortcut, ...] = (),
    ) -> None:
        """Initialize ShortcutManager.

        Args:
            config_dir: Directory where config files are stored
            app_name: Name used for the config file (becomes <app_name>_shortcuts.toml)
            default_shortcuts: Tuple of ActionShortcut definitions for the app
        """
        self._config_dir = config_dir
        self._app_name = app_name
        self._default_shortcuts = default_shortcuts
        self._config_path: Path = config_dir / f"{app_name}_shortcuts.toml"
        self._config: ShortcutConfig | None = None

    @property
    def config_path(self) -> Path:
        """Get the path to the shortcuts config file."""
        return self._config_path

    def load(self) -> Result[ShortcutConfig, str]:
        """Load shortcuts from config file.

        If the file doesn't exist, creates it with default shortcuts.

        Returns:
            Ok(ShortcutConfig) if successful, Err(message) if failed
        """
        if self._config is not None:
            return Ok(self._config)

        if not self._config_path.exists():
            # Create default config
            result = self._create_default_config()
            if result.is_err:
                return result
            self._config = result.unwrap()
            return Ok(self._config)

        try:
            # tomli.loads returns Any, so we need to ignore the type error
            raw_data = tomli.loads(self._config_path.read_text(encoding="utf-8"))  # type: ignore[assignment]  # tomli.loads returns Any, need dict for downstream processing
        except tomli.TOMLDecodeError as exc:
            return Err(f"Invalid shortcuts file: {exc}")
        except OSError as exc:
            return Err(f"Failed to read shortcuts file: {exc}")

        if not isinstance(raw_data, dict):
            return Err("Invalid shortcuts file: expected a TOML table")

        config_result = ShortcutConfig.from_toml(cast(dict[str, object], raw_data))
        if config_result.is_ok:
            self._config = config_result.unwrap()
        else:
            logger.warning(f"Failed to load shortcuts config: {config_result.unwrap_err()}")
        return config_result

    def _create_default_config(self) -> Result[ShortcutConfig, str]:
        """Create default shortcuts config file.

        Returns:
            Ok(ShortcutConfig) if successful, Err(message) if failed
        """
        default_shortcuts: dict[str, str] = {}
        for action_shortcut in self._default_shortcuts:
            default_shortcuts[action_shortcut.action_id] = action_shortcut.get_default_for_platform()

        config = ShortcutConfig(shortcuts=default_shortcuts)
        save_result = config.save(self._config_path)
        if save_result.is_err:
            return Err(save_result.unwrap_err())

        self._config = config
        return Ok(config)

    def get_shortcut(self, action_id: str) -> str:
        """Get the shortcut for an action, with default fallback.

        Args:
            action_id: The action identifier

        Returns:
            The key sequence string (never None, defaults to platform default)
        """
        config_result = self.load()
        if config_result.is_err:
            logger.warning(f"Failed to load shortcuts: {config_result.unwrap_err()}")
            return self._get_default(action_id)

        config = config_result.unwrap()
        configured = config.get_shortcut(action_id)
        if configured is not None:
            return configured

        return self._get_default(action_id)

    def _get_default(self, action_id: str) -> str:
        """Get the default shortcut for an action.

        Args:
            action_id: The action identifier

        Returns:
            The default key sequence for the current platform
        """
        for action_shortcut in self._default_shortcuts:
            if action_shortcut.action_id == action_id:
                return action_shortcut.get_default_for_platform()
        return ""

    def reload(self) -> Result[ShortcutConfig, str]:
        """Reload shortcuts from config file.

        Useful after external editor modifies the file.

        Returns:
            Ok(ShortcutConfig) if successful, Err(message) if failed
        """
        self._config = None
        return self.load()
