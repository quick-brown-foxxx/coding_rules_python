# Testing Guide (Heavyweight)

Aspirational testing infrastructure for projects that warrant the investment.
Same philosophy as [testing-lightweight.md](testing-lightweight.md), higher infrastructure complexity.

**Status: Design document. Not yet fully implemented.**

---

## When to Use Heavyweight Testing

- Project has external dependencies (APIs, databases, system services)
- Features depend on specific system state (installed binaries, running daemons)
- Integration failures are costly or hard to debug
- Project is long-lived and maintained by multiple people

---

## Core Idea

Replace monkey-patching and unittest.mock with real-like infrastructure:

| Instead of...                 | Use...                                             |
| ----------------------------- | -------------------------------------------------- |
| `@patch("requests.get")`      | Real HTTP server (pytest-httpserver or custom)     |
| `@patch("subprocess.run")`    | Custom lightweight binary that mimics the real one |
| `unittest.mock.Mock()` for DB | Real database in container                         |
| Monkeypatched file operations | Real filesystem in tmp_path or container volume    |
| Mocked system services (DBus) | Real daemon instance for tests                     |

---

## Containerized Test Environments

### Structure

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
import subprocess
import pytest

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

---

## Mock Binaries

Instead of patching `subprocess.run()`, provide a real binary that behaves predictably:

### Example: Mock Telegram Desktop

```bash
#!/bin/bash
# tests/containers/mock-bins/mock-telegram
# Simulates Telegram Desktop startup behavior

echo "Telegram Desktop Mock v1.0"
echo "Working directory: $PWD"

# Check expected flags
if [[ "$1" == "-many" && "$2" == "-workdir" ]]; then
    echo "Started with profile: $3"
    # Stay alive like a real process
    sleep "${MOCK_TELEGRAM_LIFETIME:-5}"
    exit 0
fi

echo "Unknown arguments: $@" >&2
exit 1
```

### Usage in Tests

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

---

## Mock HTTP Servers

### Stateful Mock API

For APIs that need to maintain state across requests:

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json

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

---

## Real Service Testing

### DBus Session Bus

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

## CI Integration

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

---

## Investment Decision

Ask before building heavyweight infrastructure:

1. Will this project live long enough to justify the setup time?
2. Are integration failures actually happening or just theoretical?
3. Can lightweight testing (real tmp dirs, pytest-httpserver) cover 80% of the risk?

If yes to all three: build it. If not: stick with [lightweight](testing-lightweight.md).
