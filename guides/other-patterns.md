# Other Patterns Reference

Project-specific patterns for manual reference. Not part of universal rules.

---

## Jinja2 Templating

Use Jinja2 when generating text output (HTML, configs, reports, markdown).

### Setup

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader(Path(__file__).parent),
    autoescape=select_autoescape(default_for_string=True, default=True),
)
template = env.get_template("template.html")
output = template.render(**data, i18n=LOCALIZATION[lang])
```

### For Markdown (No HTML Escaping)

```python
env = Environment(
    loader=FileSystemLoader(Path(__file__).parent),
    autoescape=select_autoescape(default_for_string=False, default=False),
)
```

### Config Merging Pattern

Load multiple YAML configs, merge (last wins), then render:

```python
def load_configs(paths: list[Path]) -> Result[dict[str, object], str]:
    merged: dict[str, object] = {}
    for path in paths:
        data = yaml.safe_load(path.read_text())
        merged.update(data)  # Later configs override earlier ones
    return Ok(merged)
```

### JSON Schema Validation

Validate merged config before rendering:

```python
from jsonschema import Draft7Validator

def validate_config(config: dict[str, object], schema_path: Path) -> Result[None, str]:
    schema = json.loads(schema_path.read_text())
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(config))
    if errors:
        return Err("\n".join(e.message for e in errors))
    return Ok(None)
```

---

## Platform Abstraction

For apps that must run on multiple platforms:

```python
from abc import ABC, abstractmethod

class PlatformBackend(ABC):
    @abstractmethod
    async def start_instance(self, profile: Profile, binary: Path) -> Result[int, str]: ...

    @abstractmethod
    def get_data_dir(self) -> Path: ...

    @abstractmethod
    def get_config_dir(self) -> Path: ...

class LinuxBackend(PlatformBackend):
    async def start_instance(self, profile: Profile, binary: Path) -> Result[int, str]:
        env = {
            "XDG_CONFIG_HOME": str(profile.path / "config"),
            "XDG_DATA_HOME": str(profile.path / "data"),
        }
        process = await asyncio.create_subprocess_exec(
            str(binary), "-many", "-workdir", str(profile.path),
            env={**os.environ, **env},
        )
        return Ok(process.pid) if process.pid else Err("Failed to start")
```

Select backend at startup:

```python
def get_backend() -> PlatformBackend:
    match sys.platform:
        case "linux":
            return LinuxBackend()
        case _:
            raise NotImplementedError(f"Unsupported platform: {sys.platform}")
```

---

## Security Patterns

### Path Validation (Symlink-Aware)

```python
def is_safe_path(path: Path, base: Path) -> bool:
    """Check that path is inside base, with symlink detection."""
    try:
        resolved = path.resolve(strict=True)
        base_resolved = base.resolve(strict=True)
        return resolved.is_relative_to(base_resolved)
    except (OSError, ValueError):
        return False
```

### Subprocess Safety

```python
# NEVER this:
subprocess.run(f"process {user_input}", shell=True)

# ALWAYS this:
subprocess.run(["process", user_input], shell=False)
```

### Cleanup on Failure

```python
def create_profile(name: str) -> Result[Profile, str]:
    profile_path = profiles_dir / name
    try:
        profile_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return Err(f"Cannot create directory: {e}")

    if not is_safe_path(profile_path, profiles_dir):
        shutil.rmtree(profile_path, ignore_errors=True)
        return Err("Unsafe path detected")

    try:
        save_profile_data(profile_path, profile)
    except OSError as e:
        shutil.rmtree(profile_path, ignore_errors=True)  # Cleanup partial state
        return Err(f"Cannot save profile: {e}")

    return Ok(profile)
```

---

## Localization Pattern

For apps with multiple languages:

```python
LOCALIZATION: Final[dict[str, dict[str, str]]] = {
    "en": {
        "section_summary": "Summary",
        "section_experience": "Experience",
    },
    "ru": {
        "section_summary": "Обзор",
        "section_experience": "Опыт работы",
    },
}

# Pass to Jinja2 template:
template.render(**config, i18n=LOCALIZATION[lang])
```

Template usage: `{{ i18n.section_summary }}`

---

## Settings Management (Qt)

Type-safe QSettings wrapper:

```python
class Settings:
    def __init__(self) -> None:
        self._settings = QSettings(APP_NAME, APP_NAME)
        self._init_defaults()

    def get_str(self, key: str, default: str = "") -> str:
        value = self._settings.value(key, default)
        return str(value) if value is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        value = self._settings.value(key, default)
        return int(value) if value is not None else default

    def set(self, key: str, value: str | int | bool) -> None:
        self._settings.setValue(key, value)
```

---

## Logging Setup

```python
import colorlog

def get_logger(name: str) -> logging.Logger:
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(name)s: %(message)s"
    ))
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
```

Usage: `logger = get_logger(__name__)`
