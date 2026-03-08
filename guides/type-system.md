# Type System Guide

Detailed reference for Python type safety patterns. See [PHILOSOPHY.md](https://github.com/quick-brown-foxxx/coding_rules_python/blob/master/PHILOSOPHY.md) section 2.

---

## Configuration

```toml
[tool.basedpyright]
pythonVersion = "3.14"
typeCheckingMode = "strict"
reportAny = "error"
reportImplicitStringConcatenation = "none"
reportUnusedCallResult = "none"
reportUnnecessaryIsInstance = "none"
```

Additional strict options (for medium-big projects):

```toml
reportExplicitAny = "error"
reportUnnecessaryTypeIgnoreComment = "error"
reportMissingModuleSource = "error"
reportPrivateUsage = "error"
reportOptionalMemberAccess = "error"
reportOptionalCall = "error"
reportAttributeAccessIssue = "error"
```

---

## Handling `Any` at Library Boundaries

Third-party libraries often return `Any`. Strategies:

### 1. Typed Wrappers (Preferred)

```python
# src/wrappers/whisper_wrapper.py
class WhisperModelWrapper:
    def __init__(self, model_size: str, device: str = "auto") -> None:
        from faster_whisper import WhisperModel as _WhisperModel
        self._model = _WhisperModel(model_size, device=device)

    def transcribe(self, audio: np.ndarray, language: str | None = None) -> TranscriptionResult:
        segments_gen, info = self._model.transcribe(audio, language=language)
        # Convert untyped output to typed dataclass
        return TranscriptionResult(
            text="".join(s.text for s in segments_gen),
            language=str(info.language),
        )
```

Enforce wrapper usage via ruff:

```toml
[tool.ruff.lint.flake8-tidy-imports.banned-api]
"faster_whisper" = { msg = "Use src/wrappers/whisper_wrapper instead" }
```

### 2. Type Stubs

For libraries used broadly, create stubs in `src/stubs/`:

```python
# src/stubs/some_library.pyi
def some_function(arg: str) -> list[int]: ...
```

Configure in pyproject.toml:

```toml
[tool.basedpyright]
stubPath = "src/stubs"
```

### 3. Inline Type Narrowing

For one-off cases where wrappers are overkill:

```python
raw_value = untyped_lib.get_value()  # returns Any
assert isinstance(raw_value, str)    # narrows to str
# basedpyright now knows raw_value is str
```

---

## TypeIs Guards

Custom type guards for complex type narrowing:

```python
from typing import TypeIs, TypedDict, Required

class ValidResponse(TypedDict):
    status: Required[str]
    data: Required[dict[str, object]]

def is_valid_response(obj: object) -> TypeIs[ValidResponse]:
    return (
        isinstance(obj, dict)
        and isinstance(obj.get("status"), str)
        and isinstance(obj.get("data"), dict)
    )

def process(response: object) -> Result[str, str]:
    if not is_valid_response(response):
        return Err("Invalid response format")
    # response is now ValidResponse — fully typed
    return Ok(response["data"]["key"])  # type-safe access
```

---

## Pattern Matching for Type Safety

```python
@dataclass
class Success:
    value: str

@dataclass
class Failure:
    error: str
    code: int

type Outcome = Success | Failure

def handle(outcome: Outcome) -> str:
    match outcome:
        case Success(value=v):
            return f"OK: {v}"
        case Failure(error=e, code=c):
            return f"Error {c}: {e}"
```

---

## Common Pitfalls

### `# type: ignore` Policy

Every `# type: ignore` must have a specific error code and rationale:

```python
# BAD
result = some_call()  # type: ignore

# GOOD
result = some_call()  # type: ignore[no-any-return]  # rationale: lib returns Any, validated below
assert isinstance(result, ExpectedType)
```

Use `check_type_ignore.py` script to enforce this:

```python
#!/usr/bin/env python3
"""Validate all type:ignore comments have rationale."""
import re, sys
from pathlib import Path

pattern = re.compile(r"#\s*type:\s*ignore(?!\[)")
errors = []
for path in Path("src").rglob("*.py"):
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if pattern.search(line):
            errors.append(f"{path}:{i}: type:ignore without specific code")

if errors:
    print("\n".join(errors))
    sys.exit(1)
```

### TYPE_CHECKING Guard

Use for imports that cause circular dependencies or are only needed for annotations:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.managers.audio_manager import AudioManager

class TranscriptionService:
    def __init__(self, audio: "AudioManager") -> None: ...
```
