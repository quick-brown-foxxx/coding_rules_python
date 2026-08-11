# Logging & Colored Output

Reusable logging setup and colored stdout/stderr output for Python apps.

- Rotating file logging (always on; default level INFO, pass `level=DEBUG` for full detail)
- Colored console logging (stdout for GUI/server; `stream=sys.stderr` for CLI tools)
- `silence_noisy_loggers()` to pin noisy third-party loggers at WARNING
- Colored non-log output helpers (`write_info`/`write_success`/`write_warning`/`write_error`)

See the `setting-up-logging` skill for full usage guide.
