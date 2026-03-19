"""Presets de reglas para PII común.

Incluye reglas predefinidas para:
- Emails
- Números de tarjeta de crédito
- Tokens JWT/Bearer
- SSN (básico)

Example:
    >>> from jsonmask.presets import get_preset, PII_PRESETS
    >>> email_rules = get_preset("email")
    >>> all_pii_rules = PII_PRESETS
"""

from typing import Any, Dict, List, Optional

# Preset para emails
EMAIL_PRESET: List[Dict[str, Any]] = [
    {
        "path": "email",
        "strategy": "redact",
        "replace_with": "****@****.***",
    },
    {
        "path": "*.email",
        "strategy": "redact",
        "replace_with": "****@****.***",
    },
    {
        "path": "user.email",
        "strategy": "redact",
        "replace_with": "****@****.***",
    },
    {
        "path": "customer.email",
        "strategy": "redact",
        "replace_with": "****@****.***",
    },
]

# Preset para tarjetas de crédito
CREDIT_CARD_PRESET: List[Dict[str, Any]] = [
    {
        "path": "card_number",
        "strategy": "partial",
        "keep_start": 4,
        "keep_end": 4,
        "mask_char": "*",
    },
    {
        "path": "*.card_number",
        "strategy": "partial",
        "keep_start": 4,
        "keep_end": 4,
        "mask_char": "*",
    },
    {
        "path": "cards.*.number",
        "strategy": "partial",
        "keep_start": 4,
        "keep_end": 4,
        "mask_char": "*",
    },
    {
        "path": "pan",
        "strategy": "partial",
        "keep_start": 6,
        "keep_end": 4,
        "mask_char": "*",
    },
    {
        "path": "cvv",
        "strategy": "redact",
        "replace_with": "***",
    },
    {
        "path": "*.cvv",
        "strategy": "redact",
        "replace_with": "***",
    },
]

# Preset para tokens (JWT, Bearer, API keys)
TOKEN_PRESET: List[Dict[str, Any]] = [
    {
        "path": "token",
        "strategy": "hash",
        "hash_prefix_length": 8,
    },
    {
        "path": "access_token",
        "strategy": "hash",
        "hash_prefix_length": 8,
    },
    {
        "path": "refresh_token",
        "strategy": "hash",
        "hash_prefix_length": 8,
    },
    {
        "path": "api_key",
        "strategy": "hash",
        "hash_prefix_length": 8,
    },
    {
        "path": "apiKey",
        "strategy": "hash",
        "hash_prefix_length": 8,
    },
    {
        "path": "headers.authorization",
        "strategy": "regex",
        "pattern": r"Bearer\s+(.+)",
        "replace_with": "Bearer ****",
    },
    {
        "path": "headers.Authorization",
        "strategy": "regex",
        "pattern": r"Bearer\s+(.+)",
        "replace_with": "Bearer ****",
    },
    {
        "path": "*.authorization",
        "strategy": "regex",
        "pattern": r"Bearer\s+(.+)",
        "replace_with": "Bearer ****",
    },
]

# Preset para SSN (Social Security Number - US)
SSN_PRESET: List[Dict[str, Any]] = [
    {
        "path": "ssn",
        "strategy": "partial",
        "keep_start": 0,
        "keep_end": 4,
        "mask_char": "*",
    },
    {
        "path": "social_security_number",
        "strategy": "partial",
        "keep_start": 0,
        "keep_end": 4,
        "mask_char": "*",
    },
    {
        "path": "*.ssn",
        "strategy": "partial",
        "keep_start": 0,
        "keep_end": 4,
        "mask_char": "*",
    },
]

# Preset para contraseñas
PASSWORD_PRESET: List[Dict[str, Any]] = [
    {
        "path": "password",
        "strategy": "redact",
        "replace_with": "********",
    },
    {
        "path": "*.password",
        "strategy": "redact",
        "replace_with": "********",
    },
    {
        "path": "secret",
        "strategy": "redact",
        "replace_with": "********",
    },
    {
        "path": "*.secret",
        "strategy": "redact",
        "replace_with": "********",
    },
]

# Preset para teléfonos
PHONE_PRESET: List[Dict[str, Any]] = [
    {
        "path": "phone",
        "strategy": "partial",
        "keep_start": 0,
        "keep_end": 4,
        "mask_char": "*",
    },
    {
        "path": "phone_number",
        "strategy": "partial",
        "keep_start": 0,
        "keep_end": 4,
        "mask_char": "*",
    },
    {
        "path": "*.phone",
        "strategy": "partial",
        "keep_start": 0,
        "keep_end": 4,
        "mask_char": "*",
    },
    {
        "path": "mobile",
        "strategy": "partial",
        "keep_start": 0,
        "keep_end": 4,
        "mask_char": "*",
    },
]

# Todos los presets PII combinados
PII_PRESETS: List[Dict[str, Any]] = (
    EMAIL_PRESET
    + CREDIT_CARD_PRESET
    + TOKEN_PRESET
    + SSN_PRESET
    + PASSWORD_PRESET
    + PHONE_PRESET
)

# Registro de presets por nombre
PRESET_REGISTRY: Dict[str, List[Dict[str, Any]]] = {
    "email": EMAIL_PRESET,
    "credit_card": CREDIT_CARD_PRESET,
    "token": TOKEN_PRESET,
    "ssn": SSN_PRESET,
    "password": PASSWORD_PRESET,
    "phone": PHONE_PRESET,
    "pii": PII_PRESETS,
    "all": PII_PRESETS,
}


def get_preset(name: str) -> Optional[List[Dict[str, Any]]]:
    """Obtiene un preset de reglas por nombre.

    Args:
        name: Nombre del preset (email, credit_card, token, ssn, password, phone, pii).

    Returns:
        Lista de reglas del preset o None si no existe.

    Example:
        >>> rules = get_preset("email")
        >>> len(rules) > 0
        True
    """
    return PRESET_REGISTRY.get(name.lower())


def list_presets() -> List[str]:
    """Lista los nombres de presets disponibles.

    Returns:
        Lista de nombres de presets.

    Example:
        >>> "email" in list_presets()
        True
    """
    return list(PRESET_REGISTRY.keys())


def combine_presets(*preset_names: str) -> List[Dict[str, Any]]:
    """Combina múltiples presets en una lista de reglas.

    Args:
        preset_names: Nombres de presets a combinar.

    Returns:
        Lista combinada de reglas (sin duplicados por path).

    Example:
        >>> rules = combine_presets("email", "token")
        >>> len(rules) > 0
        True
    """
    combined: List[Dict[str, Any]] = []
    seen_paths: set = set()

    for name in preset_names:
        preset = get_preset(name)
        if preset:
            for rule in preset:
                path = rule.get("path", "")
                if path not in seen_paths:
                    combined.append(rule)
                    seen_paths.add(path)

    return combined
