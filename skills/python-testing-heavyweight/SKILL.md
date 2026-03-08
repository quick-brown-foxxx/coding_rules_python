---
name: python-testing-heavyweight
description: Use when a project needs containerized test environments, mock servers, custom mock binaries, or real service testing infrastructure
---

# Python Testing (Heavyweight)

## Overview

Same philosophy as lightweight testing, but with real infrastructure instead of monkey-patching. Containers, mock servers, custom mock binaries.

## When to Use

- Project has external API dependencies
- Features depend on system services (DBus, specific binaries)
- Integration failures are costly to debug
- Lightweight testing can't cover the critical paths

## Core Idea

| Instead of... | Use... |
|---------------|--------|
| `@patch("requests.get")` | Real HTTP server |
| `@patch("subprocess.run")` | Custom mock binary |
| `Mock()` for database | Real DB in container |
| Monkeypatched file ops | Real filesystem in tmp_path |
| Mocked system services | Real daemon instance |

## Key Patterns

- **Containerized services**: `docker-compose.test.yml` with mock API, test DB
- **Mock binaries**: real executables that mimic expected behavior
- **Session-scoped fixtures**: start containers once per test session
- **Real DBus**: start `dbus-daemon --session` for tests

## Investment Decision

1. Will the project live long enough to justify setup time?
2. Are integration failures actually happening?
3. Can lightweight testing cover 80% of the risk?

If not all three: stick with lightweight.

## Reference

See `guides/testing-heavyweight.md` for container setup, mock binary examples, CI integration, and stateful mock servers.
