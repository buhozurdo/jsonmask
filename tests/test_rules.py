"""Tests para el módulo de reglas."""

import tempfile
from pathlib import Path

import pytest

from jsonmask.rules import (
    Rule,
    RuleValidationError,
    RulesParser,
    compile_rules,
    validate_rules,
)


class TestRule:
    """Tests para la clase Rule."""

    def test_rule_creation(self):
        """Crea una regla válida."""
        rule = Rule(path="user.email", strategy="redact")

        assert rule.path == "user.email"
        assert rule.strategy_name == "redact"
        assert rule.options == {}

    def test_rule_with_options(self):
        """Crea una regla con opciones."""
        rule = Rule(
            path="card.number",
            strategy="partial",
            options={"keep_start": 4, "keep_end": 4}
        )

        assert rule.options["keep_start"] == 4
        assert rule.options["keep_end"] == 4

    def test_rule_invalid_strategy(self):
        """Error con estrategia inválida."""
        with pytest.raises(RuleValidationError, match="desconocida"):
            Rule(path="test", strategy="invalid_strategy")

    def test_rule_matches(self):
        """Rule matches funciona correctamente."""
        rule = Rule(path="user.email", strategy="redact")

        assert rule.matches("user.email") is True
        assert rule.matches("user.name") is False

    def test_rule_apply(self):
        """Rule apply ejecuta la estrategia."""
        rule = Rule(path="secret", strategy="redact")
        result = rule.apply("password123")
        assert result == "****"

    def test_rule_to_dict(self):
        """Convierte regla a dict."""
        rule = Rule(
            path="email",
            strategy="redact",
            options={"replace_with": "***"}
        )

        result = rule.to_dict()

        assert result["path"] == "email"
        assert result["strategy"] == "redact"
        assert result["replace_with"] == "***"

    def test_rule_repr(self):
        """Representación string de Rule."""
        rule = Rule(path="test.path", strategy="hash")
        repr_str = repr(rule)
        assert "Rule" in repr_str
        assert "test.path" in repr_str
        assert "hash" in repr_str


class TestRulesParser:
    """Tests para RulesParser."""

    def test_from_dict(self):
        """Parsea regla desde dict."""
        rule_dict = {"path": "email", "strategy": "redact"}
        rule = RulesParser.from_dict(rule_dict)

        assert rule.path == "email"
        assert rule.strategy_name == "redact"

    def test_from_dict_missing_path(self):
        """Error si falta path."""
        with pytest.raises(RuleValidationError, match="path"):
            RulesParser.from_dict({"strategy": "redact"})

    def test_from_dict_missing_strategy(self):
        """Error si falta strategy."""
        with pytest.raises(RuleValidationError, match="strategy"):
            RulesParser.from_dict({"path": "email"})

    def test_from_list(self):
        """Parsea lista de reglas."""
        rules_list = [
            {"path": "email", "strategy": "redact"},
            {"path": "token", "strategy": "hash"},
        ]
        rules = RulesParser.from_list(rules_list)

        assert len(rules) == 2
        assert rules[0].path == "email"
        assert rules[1].path == "token"

    def test_from_yaml(self):
        """Parsea YAML con clave 'rules'."""
        yaml_content = """
rules:
  - path: "user.email"
    strategy: "redact"
  - path: "token"
    strategy: "hash"
"""
        rules = RulesParser.from_yaml(yaml_content)

        assert len(rules) == 2

    def test_from_yaml_list_format(self):
        """Parsea YAML como lista directa."""
        yaml_content = """
- path: "email"
  strategy: "redact"
- path: "password"
  strategy: "hash"
"""
        rules = RulesParser.from_yaml(yaml_content)

        assert len(rules) == 2

    def test_from_yaml_empty(self):
        """YAML vacío retorna lista vacía."""
        rules = RulesParser.from_yaml("")
        assert rules == []

    def test_from_json(self):
        """Parsea JSON."""
        json_content = '''
{
    "rules": [
        {"path": "email", "strategy": "redact"}
    ]
}
'''
        rules = RulesParser.from_json(json_content)

        assert len(rules) == 1

    def test_from_json_list_format(self):
        """Parsea JSON como lista directa."""
        json_content = '''[
    {"path": "email", "strategy": "redact"}
]'''
        rules = RulesParser.from_json(json_content)

        assert len(rules) == 1

    def test_from_file_yaml(self):
        """Carga reglas desde archivo YAML."""
        yaml_content = """
rules:
  - path: "secret"
    strategy: "redact"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            rules = RulesParser.from_file(f.name)

            assert len(rules) == 1

            # Cleanup
            Path(f.name).unlink()

    def test_from_file_not_found(self):
        """Error si archivo no existe."""
        with pytest.raises(FileNotFoundError):
            RulesParser.from_file("/nonexistent/rules.yaml")


class TestCompileRules:
    """Tests para compile_rules."""

    def test_compile_from_dicts(self):
        """Compila desde lista de dicts."""
        rules = compile_rules([
            {"path": "a", "strategy": "redact"},
            {"path": "b", "strategy": "hash"},
        ])

        assert len(rules) == 2
        assert all(isinstance(r, Rule) for r in rules)

    def test_compile_from_rules(self):
        """Compila desde lista de Rules (no-op)."""
        original = [
            Rule(path="a", strategy="redact"),
            Rule(path="b", strategy="hash"),
        ]
        rules = compile_rules(original)

        assert rules == original

    def test_compile_invalid_type(self):
        """Error con tipo inválido."""
        with pytest.raises(RuleValidationError):
            compile_rules(["not a rule"])


class TestValidateRules:
    """Tests para validate_rules."""

    def test_validate_valid_rules(self):
        """Reglas válidas retornan lista vacía."""
        rules = [
            {"path": "email", "strategy": "redact"},
            {"path": "token", "strategy": "hash"},
        ]
        errors = validate_rules(rules)
        assert errors == []

    def test_validate_missing_path(self):
        """Detecta falta de path."""
        rules = [{"strategy": "redact"}]
        errors = validate_rules(rules)
        assert len(errors) == 1
        assert "path" in errors[0]

    def test_validate_missing_strategy(self):
        """Detecta falta de strategy."""
        rules = [{"path": "email"}]
        errors = validate_rules(rules)
        assert len(errors) == 1
        assert "strategy" in errors[0]

    def test_validate_invalid_strategy(self):
        """Detecta estrategia inválida."""
        rules = [{"path": "email", "strategy": "unknown"}]
        errors = validate_rules(rules)
        assert len(errors) == 1
        assert "desconocida" in errors[0]

    def test_validate_not_dict(self):
        """Detecta regla que no es dict."""
        rules = ["not a dict"]
        errors = validate_rules(rules)
        assert len(errors) == 1
        assert "diccionario" in errors[0]
