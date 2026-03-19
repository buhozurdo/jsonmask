"""Parser y validador de reglas de enmascarado.

Formato de reglas soportado:
```yaml
rules:
  - path: "user.email"
    strategy: "redact"
  - path: "cards.*.number"
    strategy: "partial"
    keep_start: 4
    keep_end: 4
```
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from .path_matcher import PathMatcher
from .strategies import STRATEGY_REGISTRY


class RuleValidationError(Exception):
    """Error de validación de reglas."""

    pass


class Rule:
    """Representa una regla de enmascarado compilada."""

    def __init__(
        self,
        path: str,
        strategy: str,
        options: Optional[Dict[str, Any]] = None,
    ):
        """Inicializa una regla.

        Args:
            path: Path pattern para matching.
            strategy: Nombre de la estrategia de enmascarado.
            options: Opciones adicionales para la estrategia.
        """
        self.path = path
        self.strategy_name = strategy
        self.options = options or {}
        self.matcher = PathMatcher(path)

        # Validar que la estrategia existe
        if strategy not in STRATEGY_REGISTRY:
            raise RuleValidationError(
                f"Estrategia desconocida: '{strategy}'. "
                f"Disponibles: {list(STRATEGY_REGISTRY.keys())}"
            )

        self.strategy = STRATEGY_REGISTRY[strategy]

    def matches(self, path: str) -> bool:
        """Verifica si un path coincide con esta regla.

        Args:
            path: Path concreto a verificar.

        Returns:
            True si coincide.
        """
        return self.matcher.matches(path)

    def apply(self, value: Any) -> Any:
        """Aplica la estrategia de enmascarado.

        Args:
            value: Valor a enmascarar.

        Returns:
            Valor enmascarado.
        """
        return self.strategy.apply(value, self.options)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la regla a diccionario.

        Returns:
            Representación en diccionario.
        """
        result = {"path": self.path, "strategy": self.strategy_name}
        if self.options:
            result.update(self.options)
        return result

    def __repr__(self) -> str:
        return f"Rule(path='{self.path}', strategy='{self.strategy_name}')"


class RulesParser:
    """Parser de reglas desde diferentes formatos."""

    @staticmethod
    def from_dict(rule_dict: Dict[str, Any]) -> Rule:
        """Crea una regla desde un diccionario.

        Args:
            rule_dict: Diccionario con la configuración de la regla.

        Returns:
            Instancia de Rule.

        Raises:
            RuleValidationError: Si el diccionario es inválido.
        """
        if "path" not in rule_dict:
            raise RuleValidationError("La regla debe tener un 'path'")

        if "strategy" not in rule_dict:
            raise RuleValidationError("La regla debe tener una 'strategy'")

        path = rule_dict["path"]
        strategy = rule_dict["strategy"]

        # Extraer opciones (todo lo que no sea path/strategy)
        options = {
            k: v for k, v in rule_dict.items() if k not in ("path", "strategy")
        }

        return Rule(path=path, strategy=strategy, options=options)

    @staticmethod
    def from_list(rules_list: List[Dict[str, Any]]) -> List[Rule]:
        """Crea reglas desde una lista de diccionarios.

        Args:
            rules_list: Lista de configuraciones de reglas.

        Returns:
            Lista de instancias de Rule.
        """
        return [RulesParser.from_dict(r) for r in rules_list]

    @staticmethod
    def from_yaml(yaml_content: str) -> List[Rule]:
        """Crea reglas desde contenido YAML.

        Args:
            yaml_content: String con contenido YAML.

        Returns:
            Lista de reglas.

        Example YAML:
            ```yaml
            rules:
              - path: "user.email"
                strategy: "redact"
            ```
        """
        data = yaml.safe_load(yaml_content)

        if data is None:
            return []

        if isinstance(data, list):
            return RulesParser.from_list(data)

        if isinstance(data, dict):
            if "rules" in data:
                return RulesParser.from_list(data["rules"])
            # Si es un solo dict, tratarlo como una regla
            return [RulesParser.from_dict(data)]

        raise RuleValidationError(
            "Formato YAML inválido: esperado dict con 'rules' o lista de reglas"
        )

    @staticmethod
    def from_json(json_content: str) -> List[Rule]:
        """Crea reglas desde contenido JSON.

        Args:
            json_content: String con contenido JSON.

        Returns:
            Lista de reglas.
        """
        data = json.loads(json_content)

        if isinstance(data, list):
            return RulesParser.from_list(data)

        if isinstance(data, dict):
            if "rules" in data:
                return RulesParser.from_list(data["rules"])
            return [RulesParser.from_dict(data)]

        raise RuleValidationError(
            "Formato JSON inválido: esperado dict con 'rules' o lista de reglas"
        )

    @staticmethod
    def from_file(file_path: Union[str, Path]) -> List[Rule]:
        """Carga reglas desde un archivo YAML o JSON.

        Args:
            file_path: Ruta al archivo de reglas.

        Returns:
            Lista de reglas.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Archivo de reglas no encontrado: {path}")

        content = path.read_text(encoding="utf-8")

        if path.suffix in (".yaml", ".yml"):
            return RulesParser.from_yaml(content)
        elif path.suffix == ".json":
            return RulesParser.from_json(content)
        else:
            # Intentar YAML primero, luego JSON
            try:
                return RulesParser.from_yaml(content)
            except Exception:
                return RulesParser.from_json(content)


def compile_rules(
    rules: Union[List[Dict[str, Any]], List[Rule]]
) -> List[Rule]:
    """Compila reglas para uso eficiente.

    Args:
        rules: Lista de reglas (dicts o Rules).

    Returns:
        Lista de reglas compiladas.
    """
    compiled = []
    for rule in rules:
        if isinstance(rule, Rule):
            compiled.append(rule)
        elif isinstance(rule, dict):
            compiled.append(RulesParser.from_dict(rule))
        else:
            raise RuleValidationError(f"Tipo de regla inválido: {type(rule)}")
    return compiled


def validate_rules(rules: List[Dict[str, Any]]) -> List[str]:
    """Valida una lista de reglas y retorna errores.

    Args:
        rules: Lista de reglas a validar.

    Returns:
        Lista de mensajes de error (vacía si todo es válido).
    """
    errors = []

    for i, rule in enumerate(rules):
        rule_id = f"Regla {i + 1}"

        if not isinstance(rule, dict):
            errors.append(f"{rule_id}: debe ser un diccionario")
            continue

        if "path" not in rule:
            errors.append(f"{rule_id}: falta campo 'path'")

        if "strategy" not in rule:
            errors.append(f"{rule_id}: falta campo 'strategy'")
        elif rule["strategy"] not in STRATEGY_REGISTRY:
            errors.append(
                f"{rule_id}: estrategia desconocida '{rule['strategy']}'"
            )

    return errors
