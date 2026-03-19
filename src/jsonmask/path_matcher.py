"""Matching de paths con soporte de dot notation, wildcards e índices.

Este módulo permite hacer matching de paths en estructuras anidadas:
- Notación punto: user.email
- Wildcards: cards.*.number
- Índices: items[0].id
"""

import re
from typing import Any, Dict, Generator, List, Optional, Tuple, Union


class PathMatcher:
    """Clase para hacer matching de paths con wildcards."""

    # Regex para parsear segmentos del path
    INDEX_PATTERN = re.compile(r"^(.+?)\[(\d+|\*)\]$")

    def __init__(self, pattern: str):
        """Inicializa el matcher con un patrón.

        Args:
            pattern: Patrón de path (ej: "user.*.email", "items[0].id")
        """
        self.pattern = pattern
        self.segments = self._parse_pattern(pattern)
        self._compiled = True

    def _parse_pattern(self, pattern: str) -> List[Tuple[str, Optional[str]]]:
        """Parsea el patrón en segmentos.

        Args:
            pattern: Patrón a parsear.

        Returns:
            Lista de tuplas (key, index) donde index puede ser None, '*' o número.
        """
        segments = []
        # Dividir por punto, pero preservar los índices
        parts = self._split_path(pattern)

        for part in parts:
            match = self.INDEX_PATTERN.match(part)
            if match:
                key, index = match.groups()
                segments.append((key, index))
            else:
                segments.append((part, None))

        return segments

    def _split_path(self, pattern: str) -> List[str]:
        """Divide un path por puntos, respetando corchetes.

        Args:
            pattern: Path a dividir.

        Returns:
            Lista de partes del path.
        """
        parts = []
        current = ""
        bracket_depth = 0

        for char in pattern:
            if char == "[":
                bracket_depth += 1
                current += char
            elif char == "]":
                bracket_depth -= 1
                current += char
            elif char == "." and bracket_depth == 0:
                if current:
                    parts.append(current)
                current = ""
            else:
                current += char

        if current:
            parts.append(current)

        return parts

    def matches(self, path: str) -> bool:
        """Verifica si un path concreto coincide con el patrón.

        Args:
            path: Path concreto a verificar (ej: "user.cards[0].number")

        Returns:
            True si coincide con el patrón.
        """
        concrete_segments = self._parse_pattern(path)

        # Expandir segmentos con índices para comparación
        # users[0].email -> [users, [0], email]
        # users.*.email -> [users, *, email]
        pattern_expanded = self._expand_segments(self.segments)
        concrete_expanded = self._expand_segments(concrete_segments)

        if len(pattern_expanded) != len(concrete_expanded):
            return False

        for p_seg, c_seg in zip(pattern_expanded, concrete_expanded):
            # Si el patrón es wildcard, acepta cualquier cosa
            if p_seg == "*":
                continue
            # Si el patrón es wildcard de índice, acepta cualquier índice
            if p_seg == "[*]":
                if not (c_seg.startswith("[") and c_seg.endswith("]")):
                    return False
                continue
            # Comparar directamente
            if p_seg != c_seg:
                return False

        return True

    def _expand_segments(
        self, segments: List[Tuple[str, Optional[str]]]
    ) -> List[str]:
        """Expande segmentos a una lista plana para comparación."""
        result = []
        for key, idx in segments:
            result.append(key)
            if idx is not None:
                result.append(f"[{idx}]")
        return result

    def __repr__(self) -> str:
        return f"PathMatcher('{self.pattern}')"


def build_path(keys: List[Union[str, int]]) -> str:
    """Construye un path string desde una lista de keys.

    Args:
        keys: Lista de claves (strings) e índices (enteros).

    Returns:
        Path en formato string.

    Example:
        >>> build_path(["user", "cards", 0, "number"])
        'user.cards[0].number'
    """
    if not keys:
        return ""

    parts = []
    i = 0

    while i < len(keys):
        key = keys[i]
        if isinstance(key, int):
            # Índice - añadir al último elemento
            if parts:
                parts[-1] = f"{parts[-1]}[{key}]"
            else:
                parts.append(f"[{key}]")
        else:
            parts.append(str(key))
        i += 1

    return ".".join(parts)


def iter_paths(
    data: Any, prefix: List[Union[str, int]] = None
) -> Generator[Tuple[str, Any, List[Union[str, int]]], None, None]:
    """Itera sobre todos los paths de una estructura.

    Args:
        data: Estructura de datos a iterar.
        prefix: Prefijo actual del path.

    Yields:
        Tuplas de (path_string, value, keys_list).

    Example:
        >>> list(iter_paths({"user": {"name": "Ana"}}))
        [('user.name', 'Ana', ['user', 'name'])]
    """
    if prefix is None:
        prefix = []

    if isinstance(data, dict):
        for key, value in data.items():
            current_keys = prefix + [key]
            if isinstance(value, (dict, list)):
                yield from iter_paths(value, current_keys)
            else:
                yield build_path(current_keys), value, current_keys
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_keys = prefix + [i]
            if isinstance(item, (dict, list)):
                yield from iter_paths(item, current_keys)
            else:
                yield build_path(current_keys), item, current_keys


def set_value_at_path(
    data: Any, keys: List[Union[str, int]], value: Any
) -> None:
    """Establece un valor en un path específico.

    Args:
        data: Estructura de datos.
        keys: Lista de claves que forman el path.
        value: Valor a establecer.

    Example:
        >>> d = {"user": {"email": "old@example.com"}}
        >>> set_value_at_path(d, ["user", "email"], "****")
        >>> d
        {'user': {'email': '****'}}
    """
    if not keys:
        return

    current = data
    for key in keys[:-1]:
        if isinstance(key, int):
            current = current[key]
        else:
            current = current[key]

    final_key = keys[-1]
    if isinstance(final_key, int):
        current[final_key] = value
    else:
        current[final_key] = value


def get_value_at_path(
    data: Any, keys: List[Union[str, int]]
) -> Tuple[bool, Any]:
    """Obtiene un valor en un path específico.

    Args:
        data: Estructura de datos.
        keys: Lista de claves que forman el path.

    Returns:
        Tupla (found, value) donde found indica si se encontró el valor.

    Example:
        >>> get_value_at_path({"user": {"name": "Ana"}}, ["user", "name"])
        (True, 'Ana')
    """
    current = data
    try:
        for key in keys:
            if isinstance(key, int):
                current = current[key]
            else:
                current = current[key]
        return True, current
    except (KeyError, IndexError, TypeError):
        return False, None
