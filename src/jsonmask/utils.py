"""Utilidades generales para jsonmask."""

import json
import math
from collections import Counter
from typing import Any, Dict, List, Union


def deep_copy_structure(data: Any) -> Any:
    """Crea una copia profunda de una estructura dict/list.

    Args:
        data: Estructura a copiar.

    Returns:
        Copia profunda de la estructura.
    """
    if isinstance(data, dict):
        return {k: deep_copy_structure(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [deep_copy_structure(item) for item in data]
    else:
        return data


def calculate_entropy(text: str) -> float:
    """Calcula la entropía de Shannon de un string.

    Args:
        text: Texto para calcular entropía.

    Returns:
        Valor de entropía en bits por carácter.
    """
    if not text:
        return 0.0

    counter = Counter(text)
    length = len(text)
    entropy = 0.0

    for count in counter.values():
        if count > 0:
            probability = count / length
            entropy -= probability * math.log2(probability)

    return entropy


def is_high_entropy(text: str, threshold: float = 3.5) -> bool:
    """Determina si un texto tiene alta entropía (posible token/secreto).

    Args:
        text: Texto a analizar.
        threshold: Umbral de entropía (default 3.5 bits/char).

    Returns:
        True si la entropía supera el umbral.
    """
    if len(text) < 8:  # Tokens muy cortos no son confiables
        return False
    return calculate_entropy(text) >= threshold


def is_json_serializable(obj: Any) -> bool:
    """Verifica si un objeto es serializable a JSON.

    Args:
        obj: Objeto a verificar.

    Returns:
        True si es serializable.
    """
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False


def flatten_dict(
    data: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, Any]:
    """Aplana un diccionario anidado.

    Args:
        data: Diccionario a aplanar.
        parent_key: Prefijo para las claves.
        sep: Separador entre niveles.

    Returns:
        Diccionario aplanado.

    Example:
        >>> flatten_dict({"user": {"name": "Ana", "email": "a@b.c"}})
        {'user.name': 'Ana', 'user.email': 'a@b.c'}
    """
    items: List[tuple] = []
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep).items())
        elif isinstance(value, list):
            for i, item in enumerate(value):
                indexed_key = f"{new_key}[{i}]"
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, indexed_key, sep).items())
                else:
                    items.append((indexed_key, item))
        else:
            items.append((new_key, value))
    return dict(items)


def merge_rules(
    *rule_lists: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Combina múltiples listas de reglas.

    Args:
        rule_lists: Listas de reglas a combinar.

    Returns:
        Lista combinada de reglas.
    """
    merged: List[Dict[str, Any]] = []
    seen_paths: set = set()

    for rules in rule_lists:
        for rule in rules:
            path = rule.get("path", "")
            if path not in seen_paths:
                merged.append(rule)
                seen_paths.add(path)

    return merged


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Trunca un string a un límite máximo.

    Args:
        text: Texto a truncar.
        max_length: Longitud máxima.
        suffix: Sufijo para indicar truncamiento.

    Returns:
        Texto truncado o el original si es más corto.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
