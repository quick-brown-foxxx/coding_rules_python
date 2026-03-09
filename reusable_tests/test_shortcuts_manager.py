"""Generic tests for ShortcutManager class.

This module provides platform-independent, reusable tests for the ShortcutManager
class that can be used across multiple applications.

These tests are generic because ShortcutManager itself is generic - it just takes
any shortcuts array and path/app strings as inputs. The tests use dummy/example
shortcuts and don't depend on any app-specific configuration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

from reusable.shortcuts.shortcuts import ActionShortcut, ShortcutManager

# Define dummy shortcuts for testing - these are generic and not app-specific
DUMMY_SHORTCUTS: Final = (
    ActionShortcut("test_action", "Test Action", "Ctrl+T", "Ctrl+T", "Cmd+T"),
    ActionShortcut("another_action", "Another Action", "Ctrl+A", "Ctrl+A", "Cmd+A"),
    ActionShortcut("save_action", "Save", "Ctrl+S", "Ctrl+S", "Cmd+S"),
    ActionShortcut("open_action", "Open", "Ctrl+O", "Ctrl+O", "Cmd+O"),
)


class TestShortcutManager:
    """Generic tests for ShortcutManager class.

    These tests are generic because they use dummy shortcuts and don't depend
    on any app-specific configuration or mocks. The ShortcutManager class itself
    is generic and just takes any shortcuts array and path/app strings.
    """

    def test_config_path_property(self, tmp_path: Path) -> None:
        """Test that config_path returns correct path."""
        manager = ShortcutManager(
            config_dir=tmp_path,
            app_name="testapp",
            default_shortcuts=DUMMY_SHORTCUTS,
        )
        assert manager.config_path == tmp_path / "testapp_shortcuts.toml"

    def test_load_creates_default_config(self, tmp_path: Path) -> None:
        """Test that load creates default config if file doesn't exist."""
        manager = ShortcutManager(
            config_dir=tmp_path,
            app_name="testapp",
            default_shortcuts=DUMMY_SHORTCUTS,
        )
        result = manager.load()

        assert result.is_ok
        config = result.unwrap()
        assert config.get_shortcut("test_action") is not None
        assert (tmp_path / "testapp_shortcuts.toml").exists()

    def test_load_existing_config(self, tmp_path: Path) -> None:
        """Test loading an existing config file."""
        import tomli_w

        # Create config file
        config_path = tmp_path / "testapp_shortcuts.toml"
        config_path.write_text(
            tomli_w.dumps({"shortcuts": {"test_action": "Ctrl+Shift+T"}}),
            encoding="utf-8",
        )

        manager = ShortcutManager(
            config_dir=tmp_path,
            app_name="testapp",
            default_shortcuts=DUMMY_SHORTCUTS,
        )
        result = manager.load()

        assert result.is_ok
        assert result.unwrap().get_shortcut("test_action") == "Ctrl+Shift+T"

    def test_load_config_with_invalid_shortcuts(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """Test loading config with some invalid shortcuts logs warnings but succeeds."""
        import logging

        import tomli_w

        caplog.set_level(logging.WARNING)

        # Create config file with valid and invalid shortcuts
        config_path = tmp_path / "testapp_shortcuts.toml"
        config_path.write_text(
            tomli_w.dumps({"shortcuts": {"test_action": "Ctrl+T", "invalid_action": "Invalid+++"}}),
            encoding="utf-8",
        )

        manager = ShortcutManager(
            config_dir=tmp_path,
            app_name="testapp",
            default_shortcuts=DUMMY_SHORTCUTS,
        )
        result = manager.load()

        # Should succeed despite invalid shortcuts
        assert result.is_ok
        config = result.unwrap()
        assert config.get_shortcut("test_action") == "Ctrl+T"
        assert config.get_shortcut("invalid_action") is None  # Skipped

        # Should have logged a warning
        assert any("Invalid shortcut for 'invalid_action'" in record.message for record in caplog.records)

    def test_load_invalid_toml(self, tmp_path: Path) -> None:
        """Test loading invalid TOML returns error."""
        config_path = tmp_path / "testapp_shortcuts.toml"
        config_path.write_text("invalid toml [", encoding="utf-8")

        manager = ShortcutManager(
            config_dir=tmp_path,
            app_name="testapp",
            default_shortcuts=DUMMY_SHORTCUTS,
        )
        result = manager.load()

        assert result.is_err
        assert "Invalid shortcuts file" in result.unwrap_err()

    def test_get_shortcut_with_default_fallback(self, tmp_path: Path) -> None:
        """Test that get_shortcut falls back to default when not configured."""
        manager = ShortcutManager(
            config_dir=tmp_path,
            app_name="testapp",
            default_shortcuts=DUMMY_SHORTCUTS,
        )
        # Should return default even without loading
        shortcut = manager.get_shortcut("test_action")
        assert shortcut  # Should not be empty

    def test_reload(self, tmp_path: Path) -> None:
        """Test reloading config from file."""
        import tomli_w

        manager = ShortcutManager(
            config_dir=tmp_path,
            app_name="testapp",
            default_shortcuts=DUMMY_SHORTCUTS,
        )

        # Initial load
        manager.load()
        initial = manager.get_shortcut("test_action")

        # Modify file externally
        config_path = tmp_path / "testapp_shortcuts.toml"
        config_path.write_text(
            tomli_w.dumps({"shortcuts": {"test_action": "Ctrl+Shift+T"}}),
            encoding="utf-8",
        )

        # Reload
        manager.reload()
        modified = manager.get_shortcut("test_action")

        assert modified == "Ctrl+Shift+T"
        assert modified != initial
