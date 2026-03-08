---
name: python-testing-lightweight
description: Use when setting up or writing tests for a Python project - covers pytest configuration, fixtures, test philosophy, and test structure
---

# Python Testing (Lightweight)

## Overview

Tests prove features work. Coverage is secondary. E2e tests beat unit tests. Real beats mocked.

## Philosophy

- **Trustworthiness > coverage.** A test that mocks away the tested thing proves nothing.
- **5 good e2e tests > 100 unit tests** with heavy mocking.
- **20/80 rule.** Test where it gives the most confidence.
- **Unit tests for pure logic only.** Functions that transform data honestly.
- **Real over mocked.** Real HTTP servers (pytest-httpserver), real tmp dirs, real processes.

## Test Priority

1. CLI / e2e tests (run actual commands, check output + exit codes)
2. Integration tests (component interaction through public API)
3. Unit tests (pure data transformation functions)
4. Skip: framework glue, UI layout, trivial getters

## Setup

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
asyncio_mode = "auto"
markers = ["unit: unit tests", "integration: integration tests"]
```

```
tests/
├── unit/
├── integration/
├── fixtures/
└── conftest.py
```

## Key Fixture Patterns

```python
# Isolated environment
@pytest.fixture
def isolated_env(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))

# Real HTTP mock server
@pytest.fixture
def mock_api(httpserver):
    httpserver.expect_request("/api/data").respond_with_json({"ok": True})
    return httpserver
```

## Running

```bash
uv run poe test                    # All
uv run pytest tests/integration/   # Integration only
uv run pytest --cov                # With coverage
```

## Reference

See `guides/testing-lightweight.md` for full patterns. For containerized testing, see `guides/testing-heavyweight.md`.
