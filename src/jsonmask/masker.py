"""Módulo principal de enmascarado.

Contiene la clase Masker y la función helper mask() para enmascarar
datos sensibles en estructuras dict/list.

Example:
    >>> from jsonmask import mask, Masker
    >>> data = {"user": {"email": "ana@example.com"}}
    >>> rules = [{"path": "user.email", "strategy": "redact"}]
    >>> mask(data, rules=rules)
    {'user': {'email': '****'}}
"""

from typing import Any, Dict, List, Optional, Union

from .path_matcher import build_path, iter_paths, set_value_at_path
from .rules import Rule, RulesParser, compile_rules
from .utils import deep_copy_structure


class MaskingReport:
    """Reporte de campos enmascarados."""

    def __init__(self) -> None:
        """Inicializa el reporte."""
        self.masked_fields: List[Dict[str, Any]] = []
        self.total_fields_checked: int = 0
        self.total_fields_masked: int = 0

    def add_masked_field(
        self, path: str, original_value: Any, masked_value: Any, rule_path: str
    ) -> None:
        """Registra un campo enmascarado.

        Args:
            path: Path del campo.
            original_value: Valor original (truncado para seguridad).
            masked_value: Valor enmascarado.
            rule_path: Path de la regla aplicada.
        """
        self.masked_fields.append(
            {
                "path": path,
                "original_type": type(original_value).__name__,
                "masked_value": str(masked_value)[:50],  # Truncar por seguridad
                "rule_applied": rule_path,
            }
        )
        self.total_fields_masked += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el reporte a diccionario.

        Returns:
            Reporte en formato diccionario.
        """
        return {
            "total_fields_checked": self.total_fields_checked,
            "total_fields_masked": self.total_fields_masked,
            "masked_fields": self.masked_fields,
        }


class Masker:
    """Clase principal para enmascarado de datos.

    Compila y cachea reglas para ejecución eficiente en múltiples datos.

    Example:
        >>> masker = Masker.from_rules([{"path": "user.email", "strategy": "redact"}])
        >>> masker.mask({"user": {"email": "test@example.com"}})
        {'user': {'email': '****'}}
    """

    def __init__(self, rules: List[Rule]) -> None:
        """Inicializa el Masker con reglas compiladas.

        Args:
            rules: Lista de reglas compiladas.
        """
        self._rules = rules

    @classmethod
    def from_rules(
        cls, rules: Union[List[Dict[str, Any]], List[Rule]]
    ) -> "Masker":
        """Crea un Masker desde una lista de reglas.

        Args:
            rules: Lista de reglas (dicts o Rules).

        Returns:
            Instancia de Masker.

        Example:
            >>> rules = [{"path": "token", "strategy": "hash"}]
            >>> masker = Masker.from_rules(rules)
        """
        compiled = compile_rules(rules)
        return cls(compiled)

    @classmethod
    def from_file(cls, file_path: str) -> "Masker":
        """Crea un Masker desde un archivo de reglas.

        Args:
            file_path: Ruta al archivo YAML o JSON.

        Returns:
            Instancia de Masker.
        """
        rules = RulesParser.from_file(file_path)
        return cls(rules)

    @property
    def rules(self) -> List[Rule]:
        """Retorna las reglas compiladas."""
        return self._rules

    def mask(
        self,
        data: Any,
        in_place: bool = False,
        generate_report: bool = False,
    ) -> Union[Any, tuple]:
        """Enmascara datos sensibles según las reglas.

        Args:
            data: Estructura de datos a enmascarar (dict/list).
            in_place: Si True, modifica el dict original.
            generate_report: Si True, retorna tupla (data, report).

        Returns:
            Datos enmascarados, o tupla (datos, reporte) si generate_report=True.

        Example:
            >>> masker = Masker.from_rules([{"path": "secret", "strategy": "redact"}])
            >>> masker.mask({"secret": "password123", "public": "hello"})
            {'secret': '****', 'public': 'hello'}
        """
        if not isinstance(data, (dict, list)):
            # Para valores escalares, retornar tal cual
            if generate_report:
                return data, MaskingReport()
            return data

        # Trabajar con copia si no es in_place
        if in_place:
            result = data
        else:
            result = deep_copy_structure(data)

        report = MaskingReport() if generate_report else None

        # Iterar sobre todos los paths y aplicar reglas
        for path, value, keys in iter_paths(result):
            if report:
                report.total_fields_checked += 1

            # Buscar regla que coincida
            for rule in self._rules:
                if rule.matches(path):
                    masked_value = rule.apply(value)
                    set_value_at_path(result, keys, masked_value)

                    if report:
                        report.add_masked_field(
                            path, value, masked_value, rule.path
                        )
                    break  # Solo aplicar primera regla que coincida

        if generate_report:
            return result, report
        return result

    def add_rule(self, rule: Union[Dict[str, Any], Rule]) -> None:
        """Añade una regla al Masker.

        Args:
            rule: Regla a añadir (dict o Rule).
        """
        if isinstance(rule, dict):
            from .rules import RulesParser

            compiled = RulesParser.from_dict(rule)
        else:
            compiled = rule
        self._rules.append(compiled)

    def __repr__(self) -> str:
        return f"Masker(rules={len(self._rules)})"


def mask(
    data: Any,
    rules: Optional[List[Dict[str, Any]]] = None,
    masker: Optional[Masker] = None,
    in_place: bool = False,
    generate_report: bool = False,
) -> Union[Any, tuple]:
    """Función helper para enmascarar datos.

    Args:
        data: Datos a enmascarar.
        rules: Lista de reglas (si no se proporciona masker).
        masker: Masker precompilado (opcional).
        in_place: Si True, modifica el dict original.
        generate_report: Si True, retorna tupla (data, report).

    Returns:
        Datos enmascarados, o tupla (datos, reporte) si generate_report=True.

    Example:
        >>> data = {"email": "test@example.com", "name": "Ana"}
        >>> rules = [{"path": "email", "strategy": "redact"}]
        >>> mask(data, rules=rules)
        {'email': '****', 'name': 'Ana'}
    """
    if masker is None:
        if rules is None:
            raise ValueError("Debes proporcionar 'rules' o 'masker'")
        masker = Masker.from_rules(rules)

    return masker.mask(data, in_place=in_place, generate_report=generate_report)
