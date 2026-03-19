"""Tests para el módulo masker."""

import pytest

from jsonmask import Masker, mask
from jsonmask.masker import MaskingReport


class TestMask:
    """Tests para la función mask()."""

    def test_mask_simple_dict(self):
        """Enmascara un campo simple en un dict."""
        data = {"email": "test@example.com", "name": "Ana"}
        rules = [{"path": "email", "strategy": "redact"}]

        result = mask(data, rules=rules)

        assert result["email"] == "****"
        assert result["name"] == "Ana"

    def test_mask_nested_dict(self):
        """Enmascara campos anidados."""
        data = {
            "user": {"email": "ana@example.com", "name": "Ana"},
            "token": "secret123",
        }
        rules = [
            {"path": "user.email", "strategy": "redact"},
            {"path": "token", "strategy": "hash"},
        ]

        result = mask(data, rules=rules)

        assert result["user"]["email"] == "****"
        assert result["user"]["name"] == "Ana"
        assert result["token"] != "secret123"  # Hasheado
        assert len(result["token"]) == 8  # Prefijo por defecto

    def test_mask_preserves_original(self):
        """Verifica que no modifica el dict original."""
        data = {"password": "secret123"}
        rules = [{"path": "password", "strategy": "redact"}]

        result = mask(data, rules=rules)

        assert data["password"] == "secret123"  # Original intacto
        assert result["password"] == "****"

    def test_mask_in_place(self):
        """Verifica modificación in-place."""
        data = {"password": "secret123"}
        rules = [{"path": "password", "strategy": "redact"}]

        result = mask(data, rules=rules, in_place=True)

        assert data["password"] == "****"  # Original modificado
        assert result is data

    def test_mask_with_list(self):
        """Enmascara valores dentro de listas."""
        data = {
            "users": [
                {"email": "a@b.com"},
                {"email": "c@d.com"},
            ]
        }
        rules = [{"path": "users.*.email", "strategy": "redact"}]

        result = mask(data, rules=rules)

        assert result["users"][0]["email"] == "****"
        assert result["users"][1]["email"] == "****"

    def test_mask_with_report(self):
        """Genera reporte de enmascarado."""
        data = {"secret": "password123", "public": "hello"}
        rules = [{"path": "secret", "strategy": "redact"}]

        result, report = mask(data, rules=rules, generate_report=True)

        assert isinstance(report, MaskingReport)
        assert report.total_fields_masked == 1
        assert len(report.masked_fields) == 1
        assert report.masked_fields[0]["path"] == "secret"

    def test_mask_no_rules(self):
        """Error cuando no hay reglas ni masker."""
        with pytest.raises(ValueError, match="rules.*masker"):
            mask({"data": "value"})

    def test_mask_scalar_value(self):
        """Maneja valores escalares sin error."""
        result = mask("simple string", rules=[])
        assert result == "simple string"


class TestMasker:
    """Tests para la clase Masker."""

    def test_masker_from_rules_dict(self):
        """Crea Masker desde lista de dicts."""
        rules = [
            {"path": "email", "strategy": "redact"},
            {"path": "token", "strategy": "hash"},
        ]

        masker = Masker.from_rules(rules)

        assert len(masker.rules) == 2

    def test_masker_reusable(self):
        """Masker es reutilizable para múltiples datos."""
        rules = [{"path": "secret", "strategy": "redact"}]
        masker = Masker.from_rules(rules)

        data1 = {"secret": "password1"}
        data2 = {"secret": "password2"}

        result1 = masker.mask(data1)
        result2 = masker.mask(data2)

        assert result1["secret"] == "****"
        assert result2["secret"] == "****"

    def test_masker_add_rule(self):
        """Añade reglas dinámicamente."""
        masker = Masker.from_rules([])
        masker.add_rule({"path": "new_field", "strategy": "redact"})

        result = masker.mask({"new_field": "value"})

        assert result["new_field"] == "****"

    def test_masker_repr(self):
        """Representación string del Masker."""
        masker = Masker.from_rules([{"path": "x", "strategy": "redact"}])
        assert "Masker" in repr(masker)
        assert "1" in repr(masker)


class TestMaskingReport:
    """Tests para MaskingReport."""

    def test_report_to_dict(self):
        """Convierte reporte a dict."""
        report = MaskingReport()
        report.total_fields_checked = 10
        report.add_masked_field("user.email", "a@b.com", "****", "user.email")

        result = report.to_dict()

        assert result["total_fields_checked"] == 10
        assert result["total_fields_masked"] == 1
        assert len(result["masked_fields"]) == 1
