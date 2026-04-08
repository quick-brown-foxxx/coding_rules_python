"""Generic, reusable tests for keyboard shortcuts configuration.

This module provides platform-independent, reusable test classes for keyboard
shortcuts that can be used across multiple applications.

ADAPTING FOR YOUR APP:
    These tests use dummy/example shortcuts and are designed to be generic.
    To use them in your app:

    1. Import the base test classes:
       from shared_tests.test_shortcuts_base import (
           TestActionShortcut,
           TestValidateKeySequence,
           TestShortcutConfig,
           TestShortcutConfigSave,
       )

    2. Create app-specific test classes that inherit from these bases

    3. Add app-specific tests that reference your app's DEFAULT_SHORTCUTS

    4. These generic tests cover:
       - ActionShortcut dataclass behavior
       - Key sequence validation
       - ShortcutConfig serialization/deserialization
       - Save/load functionality

    NOTE: Tests for ShortcutManager are NOT included here because they
    require app-specific mocks and configuration. Each app should write
    their own ShortcutManager tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final, cast

import pytest

from reusable.shortcuts import (
    ActionShortcut,
    ShortcutConfig,
    validate_key_sequence,
)


class TestActionShortcut:
    """Generic tests for ActionShortcut dataclass.

    These tests verify the core behavior of the ActionShortcut dataclass
    without depending on app-specific default shortcuts.

    App-specific tests that verify DEFAULT_SHORTCUTS content should be
    written in each app's test file.
    """

    def test_get_default_for_platform_linux(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting Linux default shortcut.

        This test uses a dummy shortcut to verify the platform selection logic.
        """
        # Ensure we're on Linux for this test
        monkeypatch.setattr("reusable.shortcuts.shortcuts.IS_WINDOWS", False)
        monkeypatch.setattr("reusable.shortcuts.shortcuts.IS_MACOS", False)
        monkeypatch.setattr("reusable.shortcuts.shortcuts.IS_LINUX", True)

        # Create a dummy shortcut with platform-specific defaults
        shortcut = ActionShortcut(
            action_id="test_action",
            display_name="Test Action",
            default_linux="Ctrl+L",
            default_windows="Ctrl+W",
            default_macos="Cmd+M",
        )
        assert shortcut.get_default_for_platform() == "Ctrl+L"

    def test_get_default_for_platform_windows(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting Windows default shortcut.

        This test uses a dummy shortcut to verify the platform selection logic.
        """
        # Ensure we're on Windows for this test
        monkeypatch.setattr("reusable.shortcuts.shortcuts.IS_WINDOWS", True)
        monkeypatch.setattr("reusable.shortcuts.shortcuts.IS_MACOS", False)
        monkeypatch.setattr("reusable.shortcuts.shortcuts.IS_LINUX", False)

        # Create a dummy shortcut with platform-specific defaults
        shortcut = ActionShortcut(
            action_id="test_action",
            display_name="Test Action",
            default_linux="Ctrl+L",
            default_windows="Ctrl+W",
            default_macos="Cmd+M",
        )
        assert shortcut.get_default_for_platform() == "Ctrl+W"

    def test_get_default_for_platform_macos(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting macOS default shortcut.

        This test uses a dummy shortcut to verify the platform selection logic.
        """
        # Ensure we're on macOS for this test
        monkeypatch.setattr("reusable.shortcuts.shortcuts.IS_WINDOWS", False)
        monkeypatch.setattr("reusable.shortcuts.shortcuts.IS_MACOS", True)
        monkeypatch.setattr("reusable.shortcuts.shortcuts.IS_LINUX", False)

        # Create a dummy shortcut with platform-specific defaults
        shortcut = ActionShortcut(
            action_id="test_action",
            display_name="Test Action",
            default_linux="Ctrl+L",
            default_windows="Ctrl+W",
            default_macos="Cmd+M",
        )
        assert shortcut.get_default_for_platform() == "Cmd+M"

    def test_get_default_fallback(self) -> None:
        """Test that Linux default is used as fallback when platform-specific defaults are not provided.

        When only default_linux is provided, it should be used for all platforms.
        """
        shortcut = ActionShortcut(
            action_id="test_action",
            display_name="Test Action",
            default_linux="Ctrl+L",
            # default_windows and default_macos omitted, should fallback to Linux
        )
        assert shortcut.default_windows == "Ctrl+L"
        assert shortcut.default_macos == "Ctrl+L"

    def test_get_default_with_explicit_empty_defaults(self) -> None:
        """Test behavior when empty strings are explicitly provided for platform defaults.

        Empty strings should still be replaced with the Linux default in __post_init__.
        """
        shortcut = ActionShortcut(
            action_id="test_action",
            display_name="Test Action",
            default_linux="Ctrl+L",
            default_windows="",  # Empty string
            default_macos="",  # Empty string
        )
        # Empty strings should be replaced with Linux default
        assert shortcut.default_windows == "Ctrl+L"
        assert shortcut.default_macos == "Ctrl+L"


class TestValidateKeySequence:
    """Generic tests for validate_key_sequence function.

    These tests verify key sequence validation logic without depending
    on app-specific shortcuts or configuration.
    """

    def test_valid_sequences(self) -> None:
        """Test validation of valid key sequences.

        Tests common valid key sequence formats that should be accepted.
        """
        valid_sequences: Final = [
            "Ctrl+N",  # Basic modifier + key
            "Ctrl+Shift+E",  # Multiple modifiers
            "F5",  # Function key
            "Del",  # Special key
            "Return",  # Enter key (recommended over "Enter")
            "",  # Empty sequence (disabled shortcut)
            "Ctrl+Return",  # Modifier + Enter
            "Shift+Delete",  # Shift + special key
            "Alt+Left",  # Alt + arrow key
            "Meta+S",  # Meta/Win/Cmd key
        ]

        for seq in valid_sequences:
            result = validate_key_sequence(seq)
            assert result.is_ok, f"Sequence '{seq}' should be valid"
            if seq:
                # Non-empty sequences should not be empty QKeySequences
                assert not result.unwrap().isEmpty(), f"Sequence '{seq}' should not be empty"

    def test_invalid_sequences(self) -> None:
        """Test validation of invalid key sequences.

        Note: QKeySequence may accept some sequences that seem invalid
        (like "Invalid+Key") by creating a sequence with unknown keys.
        The validation primarily catches truly malformed sequences.

        This test documents the current behavior rather than enforcing
        strict validation, as Qt's QKeySequence is permissive.
        """
        # Test truly invalid sequences
        invalid_sequences = [
            "Ctrl+",  # Modifier without key
            "+++",  # Multiple modifiers without key
            "Shift+",  # Modifier without key
        ]

        for seq in invalid_sequences:
            result = validate_key_sequence(seq)
            assert result.is_err, f"'{seq}' should be rejected"


class TestShortcutConfig:
    """Generic tests for ShortcutConfig dataclass.

    These tests verify serialization, deserialization, and manipulation
    of shortcut configurations without depending on app-specific shortcuts.
    """

    def test_to_toml(self) -> None:
        """Test serialization to TOML format.

        Verifies that ShortcutConfig can be serialized to TOML with
        proper formatting and header comments.
        """
        # Create a config with dummy shortcuts
        config = ShortcutConfig(shortcuts={"test_action": "Ctrl+T", "another_action": "F5"})
        toml_str = config.to_toml()

        # Verify structure
        assert "shortcuts" in toml_str
        assert "test_action" in toml_str
        assert "Ctrl+T" in toml_str
        assert "another_action" in toml_str
        assert "F5" in toml_str

        # Check for header comment
        assert "# Edit keyboard shortcuts" in toml_str
        assert "# MODIFIERS:" in toml_str

    def test_from_toml_valid(self) -> None:
        """Test deserialization from valid TOML dict.

        Verifies that valid TOML data can be loaded into a ShortcutConfig.
        """
        data: dict[str, object] = {  # lint-ignore[restricted-object]: testing untyped input
            "shortcuts": {
                "test_action": "Ctrl+T",
                "another_action": "F5",
                "disabled_action": "",  # Empty string to disable
            }
        }

        result = ShortcutConfig.from_toml(data)
        assert result.is_ok, "Should successfully load valid TOML"

        config = result.unwrap()
        assert config.get_shortcut("test_action") == "Ctrl+T"
        assert config.get_shortcut("another_action") == "F5"
        assert config.get_shortcut("disabled_action") == ""

    def test_from_toml_invalid_type(self) -> None:
        """Test deserialization fails when input is not a dictionary.

        Verifies proper error handling for invalid input types.
        """
        result = ShortcutConfig.from_toml("not a dict")  # type: ignore[arg-type]  # intentionally passing wrong type to test error handling
        assert result.is_err
        assert "must be a dictionary" in result.unwrap_err()

    def test_from_toml_invalid_shortcuts_type(self) -> None:
        """Test deserialization fails when shortcuts is not a dict.

        Verifies proper error handling when shortcuts field has wrong type.
        """
        result = ShortcutConfig.from_toml({"shortcuts": "not a dict"})
        assert result.is_err
        assert "'shortcuts' must be a dictionary" in result.unwrap_err()

    def test_from_dict_valid(self) -> None:
        """Test deserialization from valid dict (backward compatibility).

        The from_dict method is an alias for from_toml for backward compatibility.
        """
        data: dict[str, object] = {  # lint-ignore[restricted-object]: testing untyped input
            "shortcuts": {
                "test_action": "Ctrl+T",
                "another_action": "F5",
                "disabled_action": "",
            }
        }

        result = ShortcutConfig.from_dict(data)
        assert result.is_ok

        config = result.unwrap()
        assert config.get_shortcut("test_action") == "Ctrl+T"
        assert config.get_shortcut("another_action") == "F5"
        assert config.get_shortcut("disabled_action") == ""

    def test_from_toml_invalid_key_sequence(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that invalid key sequences are logged and skipped.

        Invalid shortcuts should not prevent loading of valid shortcuts.
        A warning should be logged for each invalid shortcut.
        """
        import logging

        caplog.set_level(logging.WARNING)

        data: dict[str, object] = {  # lint-ignore[restricted-object]: testing untyped input
            "shortcuts": {
                "valid_action": "Ctrl+N",
                "invalid_action": "Invalid+++",  # Invalid sequence
                "another_valid": "F5",
            }
        }
        result = ShortcutConfig.from_toml(data)

        # Should succeed but log a warning about the invalid shortcut
        assert result.is_ok, "Should succeed despite invalid shortcut"
        assert any("Invalid shortcut for 'invalid_action'" in record.message for record in caplog.records), (
            "Should log warning about invalid shortcut"
        )

        # Valid shortcuts should still be loaded
        config = result.unwrap()
        assert config.get_shortcut("valid_action") == "Ctrl+N"
        assert config.get_shortcut("another_valid") == "F5"
        assert config.get_shortcut("invalid_action") is None  # Skipped due to invalid value

    def test_from_toml_invalid_action_id(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that non-string action IDs are logged and skipped.

        Action IDs must be strings; other types should be rejected with a warning.
        """
        import logging

        caplog.set_level(logging.WARNING)

        data: dict[str, object] = {  # lint-ignore[restricted-object]: testing untyped input
            "shortcuts": {
                "valid_action": "Ctrl+N",
                123: "Ctrl+E",  # type: ignore[dict-item]  # intentionally passing non-string key to test validation
            }
        }
        result = ShortcutConfig.from_toml(data)

        # Should succeed but log a warning about the invalid action ID
        assert result.is_ok
        assert any("Action ID must be a string" in record.message for record in caplog.records)

        # Valid shortcuts should still be loaded
        config = result.unwrap()
        assert config.get_shortcut("valid_action") == "Ctrl+N"

    def test_from_toml_invalid_sequence_type(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that non-string sequences are logged and skipped.

        Shortcut sequences must be strings or null; other types should be rejected.
        """
        import logging

        caplog.set_level(logging.WARNING)

        data: dict[str, object] = {  # lint-ignore[restricted-object]: testing untyped input
            "shortcuts": {
                "valid_action": "Ctrl+N",
                "invalid_action": 123,  # type: ignore[dict-item]  # intentionally passing non-string value to test validation
            }
        }
        result = ShortcutConfig.from_toml(data)

        # Should succeed but log a warning about the invalid sequence type
        assert result.is_ok
        assert any("must be a string or null" in record.message for record in caplog.records)

        # Valid shortcuts should still be loaded
        config = result.unwrap()
        assert config.get_shortcut("valid_action") == "Ctrl+N"
        assert config.get_shortcut("invalid_action") is None  # Skipped

    def test_from_toml_null_sequence(self) -> None:
        """Test that null sequences are treated as disabled shortcuts.

        A null (None) value should be treated the same as an empty string.
        """
        data: dict[str, object] = {  # lint-ignore[restricted-object]: testing untyped input
            "shortcuts": {
                "disabled_action": None,  # type: ignore[dict-item]  # intentionally passing None to test null-as-disabled handling
            }
        }
        result = ShortcutConfig.from_toml(data)

        assert result.is_ok
        config = result.unwrap()
        assert config.get_shortcut("disabled_action") == ""

    def test_get_shortcut_not_configured(self) -> None:
        """Test getting a shortcut that wasn't configured.

        Should return None for actions that haven't been configured.
        """
        config = ShortcutConfig(shortcuts={})
        assert config.get_shortcut("nonexistent") is None

    def test_set_shortcut_valid(self) -> None:
        """Test setting a valid shortcut.

        Should successfully add a new shortcut to the configuration.
        """
        config = ShortcutConfig(shortcuts={})
        result = config.set_shortcut("test_action", "Ctrl+T")

        assert result.is_ok
        assert config.get_shortcut("test_action") == "Ctrl+T"

    def test_set_shortcut_invalid(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test setting an invalid shortcut.

        Note: QKeySequence may accept sequences with unknown keys.
        The set_shortcut method validates but may accept some invalid-looking
        sequences due to Qt's permissive parsing.

        This test documents the current behavior rather than enforcing
        strict rejection of invalid sequences.
        """
        config = ShortcutConfig(shortcuts={})
        result = config.set_shortcut("test_action", "Invalid+++")

        assert result.is_err

    def test_set_shortcut_empty(self) -> None:
        """Test setting an empty shortcut (disable).

        Empty strings are valid and represent disabled shortcuts.
        """
        config = ShortcutConfig(shortcuts={})
        result = config.set_shortcut("test_action", "")

        assert result.is_ok
        assert config.get_shortcut("test_action") == ""

    def test_set_shortcut_overwrite(self) -> None:
        """Test overwriting an existing shortcut.

        Setting a shortcut for an action that already has one should
        replace the existing value.
        """
        config = ShortcutConfig(shortcuts={"test_action": "Ctrl+T"})

        # Overwrite with new shortcut
        result = config.set_shortcut("test_action", "Ctrl+Shift+T")
        assert result.is_ok
        assert config.get_shortcut("test_action") == "Ctrl+Shift+T"


class TestShortcutConfigSave:
    """Generic tests for ShortcutConfig.save method.

    These tests verify file I/O operations for shortcut configurations.
    """

    def test_save_and_load(self, tmp_path: Path) -> None:
        """Test saving and loading config file.

        Verifies that a config can be saved to disk and loaded back
        with the same values.
        """
        # Create a config with dummy shortcuts
        config = ShortcutConfig(shortcuts={"test_action": "Ctrl+T"})
        save_path = tmp_path / "shortcuts.toml"

        # Save
        save_result = config.save(save_path)
        assert save_result.is_ok
        assert save_path.exists()

        # Load and verify
        import tomli

        loaded: dict[str, Any] = tomli.loads(save_path.read_text(encoding="utf-8"))
        shortcuts = cast(dict[str, Any], loaded.get("shortcuts"))
        assert shortcuts is not None
        assert isinstance(shortcuts, dict)
        assert cast(str, shortcuts.get("test_action")) == "Ctrl+T"

    def test_save_creates_directories(self, tmp_path: Path) -> None:
        """Test that save creates parent directories.

        Verifies that save() creates parent directories if they don't exist.
        """
        config = ShortcutConfig(shortcuts={})
        save_path = tmp_path / "subdir" / "nested" / "shortcuts.toml"

        save_result = config.save(save_path)
        assert save_result.is_ok
        assert save_path.exists()

    def test_save_includes_header(self, tmp_path: Path) -> None:
        """Test that saved file includes header comments.

        Verifies that the saved TOML file includes the helpful header
        comments that explain the format.
        """
        config = ShortcutConfig(shortcuts={"test_action": "Ctrl+T"})
        save_path = tmp_path / "shortcuts.toml"

        save_result = config.save(save_path)
        assert save_result.is_ok

        content = save_path.read_text(encoding="utf-8")
        assert "# Edit keyboard shortcuts" in content
        assert "# MODIFIERS:" in content

    def test_save_empty_config(self, tmp_path: Path) -> None:
        """Test saving an empty configuration.

        Verifies that a config with no shortcuts can be saved and loaded.
        """
        config = ShortcutConfig(shortcuts={})
        save_path = tmp_path / "shortcuts.toml"

        save_result = config.save(save_path)
        assert save_result.is_ok

        # Load and verify
        import tomli

        loaded: dict[str, Any] = tomli.loads(save_path.read_text(encoding="utf-8"))
        shortcuts = cast(dict[str, Any], loaded.get("shortcuts"))
        assert shortcuts is not None
        assert isinstance(shortcuts, dict)
        assert len(shortcuts) == 0

    def test_save_multiple_shortcuts(self, tmp_path: Path) -> None:
        """Test saving a configuration with multiple shortcuts.

        Verifies that all shortcuts are preserved when saving and loading.
        """
        config = ShortcutConfig(
            shortcuts={
                "action1": "Ctrl+A",
                "action2": "Ctrl+B",
                "action3": "F5",
                "action4": "",  # Disabled
            }
        )
        save_path = tmp_path / "shortcuts.toml"

        save_result = config.save(save_path)
        assert save_result.is_ok

        # Load and verify all shortcuts
        import tomli

        loaded: dict[str, Any] = tomli.loads(save_path.read_text(encoding="utf-8"))
        shortcuts = cast(dict[str, Any], loaded.get("shortcuts"))
        assert shortcuts is not None
        assert isinstance(shortcuts, dict)

        assert cast(str, shortcuts.get("action1")) == "Ctrl+A"
        assert cast(str, shortcuts.get("action2")) == "Ctrl+B"
        assert cast(str, shortcuts.get("action3")) == "F5"
        assert cast(str, shortcuts.get("action4")) == ""

    def test_save_overwrites_existing(self, tmp_path: Path) -> None:
        """Test that save overwrites an existing file.

        Verifies that saving to an existing file replaces its contents.
        """
        # Create initial file
        config1 = ShortcutConfig(shortcuts={"old_action": "Ctrl+O"})
        save_path = tmp_path / "shortcuts.toml"
        config1.save(save_path)

        # Overwrite with new config
        config2 = ShortcutConfig(shortcuts={"new_action": "Ctrl+N"})
        config2.save(save_path)

        # Load and verify it has new content
        import tomli

        loaded: dict[str, Any] = tomli.loads(save_path.read_text(encoding="utf-8"))
        shortcuts = cast(dict[str, Any], loaded.get("shortcuts"))
        assert shortcuts is not None
        assert isinstance(shortcuts, dict)

        assert "old_action" not in shortcuts
        assert cast(str, shortcuts.get("new_action")) == "Ctrl+N"
