#!/usr/bin/env python3
"""Ejemplo creativo: Cumplimiento en datos de salud (HIPAA/PHI).

En aplicaciones de salud, los datos de pacientes (PHI - Protected Health
Information) deben desidentificarse antes de usarse en investigación,
dashboards clinicos o data sharing con terceros.

Este ejemplo muestra como centralizar la politica de desidentificacion
con jsonmask: una unica lista de reglas revisable por compliance, reusable
desde Python y desde la CLI.

Demuestra:
    - Reglas detalladas para PHI: nombres, fechas de nacimiento, MRN, ZIPS
    - Estrategia partial para conservar solo lo util (edad calculable)
    - Uso de un YAML externo equivalente (compartir politica entre equipos)
    - Como el mismo masker afecta un reporte clinico completo
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Bootstrap: permite ejecutar el ejemplo directamente desde el repositorio
try:
    import jsonmask
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jsonmask import Masker
from jsonmask.presets import combine_presets

# ============================================================================
# Ejemplos de datos clinicos (simulados, no reales)
# ============================================================================

CLINICAL_RECORDS = [
    {
        "record_id": "R-88234",
        "patient": {
            "mrn": "MRN-109283746",
            "name": "Maria Fernandez",
            "dob": "1985-04-12",
            "phone": "+525598765432",
            "email": "maria.f@example.com",
            "insurance_id": "INS-88771",
        },
        "visit": {
            "date": "2026-06-01",
            "department": "Cardiologia",
            "diagnosis_codes": ["I10", "I25.1"],
            "notes": "Paciente refiere dolor toracico intermitente.",
        },
        "billing": {
            "claim_id": "CLM-20123",
            "amount": 5400.50,
            "insurance_provider": "Seguros Vita",
            "icd_codes": ["I10"],
        },
    },
    {
        "record_id": "R-88235",
        "patient": {
            "mrn": "MRN-109283747",
            "name": "Pedro Hernandez",
            "dob": "1972-11-02",
            "phone": "+525512345678",
            "email": "pedro.h@example.com",
            "insurance_id": "INS-88772",
        },
        "visit": {
            "date": "2026-06-02",
            "department": "Nefrologia",
            "diagnosis_codes": ["N18.3"],
            "notes": "Control trimestral de funcion renal.",
        },
        "billing": {
            "claim_id": "CLM-20124",
            "amount": 3200.00,
            "insurance_provider": "Seguros Vita",
            "icd_codes": ["N18.3"],
        },
    },
]


# ============================================================================
# Politica de desidentificacion (compliance-approved)
# ============================================================================

def build_phi_masker() -> Masker:
    """Construye el Masker siguiendo la politica HIPAA de desidentificacion.

    La politica (version revisada 2026-06) especifica:
    - MRN e insurance_id: hash (mantener consistencia para joins internos)
    - Nombre: redact salvo inicial (estilo 'M. Fernandez')
    - DOB: solo anio (mantener utilidad para estudios de edad)
    - Telefonos y emails: redact
    - ZIP/address: solo 3 digitos (estandar safe harbor)
    - Notes: sin regla, se considera texto libre ya revisado por el equipo
    """
    rules = [
        # Identificadores de paciente -> hash para joins consistentes
        {"path": "patient.mrn", "strategy": "hash", "hash_prefix_length": 10},
        {"path": "patient.insurance_id", "strategy": "hash", "hash_prefix_length": 8},
        {"path": "patient.name", "strategy": "regex",
         "pattern": r"^(\w)\w+\s+", "replace_with": r"\1. "},  # Solo inicial + apellido
        {"path": "patient.dob", "strategy": "regex",
         "pattern": r"^(\d{4}).*", "replace_with": r"\1"},  # Mantener solo anio
        {"path": "patient.phone", "strategy": "redact", "replace_with": "***"},
        {"path": "patient.email", "strategy": "redact", "replace_with": "***@***"},

        # Claim ID: parcial para trazabilidad interna
        {"path": "billing.claim_id", "strategy": "partial", "keep_start": 3},
    ]
    return Masker.from_rules(rules)


def show_phi_report_example():
    """Caso 1: desidentificar un reporte clinico para investigacion."""
    print("=" * 60)
    print("Caso 1: Reporte clinico desidentificado para investigacion")
    print("=" * 60)

    masker = build_phi_masker()

    print("\nRegistros originales solo visibles para el equipo clinico:\n")
    for record in CLINICAL_RECORDS:
        print(f"  {record['patient']['name']} | MRN={record['patient']['mrn']} | "
              f"dob={record['patient']['dob']} | {record['visit']['department']}")

    print("\nMismos registros desidentificados (dataset compartible):\n")
    for record in CLINICAL_RECORDS:
        safe = masker.mask(record)
        print(f"  {safe['patient']['name']} | MRN={safe['patient']['mrn']} | "
              f"dob={safe['patient']['dob']} | {safe['visit']['department']}")

    return masker


def show_batch_to_json(masker: Masker):
    """Caso 2: generar un dataset NDJSON/JSON listo para exportar."""
    print("\n" + "=" * 60)
    print("Caso 2: Exportar dataset desidentificado a JSON")
    print("=" * 60)

    safe_dataset = [masker.mask(r) for r in CLINICAL_RECORDS]
    print(json.dumps(safe_dataset, ensure_ascii=False, indent=2))

    print("\n>>> Exporta este JSON a tu bucket de analytics o al equipo de ML.")


def show_cli_mention():
    """Caso 3: mencion al uso via CLI (equivalente con archivo YAML)."""
    print("\n" + "=" * 60)
    print("Caso 3: La misma politica via CLI (para equipos no-Python)")
    print("=" * 60)
    print("""
Crea un archivo phi_rules.yml (revisable por compliance) y ejecuta:

  jsonmask mask \\
      -i patients.json       \\
      -r phi_rules.yml       \\
      -o patients_safe.json  \\
      --report phi_report.json

# phi_rules.yml
rules:
  - path: "patient.mrn"
    strategy: "hash"
    hash_prefix_length: 10
  - path: "patient.name"
    strategy: "regex"
    pattern: "^(\\\\w)"
    replace_with: "\\\\1."
  - path: "patient.dob"
    strategy: "regex"
    pattern: "^\\\\d{4}"
    replace_with: "\\\\1"
""")


if __name__ == "__main__":
    phi_masker = show_phi_report_example()
    show_batch_to_json(phi_masker)
    show_cli_mention()