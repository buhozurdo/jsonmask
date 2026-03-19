# Contribuir a jsonmask

¡Gracias por tu interés en contribuir a jsonmask! Este documento describe cómo puedes participar en el desarrollo del proyecto.

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [Setup de Desarrollo](#setup-de-desarrollo)
- [Estándares de Código](#estándares-de-código)
- [Proceso de Pull Request](#proceso-de-pull-request)
- [Ejecutar Tests](#ejecutar-tests)
- [Estructura del Proyecto](#estructura-del-proyecto)

---

## 🤝 Código de Conducta

Este proyecto sigue el [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). Al participar, se espera que respetes este código.

---

## 🛠️ Setup de Desarrollo

### Requisitos

- Python 3.8+
- pip
- Git

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/raelcorrales/jsonmask.git
cd jsonmask

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
.\venv\Scripts\activate  # Windows

# Instalar dependencias de desarrollo
pip install -e ".[dev]"
```

### Verificar instalación

```bash
# Ejecutar tests
pytest

# Verificar CLI
jsonmask --help
```

---

## 📝 Estándares de Código

### Estilo

Seguimos **PEP 8** con las siguientes herramientas:

| Herramienta | Propósito |
|-------------|----------|
| **Black** | Formateo automático |
| **isort** | Ordenamiento de imports |
| **ruff** | Linting rápido |
| **mypy** | Type checking |

### Ejecutar formateo

```bash
# Formatear código
black src/ tests/
isort src/ tests/

# Verificar linting
ruff check src/ tests/

# Type checking
mypy src/
```

### Docstrings

Usamos el estilo **Google** para docstrings:

```python
def mask(data: dict, rules: list) -> dict:
    """Enmascara datos sensibles según las reglas.

    Args:
        data: Diccionario con datos a enmascarar.
        rules: Lista de reglas de enmascarado.

    Returns:
        Diccionario con datos enmascarados.

    Raises:
        RuleValidationError: Si las reglas son inválidas.

    Example:
        >>> mask({"email": "a@b.com"}, [{"path": "email", "strategy": "redact"}])
        {'email': '****'}
    """
```

### Type Hints

Todas las funciones públicas deben tener type hints:

```python
from typing import Any, Dict, List, Optional

def process_rules(rules: List[Dict[str, Any]]) -> List[Rule]:
    ...
```

---

## 🔄 Proceso de Pull Request

### 1. Crear branch

```bash
# Desde main actualizado
git checkout main
git pull origin main

# Crear branch descriptivo
git checkout -b feature/nueva-estrategia
# o
git checkout -b fix/bug-en-regex
```

### 2. Hacer cambios

- Escribe código limpio y documentado
- Añade tests para nuevas funcionalidades
- Actualiza documentación si es necesario

### 3. Commits

Usamos **Conventional Commits**:

```
feat(strategies): add new 'truncate' strategy
fix(path_matcher): handle empty paths correctly
docs(readme): add CLI examples
test(masker): add edge case tests
refactor(rules): simplify validation logic
```

Tipos comunes:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `test`: Añadir o modificar tests
- `refactor`: Refactorización sin cambio funcional
- `chore`: Tareas de mantenimiento

### 4. Verificar antes de PR

```bash
# Formatear
black src/ tests/
isort src/ tests/

# Verificar
ruff check src/ tests/
mypy src/

# Tests con cobertura
pytest --cov=src/jsonmask --cov-report=term-missing
```

### 5. Crear Pull Request

- Título descriptivo
- Descripción de cambios
- Referencia a issues relacionados
- Screenshots si aplica

---

## 🧪 Ejecutar Tests

### Todos los tests

```bash
pytest
```

### Con cobertura

```bash
pytest --cov=src/jsonmask --cov-report=term-missing
```

### Tests específicos

```bash
# Por archivo
pytest tests/test_masker.py

# Por clase
pytest tests/test_masker.py::TestMasker

# Por función
pytest tests/test_masker.py::TestMasker::test_mask_simple_dict -v
```

### Cobertura mínima

Buscamos mantener **>80% de cobertura**. Nuevas funcionalidades deben incluir tests.

---

## 📁 Estructura del Proyecto

```
jsonmask/
├── pyproject.toml       # Configuración del proyecto
├── README.md            # Documentación principal
├── CONTRIBUTING.md      # Este archivo
├── LICENSE              # Licencia MIT
├── src/
│   └── jsonmask/
│       ├── __init__.py      # Exportaciones públicas
│       ├── masker.py        # Clase Masker principal
│       ├── strategies.py    # Estrategias de enmascarado
│       ├── rules.py         # Parser de reglas
│       ├── path_matcher.py  # Matching de paths
│       ├── logging_integration.py  # Integración logging
│       ├── cli.py           # Interfaz CLI
│       ├── presets.py       # Presets PII
│       └── utils.py         # Utilidades
├── tests/
│   ├── test_*.py        # Tests unitarios
│   └── fixtures/        # Datos de prueba
├── examples/            # Ejemplos de uso
└── .github/
    └── workflows/
        └── ci.yml       # GitHub Actions
```

---

## 💡 Ideas para Contribuir

### Good First Issues

- Añadir más tests de edge cases
- Mejorar mensajes de error
- Añadir ejemplos de uso
- Documentar presets

### Funcionalidades Pendientes

- Integración con structlog
- Integración con Loguru
- Nueva estrategia `truncate`
- Soporte JSONPath completo
- Pre-commit hook
- GitHub Action

---

## ❓ ¿Preguntas?

Si tienes dudas:

1. Revisa la [documentación](README.md)
2. Busca en [issues existentes](https://github.com/raelcorrales/jsonmask/issues)
3. Abre un nuevo issue con tu pregunta

---

¡Gracias por contribuir! 🦉
