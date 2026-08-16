---
name: openai-ai-integration
description: >-
  Use when integrating an OpenAI-compatible LLM API into an app, CLI, tool, or service: choosing the SDK, shaping chat-completion requests, configuring base URL/model/reasoning-effort, structured output via response_format, resilient JSON parsing, and retry handling.
  Language-agnostic guidance with Python examples and TypeScript references.
---

# OpenAI API Integration

## Prerequisites

Load myai's `engineering-principles` first. This skill is a language-agnostic extension that covers only how to talk to an OpenAI-compatible LLM API: client choice, request shaping, configuration, structured output, resilient parsing, and retries. Examples are in Python with TypeScript references; the rules apply in any language with an official OpenAI SDK.

The OpenAI API is a weakly-typed dynamic boundary: it accepts untyped request dicts and returns untyped JSON. Treat it like a network boundary, not a type system — validate everything you consume and type everything you build on top.

## Key Principles

- **Use the official OpenAI SDK** (`openai` in Python and TypeScript, and in many other languages). Never hand-roll the HTTP calls — the SDK handles auth headers, timeouts, connection pooling, and error taxonomy.
- **Use `chat.completions`** (Chat Completions format). It is the most compatible surface across OpenAI-compatible providers (OpenAI, OpenRouter, Ollama, ...), so the same code works against any of them via `base_url`.
- **Everything about the endpoint is configurable**: base URL, model, reasoning effort, and API key must all be overridable through environment variables, config files, or app settings. The exact mechanism is application-specific.
- **Modern models need very few knobs.** Do not send `temperature` or `max_tokens` by default. The only request parameters you normally touch are `model`, `messages`, `response_format`, and optionally `reasoning_effort`.

## Defaults

| Concern | Default |
|---|---|
| Client | official `openai` SDK |
| Protocol | `chat.completions` |
| Temperature | not sent |
| `max_tokens` | not sent (only for genuinely bounded outputs) |
| `reasoning_effort` | free-form passthrough, omitted when unset |
| Prompt | separate template file, single `user` message (one-shot) |
| Structured output | `response_format` `json_schema` with `strict: true`, validated on response |
| Retries | manual loop, 3 attempts, exponential backoff, covers network + validation failures |

## Configuration and Credentials

`base_url`, `model`, `reasoning_effort`, and the API key come from env vars / config / app settings (mechanism is application-specific). Provide sensible defaults for `base_url` (OpenAI, or your provider) and `model`, and fail fast with a clear error when the key is missing.

```python
client = openai.AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)
```

```ts
const client = new OpenAI({ apiKey: config.apiKey, baseURL: config.baseURL });
```

**Never log the API key.** Keep it only inside the SDK client constructor; build log payloads from your typed request objects, which carry no credentials.

## Request Shaping

- **No `temperature`.** It is no longer relevant for basic cases with modern reasoning models — some ignore it, others behave unexpectedly. Omit it entirely.
- **No `max_tokens` by default.** It is rarely needed and silently truncates long outputs. Use it only when the output is genuinely bounded (e.g. a captcha answer needs ~20 tokens); otherwise you get cut-off JSON and text.
- **`reasoning_effort` is a free-form passthrough** (`str | None`). Allowed values are provider-dependent (OpenAI: `low`/`medium`/`high`; Gemini-compatible: `true`/`false`), so accept any string and forward it verbatim; omit the parameter entirely when unset. The SDK types it as a closed literal — that type is wrong for multi-provider use, so treat it as a string passthrough.

```python
completion = await client.chat.completions.create(
    model=request.model,
    messages=[{"role": "user", "content": prompt}],
    reasoning_effort=request.reasoning_effort,  # None omits the parameter
)
```

## Prompts

- **One-shot / transient requests: send everything in a single `user` message.** No `system` message, no wrapping. This avoids artificial split of a unifromed task into two prompts, and works fine with modern models.
- **Use a `system` prompt only for chats / multi-turn conversations**, where a persistent role is meaningful.
- **Keep prompts in separate template files, not code strings** (Jinja2 in Python, any template engine in TS). The template is the source of truth for the variable list — render with strict undefined handling so a missing variable fails fast instead of silently producing empty text.

```python
# prompts/score.j2  — a file, not a string literal
body = template.render(resume_formatted=resume, vacancy_formatted=vacancy)
```

## Structured Output

When you need a structured result from the model, use Structured Outputs via `response_format` and **always validate the schema on the response**. Do not regex-extract, and do not trust the raw text.

```python
completion = await client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": prompt}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "scoring_result",
            "schema": {
                "type": "object",
                "properties": {
                    "fit_score": {"type": "integer", "minimum": 1, "maximum": 5},
                    "comment": {"type": "string"},
                },
                "required": ["fit_score", "comment"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    },
)
```

```ts
const completion = await client.chat.completions.create({
  model,
  messages: [{ role: "user", content: prompt }],
  response_format: {
    type: "json_schema",
    json_schema: {
      name: "scoring_result",
      schema: {
        type: "object",
        properties: {
          fit_score: { type: "integer", minimum: 1, maximum: 5 },
          comment: { type: "string" },
        },
        required: ["fit_score", "comment"],
        additionalProperties: false,
      },
      strict: true,
    },
  },
});
```

Rules:

- **Schema**: require the fields your logic depends on (`required`), forbid extras if needed (`additionalProperties: false`), and encode ranges/enums in the schema (`minimum`/`maximum`) so the model produces in-range values.
- **Validate on the response**: decode and check using any schema-validation tooling, even with `strict: true`, cause schema enforcement differs between providers. Return a structured error carrying the raw completion text for diagnostics.
- **Keep freeform text fields unvalidated.** A string field like `comment` is intentionally not validated.

### Healing (optimistic) parsing

Not every endpoint honors `response_format` — free-tier / non-strict providers may treat it as a hint and return the JSON wrapped in a markdown code fence (`` ```json `` or plain `` ``` ``) or in prose. Extract the payload with three layers of tolerance, in order:

1. bare JSON object (fast path for real structured-output endpoints);
2. a markdown fenced block, whatever the language tag;
3. the substring between the first `{` and the last `}`.

Log at **DEBUG** when extraction had to happen — this is a known, expected behavior, not a warning. Text with no JSON object is returned unchanged so the caller's parse error stays truthful about the raw output.

```python
def extract_json_text(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return text
    lines = stripped.splitlines()
    if len(lines) >= 3 and lines[0].strip().startswith("```") and lines[-1].strip() == "```":
        body = "\n".join(lines[1:-1])
        if body.strip():
            return body
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return text[start : end + 1]
    return text
```

## Retries

Use a **manual retry loop with exponential backoff, 3 attempts by default**. Do not rely on the SDK's built-in retries (`max_retries`) — they cover only transient network errors, not validation failures.

The retry loop must cover **both** failure classes:

- transient network/API failures (exceptions from the SDK call);
- structured-output **validation** failures — a model that returns invalid JSON (or an out-of-range value) is simply asked again.

Validation therefore lives *inside* the retry budget. When the budget is exhausted, return the **last** failure (exception message or parse error) — never swallow it.

```python
_MAX_ATTEMPTS = 3
_BACKOFF_BASE_SECONDS = 1.0

for attempt in range(1, _MAX_ATTEMPTS + 1):
    try:
        content = await completions(request)
    except Exception as exc:
        last_failure = f"call failed: {exc}"
    else:
        parsed = parse(content)
        if parsed.is_ok:
            return Ok(parsed.unwrap())
        last_failure = parsed.unwrap_err()
    if attempt < _MAX_ATTEMPTS:
        await asyncio.sleep(_BACKOFF_BASE_SECONDS * (2.0 ** (attempt - 1)))
return Err(last_failure)
```

## Boundaries and Typing (Python)

The SDK is an untyped dynamic boundary — do not leak its `Any` into your business logic.

- **Isolate it behind one typed module**: typed frozen dataclasses for requests and results; the SDK is touched in exactly one place.
- **Protocol for consumers + injectable low-level call seam**: the consumer (your stage/handler) depends on a narrow Protocol; the concrete wrapper takes an injectable `CompletionsFn` so tests stub the seam and never hit the network.
- **Client lifecycle**: create the client per call and `await client.close()` in a `finally` (releases the httpx connection pool; the seam stays stateless), or keep a single long-lived client in a service. Per-call is simpler for CLI/tool code; long-lived is right for servers.

## Error Handling

- Expected failures — network errors, malformed JSON, out-of-range values, provider errors — are typed errors / `Result` values. Exceptions are bugs only. Map the SDK's `openai.OpenAIError` to app-level typed errors at a single boundary.
- **Empty completion content is a failure**: `completion.choices[0].message.content` being `None`/empty means the call did not produce usable output — treat it as a failed attempt (retried, then a typed error), never as success with empty text.

```python
content = completion.choices[0].message.content
if content is None:
    raise AiBoundaryError("empty completion")  # caught -> retried -> Err
```

## Logging (optional)

Not required by default. Add DEBUG-level request/response logging only when the app needs reach-debugging / tracing of AI output problems (e.g. invalid JSON). Pretty-print JSON payloads; keep unparseable output verbatim so the raw text is available for diagnostics. The API key must never appear in a logged payload. By default, OpenAI lib not exposes it.

## Multimodal Input

For image input, send a `content` array with the text prompt first, then the image as a base64 data URL (text-first is a provider convention, e.g. OpenRouter).

```python
content = [
    {"type": "text", "text": question},
    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
]
completion = await client.chat.completions.create(
    model=model, messages=[{"role": "user", "content": content}]
)
```

## Common Mistakes

- Hand-rolling HTTP instead of using the official SDK.
- Sending `temperature` or `max_tokens` out of habit.
- Trusting `strict: true` output without validating the response.
- Putting prompts in code strings instead of template files.
- Using a `system` message for a transient one-shot request.
- Relying on SDK built-in retries that ignore validation failures.
- Logging request payloads that include the API key.

## Related Skills

- **`engineering-principles`** — Parent skill. Language-agnostic philosophy (error handling, boundaries, fail fast).
- **`writing-python-code`** — Python typing and `Result` conventions for the wrapper module.
- **`setting-up-python-backends`** — Where the AI client lives in a service/API repo.
