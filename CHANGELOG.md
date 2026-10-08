# Changelog

Todos los cambios notables en este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.1] - 2026-10-08

### Added
- Native integration with `structlog` (`structlog_processor`) and `Loguru` (`loguru_patcher`) in `logging_integration.py`.
- "Learning" mode (dry-run) added to the `mask()` method to allow testing rules and receiving a report without modifying the data (`learning_mode=True`).

---

## [0.1.10] - 2026-08-01
- Added PyPI release.yml

---

## [0.1.0] - 2026-07-21

### Added

#### Core Functionality
- **Declarative masking library**: Core system for masking sensitive data in Python, JSON, and NDJSON structures
- **`Masker` class**: Reusable core engine for applying compiled masking rules
- **`mask()` function**: Simplified API for ad-hoc masking
- **Flexible rule system**: Support for dot notation paths, wildcards, indices, and complex patterns
- Path notation: `user.email`, `cards.*.number`, `items[0].id`, `items[*].secret`

#### Masking Strategies
- `redact`: Replaces with a configurable placeholder
- `replace`: Replaces with a literal value
- `hash`: SHA256 with a configurable prefix
- `partial`: Preserves the start/end of the value
- `regex`: Application of regex patterns
- `entropy`: High-entropy detection

#### Presets PII
- Predefined presets: `email`, `credit_card`, `token`, `ssn`, `password`, `phone`, `pii`
- `combine_presets()` function to mix multiple presets
- Rule validation included

#### Logging Integration
- **`MaskingFilter`**: Filter for Python's standard `logging` module
- **`StructuredLogMasker`**: Masking for structured logs (JSON)
- `mask_log_entry()` method for dictionaries
- `mask_json_string()` method for JSON strings

#### CLI Interface
- `jsonmask mask`: Process JSON/NDJSON files using rules
- Options: `--input`, `--rules`, `--output`, `--ndjson`, `--report`
- `jsonmask validate`: Validate YAML rule files
- `jsonmask list-strategies`: List available strategies
- `jsonmask generate-rules`: Generate a rules template
- Support for stdin/stdout

#### Reports and Analysis
- Masking report generation: `generate_report=True`
- Statistics on processed and masked fields
- Detailed list of affected fields

#### Development and Testing
- Test suite with >80% coverage
- GitHub Actions configuration for CI/CD
- Linting with `ruff`, formatting with `black`, import sorting with `isort`
- Type checking with `mypy`
- Pytest for test execution

#### Project Configuration
- `pyproject.toml` with PEP 517 specification
- Clearly defined development and production dependencies
- Project metadata (author, MIT license, description)
- CLI entry point: `jsonmask`

### Fixed
- N/A (versión inicial)

### Changed
- N/A (versión inicial)

### Removed
- N/A (versión inicial)

### Security
- Automatic masking of sensitive data
- Rule validation to prevent injection attacks
- Avoidance of unnecessary in-memory storage of unmasked data

---

[Unreleased]: https://github.com/buhozurdo/jsonmask/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/buhozurdo/jsonmask/releases/tag/v0.1.0
