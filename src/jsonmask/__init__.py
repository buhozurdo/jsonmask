"""jsonmask - Masking y redacción de datos sensibles en dicts, JSON y logs.

Una librería simple y configurable para detectar y enmascarar información sensible
dentro de estructuras de datos Python (dict/list), JSON y mensajes de logging.

Example:
    >>> from jsonmask import mask, Masker
    >>> data = {"user": {"email": "ana@example.com"}, "token": "secret123"}
    >>> rules = [{"path": "user.email", "strategy": "redact"}]
    >>> mask(data, rules=rules)
    {'user': {'email': '****'}, 'token': 'secret123'}

"""

from .logging_integration import MaskingFilter, MaskingHandler, StructuredLogMasker
from .masker import Masker, mask
from .presets import PII_PRESETS, get_preset, list_presets
from .strategies import (
    EntropyStrategy,
    HashStrategy,
    PartialStrategy,
    RedactStrategy,
    RegexStrategy,
    ReplaceStrategy,
)

__version__ = "0.1.0"
__author__ = "Rael Corrales"
__email__ = "raelcorrales@gmail.com"

__all__ = [
    # Core
    "Masker",
    "mask",
    # Logging
    "MaskingHandler",
    "MaskingFilter",
    "StructuredLogMasker",
    # Strategies
    "RedactStrategy",
    "ReplaceStrategy",
    "HashStrategy",
    "PartialStrategy",
    "RegexStrategy",
    "EntropyStrategy",
    # Presets
    "PII_PRESETS",
    "get_preset",
    "list_presets",
    # Meta
    "__version__",
]
