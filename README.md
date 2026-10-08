# jsonmask

[![CI](https://github.com/buhozurdo/jsonmask/actions/workflows/ci.yml/badge.svg)](https://github.com/buhozurdo/jsonmask/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/github/buhozurdo/jsonmask/graph/badge.svg?token=3MZZSZST5C)](https://codecov.io/github/buhozurdo/jsonmask)
[![PyPI version](https://img.shields.io/pypi/v/buhozurdo-jsonmask.svg)](https://pypi.org/project/buhozurdo-jsonmask/)
[![Python versions](https://img.shields.io/pypi/pyversions/buhozurdo-jsonmask.svg)](https://pypi.org/project/buhozurdo-jsonmask/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Deterministic masking and PII redaction for Python dictionaries, JSON payloads, and logs.

Part of the [Búho Zurdo](https://github.com/buhozurdo) ecosystem 🦉

---

## Overview

`jsonmask` is an extensible security and data privacy library designed to sanitize sensitive information (PII, authentication tokens, credentials) before persisting data or emitting logs.

- **Rule-based Declarative Masking:** Path-based targeting with wildcard support (`*`, `[*]`).
- **Deterministic Strategies:** Full redaction, partial masking, HMAC/SHA-256 token hashing, entropy threshold detection, and custom callbacks.
- **Built-in Presets:** Out-of-the-box configurations for emails, credit cards, credentials, SSNs, and phone numbers.
- **Logging Integration:** First-class filters for standard Python `logging`, `structlog`, and `Loguru`, plus structured JSON logs.
- **Learning Mode (Dry-Run):** Validate rules and generate match reports without mutating original data.
- **High Performance:** Core masking logic and dictionary traversals are compiled to native C extensions via `mypyc`.
- **CLI Utility:** Native command-line tool for stream processing (JSON / NDJSON) in CI/CD pipelines.

---

## Installation

```bash
pip install buhozurdo-jsonmask

# Optional: To use third-party logging integrations (structlog, loguru)
pip install "buhozurdo-jsonmask[loggers]"
```

> **PyPI Note:** The package is published on PyPI under the name `buhozurdo-jsonmask`. It is imported in Python directly as `jsonmask`.

For development:

```bash
git clone https://github.com/buhozurdo/jsonmask.git
cd jsonmask
pip install -e ".[dev]"
```

---

## Quick Start

### Python API

```python
from jsonmask import mask, Masker

data = {
    "user": {
        "name": "Ana",
        "email": "ana@example.com"
    },
    "token": "eyJhbGciOiJIUzI1NiIsIn..."
}

rules = [
    {"path": "user.email", "strategy": "redact"},
    {"path": "token", "strategy": "hash"}
]

# Quick masking
masked_data = mask(data, rules=rules)
print(masked_data)
# {
#   "user": {"name": "Ana", "email": "****"},
#   "token": "7e2c25d4"
# }
```

### Learning Mode (Dry-Run)

Safely test rules in production without altering the real data by generating a report of what *would* have been masked.

```python
from jsonmask import mask

# The original data remains completely untouched
data, report = mask(data, rules=rules, learning_mode=True)

print(f"Would have masked {report.total_fields_masked} fields.")
print("Details:", report.to_dict())
```

### Reusable Masker (Recommended for Services)

```python
from jsonmask import Masker

# Compile rules once for maximum throughput
masker = Masker.from_rules(rules)

for record in records:
    clean_record = masker.mask(record)
```

Rules can also be loaded directly from YAML or JSON files:

```python
masker = Masker.from_file("rules.yml")
clean_record = masker.mask(record)
```

---

## Logging Integration

### Standard Library Logging Filter

```python
import logging
from jsonmask import Masker, MaskingFilter

rules = [
    {"path": "request.headers.authorization", "strategy": "partial"},
    {"path": "user.email", "strategy": "redact"}
]

masker = Masker.from_rules(rules)

handler = logging.StreamHandler()
handler.addFilter(MaskingFilter(masker))

logger = logging.getLogger("app")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Sensitive data passed in `extra` will be sanitized automatically
logger.info("Incoming request", extra={"request": {"headers": {"authorization": "Bearer abc123def456"}}})
```

### structlog Integration

```python
import structlog
from jsonmask import Masker
from jsonmask.logging_integration import structlog_processor

masker = Masker.from_rules([{"path": "user.email", "strategy": "redact"}])

structlog.configure(
    processors=[
        structlog_processor(masker),
        structlog.processors.JSONRenderer()
    ]
)
```

### Loguru Integration

```python
from loguru import logger
from jsonmask import Masker
from jsonmask.logging_integration import loguru_patcher

masker = Masker.from_rules([{"path": "secret", "strategy": "redact"}])
logger = logger.patch(loguru_patcher(masker))

# Secrets within the `extra` dict are automatically intercepted and sanitized
logger.info("Test payload", extra={"secret": "12345"})
```

---

## Command Line Interface (CLI)

```bash
# Process a JSON file
jsonmask mask --input data.json --rules rules.yml --output masked.json

# Process NDJSON streams via stdin
cat data.ndjson | jsonmask mask --rules rules.yml --ndjson > masked.ndjson

# Generate an execution report
jsonmask mask -i data.json -r rules.yml -o out.json --report report.json

# Validate rules file syntax
jsonmask validate -r rules.yml

# List available strategies
jsonmask list-strategies

# Generate a sample rules template
jsonmask generate-rules > rules.template.yml
```

---

## Rule Definitions

### YAML Specification

```yaml
rules:
  - path: "user.email"
    strategy: "redact"
    replace_with: "****"

  - path: "cards.*.number"
    strategy: "partial"
    keep_start: 4
    keep_end: 4
    mask_char: "*"

  - path: "headers.authorization"
    strategy: "regex"
    pattern: "Bearer\\s+(.+)"
    replace_with: "Bearer ****"

  - path: "token"
    strategy: "entropy"
    entropy_min: 3.5
```

### Path Syntax Reference

| Syntax | Example | Description |
|---|---|---|
| Dot notation | `user.email` | Nested dictionary access |
| Wildcard key | `cards.*.number` | Any key at target level |
| Index | `items[0].id` | Specific list element index |
| Wildcard index | `items[*].secret` | All elements inside a list |

---

## Available Strategies

| Strategy | Description | Key Parameters |
|---|---|---|
| `redact` | Replaces value with placeholder | `replace_with` (default `****`) |
| `replace` | Replaces with exact literal | `replace_with` |
| `hash` | Truncated SHA-256 hash | `hash_prefix_length`, `hash_prefix` |
| `partial` | Retains start/end characters | `keep_start`, `keep_end`, `mask_char` |
| `regex` | Matches regex group and masks | `pattern`, `replace_with` |
| `entropy` | Evaluates Shannon entropy | `entropy_min`, `replace_with` |

---

## Regulatory Presets

Pre-configured rules are available for common privacy requirements:

```python
from jsonmask import Masker
from jsonmask.presets import combine_presets

rules = combine_presets("email", "credit_card", "token", "password")
masker = Masker.from_rules(rules)
```

Available presets: `email`, `credit_card`, `token`, `ssn`, `password`, `phone`, `pii` (all combined).

---

## Known Limitations

- **Recursive Traversal:** Traversal relies on recursive tree inspection. Extremely deep data structures (thousands of nested levels) may trigger a `RecursionError`.
- **JSONPath Scope:** Supports dot notation, dictionary wildcards (`*`), and list indices (`[*]`). Complex filter expressions (such as `[?(@.price > 10)]`) are not supported in the standard matcher.

---

## Testing

```bash
# Run test suite
pytest

# Run tests with coverage
pytest --cov=src/jsonmask --cov-report=term-missing
```

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and adhere to [Búho Zurdo Engineering Standards](https://github.com/buhozurdo).

1. Fork repository.
2. Create feature branch (`git checkout -b feat/privacy-feature`).
3. Add tests and verify formatting.
4. Open Pull Request.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
