"""Tests para el módulo utils."""

import pytest

from jsonmask.utils import (
    calculate_entropy,
    deep_copy_structure,
    flatten_dict,
    is_high_entropy,
    is_json_serializable,
    merge_rules,
    truncate_string,
)


class TestUtils:
    """Tests para las utilidades de jsonmask."""

    def test_deep_copy_structure(self):
        """Verifica copiado profundo de dicts, listas y primitivos."""
        data = {
            "name": "Ana",
            "numbers": [1, 2, [3, 4]],
            "meta": {"nested": "value"},
        }
        copied = deep_copy_structure(data)
        assert copied == data
        assert copied is not data
        assert copied["numbers"] is not data["numbers"]
        assert copied["meta"] is not data["meta"]

        # Primitivo
        assert deep_copy_structure("simple") == "simple"
        assert deep_copy_structure(123) == 123
        assert deep_copy_structure(None) is None

    def test_calculate_entropy(self):
        """Calcula la entropía de Shannon."""
        assert calculate_entropy("") == 0.0
        # Texto uniforme tiene entropía 0
        assert calculate_entropy("aaaaaaa") == 0.0
        # Texto con variedad de caracteres tiene entropía positiva
        entropy = calculate_entropy("abcdefgh")
        assert entropy > 0.0

    def test_is_high_entropy(self):
        """Evalúa si un texto supera el umbral de entropía."""
        # Tokens cortos (<8 chars) deben dar False
        assert is_high_entropy("abc") is False
        assert is_high_entropy("") is False

        # Token aleatorio largo (alta entropía)
        high_token = "K8x!9$mQ2#zL5@vP"
        assert is_high_entropy(high_token, threshold=3.0) is True

        # Texto repetitivo largo (baja entropía)
        low_text = "aaaaaaaaaaaaaaa"
        assert is_high_entropy(low_text) is False

    def test_is_json_serializable(self):
        """Verifica serializabilidad a JSON."""
        assert is_json_serializable({"a": 1, "b": [1, 2, "c"]}) is True
        assert is_json_serializable("hello") is True
        assert is_json_serializable(123) is True

        # Objetos no serializables por defecto (como sets u objects arbitrarios)
        assert is_json_serializable({1, 2, 3}) is False
        assert is_json_serializable(object()) is False

    def test_flatten_dict(self):
        """Aplana estructuras anidadas."""
        nested = {
            "user": {
                "name": "Ana",
                "contacts": [
                    {"type": "email", "value": "a@b.com"},
                    "direct_val",
                ],
            },
            "active": True,
        }
        flat = flatten_dict(nested)
        assert flat["user.name"] == "Ana"
        assert flat["user.contacts[0].type"] == "email"
        assert flat["user.contacts[0].value"] == "a@b.com"
        assert flat["user.contacts[1]"] == "direct_val"
        assert flat["active"] is True

    def test_merge_rules(self):
        """Combina listas de reglas descartando rutas duplicadas."""
        list1 = [
            {"path": "email", "strategy": "redact"},
            {"path": "phone", "strategy": "mask"},
        ]
        list2 = [
            {"path": "email", "strategy": "hash"},  # Duplicado, debe ignorarse
            {"path": "ssn", "strategy": "redact"},
        ]
        merged = merge_rules(list1, list2)
        assert len(merged) == 3
        paths = [r["path"] for r in merged]
        assert paths == ["email", "phone", "ssn"]
        assert merged[0]["strategy"] == "redact"

    def test_truncate_string(self):
        """Trunca strings según max_length."""
        assert truncate_string("short", max_length=10) == "short"
        assert truncate_string("this is a long text", max_length=10) == "this is..."
        assert truncate_string("exact10len", max_length=10) == "exact10len"
