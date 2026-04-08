"""Generic keyboard shortcuts manager for PySide6 apps.

This module provides a reusable shortcuts configuration system that can be
copied to any PySide6 application.

Usage in your app:
1. Copy this module to your_app/shared/shortcuts/
2. Define DEFAULT_SHORTCUTS in your app's config.py
3. Initialize ShortcutManager with your app's config_dir and defaults

Example:
    from shared.shortcuts import ShortcutManager, ActionShortcut
    from your_app.config import DEFAULT_SHORTCUTS

    manager = ShortcutManager(
        config_dir=app_config_dir,
        app_name="myapp",
        default_shortcuts=DEFAULT_SHORTCUTS,
    )
"""

# Import validation function for advanced users who need custom validation
from reusable.shortcuts.shortcuts import (
    ActionShortcut,
    ShortcutConfig,
    ShortcutManager,
    validate_key_sequence,
)

__all__ = [
    "ActionShortcut",
    "ShortcutConfig",
    "ShortcutManager",
    "validate_key_sequence",
]
