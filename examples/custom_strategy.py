#!/usr/bin/env python3
"""Ejemplo creativo: Estrategia personalizada para jsonmask.

jsonmask permite registrar estrategias propias ademas de las seis integradas
(redact, replace, hash, partial, regex, entropy). Esto es ideal cuando tu
dominio necesita un comportamiento de enmascarado especifico.

En este ejemplo creamos una estrategia que "anonimiza" nombres de personas
manteniendo la inicial, lo cual es util para datasets de demostracion,
dashboards compartidos o entrenamiento de modelos.

Demuestra:
    - Como extender jsonmask con una estrategia propia (register_strategy)
    - Uso de la nueva estrategia con path wildcards
    - La funcion list-strategies de la CLI tambien la mostrara
"""

import random
import sys
from pathlib import Path

# Bootstrap: permite ejecutar el ejemplo directamente desde el repositorio
try:
    import jsonmask
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jsonmask import Masker
from jsonmask.strategies import BaseStrategy, register_strategy

# Nombres de reemplazo (como "fake names" para tests de maqueta)
_SURNAMES = [
    "Garcia", "Martinez", "Lopez", "Sanchez", "Perez",
    "Gomez", "Fernandez", "Torres", "Rivera", "Morales",
]


class NameMaskingStrategy(BaseStrategy):
    """Reemplaza un nombre por una inicial + apellido ficticio.

    'Ana Garcia' -> 'A. Gomez'
    """

    @property
    def name(self) -> str:
        return "name_alias"

    def apply(self, value, options):
        """Aplica el enmascarado de nombres.

        Args:
            value: Nombre completo a anonimizar.
            options:
                - keep_initial: bool, conservar la inicial real (default: True)
        """
        text = str(value).strip()
        if not text:
            return text

        words = text.split()
        first_name = words[0]
        keep_initial = options.get("keep_initial", True)

        initial = first_name[0] if keep_initial else "X"
        fake_surname = random.choice(_SURNAMES)

        return f"{initial}. {fake_surname}"


def main():
    print("=" * 60)
    print("jsonmask - Estrategia personalizada: name_alias")
    print("=" * 60)

    # 1) Registrar la estrategia personalizada
    register_strategy("name_alias", NameMaskingStrategy())
    print("\n1) Estrategia 'name_alias' registrada")

    # 2) Usarla junto con estrategias integradas
    rules = [
        {"path": "employees.*.name", "strategy": "name_alias"},
        {"path": "employees.*.email", "strategy": "redact", "replace_with": "***"},
        {"path": "employees.*.salary", "strategy": "partial", "keep_end": 2},
    ]
    masker = Masker.from_rules(rules)

    team = {
        "department": "Engineering",
        "employees": [
            {"name": "Ana Garcia", "email": "ana@example.com", "salary": 85000},
            {"name": "Carlos Jimenez", "email": "carlos@example.com", "salary": 92000},
            {"name": "Luis Torres", "email": "luis@example.com", "salary": 78000},
        ],
    }

    print("\n2) Equipo original:")
    for emp in team["employees"]:
        print(f"   - {emp['name']} <{emp['email']}> ${emp['salary']}")

    masked = masker.mask(team)

    print("\n3) Equipo anonimizado para dashboard compartido:")
    for emp in masked["employees"]:
        print(f"   - {emp['name']} <{emp['email']}> ${emp['salary']}")

    # 3) Tambien se puede usar sobre todo un dataset
    from jsonmask import get_preset
    from jsonmask.presets import combine_presets

    full_rules = combine_presets("email") + rules
    full_masker = Masker.from_rules(full_rules)

    customer_data = {
        "customer": {"name": "Maria Lopez", "email": "maria@example.com"},
        "orders": [{"id": 1, "total": 99.5}],
    }
    masked_customer = full_masker.mask(customer_data)

    print("\n4) Cliente enmascarado con presets + custom strategy:")
    print(f"   {masked_customer}")


if __name__ == "__main__":
    main()