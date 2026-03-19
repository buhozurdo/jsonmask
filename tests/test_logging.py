"""Tests para la integración con logging."""

import json
import logging
from io import StringIO

import pytest

from jsonmask import Masker, MaskingFilter, MaskingHandler
from jsonmask.logging_integration import StructuredLogMasker


class TestMaskingFilter:
    """Tests para MaskingFilter."""

    def test_filter_masks_extras(self):
        """El filtro enmascara datos en extras."""
        rules = [{"path": "password", "strategy": "redact"}]
        masker = Masker.from_rules(rules)
        filter = MaskingFilter(masker)

        # Crear un LogRecord con extras
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.data = {"password": "secret123", "user": "ana"}

        result = filter.filter(record)

        assert result is True  # Siempre permite
        assert record.data["password"] == "****"
        assert record.data["user"] == "ana"

    def test_filter_returns_true(self):
        """El filtro siempre retorna True."""
        masker = Masker.from_rules([])
        filter = MaskingFilter(masker)

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="",
            lineno=1, msg="test", args=(), exc_info=None
        )

        assert filter.filter(record) is True


class TestMaskingHandler:
    """Tests para MaskingHandler."""

    def test_handler_masks_dict_args(self):
        """El handler enmascara args tipo dict."""
        rules = [{"path": "secret", "strategy": "redact"}]
        masker = Masker.from_rules(rules)
        handler = MaskingHandler(masker)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Data: %s",
            args=({"secret": "password123"},),
            exc_info=None,
        )

        result = handler.filter(record)

        assert result is True
        # After masking, the secret should be masked
        # Args might be a tuple or dict depending on the masking path
        if isinstance(record.args, tuple):
            assert record.args[0]["secret"] == "****"
        else:
            assert record.args["secret"] == "****"

    def test_handler_masks_record_dict(self):
        """El handler enmascara __dict__ del record."""
        rules = [{"path": "token", "strategy": "hash"}]
        masker = Masker.from_rules(rules)
        handler = MaskingHandler(masker)

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="",
            lineno=1, msg="test", args=(), exc_info=None
        )
        record.request_data = {"token": "bearer_token_123"}

        handler.filter(record)

        # Token debe estar hasheado
        assert record.request_data["token"] != "bearer_token_123"
        assert len(record.request_data["token"]) == 8


class TestStructuredLogMasker:
    """Tests para StructuredLogMasker."""

    def test_mask_log_entry(self):
        """Enmascara entrada de log estructurado."""
        rules = [{"path": "user.email", "strategy": "redact"}]
        masker = Masker.from_rules(rules)
        log_masker = StructuredLogMasker(masker)

        entry = {
            "user": {"email": "test@example.com", "name": "Test"},
            "action": "login"
        }

        result = log_masker.mask_log_entry(entry)

        assert result["user"]["email"] == "****"
        assert result["user"]["name"] == "Test"

    def test_mask_json_string(self):
        """Enmascara string JSON."""
        rules = [{"path": "password", "strategy": "redact"}]
        masker = Masker.from_rules(rules)
        log_masker = StructuredLogMasker(masker)

        json_str = '{"password": "secret", "username": "ana"}'
        result = log_masker.mask_json_string(json_str)

        parsed = json.loads(result)
        assert parsed["password"] == "****"
        assert parsed["username"] == "ana"

    def test_mask_invalid_json_returns_original(self):
        """JSON inválido retorna string original."""
        masker = Masker.from_rules([])
        log_masker = StructuredLogMasker(masker)

        invalid_json = "not valid json"
        result = log_masker.mask_json_string(invalid_json)

        assert result == invalid_json

    def test_callable(self):
        """Se puede usar como callable."""
        rules = [{"path": "x", "strategy": "redact"}]
        masker = Masker.from_rules(rules)
        log_masker = StructuredLogMasker(masker)

        result = log_masker({"x": "secret"})

        assert result["x"] == "****"


class TestLoggingIntegration:
    """Tests de integración completa con logging."""

    def test_full_logging_flow(self):
        """Flujo completo de logging con enmascarado."""
        # Setup
        rules = [
            {"path": "password", "strategy": "redact"},
            {"path": "token", "strategy": "hash"},
        ]
        masker = Masker.from_rules(rules)

        # Crear logger con stream capturado
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.addFilter(MaskingFilter(masker))
        handler.setFormatter(logging.Formatter('%(message)s'))

        logger = logging.getLogger("test_integration")
        logger.setLevel(logging.INFO)
        logger.handlers = [handler]

        # Log con datos sensibles en extras
        logger.info("User login")

        # El mensaje debe estar en el output
        output = stream.getvalue()
        assert "User login" in output
