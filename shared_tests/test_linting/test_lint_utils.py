"""Tests for lint_utils shared utilities."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from shared.linting.lint_utils import (
    collect_files,
    has_bare_ignore,
    is_final_annotation,
    is_ignored,
    read_source_lines,
    report,
)


class TestCollectFiles:
    def test_explicit_py_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "a.py").write_text("# a")
        (tmp_path / "b.txt").write_text("# b")
        result = collect_files(["a.py", "b.txt", "c.py"])
        assert result == [Path("a.py"), Path("c.py")]

    def test_empty_args_scans_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "main.py").write_text("# main")
        sub = tmp_path / "pkg"
        sub.mkdir()
        (sub / "mod.py").write_text("# mod")
        result = collect_files([])
        paths = {str(p) for p in result}
        assert "main.py" in paths
        assert str(Path("pkg/mod.py")) in paths

    def test_excluded_dirs_skipped(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "good.py").write_text("# ok")
        for dirname in (".venv", "__pycache__", "node_modules", "fixtures"):
            d = tmp_path / dirname
            d.mkdir()
            (d / "hidden.py").write_text("# hidden")
        result = collect_files([])
        names = [p.name for p in result]
        assert "good.py" in names
        assert "hidden.py" not in names


class TestIsIgnored:
    def test_matching_check_name(self) -> None:
        line = "x = []  # lint-ignore[mutable-module]: needed for cache"
        assert is_ignored(line, "mutable-module") is True

    def test_non_matching_check_name(self) -> None:
        line = "x = []  # lint-ignore[mutable-module]: needed for cache"
        assert is_ignored(line, "unfrozen-dataclass") is False

    def test_multiple_ignores_on_one_line(self) -> None:
        line = "x: object = {}  # lint-ignore[raw-dict]: ok  # lint-ignore[mutable-module]: ok"
        assert is_ignored(line, "raw-dict") is True
        assert is_ignored(line, "mutable-module") is True
        assert is_ignored(line, "other-check") is False

    def test_multiple_ignores_mixed_bare_and_with_rationale(self) -> None:
        line = "x: object = {}  # lint-ignore[restricted-object]  # lint-ignore[raw-dict]: boundary shim"
        assert is_ignored(line, "restricted-object") is False
        assert is_ignored(line, "raw-dict") is True

    def test_no_ignore_comment(self) -> None:
        line = "x = 42  # just a regular comment"
        assert is_ignored(line, "anything") is False


class TestHasBareIgnore:
    def test_with_rationale_is_not_bare(self) -> None:
        line = "x = []  # lint-ignore[mutable-module]: needed for cache"
        assert has_bare_ignore(line, "mutable-module") is False

    def test_without_rationale_is_bare(self) -> None:
        line = "x = []  # lint-ignore[mutable-module]"
        assert has_bare_ignore(line, "mutable-module") is True

    def test_colon_no_text_is_bare(self) -> None:
        line = "x = []  # lint-ignore[mutable-module]:"
        assert has_bare_ignore(line, "mutable-module") is True

    def test_no_ignore_at_all(self) -> None:
        line = "x = 42"
        assert has_bare_ignore(line, "mutable-module") is False

    def test_bare_ignore_when_other_check_has_rationale(self) -> None:
        line = "x: object = {}  # lint-ignore[restricted-object]  # lint-ignore[raw-dict]: boundary shim"
        assert has_bare_ignore(line, "restricted-object") is True
        assert has_bare_ignore(line, "raw-dict") is False

    def test_bare_ignore_wrong_check_name(self) -> None:
        line = "x = []  # lint-ignore[mutable-module]"
        assert has_bare_ignore(line, "other-check") is False


class TestReadSourceLines:
    def test_valid_py_file(self, tmp_path: Path) -> None:
        f = tmp_path / "sample.py"
        f.write_text("line1\nline2\nline3", encoding="utf-8")
        lines = read_source_lines(f)
        assert lines == ["line1", "line2", "line3"]

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        f = tmp_path / "missing.py"
        assert read_source_lines(f) == []

    def test_encoding_error(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.py"
        f.write_bytes(b"\x80\x81\x82\xff")
        assert read_source_lines(f) == []


class TestIsFinalAnnotation:
    def test_bare_final(self) -> None:
        node = ast.parse("x: Final = 1", mode="exec").body[0]
        assert is_final_annotation(node.annotation) is True  # type: ignore[attr-defined]  # ast.parse("x: ... = ...") returns stmt; tests intentionally access AnnAssign.annotation

    def test_typing_final(self) -> None:
        node = ast.parse("x: typing.Final = 1", mode="exec").body[0]
        assert is_final_annotation(node.annotation) is True  # type: ignore[attr-defined]  # ast.parse("x: ... = ...") returns stmt; tests intentionally access AnnAssign.annotation

    def test_final_with_type_param(self) -> None:
        node = ast.parse("x: Final[int] = 1", mode="exec").body[0]
        assert is_final_annotation(node.annotation) is True  # type: ignore[attr-defined]  # ast.parse("x: ... = ...") returns stmt; tests intentionally access AnnAssign.annotation

    def test_typing_final_with_type_param(self) -> None:
        node = ast.parse("x: typing.Final[str] = ''", mode="exec").body[0]
        assert is_final_annotation(node.annotation) is True  # type: ignore[attr-defined]  # ast.parse("x: ... = ...") returns stmt; tests intentionally access AnnAssign.annotation

    def test_none_annotation(self) -> None:
        assert is_final_annotation(None) is False

    def test_non_final_annotation(self) -> None:
        node = ast.parse("x: int = 1", mode="exec").body[0]
        assert is_final_annotation(node.annotation) is False  # type: ignore[attr-defined]  # ast.parse("x: ... = ...") returns stmt; tests intentionally access AnnAssign.annotation

    def test_non_final_subscript(self) -> None:
        node = ast.parse("x: list[int] = []", mode="exec").body[0]
        assert is_final_annotation(node.annotation) is False  # type: ignore[attr-defined]  # ast.parse("x: ... = ...") returns stmt; tests intentionally access AnnAssign.annotation


class TestReport:
    def test_output_format(self) -> None:
        result = report(Path("src/main.py"), 42, "my-check", "something is wrong")
        assert result == "src/main.py:42: [my-check] something is wrong"

    def test_output_format_line_one(self) -> None:
        result = report(Path("a.py"), 1, "check", "msg")
        assert result == "a.py:1: [check] msg"
