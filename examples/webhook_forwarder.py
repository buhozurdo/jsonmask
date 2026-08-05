#!/usr/bin/env python3
"""Ejemplo creativo: Reenviar webhooks sin filtrar datos sensibles.

Los proveedores de pago (Stripe, PayPal), CRM y todo tipo de SaaS te
envian webhooks con mucha mas informacion de la que necesitas reenviar.
Este ejemplo muestra como construir un "relay" de webhooks con jsonmask:
recibe el payload completo, enmascara lo que no debe salir de tu
infraestructura, y recien ahi lo reenvia al webhook handler propio o
a un servicio de analytics.

Demuestra:
    - Sanitizar multiples tipos de webhook (payment, customer, auth)
    - Estrategia regex sobre strings completos (ej: Bearer tokens)
    - Estrategia entropy para detectar tokens de alto secreto
    - Reutilizacion del mismo Masker en el loop principal
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Bootstrap: permite ejecutar el ejemplo directamente desde el repositorio
try:
    import jsonmask
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jsonmask import Masker

# ============================================================================
# Webhooks de ejemplo de un proveedor de pagos
# ============================================================================

WEBHOOKS = [
    # Webhook de pago cobrado
    {
        "type": "payment_intent.succeeded",
        "object": {
            "id": "pi_1234567890",
            "amount": 9990,
            "currency": "usd",
            "customer_email": "ana@example.com",
            "payment_method_details": {
                "card": {
                    "last4": "4242",
                    "brand": "visa",
                    "fingerprint": "abcdef123456",
                }
            },
            "receipt_url": "https://pay.stripe.com/receipts/abc123",
            "metadata": {"order_ids": "ORD-1001, ORD-1002"},
        },
    },
    # Webhook de nueva subscripcion
    {
        "type": "customer.subscription.created",
        "object": {
            "id": "sub_98765",
            "customer": "cus_555",
            "default_payment_method": "pm_card_visa",
            "items": {"data": [{"price": {"id": "price_M2"}}]},
            "billing_cycle_anchor": 1633046400,
        },
    },
    # Webhook de autenticacion (llega con token de menor privilegio)
    {
        "type": "auth.login.succeeded",
        "user": {"id": "user_42", "email": "carlos@example.com"},
        "session": {"jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"},
        "request": {"ip": "203.0.113.9"},
        "razorpay_signature": "f4f5cdca68c91f4d4d2acb2f6c9c69f7",
    },
]

# ============================================================================
# Reglas del relay
# ============================================================================

# Estrategia entropy: detecta cualquier string de alta entropia (tokens,
# signatures, fingerprints) que no estemos cubriendo por path explicito.
RULES = [
    # Datos bancarios/tarjeta
    {"path": "object.payment_method_details.card.fingerprint", "strategy": "hash", "hash_prefix_length": 8},
    {"path": "object.payment_method_details.card.last4", "strategy": "partial", "keep_end": 2},
    {"path": "object.receipt_url", "strategy": "regex", "pattern": r"receipts/\w+", "replace_with": "receipts/***"},

    # Clientes y emails
    {"path": "object.customer_email", "strategy": "redact", "replace_with": "***@***"},
    {"path": "user.email", "strategy": "redact", "replace_with": "***@***"},

    # Tokens de sesion y firmas
    {"path": "session.jwt", "strategy": "hash", "hash_prefix_length": 12},
    {"path": "*.signature", "strategy": "hash", "hash_prefix_length": 8},
    {"path": "razorpay_signature", "strategy": "hash", "hash_prefix_length": 8},

    # Entropia como red de seguridad final
    {"path": "*.fingerprint", "strategy": "entropy", "entropy_min": 3.0},
]

relay_masker = Masker.from_rules(RULES)


def forward_webhook(payload: Dict[str, Any], destination: str) -> None:
    """Simula el envio del webhook al destino final (analytics/webhook endpoint)."""
    # Enmascarar antes de serializar
    safe_payload = relay_masker.mask(payload)

    print(f"\n>> Enviando a '{destination}':")
    print(json.dumps(safe_payload, ensure_ascii=False, indent=2))


def main():
    print("=" * 60)
    print("jsonmask - Webhook relay seguro")
    print("=" * 60)

    # Broadcast a dos destinos: analytics y el endpoint propio
    # Ambos reciben el payload ya saneado.
    print("1) Procesando webhooks entrantes...\n")
    for i, webhook in enumerate(WEBHOOKS, 1):
        print("-" * 60)
        print(f"Webhook {i}: type={webhook['type']}")
        print("-" * 60)
        forward_webhook(webhook, "https://analytics.internal/collect")
        forward_webhook(webhook, "https://webhooks.mi-app.com/events")

    # Bonus: mostrar el equivalente CLI para un guardado a disco sin tocar
    # la codificacion. En produccion podrias usar:
    #   jsonmask mask -i backups/webhook.log --ndjson -r rules.yml > backups/webhook-safe.log
    print("\n" + "=" * 60)
    print("Tip: el mismo Masker se puede aplicar via CLI a lotes:")
    print('  cat webhooks.ndjson | jsonmask mask --ndjson -r rules.yml > webhooks-safe.ndjson')
    print("=" * 60)


if __name__ == "__main__":
    main()