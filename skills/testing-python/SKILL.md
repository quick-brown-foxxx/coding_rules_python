---
name: testing-python
description: >
  Python-specific extension to myai's `high-level-testing-strategy`, `test-driven-development`, and `manual-testing`. Load after those myai skills when writing Python tests, adding fixtures, or setting up pytest.
  Python testing with pytest: fixtures, CLI/e2e tests, mock servers, containerized testing, pytest-qt.
---

# Testing Python

## Prerequisites

This skill extends myai's `high-level-testing-strategy`, `test-driven-development`, and `manual-testing`. Load those first. `using-my-skills` and `engineering-principles` are assumed already loaded via myai bootstrap.

For the general testing philosophy (trustworthiness over coverage, e2e over unit, real over mocked, Pareto principle), see myai's `engineering-principles` and `high-level-testing-strategy`. For the TDD red-green-refactor workflow, see myai's `test-driven-development`. For manual verification patterns, see myai's `manual-testing`. This skill covers only Python-specific testing tooling and patterns: pytest fixtures, CLI/e2e test patterns, containerized testing, mock servers, and pytest-qt.

---

## Test Planning & Priority

**Python-specific test priority:**

1. **CLI / e2e tests** — run actual commands via `subprocess.run(["uv", "run", "poe", "app", ...])`, check output + exit codes
2. **Integration tests** — component interaction through public API, real tmp dirs, pytest-httpserver
3. **Unit tests** — pure data transformation functions
4. **Skip** — framework glue, UI layout, trivial getters

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
addopts = ["-n", "auto", "--dist", "worksteal"]

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
    "pytest-xdist>=3.5.0",
    "pytest-cov>=7.0.0",
    "pytest-asyncio>=1.3.0",
    # "pytest-qt>=4.5.0",          # For Qt apps
    # "pytest-httpserver>=1.1.0",  # For HTTP mocking
]
```

---

## Test Examples

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

Tests run in parallel by default (`-n auto` via addopts). Override with `-n0` (sequential) or `-n4` (exact count).

```bash
uv run poe test                    # All tests (parallel, auto workers)
uv run pytest tests/unit/          # Unit only
uv run pytest -n0                  # Force sequential (debugging)
uv run pytest --cov                # With coverage report
```

---

## Test Isolation

Python-specific: use `tmp_path` for files, `monkeypatch` for env vars, `yield` fixtures for teardown.

---

## Flaky Tests

> **For the general approach to flaky tests, see myai's `systematic-debugging`.**

---

## Coverage Guidelines

> **For the general coverage philosophy (guideline, not target), see myai's `engineering-principles`.** Python-specific sanity checks:

| Area | Guideline |
|------|-----------|
| Core business logic | >70% |
| CLI commands | >70% |
| UI components | >40% |
| Utilities | As needed |



---

## Test Validation

> **For the general test quality review process, see myai's `doing-code-review` and `verification-before-completion`.**

---

## Heavyweight Testing

When lightweight testing isn't enough. Same philosophy, higher infrastructure complexity.

### Core Idea

| Instead of... | Use... |
|---------------|--------|
| `@patch("requests.get")` | Real HTTP server (pytest-httpserver or custom) |
| `@patch("subprocess.run")` | Custom lightweight binary that mimics the real one |
| `unittest.mock.Mock()` for DB | Real database in container |
| Monkeypatched file operations | Real filesystem in tmp_path or container volume |
| Mocked system services (DBus) | Real daemon instance for tests |

### Containerized Test Environments

```
tests/
├── containers/
│   ├── Dockerfile.test-env        # Base test environment
│   ├── Dockerfile.mock-api        # Mock API server
│   ├── docker-compose.test.yml    # Orchestration
│   └── mock-bins/                 # Custom mock binaries
│       ├── mock-telegram          # Fake Telegram Desktop
│       └── mock-ffmpeg            # Fake ffmpeg (returns predefined output)
├── integration/
│   └── test_with_containers.py
└── conftest.py                    # Container lifecycle fixtures
```

### Docker Compose for Test Services

```yaml
# tests/containers/docker-compose.test.yml
services:
  mock-api:
    build:
      context: .
      dockerfile: Dockerfile.mock-api
    ports:
      - "18080:8080"

  test-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: test
      POSTGRES_PASSWORD: test
    ports:
      - "15432:5432"
```

### Container Lifecycle Fixture

```python
@pytest.fixture(scope="session")
def test_services():
    """Start all test containers, yield, then tear down."""
    compose_file = Path(__file__).parent / "containers" / "docker-compose.test.yml"
    subprocess.run(
        ["podman-compose", "-f", str(compose_file), "up", "-d", "--wait"],
        check=True,
    )
    yield
    subprocess.run(
        ["podman-compose", "-f", str(compose_file), "down", "-v"],
        check=True,
    )
```

### Mock Binaries

Instead of patching `subprocess.run()`, provide a real binary that behaves predictably:

```python
#!/bin/env python3
# tests/containers/mock-bins/mock-telegram
import sys, time, os

print("Telegram Desktop Mock v1.0")
print(f"Working directory: {os.getcwd()}")

if "-many" in sys.argv and "-workdir" in sys.argv:
    print(f"Mock Telegram started in {sys.argv[sys.argv.index('-workdir') + 1]}")
    time.sleep(int(os.environ.get("MOCK_TELEGRAM_LIFETIME", "5")))
    sys.exit(0)

print("Unknown arguments", sys.argv, file=sys.stderr)
sys.exit(1)
```

```python
@pytest.fixture
def mock_telegram_bin(tmp_path: Path) -> Path:
    mock_bin = tmp_path / "telegram"
    mock_bin.write_text(MOCK_TELEGRAM_SCRIPT)
    mock_bin.chmod(0o755)
    return mock_bin

async def test_start_instance(mock_telegram_bin: Path) -> None:
    result = await start_instance(profile, binary_path=mock_telegram_bin)
    assert result.is_ok
    pid = result.unwrap()
    assert pid > 0
```

### Stateful Mock API

For APIs that need to maintain state across requests:

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading, json

class MockAPIHandler(BaseHTTPRequestHandler):
    profiles: dict[str, dict[str, str | int | bool]] = {}

    def do_POST(self) -> None:
        if self.path == "/api/profiles":
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.profiles[data["id"]] = data
            self.send_response(201)
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

    def do_GET(self) -> None:
        if self.path == "/api/profiles":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(list(self.profiles.values())).encode())

@pytest.fixture(scope="session")
def mock_api() -> Generator[str, None, None]:
    server = HTTPServer(("127.0.0.1", 0), MockAPIHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
```

### Real Service Testing (DBus)

```python
@pytest.fixture(scope="session")
def dbus_session() -> Generator[str, None, None]:
    """Start a real DBus session daemon for tests."""
    process = subprocess.Popen(
        ["dbus-daemon", "--session", "--print-address", "--nofork"],
        stdout=subprocess.PIPE,
    )
    address = process.stdout.readline().decode().strip()
    os.environ["DBUS_SESSION_BUS_ADDRESS"] = address
    yield address
    process.terminate()
    process.wait()
```

---

## Related myai Skills

- **`high-level-testing-strategy`** — Parent skill. BDD-first test planning, behavior scenarios, automation scope, mock boundaries.
- **`test-driven-development`** — Parent skill. Red-green-refactor workflow for automated tests.
- **`manual-testing`** — Parent skill. Realistic manual verification with environment preflight, isolation, evidence.
- **`architecting-test-infra`** — For setting up test infrastructure, fixtures, state isolation, seed layers.
- **`engineering-principles`** — Language-agnostic testing philosophy: trustworthiness over coverage, real over mocked.
- **`writing-python-code`** — Python-specific coding rules that apply to test code too.

