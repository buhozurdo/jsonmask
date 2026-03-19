"""Tests para las estrategias de enmascarado."""

import pytest

from jsonmask.strategies import (
    STRATEGY_REGISTRY,
    EntropyStrategy,
    HashStrategy,
    PartialStrategy,
    RedactStrategy,
    RegexStrategy,
    ReplaceStrategy,
    get_strategy,
    register_strategy,
)


class TestRedactStrategy:
    """Tests para RedactStrategy."""

    def test_redact_default(self):
        """Redact con placeholder por defecto."""
        strategy = RedactStrategy()
        result = strategy.apply("secret@email.com", {})
        assert result == "****"

    def test_redact_custom_placeholder(self):
        """Redact con placeholder personalizado."""
        strategy = RedactStrategy()
        result = strategy.apply("secret", {"replace_with": "[REDACTED]"})
        assert result == "[REDACTED]"

    def test_redact_name(self):
        """Nombre de la estrategia."""
        assert RedactStrategy().name == "redact"


class TestReplaceStrategy:
    """Tests para ReplaceStrategy."""

    def test_replace_with_value(self):
        """Replace con valor específico."""
        strategy = ReplaceStrategy()
        result = strategy.apply("original", {"replace_with": "nuevo"})
        assert result == "nuevo"

    def test_replace_default(self):
        """Replace sin especificar valor usa default."""
        strategy = ReplaceStrategy()
        result = strategy.apply("original", {})
        assert result == "****"


class TestHashStrategy:
    """Tests para HashStrategy."""

    def test_hash_default_length(self):
        """Hash con longitud por defecto."""
        strategy = HashStrategy()
        result = strategy.apply("secret", {})
        assert len(result) == 8

    def test_hash_custom_length(self):
        """Hash con longitud personalizada."""
        strategy = HashStrategy()
        result = strategy.apply("secret", {"hash_prefix_length": 16})
        assert len(result) == 16

    def test_hash_with_prefix(self):
        """Hash con prefijo personalizado."""
        strategy = HashStrategy()
        result = strategy.apply("secret", {"hash_prefix": "HASH:"})
        assert result.startswith("HASH:")

    def test_hash_consistent(self):
        """Hash es consistente para el mismo valor."""
        strategy = HashStrategy()
        result1 = strategy.apply("secret", {})
        result2 = strategy.apply("secret", {})
        assert result1 == result2

    def test_hash_different_values(self):
        """Hash es diferente para valores distintos."""
        strategy = HashStrategy()
        result1 = strategy.apply("secret1", {})
        result2 = strategy.apply("secret2", {})
        assert result1 != result2


class TestPartialStrategy:
    """Tests para PartialStrategy."""

    def test_partial_keep_start_end(self):
        """Partial manteniendo inicio y fin."""
        strategy = PartialStrategy()
        result = strategy.apply(
            "4111111111111111",
            {"keep_start": 4, "keep_end": 4}
        )
        assert result == "4111********1111"

    def test_partial_only_keep_start(self):
        """Partial manteniendo solo inicio."""
        strategy = PartialStrategy()
        result = strategy.apply(
            "1234567890",
            {"keep_start": 4, "keep_end": 0}
        )
        assert result == "1234******"

    def test_partial_only_keep_end(self):
        """Partial manteniendo solo fin."""
        strategy = PartialStrategy()
        result = strategy.apply(
            "1234567890",
            {"keep_start": 0, "keep_end": 4}
        )
        assert result == "******7890"

    def test_partial_custom_mask_char(self):
        """Partial con carácter personalizado."""
        strategy = PartialStrategy()
        result = strategy.apply(
            "12345678",
            {"keep_start": 2, "keep_end": 2, "mask_char": "#"}
        )
        assert result == "12####78"

    def test_partial_value_too_short(self):
        """Partial con valor más corto que keep_start + keep_end."""
        strategy = PartialStrategy()
        result = strategy.apply(
            "123",
            {"keep_start": 4, "keep_end": 4}
        )
        assert result == "***"  # Todo enmascarado


class TestRegexStrategy:
    """Tests para RegexStrategy."""

    def test_regex_bearer_token(self):
        """Regex para token Bearer."""
        strategy = RegexStrategy()
        result = strategy.apply(
            "Bearer abc123token",
            {"pattern": r"Bearer\s+(.+)", "replace_with": "Bearer ****"}
        )
        assert result == "Bearer ****"

    def test_regex_partial_match(self):
        """Regex con reemplazo parcial."""
        strategy = RegexStrategy()
        result = strategy.apply(
            "email: test@example.com here",
            {"pattern": r"\S+@\S+", "replace_with": "****@****.***"}
        )
        assert "****@****.***" in result

    def test_regex_invalid_pattern(self):
        """Regex inválido devuelve valor original."""
        strategy = RegexStrategy()
        result = strategy.apply(
            "original",
            {"pattern": "[invalid(regex", "replace_with": "nuevo"}
        )
        assert result == "original"

    def test_regex_no_match(self):
        """Regex sin match devuelve valor original."""
        strategy = RegexStrategy()
        result = strategy.apply(
            "no match here",
            {"pattern": r"Bearer\s+(.+)", "replace_with": "Bearer ****"}
        )
        assert result == "no match here"


class TestEntropyStrategy:
    """Tests para EntropyStrategy."""

    def test_entropy_high_entropy_masked(self):
        """Valor con alta entropía es enmascarado."""
        strategy = EntropyStrategy()
        # Token con alta entropía
        high_entropy = "aB3xK9mPq2LfNwYz"
        result = strategy.apply(high_entropy, {"entropy_min": 3.5})
        assert result == "****"

    def test_entropy_low_entropy_preserved(self):
        """Valor con baja entropía no es enmascarado."""
        strategy = EntropyStrategy()
        # Texto repetitivo = baja entropía
        low_entropy = "aaaaaaaaaa"
        result = strategy.apply(low_entropy, {"entropy_min": 3.5})
        assert result == low_entropy

    def test_entropy_short_value_preserved(self):
        """Valores cortos no se enmascaran."""
        strategy = EntropyStrategy()
        short = "abc123"
        result = strategy.apply(short, {"entropy_min": 3.5})
        assert result == short

    def test_entropy_custom_replacement(self):
        """Entropy con reemplazo personalizado."""
        strategy = EntropyStrategy()
        high_entropy = "aB3xK9mPq2LfNwYz123"
        result = strategy.apply(
            high_entropy,
            {"entropy_min": 3.0, "replace_with": "[HIGH-ENTROPY]"}
        )
        assert result == "[HIGH-ENTROPY]"


class TestStrategyRegistry:
    """Tests para el registro de estrategias."""

    def test_get_strategy_exists(self):
        """Obtiene estrategia existente."""
        strategy = get_strategy("redact")
        assert strategy is not None
        assert strategy.name == "redact"

    def test_get_strategy_not_exists(self):
        """Obtener estrategia inexistente devuelve None."""
        strategy = get_strategy("nonexistent")
        assert strategy is None

    def test_all_strategies_registered(self):
        """Todas las estrategias están registradas."""
        expected = ["redact", "replace", "hash", "partial", "regex", "entropy"]
        for name in expected:
            assert name in STRATEGY_REGISTRY
