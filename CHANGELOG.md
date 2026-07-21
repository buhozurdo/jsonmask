# Changelog

Todos los cambios notables en este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Nuevas funcionalidades en desarrollo

### Changed
- Cambios a funcionalidades existentes

### Fixed
- Correcciones de bugs

---

## [0.1.0] - 2026-07-21

### Added

#### Core Functionality
- **Librería de masking declarativo**: Sistema principal para enmascarar datos sensibles en estructuras Python, JSON y NDJSON
- **Clase `Masker`**: Motor principal reutilizable para aplicar reglas de enmascarado compiladas
- **Función `mask()`**: API simplificada para enmascarado puntual
- **Sistema de reglas flexible**: Soporte para paths con punto, wildcards, índices y patrones complejos
  - Path notation: `user.email`, `cards.*.number`, `items[0].id`, `items[*].secret`

#### Estrategias de Enmascarado
- `redact`: Reemplaza con placeholder configurable
- `replace`: Reemplaza con valor literal
- `hash`: SHA256 con prefijo configurable
- `partial`: Mantiene inicio/fin del valor
- `regex`: Aplicación de patrones regex
- `entropy`: Detección de alta entropía

#### Presets PII
- Presets predefinidos: `email`, `credit_card`, `token`, `ssn`, `password`, `phone`, `pii`
- Función `combine_presets()` para mezclar múltiples presets
- Validación de reglas incluida

#### Integración con Logging
- **`MaskingFilter`**: Filtro para el módulo `logging` estándar de Python
- **`StructuredLogMasker`**: Enmascarado de logs estructurados (JSON)
  - Método `mask_log_entry()` para diccionarios
  - Método `mask_json_string()` para strings JSON

#### Interfaz CLI
- `jsonmask mask`: Procesar archivos JSON/NDJSON con reglas
  - Opciones: `--input`, `--rules`, `--output`, `--ndjson`, `--report`
- `jsonmask validate`: Validar archivos de reglas YAML
- `jsonmask list-strategies`: Listar estrategias disponibles
- `jsonmask generate-rules`: Generar template de reglas
- Soporte para stdin/stdout

#### Reportes y Análisis
- Generación de reportes de enmascarado: `generate_report=True`
- Estadísticas de campos procesados y enmascarados
- Listado detallado de campos afectados

#### Documentación
- README.md con guía de uso rápido
- CONTRIBUTING.md con estándares de desarrollo
- Ejemplos de código en todo el repositorio
- Docstrings estilo Google en todas las funciones públicas

#### Desarrollo y Testing
- Suite de tests con cobertura >80%
- Configuración de GitHub Actions para CI/CD
- Linting con `ruff`, formateo con `black`, ordenamiento de imports con `isort`
- Type checking con `mypy`
- Pytest para ejecución de tests

#### Configuración del Proyecto
- `pyproject.toml` con especificación PEP 517
- Dependencias de desarrollo y producción claramente definidas
- Metadatos del proyecto (autor, licencia MIT, descripción)
- Entry point CLI: `jsonmask`

### Fixed
- N/A (versión inicial)

### Changed
- N/A (versión inicial)

### Removed
- N/A (versión inicial)

### Security
- Enmascarado automático de datos sensibles
- Validación de reglas para evitar inyecciones
- No almacenamiento de datos sin enmascarar en memoria innecesariamente

---

## Estructura de Versiones Futuras

### Próximas Versiones Planeadas

**v0.2.0** (Mejoras)
- Integración nativa con `structlog` y `Loguru`
- Modo "learning" para reducir falsos positivos
- Extensiones en C para hotspots de rendimiento

**v0.3.0** (Expansión)
- Plugin pre-commit
- GitHub Action
- JSONPath full support
- Exportadores para Fluentd/Logstash

**v1.0.0** (Estabilidad)
- API estable y congelada
- Documentación completa
- Suite de tests exhaustiva

---

[Unreleased]: https://github.com/buhozurdo/jsonmask/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/buhozurdo/jsonmask/releases/tag/v0.1.0
