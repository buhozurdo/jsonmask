#!/usr/bin/env python3
"""Ejemplo creativo: ETL seguro — procesar eventos y streams NDJSON.

En un pipeline de datos (por ejemplo: eventos de una app -> Kinesis ->
S3 -> analytics) los datos pasan por muchos sistemas intermedios.
Con jsonmask se puede crear un "map" seguro en cada etapa: se aplica
el mismo Masker compilado a millones de eventos sin re-compilar
reglas ni preocuparse por olvidar campos.

Demuestra:
    - Procesar un stream NDJSON sin cargarlo todo en memoria
    - Un mismo Masker reutilizable en modo "worker"
    - Combinacion de pipelines: enmascarar y filtrar en el mismo paso
    - Reporte acumulado de cuantos campos se enmascararon
"""

import io
import json
import sys
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

# Bootstrap: permite ejecutar el ejemplo directamente desde el repositorio
try:
    import jsonmask
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jsonmask import Masker
from jsonmask.presets import combine_presets

# ============================================================================
# Datos de ejemplo: eventos de una aplicacion de e-commerce
# ============================================================================

SAMPLE_EVENTS = [
    {
        "event": "order.created",
        "order_id": "A-1001",
        "customer": {
            "name": "Ana Garcia",
            "email": "ana@example.com",
            "phone": "+523311223344",
            "address": {"street": "Av Reforma 123", "zip": "06600"},
        },
        "payment": {
            "card_number": "4111111111111111",
            "cvv": "123",
            "token": "tok_1Ey0Cx2eZvKYlo2C9tFkGhAb",
        },
        "items": [{"sku": "SKU-1", "qty": 2}],
    },
    {
        "event": "order.shipped",
        "order_id": "A-1001",
        "carrier": "DHL",
        "tracking": {"number": "DHL1234567890", "driver_phone": "+5215512345678"},
    },
    {
        "event": "auth.login",
        "user_id": "u_100",
        "ip": "203.0.113.42",
        "user_agent": "Mozilla/5.0",
        "session": {"jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"},
    },
]


def build_pipeline_masker() -> Masker:
    """Construye el Masker de todo el pipeline (una sola vez).

    Combina presets listos (email, tarjeta, token, telefono) y agrega
    reglas propias del dominio. Nota: los presets cubren claves muy
    comunes (token, phone) pero los campos anidados del dominio
    (payment.token, session.jwt, driver_phone) necesitan reglas extra.
    """
    rules = combine_presets("email", "credit_card", "token", "phone") + [
        # Campos anidados que los presets no cubren por wildcard
        {"path": "*.token", "strategy": "hash", "hash_prefix_length": 8},
        {"path": "*.jwt", "strategy": "hash", "hash_prefix_length": 12},
        {"path": "*.driver_phone", "strategy": "partial", "keep_end": 4},
        # Campos de dominio propio
        {"path": "customer.address.street", "strategy": "partial", "keep_end": 4},
        {"path": "tracking.number", "strategy": "partial", "keep_start": 3, "keep_end": 4},
    ]
    return Masker.from_rules(rules)


def mask_ndjson_stream(
    stream: io.TextIOBase,
    masker: Masker,
    output: io.TextIOBase,
    generate_report: bool = False,
) -> Dict[str, Any]:
    """Procesa un stream NDJSON linea por linea, sin cargarlo completo.

    Args:
        stream: Fuente de datos (archivo, pipe, socket, etc.)
        masker: Masker compilado y reutilizable.
        output: Destino del NDJSON enmascarado.
        generate_report: Si True, acumula un reporte global del stream.

    Returns:
        Reporte global del procesamiento.
    """
    total_events = 0
    total_masked_fields = 0

    for raw_line in stream:
        line = raw_line.strip()
        if not line:
            continue

        event = json.loads(line)
        total_events += 1

        if generate_report:
            masked_event, report = masker.mask(event, generate_report=True)
            total_masked_fields += report.total_fields_masked
        else:
            masked_event = masker.mask(event)

        output.write(json.dumps(masked_event, ensure_ascii=False) + "\n")

    return {
        "total_events": total_events,
        "total_masked_fields": total_masked_fields,
    }


def simple_pipeline_example():
    """Caso 1: pipeline de eventos con reporte global."""
    print("=" * 60)
    print("Caso 1: Stream NDJSON -> Masker -> NDJSON seguro")
    print("=" * 60)

    masker = build_pipeline_masker()

    # Simular un archivo NDJSON en memoria
    input_stream = io.StringIO(
        "\n".join(json.dumps(e) for e in SAMPLE_EVENTS) + "\n"
    )
    output_stream = io.StringIO()

    stats = mask_ndjson_stream(input_stream, masker, output_stream, generate_report=True)

    print(f"\nEventos procesados: {stats['total_events']}")
    print(f"Campos enmascarados en total: {stats['total_masked_fields']}")
    print("\nSalida NDJSON enmascarada:")
    print(output_stream.getvalue())


def two_layer_etl_example():
    """Caso 2: ETL de dos capas — la salida del primer paso alimenta otro.

    En pipelines reales se suele hacer enmascarado temprano (en el edge)
    y luego enmascarado adicional segun el destino (analitica, soporte,
    auditoria). Muestra como encadenar Maskers.
    """
    print("\n" + "=" * 60)
    print("Caso 2: ETL de dos capas (edge + destino)")
    print("=" * 60)

    # Capa 1 (edge): el mismo masker completo del pipeline, en el origen.
    # En produccion este iria en un servicio Lambda o worker al borde.
    edge_masker = build_pipeline_masker()

    # Capa 2 (analitica): ademas, quitar la direccion casi completa
    analytics_masker = Masker.from_rules(
        [
            {"path": "customer.address.street", "strategy": "partial", "keep_end": 0},
            {"path": "customer.address.zip", "strategy": "redact", "replace_with": "*****"},
            {"path": "tracking.number", "strategy": "redact", "replace_with": "####"},
        ]
    )

    # Procesar: primero el stream con la capa edge, luego aplicar la capa analitica
    input_stream = io.StringIO(
        "\n".join(json.dumps(e) for e in SAMPLE_EVENTS) + "\n"
    )
    edge_output = io.StringIO()
    mask_ndjson_stream(input_stream, edge_masker, edge_output)

    # Ahora la capa 2 sobre el resultado ya saneado
    final_output = io.StringIO()
    mask_ndjson_stream(io.StringIO(edge_output.getvalue()), analytics_masker, final_output)

    print("\nEvento 1 tras capa edge + capa analitica:")
    first_event = final_output.getvalue().strip().split("\n")[0]
    print(json.dumps(json.loads(first_event), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    simple_pipeline_example()
    two_layer_etl_example()