# Other Patterns Reference

Project-specific patterns for manual reference. Not part of universal rules.

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

## Config Merging Pattern

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
