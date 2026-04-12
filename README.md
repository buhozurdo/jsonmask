# jsonmask

[![Build Status](https://i.ytimg.com/vi/GlqQGLz6hfs/hqdefault.jpg)
[![Coverage](https://i.ytimg.com/vi/bNVRxb-MKGo/sddefault.jpg)
[![PyPI version](https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/PyPI-Logo-notext.svg/3840px-PyPI-Logo-notext.svg.png)
[![Python versions](https://img.shields.io/pypi/pyversions/jsonmask.svg)](https://pypi.org/project/jsonmask/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Masking y redacción de datos sensibles en dicts, JSON y logs — simple, configurable y listo para integrarse en pipelines y aplicaciones Python.**

<p align="center">
  <img src="https://i.ytimg.com/vi/0gLzjbfsqDM/maxresdefault.jpg" alt="jsonmask logo" width="200">
</p>

---

## 🦉 Parte del Ecosistema Búho Zurdo

`jsonmask` es una herramienta open-source desarrollada por [Búho Zurdo](https://github.com/buhozurdo), enfocada en la protección de datos sensibles con la misma lealtad y precisión que caracterizan a nuestro ecosistema.

---

## ¿Qué es jsonmask?

`jsonmask` es una librería Python para detectar y enmascarar información sensible dentro de:
- Estructuras de datos Python (dict/list)
- Archivos JSON y NDJSON
- Mensajes de logging

Está pensada para integrarse fácilmente en aplicaciones, scripts y pipelines CI/CD donde quieras prevenir que PII, tokens o cualquier dato confidencial se filtre a logs, dumps o salidas externas.

### Principales objetivos

- ✅ Enmascarado declarativo por reglas (paths, patrones, entropía)
- ✅ Integración plug-and-play con el sistema `logging`
- ✅ Presets para PII comunes
- ✅ CLI para procesar archivos JSON/NDJSON
- ✅ Salida segura y configuraciones aptas para uso en CI

---

## 🚀 Instalación

```bash
pip install jsonmask
```

Para desarrollo:

```bash
git clone https://github.com/buhozurdo/jsonmask.git
cd jsonmask
pip install -e ".[dev]"
```

---

## 📖 Uso Rápido

### API Básica

```python
from jsonmask import mask, Masker

# Datos con información sensible
data = {
    "user": {"name": "Ana", "email": "ana@example.com"},
    "token": "eyJhbGciOiJIUzI1..."
}

# Definir reglas de enmascarado
rules = [
    {"path": "user.email", "strategy": "redact"},
    {"path": "token", "strategy": "hash"}
]

# Enmascarar
masked = mask(data, rules=rules)
print(masked)
# {
#   "user": {"name": "Ana", "email": "****"},
#   "token": "3a7bd3f..."  # valor hasheado
# }
```

### Masker Reutilizable (Recomendado para producción)

```python
from jsonmask import Masker

masker = Masker.from_rules(rules)
masked = masker.mask(data)

# Reutilizar para múltiples datos
for record in records:
    clean_record = masker.mask(record)
```

---

## 🔐 Integración con Logging

### Filtro de Masking para Logs Estándar

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

# Los datos sensibles serán enmascarados automáticamente
logger.info("Request", extra={"request": {"headers": {"authorization": "Bearer abc123"}}})
```

### Masking para Logs Estructurados (JSON)

```python
from jsonmask import Masker, StructuredLogMasker

rules = [
    {"path": "user.email", "strategy": "redact"},
    {"path": "credentials.api_key", "strategy": "hash"}
]

masker = Masker.from_rules(rules)
log_masker = StructuredLogMasker(masker)

# Enmascarar entrada de log estructurado
log_entry = {
    "level": "info",
    "message": "User logged in",
    "user": {"email": "test@example.com"}
}
masked_entry = log_masker.mask_log_entry(log_entry)

# Enmascarar string JSON directamente
json_log = '{"user": {"email": "test@example.com"}}'
masked_json = log_masker.mask_json_string(json_log)
```

---

## ⌨️ CLI

```bash
# Procesar archivo JSON
jsonmask mask --input data.json --rules rules.yml --output masked.json

# Procesar NDJSON desde stdin
cat data.ndjson | jsonmask mask --rules rules.yml --ndjson > masked.ndjson

# Generar reporte de campos enmascarados
jsonmask mask -i data.json -r rules.yml -o out.json --report report.json

# Validar archivo de reglas
jsonmask validate -r rules.yml

# Listar estrategias disponibles
jsonmask list-strategies

# Generar archivo de ejemplo de reglas
jsonmask generate-rules -o example_rules.yml
```

---

## 📋 Formato de Reglas

### Archivo YAML

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

### Soporte de Paths

| Tipo | Ejemplo | Descripción |
|------|---------|-------------|
| Notación punto | `user.email` | Acceso a campos anidados |
| Wildcard | `cards.*.number` | Cualquier clave en ese nivel |
| Índices | `items[0].id` | Índice específico en lista |
| Wildcard índice | `items[*].secret` | Todos los elementos de lista |

---

## 🎯 Estrategias de Enmascarado

| Estrategia | Descripción | Opciones |
|------------|-------------|----------|
| `redact` | Reemplaza con placeholder | `replace_with` |
| `replace` | Reemplaza con valor literal | `replace_with` |
| `hash` | SHA256 con prefijo | `hash_prefix_length`, `hash_prefix` |
| `partial` | Mantiene inicio/fin | `keep_start`, `keep_end`, `mask_char` |
| `regex` | Aplica regex | `pattern`, `replace_with` |
| `entropy` | Detecta alta entropía | `entropy_min`, `replace_with` |

---

## 📦 Presets PII

```python
from jsonmask import Masker
from jsonmask.presets import get_preset, combine_presets

# Usar preset individual
email_rules = get_preset("email")

# Combinar presets
rules = combine_presets("email", "credit_card", "token")
masker = Masker.from_rules(rules)
```

Presets disponibles: `email`, `credit_card`, `token`, `ssn`, `password`, `phone`, `pii` (todos)

---

## 📊 Generación de Reportes

```python
from jsonmask import mask

data = {"email": "test@example.com", "password": "secret"}
rules = [
    {"path": "email", "strategy": "redact"},
    {"path": "password", "strategy": "redact"}
]

masked, report = mask(data, rules=rules, generate_report=True)

print(report.to_dict())
# {
#   "total_fields_checked": 2,
#   "total_fields_masked": 2,
#   "masked_fields": [...]
# }
```

---

## ⚡ Rendimiento

- `Masker` compila reglas para ejecución repetida
- Recorrido iterativo para evitar stack overflow
- Recomendaciones para alta carga:
  - Usar sampling (procesar 1 de N mensajes)
  - Pre-filtrado por keys relevantes
  - Ejecutar en hilo/proceso separado

---

## 🛠️ Buenas Prácticas

1. **Prefiere reglas por `path`** en lugar de solo regex para disminuir falsos positivos
2. **Usa `Masker` reutilizable** en servicios de larga vida
3. **Versiona tu archivo `rules.yml`** y revísalo con el equipo de seguridad
4. **En CI**, ejecuta `jsonmask` antes de publicar artefactos con datos

---

## 🗺️ Roadmap

- [ ] Modo "learning" para reducir falsos positivos
- [ ] Integración nativa con `structlog` y `Loguru`
- [ ] Plugin pre-commit y GitHub Action
- [ ] Exportadores para Fluentd/Logstash
- [ ] JSONPath full support
- [ ] Extensiones en C para hotspots de rendimiento

---

## 🧪 Tests

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=src/jsonmask --cov-report=term-missing

# Solo tests específicos
pytest tests/test_masker.py -v
```

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor, lee [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles.

1. Fork del repositorio
2. Crear branch `feature/xxx`
3. Añadir tests y documentación
4. Crear Pull Request

---

## 📄 Licencia

MIT — ver [LICENSE](LICENSE) para más detalles.

---

## 👤 Mantenedor

**Rael Corrales** - [@raelcorrales](https://github.com/raelcorrales)

Proyecto parte del ecosistema [Búho Zurdo](https://github.com/buhozurdo) 🦉
