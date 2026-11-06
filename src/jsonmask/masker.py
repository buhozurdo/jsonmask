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
        learning_mode: bool = False,
    ) -> Union[Any, tuple]:
        """Enmascara datos sensibles según las reglas en una sola pasada.

        Args:
            data: Estructura de datos a enmascarar (dict/list).
            in_place: Si True, modifica el dict original.
            generate_report: Si True, retorna tupla (data, report).
            learning_mode: Si True, opera en modo aprendizaje (dry-run): 
                           evalúa las reglas pero no altera los datos.

        Returns:
            Datos enmascarados, o tupla (datos, reporte) si generate_report=True o learning_mode=True.

        Example:
            >>> masker = Masker.from_rules([{"path": "secret", "strategy": "redact"}])
            >>> masker.mask({"secret": "password123", "public": "hello"})
            {'secret': '****', 'public': 'hello'}
        """
        needs_report = generate_report or learning_mode
        if not isinstance(data, (dict, list)):
            if needs_report:
                return data, MaskingReport()
            return data

        report = MaskingReport() if needs_report else None

        if learning_mode:
            self._traverse_learning(data, "", report)
            return data, report

        if in_place:
            self._traverse_inplace(data, "", report)
            if generate_report:
                return data, report
            return data

        result = self._traverse_copy(data, "", report)
        if generate_report:
            return result, report
        return result

    def _mask_leaf(
        self,
        path: str,
        value: Any,
        report: Optional[MaskingReport],
    ) -> Any:
        """Aplica la primera regla que coincida con el campo hoja."""
        if report:
            report.total_fields_checked += 1

        for rule in self._rules:
            if rule.matches(path):
                masked_value = rule.apply(value)
                if report:
                    report.add_masked_field(path, value, masked_value, rule.path)
                return masked_value

        return value

    def _traverse_copy(
        self,
        node: Any,
        path_str: str,
        report: Optional[MaskingReport],
    ) -> Any:
        """Recorrido en una sola pasada clonando y enmascarando sin deepcopy."""
        if isinstance(node, dict):
            new_dict = {}
            for k, v in node.items():
                cur_path = f"{path_str}.{k}" if path_str else str(k)
                if isinstance(v, (dict, list)):
                    new_dict[k] = self._traverse_copy(v, cur_path, report)
                else:
                    new_dict[k] = self._mask_leaf(cur_path, v, report)
            return new_dict
        elif isinstance(node, list):
            new_list = [None] * len(node)
            for idx, item in enumerate(node):
                cur_path = f"{path_str}[{idx}]"
                if isinstance(item, (dict, list)):
                    new_list[idx] = self._traverse_copy(item, cur_path, report)
                else:
                    new_list[idx] = self._mask_leaf(cur_path, item, report)
            return new_list
        return node

    def _traverse_inplace(
        self,
        node: Any,
        path_str: str,
        report: Optional[MaskingReport],
    ) -> None:
        """Recorrido en una sola pasada modificando in-place."""
        if isinstance(node, dict):
            for k, v in node.items():
                cur_path = f"{path_str}.{k}" if path_str else str(k)
                if isinstance(v, (dict, list)):
                    self._traverse_inplace(v, cur_path, report)
                else:
                    node[k] = self._mask_leaf(cur_path, v, report)
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                cur_path = f"{path_str}[{idx}]"
                if isinstance(item, (dict, list)):
                    self._traverse_inplace(item, cur_path, report)
                else:
                    node[idx] = self._mask_leaf(cur_path, item, report)

    def _traverse_learning(
        self,
        node: Any,
        path_str: str,
        report: MaskingReport,
    ) -> None:
        """Recorrido de solo lectura en modo learning (dry-run)."""
        if isinstance(node, dict):
            for k, v in node.items():
                cur_path = f"{path_str}.{k}" if path_str else str(k)
                if isinstance(v, (dict, list)):
                    self._traverse_learning(v, cur_path, report)
                else:
                    self._mask_leaf(cur_path, v, report)
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                cur_path = f"{path_str}[{idx}]"
                if isinstance(item, (dict, list)):
                    self._traverse_learning(item, cur_path, report)
                else:
                    self._mask_leaf(cur_path, item, report)

    def _apply_rules_to_path(
        self,
        path: str,
        value: Any,
        keys: List[Union[str, int]],
        result: Any,
        report: Optional[MaskingReport],
        learning_mode: bool,
    ) -> None:
        """Busca y aplica la primera regla que coincida con el path (compatibilidad)."""
        for rule in self._rules:
            if rule.matches(path):
                masked_value = rule.apply(value)
                if not learning_mode:
                    set_value_at_path(result, keys, masked_value)
                if report:
                    report.add_masked_field(
                        path, value, masked_value, rule.path
                    )
                break

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
    learning_mode: bool = False,
) -> Union[Any, tuple]:
    """Función helper para enmascarar datos.

    Args:
        data: Datos a enmascarar.
        rules: Lista de reglas (si no se proporciona masker).
        masker: Masker precompilado (opcional).
        in_place: Si True, modifica el dict original.
        generate_report: Si True, retorna tupla (data, report).
        learning_mode: Si True, no modifica los datos y evalúa como dry-run.

    Returns:
        Datos enmascarados, o tupla (datos, reporte) si generate_report=True o learning_mode=True.

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

    return masker.mask(
        data, 
        in_place=in_place, 
        generate_report=generate_report,
        learning_mode=learning_mode
    )
