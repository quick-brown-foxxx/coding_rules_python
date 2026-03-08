# Testing Guide (Lightweight)

Practical pytest setup for most projects. See [PHILOSOPHY.md](../PHILOSOPHY.md) section 5.

---

## Philosophy Recap

- Tests prove features work, not produce green checkmarks
- E2e/CLI tests are the primary safety net
- Unit tests for pure logic only
- Real over mocked. 20/80 rule.
- Coverage is a guideline, not a goal

---

## Project Setup

### Directory Structure

```
tests/
├── unit/              # Pure function tests
├── integration/       # CLI tests, component interaction
├── fixtures/          # Shared test data and helpers
└── conftest.py        # Shared fixtures
```

### pyproject.toml Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"

markers = [
    "unit: unit tests",
    "integration: integration tests",
]
```

### Dependencies

```toml
[dependency-groups]
dev = [
    "pytest>=9.0.1",
    "pytest-cov>=7.0.0",
    "pytest-asyncio>=1.3.0",
    # "pytest-qt>=4.5.0",          # For Qt apps
    # "pytest-httpserver>=1.1.0",  # For HTTP mocking
]
```

---

## What to Test (Priority Order)

1. **CLI/e2e tests** — run the actual command, check output and exit codes
2. **Integration tests** — test component interactions through public API
3. **Unit tests** — pure functions that transform data (worth testing honestly)
4. **Skip** — testing framework glue, UI layout, trivial getters/setters

### CLI Test Example

```python
import subprocess

def test_list_profiles_empty() -> None:
    result = subprocess.run(
        ["uv", "run", "poe", "app", "list"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "No profiles found" in result.stdout

def test_create_and_list_profile(tmp_path: Path) -> None:
    env = {**os.environ, "APP_DATA_DIR": str(tmp_path)}
    subprocess.run(
        ["uv", "run", "poe", "app", "create", "test-profile"],
        env=env, check=True,
    )
    result = subprocess.run(
        ["uv", "run", "poe", "app", "list"],
        capture_output=True, text=True, env=env,
    )
    assert "test-profile" in result.stdout
```

### Result Pattern Test Example

```python
def test_load_config_missing_file() -> None:
    result = load_config(Path("/nonexistent"))
    assert result.is_err
    assert "not found" in result.unwrap_err()

def test_load_config_valid() -> None:
    result = load_config(Path("tests/fixtures/valid_config.yaml"))
    assert result.is_ok
    config = result.unwrap()
    assert config.name == "test"
```

### Async Test Example

```python
import pytest

@pytest.mark.asyncio
async def test_fetch_data() -> None:
    result = await fetch_data("https://httpbin.org/get")
    assert result.is_ok
```

---

## Fixtures

### Temporary Directories

```python
@pytest.fixture
def app_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir
```

### Environment Override

```python
@pytest.fixture
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path]:
    config = tmp_path / "config"
    data = tmp_path / "data"
    config.mkdir()
    data.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config))
    monkeypatch.setenv("XDG_DATA_HOME", str(data))
    return config, data
```

### Sample Data

```python
# tests/fixtures/audio_fixtures.py

@pytest.fixture
def sample_audio_16khz() -> np.ndarray:
    return np.zeros(16000, dtype=np.float32)  # 1 second of silence
```

### HTTP Server Mock (Real Server, Not Patched)

```python
@pytest.fixture
def mock_api(httpserver: HTTPServer) -> HTTPServer:
    httpserver.expect_request("/api/data").respond_with_json({"status": "ok"})
    return httpserver

def test_fetch_from_api(mock_api: HTTPServer) -> None:
    result = fetch_data(mock_api.url_for("/api/data"))
    assert result.is_ok
```

---

## Running Tests

```bash
uv run poe test                    # All tests
uv run pytest tests/unit/          # Unit only
uv run pytest tests/integration/   # Integration only
uv run pytest -m "not slow"        # Skip slow tests
uv run pytest --cov                # With coverage report
```

---

## Coverage Guidelines

Not targets to chase, but sanity checks:

| Area                | Guideline |
| ------------------- | --------- |
| Core business logic | >70%      |
| CLI commands        | >70%      |
| UI components       | >40%      |
| Utilities           | As needed |

If coverage is low but e2e tests cover the workflows, that's fine.
