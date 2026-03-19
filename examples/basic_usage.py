#!/usr/bin/env python3
"""Ejemplo básico de uso de jsonmask.

Demuestra cómo enmascarar datos sensibles en diccionarios Python.
"""

from jsonmask import Masker, mask


def example_basic_masking():
    """Ejemplo básico con la función mask()."""
    print("=" * 50)
    print("Ejemplo 1: Enmascarado básico")
    print("=" * 50)

    # Datos con información sensible
    data = {
        "user": {
            "name": "Ana García",
            "email": "ana.garcia@example.com",
            "phone": "+34612345678"
        },
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }

    # Definir reglas de enmascarado
    rules = [
        {"path": "user.email", "strategy": "redact"},
        {"path": "user.phone", "strategy": "partial", "keep_start": 0, "keep_end": 4},
        {"path": "token", "strategy": "hash", "hash_prefix_length": 8}
    ]

    # Aplicar enmascarado
    masked = mask(data, rules=rules)

    print("\nDatos originales:")
    print(f"  Email: {data['user']['email']}")
    print(f"  Teléfono: {data['user']['phone']}")
    print(f"  Token: {data['token'][:30]}...")

    print("\nDatos enmascarados:")
    print(f"  Email: {masked['user']['email']}")
    print(f"  Teléfono: {masked['user']['phone']}")
    print(f"  Token: {masked['token']}")


def example_reusable_masker():
    """Ejemplo con Masker reutilizable."""
    print("\n" + "=" * 50)
    print("Ejemplo 2: Masker reutilizable")
    print("=" * 50)

    # Crear Masker una vez, reutilizar múltiples veces
    rules = [
        {"path": "password", "strategy": "redact"},
        {"path": "*.password", "strategy": "redact"},
        {"path": "secret", "strategy": "hash"}
    ]
    masker = Masker.from_rules(rules)

    # Procesar múltiples registros
    records = [
        {"user": "ana", "password": "pass123"},
        {"user": "bob", "password": "secret456"},
        {"user": "carlos", "password": "mypass789"},
    ]

    print("\nRegistros enmascarados:")
    for i, record in enumerate(records, 1):
        masked = masker.mask(record)
        print(f"  {i}. {masked}")


def example_with_report():
    """Ejemplo con generación de reporte."""
    print("\n" + "=" * 50)
    print("Ejemplo 3: Generación de reporte")
    print("=" * 50)

    data = {
        "credentials": {
            "api_key": "sk_live_abcdef123456",
            "secret": "super_secret_value"
        },
        "public_info": "Esta información es pública"
    }

    rules = [
        {"path": "credentials.api_key", "strategy": "hash"},
        {"path": "credentials.secret", "strategy": "redact"}
    ]

    masked, report = mask(data, rules=rules, generate_report=True)

    print("\nReporte de enmascarado:")
    print(f"  Campos revisados: {report.total_fields_checked}")
    print(f"  Campos enmascarados: {report.total_fields_masked}")
    print("\n  Detalles:")
    for field in report.masked_fields:
        print(f"    - {field['path']}: regla '{field['rule_applied']}'")


def example_wildcards():
    """Ejemplo con wildcards en paths."""
    print("\n" + "=" * 50)
    print("Ejemplo 4: Wildcards en paths")
    print("=" * 50)

    data = {
        "users": [
            {"email": "user1@example.com", "name": "User 1"},
            {"email": "user2@example.com", "name": "User 2"},
            {"email": "user3@example.com", "name": "User 3"}
        ],
        "cards": [
            {"number": "4111111111111111", "holder": "User 1"},
            {"number": "5500000000000004", "holder": "User 2"}
        ]
    }

    rules = [
        {"path": "users.*.email", "strategy": "redact"},
        {"path": "cards.*.number", "strategy": "partial", "keep_start": 4, "keep_end": 4}
    ]

    masked = mask(data, rules=rules)

    print("\nEmails enmascarados:")
    for user in masked["users"]:
        print(f"  - {user['name']}: {user['email']}")

    print("\nTarjetas enmascaradas:")
    for card in masked["cards"]:
        print(f"  - {card['holder']}: {card['number']}")


def main():
    """Ejecuta todos los ejemplos."""
    example_basic_masking()
    example_reusable_masker()
    example_with_report()
    example_wildcards()

    print("\n" + "=" * 50)
    print("¡Ejemplos completados!")
    print("=" * 50)


if __name__ == "__main__":
    main()
