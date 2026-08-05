#!/usr/bin/env python3
"""Ejemplo creativo: Sanitizar respuestas de API antes de enviarlas.

Cuando devuelves datos de usuarios, pedidos u otras entidades desde un
backend, es facil olvidar un campo sensible. jsonmask puede actuar como
una capa final de seguridad sobre la respuesta: pase lo que pase,
los campos protegidos nunca salen al cliente.

Este ejemplo simula un endpoint de API (sin dependencias externas,
solo la libreria estandar) demuestra:
    - Crear un Masker reutilizable por endpoint
    - Sanitizar la respuesta JSON antes de serializarla
    - Patron "middleware" aplicable a FastAPI, Flask, Django Rest, etc.
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable, Dict

# Bootstrap: permite ejecutar el ejemplo directamente desde el repositorio
try:
    import jsonmask
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jsonmask import Masker
from jsonmask.presets import combine_presets


class UserProfile:
    """Entidad de negocio que podria venir de una base de datos."""

    def __init__(self, user_id: str, name: str, email: str, ssn: str, api_key: str):
        self.id = user_id
        self.name = name
        self.email = email
        self.ssn = ssn
        self.api_key = api_key

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el objeto como dict (tipico de ORMs)."""
        return {
            "id": self.id,
            "profile": {
                "name": self.name,
                "email": self.email,
                "ssn": self.ssn,
            },
            "credentials": {
                "api_key": self.api_key,
            },
        }


# ============================================================================
# Saneamiento con jsonmask
# ============================================================================

# Reglas de proteccion: combinamos preset de SSN + API keys y anadimos email
SANITIZED_RULES = combine_presets("ssn", "token") + [
    {"path": "profile.email", "strategy": "redact", "replace_with": "***@***"},
    {"path": "profile.name", "strategy": "partial", "keep_start": 1},
]

api_masker = Masker.from_rules(SANITIZED_RULES)


def safe_response(payload: Any) -> str:
    """Serializa un payload con los campos sensibles ya enmascarados.

    Este es el reemplazo directo de json.dumps() en cualquier framework:
    FastAPI -> dependencia/getter, Flask -> before_request, etc.
    """
    masked = api_masker.mask(payload)
    return json.dumps(masked, ensure_ascii=False, indent=2)


# ============================================================================
# Simulacion de un endpoint HTTP (stdlib: http.server)
# ============================================================================

USERS_DB = {
    "42": UserProfile("42", "Ana Garcia", "ana@example.com", "123-45-6789", "sk_live_abc123"),
    "77": UserProfile("77", "Carlos Lopez", "carlos@example.com", "987-65-4321", "sk_live_xyz789"),
}


class UsersAPIHandler(BaseHTTPRequestHandler):
    """Mini API REST: GET /users/<id> con la respuesta saneada."""

    def do_GET(self):
        # Path como "/users/42"
        parts = self.path.strip("/").split("/")
        if len(parts) == 2 and parts[0] == "users" and parts[1].isdigit():
            user = USERS_DB.get(parts[1])
            if user is None:
                self._send_json(404, {"error": "not_found"})
                return

            # Aqui esta la magia: el objeto se serializa de forma segura
            body = safe_response(user.to_dict())
            self._send_json(200, body)
        else:
            self._send_json(400, {"error": "bad_request"})

        # Log de auditoria en el servidor: el dato interno NO se filtra al log
        print(f"[AUDIT] GET {self.path} -> respuesta enviada con campos protegidos")

    def _send_json(self, status: int, body: Any) -> None:
        payload = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("X-Masked-By", "jsonmask")
        self.end_headers()
        self.wfile.write(payload.encode("utf-8"))

    def log_message(self, fmt, *args):
        # Suprimir el log por defecto para una salida limpia
        pass


def main():
    print("=" * 60)
    print("jsonmask - Sanitizar respuestas de API")
    print("=" * 60)

    # Primero mostramos que el mismo payload se ve diferente si
    # se envia crudo o si pasa por jsonmask.
    print("\n1) Payload interno (lo que la BD devuelve):")
    internal = USERS_DB["42"].to_dict()
    print(json.dumps(internal, ensure_ascii=False, indent=2))

    print("\n2) Respuesta publica enviada al cliente:")
    print(safe_response(internal))

    print("\n" + "-" * 60)
    print("3) Levantando mini servidor HTTP en http://localhost:8080")
    print("   Prueba: curl -s http://localhost:8080/users/42")
    print("-" * 60)

    server = HTTPServer(("127.0.0.1", 8080), UsersAPIHandler)
    print("   Servidor listo. Ctrl+C para detener.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n   Servidor detenido.")


if __name__ == "__main__":
    main()