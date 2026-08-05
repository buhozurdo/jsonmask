#!/usr/bin/env python3
"""Ejemplo creativo: Pedidos de e-commerce — combinar todas las estrategias.

Un carrito/pedido tipico tiene PII del cliente, datos de pago, cupones,
direcciones y quizas datos de la tarjeta guardada. Este ejemplo muestra
como resolverlo con jsonmask usando TODAS las estrategias integradas
en un solo masker.

Demuestra:
    - redact: reemplazar valores completos
    - replace: sustituir por texto de negocio
    - hash: mantener consistencia para joins sin exponer el valor
    - partial: conservar lo util (ultimos 4 de tarjeta, ZIP)
    - regex: enmascarar dentro de strings compuestos
    - entropy: red de seguridad para valores random (cupones, ids)
    - Presets combinados: email, telefono, tarjeta, token
"""

import json
import sys
from pathlib import Path

# Bootstrap: permite ejecutar el ejemplo directamente desde el repositorio
try:
    import jsonmask
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jsonmask import Masker
from jsonmask.presets import combine_presets

# ============================================================================
# Pedido completo de una tienda online
# ============================================================================

ORDER = {
    "order": {
        "id": "ORD-20260601-4821",
        "date": "2026-06-01T12:34:56Z",
        "status": "paid",
    },
    "customer": {
        "id": "CUST-7788",
        "email": "valentina@example.com",
        "phone": "+524456789012",
        "firstName": "Valentina",
        "lastName": "Ramirez",
    },
    "shipping": {
        "address": "Av Central 456, Col Narvarte",
        "city": "CDMX",
        "zip": "03020",
    },
    "payment": {
        "provider": "stripe",
        "card": {
            "brand": "visa",
            "number": "4111111111111111",
            "exp_month": 8,
            "exp_year": 2028,
            "cvv": "123",
        },
        "transaction_id": "ch_3OqYhxLkdjf8Hkqlp1A",
    },
    "items": [
        {"sku": "SKU-HE-001", "name": "Audifonos X", "qty": 1, "price": 129.99},
        {"sku": "SKU-HE-002", "name": "Cable USB-C", "qty": 2, "price": 15.50},
    ],
    "discounts": [
        {"code": "SUMMER25", "type": "percent", "value": 25},
        {"code": "WELCOME10", "type": "fixed", "value": 10},
    ],
    "notes": "Cliente solicita entrega en horario de 2pm a 6pm",
    "coupon_reference": "CPN-AZB32XK9QW7",
}


def build_order_masker() -> Masker:
    """Construye un masker que aprovecha cada estrategia."""
    rules = (
        # --- Presets listos ---
        combine_presets("email", "credit_card", "token", "phone")
        + [
            # --- redact ---
            {"path": "customer.firstName", "strategy": "redact", "replace_with": "[Nombre]"},
            {"path": "customer.lastName", "strategy": "redact", "replace_with": "[Apellido]"},

            # --- replace (valor de negocio) ---
            {"path": "shipping.address", "strategy": "replace", "replace_with": "[Direccion protegida]"},

            # --- partial ---
            # Nota: los presets cubren 'card_number', 'cards.*.number' y '*.cvv',
            # pero NO este path anidado especifico del dominio. Hay que anadirlo.
            {"path": "payment.card.number", "strategy": "partial", "keep_start": 4, "keep_end": 4},
            {"path": "payment.card.cvv", "strategy": "redact", "replace_with": "***"},
            {"path": "shipping.zip", "strategy": "partial", "keep_start": 3},
            {"path": "payment.transaction_id", "strategy": "partial", "keep_end": 4},

            # --- regex: enmascarar dentro de strings compuestos ---
            {"path": "order.id", "strategy": "regex",
             "pattern": r"(ORD-\d{8}-)\w+", "replace_with": r"\1***"},
            {"path": "shipping.city", "strategy": "regex",
             "pattern": r"^\w", "replace_with": "*"},  # Solo primera letra

            # --- entropy: los codigos de cupon son alta entropia ---
            {"path": "*.coupon_reference", "strategy": "entropy", "entropy_min": 3.0,
             "replace_with": "[Cupon]"},
        ]
    )
    return Masker.from_rules(rules)


def main():
    print("=" * 60)
    print("jsonmask - Pedido e-commerce con todas las estrategias")
    print("=" * 60)

    masker = build_order_masker()

    print("\n1) Pedido original (como llega del checkout):")
    print(json.dumps(ORDER, ensure_ascii=False, indent=2)[:900])
    print("   ...")

    print("\n" + "-" * 60)
    print("2) Pedido enmascarado (pasado al ERP / soporte / log):")
    masked = masker.mask(ORDER)
    print(json.dumps(masked, ensure_ascii=False, indent=2))

    print("\n" + "-" * 60)
    print("3) Estrategias usadas en este ejemplo:")
    print("   redact    -> firstName, lastName")
    print("   replace   -> shipping.address")
    print("   hash      -> token/api_key (presets), transaction_id")
    print("   partial   -> card number (preset), zip, transaction_id")
    print("   regex     -> order.id, shipping.city")
    print("   entropy   -> coupon_reference (cualquier valor random)")
    print("   presets   -> email, credit_card, token, phone")


if __name__ == "__main__":
    main()