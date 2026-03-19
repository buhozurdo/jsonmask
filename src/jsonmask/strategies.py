"""Estrategias de enmascarado para jsonmask.

Este módulo contiene las diferentes estrategias de enmascarado disponibles:
- RedactStrategy: Reemplaza el valor completo con un placeholder.
- ReplaceStrategy: Reemplaza con un valor literal.
- HashStrategy: Aplica SHA256 y muestra un prefijo.
- PartialStrategy: Mantiene inicio/fin y enmascara el medio.
- RegexStrategy: Aplica expresión regular con grupos.
- EntropyStrategy: Detecta alta entropía y enmascara.
"""

import hashlib
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .utils import calculate_entropy


class BaseStrategy(ABC):
    """Clase base abstracta para estrategias de enmascarado."""

    @abstractmethod
    def apply(self, value: Any, options: Dict[str, Any]) -> Any:
        """Aplica la estrategia de enmascarado al valor.

        Args:
            value: Valor a enmascarar.
            options: Opciones de configuración de la estrategia.

        Returns:
            Valor enmascarado.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre de la estrategia."""
        pass


class RedactStrategy(BaseStrategy):
    """Reemplaza el valor completo con un placeholder.

    Example:
        >>> strategy = RedactStrategy()
        >>> strategy.apply("secret@email.com", {})
        '****'
    """

    @property
    def name(self) -> str:
        return "redact"

    def apply(self, value: Any, options: Dict[str, Any]) -> Any:
        """Reemplaza el valor con un placeholder.

        Args:
            value: Valor a redactar.
            options: Puede contener 'replace_with' para personalizar el placeholder.

        Returns:
            Placeholder (default: '****').
        """
        return options.get("replace_with", "****")


class ReplaceStrategy(BaseStrategy):
    """Reemplaza con un valor literal especificado.

    Example:
        >>> strategy = ReplaceStrategy()
        >>> strategy.apply("secret", {"replace_with": "[REDACTED]"})
        '[REDACTED]'
    """

    @property
    def name(self) -> str:
        return "replace"

    def apply(self, value: Any, options: Dict[str, Any]) -> Any:
        """Reemplaza con el valor literal especificado.

        Args:
            value: Valor original (ignorado).
            options: Debe contener 'replace_with' con el valor de reemplazo.

        Returns:
            Valor de reemplazo o '****' si no se especifica.
        """
        return options.get("replace_with", "****")


class HashStrategy(BaseStrategy):
    """Aplica SHA256 y devuelve un prefijo del hash.

    Example:
        >>> strategy = HashStrategy()
        >>> result = strategy.apply("secret", {"hash_prefix_length": 8})
        >>> len(result)
        8
    """

    @property
    def name(self) -> str:
        return "hash"

    def apply(self, value: Any, options: Dict[str, Any]) -> Any:
        """Calcula hash SHA256 del valor.

        Args:
            value: Valor a hashear.
            options: Puede contener:
                - hash_prefix_length: Longitud del prefijo (default: 8)
                - hash_prefix: Prefijo a añadir antes del hash

        Returns:
            Hash truncado del valor.
        """
        str_value = str(value)
        hash_bytes = hashlib.sha256(str_value.encode("utf-8")).hexdigest()

        prefix_length = options.get("hash_prefix_length", 8)
        prefix = options.get("hash_prefix", "")

        return f"{prefix}{hash_bytes[:prefix_length]}"


class PartialStrategy(BaseStrategy):
    """Mantiene inicio y fin del valor, enmascara el medio.

    Example:
        >>> strategy = PartialStrategy()
        >>> strategy.apply("4111111111111111", {"keep_start": 4, "keep_end": 4})
        '4111********1111'
    """

    @property
    def name(self) -> str:
        return "partial"

    def apply(self, value: Any, options: Dict[str, Any]) -> Any:
        """Enmascara parcialmente el valor.

        Args:
            value: Valor a enmascarar parcialmente.
            options: Puede contener:
                - keep_start: Caracteres a mantener al inicio (default: 0)
                - keep_end: Caracteres a mantener al final (default: 0)
                - mask_char: Carácter de enmascarado (default: '*')

        Returns:
            Valor parcialmente enmascarado.
        """
        str_value = str(value)
        keep_start = options.get("keep_start", 0)
        keep_end = options.get("keep_end", 0)
        mask_char = options.get("mask_char", "*")

        if len(str_value) <= keep_start + keep_end:
            return mask_char * len(str_value)

        start_part = str_value[:keep_start] if keep_start > 0 else ""
        end_part = str_value[-keep_end:] if keep_end > 0 else ""
        middle_length = len(str_value) - keep_start - keep_end

        return f"{start_part}{mask_char * middle_length}{end_part}"


class RegexStrategy(BaseStrategy):
    """Aplica expresión regular con reemplazo.

    Example:
        >>> strategy = RegexStrategy()
        >>> options = {"pattern": r"Bearer\\s+(.+)", "replace_with": "Bearer ****"}
        >>> strategy.apply("Bearer abc123token", options)
        'Bearer ****'
    """

    @property
    def name(self) -> str:
        return "regex"

    def apply(self, value: Any, options: Dict[str, Any]) -> Any:
        """Aplica regex y reemplaza matches.

        Args:
            value: Valor donde aplicar el regex.
            options: Debe contener:
                - pattern: Expresión regular
                - replace_with: Valor de reemplazo

        Returns:
            Valor con reemplazos aplicados.
        """
        str_value = str(value)
        pattern = options.get("pattern", "")
        replace_with = options.get("replace_with", "****")

        if not pattern:
            return str_value

        try:
            compiled = re.compile(pattern)
            return compiled.sub(replace_with, str_value)
        except re.error:
            # Si el regex es inválido, devolver el valor original
            return str_value


class EntropyStrategy(BaseStrategy):
    """Detecta valores de alta entropía y los enmascara.

    Útil para detectar tokens aleatorios, secretos, API keys, etc.

    Example:
        >>> strategy = EntropyStrategy()
        >>> # Un token aleatorio tiene alta entropía
        >>> strategy.apply("aB3xK9mPq2LfNwYz", {"entropy_min": 3.5})
        '****'
    """

    @property
    def name(self) -> str:
        return "entropy"

    def apply(self, value: Any, options: Dict[str, Any]) -> Any:
        """Enmascara si el valor tiene alta entropía.

        Args:
            value: Valor a analizar.
            options: Puede contener:
                - entropy_min: Umbral mínimo de entropía (default: 3.5)
                - replace_with: Valor de reemplazo si alta entropía

        Returns:
            Valor enmascarado si supera umbral, o el original.
        """
        str_value = str(value)
        entropy_min = options.get("entropy_min", 3.5)
        replace_with = options.get("replace_with", "****")

        entropy = calculate_entropy(str_value)

        if entropy >= entropy_min and len(str_value) >= 8:
            return replace_with

        return str_value


# Registro de estrategias disponibles
STRATEGY_REGISTRY: Dict[str, BaseStrategy] = {
    "redact": RedactStrategy(),
    "replace": ReplaceStrategy(),
    "hash": HashStrategy(),
    "partial": PartialStrategy(),
    "regex": RegexStrategy(),
    "entropy": EntropyStrategy(),
}


def get_strategy(name: str) -> Optional[BaseStrategy]:
    """Obtiene una estrategia por nombre.

    Args:
        name: Nombre de la estrategia.

    Returns:
        Instancia de la estrategia o None si no existe.
    """
    return STRATEGY_REGISTRY.get(name)


def register_strategy(name: str, strategy: BaseStrategy) -> None:
    """Registra una estrategia personalizada.

    Args:
        name: Nombre para la estrategia.
        strategy: Instancia de la estrategia.
    """
    STRATEGY_REGISTRY[name] = strategy
