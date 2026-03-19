#!/usr/bin/env python3
"""Ejemplo de integración de jsonmask con logging.

Demuestra cómo enmascarar automáticamente datos sensibles
en mensajes de log usando MaskingHandler y MaskingFilter.
"""

import json
import logging

from jsonmask import Masker, MaskingFilter, MaskingHandler
from jsonmask.logging_integration import StructuredLogMasker


def setup_logger_with_filter():
    """Configura logger con MaskingFilter."""
    print("=" * 50)
    print("Ejemplo 1: Logger con MaskingFilter")
    print("=" * 50)

    # Definir reglas
    rules = [
        {"path": "password", "strategy": "redact"},
        {"path": "token", "strategy": "hash", "hash_prefix_length": 8},
        {"path": "user.email", "strategy": "redact"},
    ]
    masker = Masker.from_rules(rules)

    # Crear logger
    logger = logging.getLogger("app.filter")
    logger.setLevel(logging.INFO)
    logger.handlers = []  # Limpiar handlers previos

    # Crear handler con filtro de enmascarado
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter('[%(levelname)s] %(message)s | %(data)s')
    )
    handler.addFilter(MaskingFilter(masker))
    logger.addHandler(handler)

    # Loggear con datos sensibles
    logger.info(
        "User login attempt",
        extra={"data": {"password": "secret123", "user": {"email": "ana@example.com"}}}
    )


def setup_logger_with_handler():
    """Configura logger con MaskingHandler."""
    print("\n" + "=" * 50)
    print("Ejemplo 2: Logger con MaskingHandler")
    print("=" * 50)

    rules = [
        {"path": "api_key", "strategy": "hash"},
        {"path": "secret", "strategy": "redact"},
    ]
    masker = Masker.from_rules(rules)

    logger = logging.getLogger("app.handler")
    logger.setLevel(logging.INFO)
    logger.handlers = []

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    handler.addFilter(MaskingHandler(masker))
    logger.addHandler(handler)

    # Loggear con argumentos que contienen datos sensibles
    logger.info("API call with key: %s", {"api_key": "sk_live_abc123", "action": "fetch"})


def structured_logging_example():
    """Ejemplo con logs estructurados (JSON)."""
    print("\n" + "=" * 50)
    print("Ejemplo 3: Logs estructurados (JSON)")
    print("=" * 50)

    rules = [
        {"path": "user.email", "strategy": "redact"},
        {"path": "user.ssn", "strategy": "partial", "keep_end": 4},
        {"path": "request.headers.authorization", "strategy": "regex",
         "pattern": r"Bearer\s+(.+)", "replace_with": "Bearer ****"},
    ]
    masker = Masker.from_rules(rules)
    log_masker = StructuredLogMasker(masker)

    # Entrada de log estructurado
    log_entry = {
        "timestamp": "2026-03-15T10:30:00Z",
        "level": "INFO",
        "message": "User authenticated",
        "user": {
            "id": "user_123",
            "email": "ana@example.com",
            "ssn": "123-45-6789"
        },
        "request": {
            "method": "POST",
            "path": "/api/auth",
            "headers": {
                "authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiYW5hIn0"
            }
        }
    }

    print("\nLog original:")
    print(json.dumps(log_entry, indent=2))

    masked_entry = log_masker.mask_log_entry(log_entry)

    print("\nLog enmascarado:")
    print(json.dumps(masked_entry, indent=2))


def json_string_masking():
    """Ejemplo de enmascarado de strings JSON."""
    print("\n" + "=" * 50)
    print("Ejemplo 4: Enmascarado de strings JSON")
    print("=" * 50)

    rules = [
        {"path": "password", "strategy": "redact"},
        {"path": "token", "strategy": "hash"},
    ]
    masker = Masker.from_rules(rules)
    log_masker = StructuredLogMasker(masker)

    # String JSON que podría venir de un sistema externo
    json_string = '{"username": "ana", "password": "secret123", "token": "abc123xyz"}'

    print(f"\nJSON original: {json_string}")

    masked_string = log_masker.mask_json_string(json_string)
    print(f"JSON enmascarado: {masked_string}")


def main():
    """Ejecuta todos los ejemplos."""
    setup_logger_with_filter()
    setup_logger_with_handler()
    structured_logging_example()
    json_string_masking()

    print("\n" + "=" * 50)
    print("¡Ejemplos de logging completados!")
    print("=" * 50)


if __name__ == "__main__":
    main()
