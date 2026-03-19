"""Integración con el sistema de logging de Python.

Proporciona MaskingHandler y MaskingFilter para enmascarar automáticamente
datos sensibles en mensajes de log.

Example:
    >>> import logging
    >>> from jsonmask import Masker, MaskingHandler
    >>>
    >>> masker = Masker.from_rules([{"path": "password", "strategy": "redact"}])
    >>> handler = logging.StreamHandler()
    >>> handler.addFilter(MaskingHandler(masker))
    >>>
    >>> logger = logging.getLogger("app")
    >>> logger.addHandler(handler)
    >>> logger.info("User data", extra={"password": "secret123"})
"""

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

if TYPE_CHECKING:
    from .masker import Masker


class MaskingFilter(logging.Filter):
    """Filtro de logging que enmascara datos sensibles en extras.

    Se usa como filter en handlers para interceptar y limpiar
    datos estructurados pasados como extra al logger.

    Example:
        >>> import logging
        >>> from jsonmask import Masker, MaskingFilter
        >>>
        >>> masker = Masker.from_rules([{"path": "token", "strategy": "hash"}])
        >>> filter = MaskingFilter(masker)
        >>>
        >>> logger = logging.getLogger("myapp")
        >>> logger.addFilter(filter)
    """

    def __init__(
        self,
        masker: "Masker",
        name: str = "",
        mask_message: bool = False,
        extra_keys: Optional[list] = None,
    ) -> None:
        """Inicializa el filtro.

        Args:
            masker: Instancia de Masker con reglas.
            name: Nombre del filtro (heredado de logging.Filter).
            mask_message: Si True, también enmascara el mensaje.
            extra_keys: Lista de claves extra a enmascarar (None = todas).
        """
        super().__init__(name)
        self.masker = masker
        self.mask_message = mask_message
        self.extra_keys = extra_keys

    def filter(self, record: logging.LogRecord) -> bool:
        """Filtra y enmascara el registro de log.

        Args:
            record: Registro de log a procesar.

        Returns:
            True (siempre permite el registro, pero lo modifica).
        """
        # Enmascarar extras
        self._mask_extras(record)

        # Opcionalmente enmascarar el mensaje
        if self.mask_message:
            self._mask_message(record)

        return True

    def _mask_extras(self, record: logging.LogRecord) -> None:
        """Enmascara los datos extra del registro."""
        # Obtener el dict del record (sin atributos estándar)
        standard_attrs = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "pathname", "process", "processName", "relativeCreated",
            "stack_info", "exc_info", "exc_text", "thread", "threadName",
            "message", "asctime"
        }

        for key in dir(record):
            if key.startswith("_") or key in standard_attrs:
                continue

            if self.extra_keys is not None and key not in self.extra_keys:
                continue

            try:
                value = getattr(record, key)
                if isinstance(value, (dict, list)):
                    masked = self.masker.mask(value)
                    setattr(record, key, masked)
            except Exception:
                # No romper logging si algo falla
                pass

    def _mask_message(self, record: logging.LogRecord) -> None:
        """Enmascara el mensaje del registro si contiene JSON."""
        try:
            msg = record.getMessage()
            # Intentar parsear como JSON
            data = json.loads(msg)
            if isinstance(data, (dict, list)):
                masked = self.masker.mask(data)
                record.msg = json.dumps(masked)
                record.args = ()
        except (json.JSONDecodeError, TypeError):
            # No es JSON, dejar el mensaje original
            pass


class MaskingHandler(logging.Filter):
    """Handler de logging que enmascara datos sensibles.

    Similar a MaskingFilter pero diseñado para usarse
    específicamente con handlers.

    Example:
        >>> import logging
        >>> from jsonmask import Masker, MaskingHandler
        >>>
        >>> masker = Masker.from_rules([{"path": "secret", "strategy": "redact"}])
        >>> handler = logging.StreamHandler()
        >>> handler.addFilter(MaskingHandler(masker))
    """

    def __init__(
        self,
        masker: "Masker",
        name: str = "",
        mask_args: bool = True,
        json_encoder: Optional[type] = None,
    ) -> None:
        """Inicializa el handler.

        Args:
            masker: Instancia de Masker.
            name: Nombre del filtro.
            mask_args: Si True, enmascara args del mensaje.
            json_encoder: Encoder JSON personalizado (opcional).
        """
        super().__init__(name)
        self.masker = masker
        self.mask_args = mask_args
        self.json_encoder = json_encoder

    def filter(self, record: logging.LogRecord) -> bool:
        """Filtra y enmascara el registro.

        Args:
            record: Registro de log.

        Returns:
            True (permite el registro).
        """
        # Enmascarar argumentos del mensaje
        if self.mask_args and record.args:
            record.args = self._mask_args(record.args)

        # Enmascarar extras
        self._mask_record_dict(record)

        return True

    def _mask_args(
        self, args: Union[tuple, Dict[str, Any]]
    ) -> Union[tuple, Dict[str, Any]]:
        """Enmascara los argumentos del mensaje."""
        if isinstance(args, dict):
            return self.masker.mask(args)
        elif isinstance(args, tuple):
            masked = []
            for arg in args:
                if isinstance(arg, (dict, list)):
                    masked.append(self.masker.mask(arg))
                else:
                    masked.append(arg)
            return tuple(masked)
        return args

    def _mask_record_dict(self, record: logging.LogRecord) -> None:
        """Enmascara el __dict__ del registro."""
        for key, value in list(record.__dict__.items()):
            if isinstance(value, (dict, list)):
                try:
                    masked = self.masker.mask(value)
                    setattr(record, key, masked)
                except Exception:
                    pass


class StructuredLogMasker:
    """Utilidad para enmascarar logs estructurados (JSON logging).

    Ideal para integración con structlog o json-logging.

    Example:
        >>> masker = Masker.from_rules([{"path": "user.email", "strategy": "redact"}])
        >>> log_masker = StructuredLogMasker(masker)
        >>> log_masker.mask_log_entry({"user": {"email": "test@x.com"}})
        {'user': {'email': '****'}}
    """

    def __init__(self, masker: "Masker") -> None:
        """Inicializa el masker de logs estructurados.

        Args:
            masker: Instancia de Masker.
        """
        self.masker = masker

    def mask_log_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Enmascara una entrada de log estructurado.

        Args:
            entry: Entrada de log (diccionario).

        Returns:
            Entrada enmascarada.
        """
        return self.masker.mask(entry)

    def mask_json_string(self, json_str: str) -> str:
        """Enmascara un string JSON.

        Args:
            json_str: String JSON.

        Returns:
            String JSON enmascarado.
        """
        try:
            data = json.loads(json_str)
            masked = self.masker.mask(data)
            return json.dumps(masked)
        except json.JSONDecodeError:
            return json_str

    def __call__(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Permite usar el objeto como callable."""
        return self.mask_log_entry(entry)
