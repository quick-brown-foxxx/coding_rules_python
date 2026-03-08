---
name: testing-python
description: "Python testing with pytest: philosophy, fixtures, mock servers, containerized testing. Use when writing tests or setting up test infrastructure."
---

# Testing Python

Tests prove features work. Coverage is secondary. E2e tests beat unit tests. Real beats mocked.

---

## Philosophy

- **Trustworthiness > coverage.** A test that mocks away the tested thing proves nothing.
- **5 good e2e tests > 100 unit tests** with heavy mocking.
- **20/80 rule.** Test where it gives the most confidence.
- **Unit tests for pure logic only.** Functions that transform data honestly.
- **Real over mocked.** Real HTTP servers (pytest-httpserver), real tmp dirs, real processes.

---

## Test Priority

1. **CLI / e2e tests** — run actual commands, check output + exit codes
2. **Integration tests** — component interaction through public API
3. **Unit tests** — pure data transformation functions
4. **Skip** — framework glue, UI layout, trivial getters

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

| Area | Guideline |
|------|-----------|
| Core business logic | >70% |
| CLI commands | >70% |
| UI components | >40% |
| Utilities | As needed |

If coverage is low but e2e tests cover the workflows, that's fine.

---

## Heavyweight Testing

When lightweight testing isn't enough. Same philosophy, higher infrastructure complexity.

**Status: Design document. Not yet fully implemented.**

### When to Use

- Project has external dependencies (APIs, databases, system services)
- Features depend on specific system state (installed binaries, running daemons)
- Integration failures are costly or hard to debug
- Project is long-lived and maintained by multiple people

### Investment Decision

Ask before building heavyweight infrastructure:

1. Will this project live long enough to justify the setup time?
2. Are integration failures actually happening or just theoretical?
3. Can lightweight testing (real tmp dirs, pytest-httpserver) cover 80% of the risk?

If yes to all three: build it. If not: stick with lightweight.

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
    profiles: dict[str, dict[str, object]] = {}

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

### CI Integration

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      mock-api:
        image: ghcr.io/org/mock-api:latest
        ports:
          - 18080:8080
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --all-extras --group dev
      - run: uv run poe test
```
