"""Interfaz de línea de comandos para jsonmask.

Uso:
    jsonmask mask --input data.json --rules rules.yml --output masked.json
    cat data.ndjson | jsonmask mask --rules rules.yml > masked.ndjson
"""

import json
import sys
from pathlib import Path
from typing import Optional, TextIO

import click
import yaml

from . import __version__
from .masker import Masker
from .rules import RulesParser


def read_input(input_file: Optional[str], is_ndjson: bool) -> list:
    """Lee datos de entrada desde archivo o stdin.

    Args:
        input_file: Ruta al archivo o None para stdin.
        is_ndjson: Si True, parsea como NDJSON.

    Returns:
        Lista de objetos a procesar.
    """
    if input_file:
        content = Path(input_file).read_text(encoding="utf-8")
    else:
        content = sys.stdin.read()

    if is_ndjson:
        lines = content.strip().split("\n")
        return [json.loads(line) for line in lines if line.strip()]
    else:
        return [json.loads(content)]


def write_output(
    data: list, output_file: Optional[str], is_ndjson: bool, indent: int
) -> None:
    """Escribe datos de salida a archivo o stdout.

    Args:
        data: Lista de objetos procesados.
        output_file: Ruta al archivo o None para stdout.
        is_ndjson: Si True, escribe como NDJSON.
        indent: Indentación para JSON (0 para compacto).
    """
    if output_file:
        out: TextIO = open(output_file, "w", encoding="utf-8")
    else:
        out = sys.stdout

    try:
        for item in data:
            if is_ndjson:
                out.write(json.dumps(item, ensure_ascii=False) + "\n")
            else:
                json_indent = indent if indent > 0 else None
                out.write(json.dumps(item, ensure_ascii=False, indent=json_indent))
                out.write("\n")
    finally:
        if output_file:
            out.close()


@click.group()
@click.version_option(__version__, prog_name="jsonmask")
def cli() -> None:
    """jsonmask - Enmascarado de datos sensibles en JSON.

    Herramienta CLI para detectar y enmascarar información sensible
    en archivos JSON y NDJSON.
    """
    pass


@cli.command()
@click.option(
    "--input", "-i",
    "input_file",
    type=click.Path(exists=True),
    help="Archivo JSON/NDJSON de entrada (stdin si se omite)",
)
@click.option(
    "--rules", "-r",
    "rules_file",
    type=click.Path(exists=True),
    required=True,
    help="Archivo de reglas YAML/JSON",
)
@click.option(
    "--output", "-o",
    "output_file",
    type=click.Path(),
    help="Archivo de salida (stdout si se omite)",
)
@click.option(
    "--ndjson", "-n",
    is_flag=True,
    help="Tratar entrada/salida como NDJSON (newline-delimited JSON)",
)
@click.option(
    "--indent",
    type=int,
    default=2,
    help="Indentación JSON (0 para compacto, default: 2)",
)
@click.option(
    "--report",
    "report_file",
    type=click.Path(),
    help="Generar reporte de campos enmascarados",
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Modo silencioso (sin mensajes de progreso)",
)
def mask(
    input_file: Optional[str],
    rules_file: str,
    output_file: Optional[str],
    ndjson: bool,
    indent: int,
    report_file: Optional[str],
    quiet: bool,
) -> None:
    """Enmascara datos sensibles en archivos JSON/NDJSON.

    Ejemplos:

        # Procesar archivo JSON
        jsonmask mask -i data.json -r rules.yml -o masked.json

        # Procesar NDJSON desde stdin
        cat data.ndjson | jsonmask mask -r rules.yml --ndjson > masked.ndjson

        # Generar reporte
        jsonmask mask -i data.json -r rules.yml -o out.json --report report.json
    """
    try:
        # Cargar reglas
        rules = RulesParser.from_file(rules_file)
        masker = Masker(rules)

        if not quiet:
            click.echo(
                f"Cargadas {len(rules)} reglas desde {rules_file}",
                err=True
            )

        # Leer datos
        data = read_input(input_file, ndjson)

        if not quiet:
            click.echo(f"Procesando {len(data)} objeto(s)...", err=True)

        # Procesar
        generate_report = report_file is not None
        results = []
        all_reports = []

        for item in data:
            if generate_report:
                masked, report = masker.mask(item, generate_report=True)
                results.append(masked)
                all_reports.append(report.to_dict())
            else:
                masked = masker.mask(item)
                results.append(masked)

        # Escribir salida
        write_output(results, output_file, ndjson, indent)

        # Escribir reporte si se solicitó
        if report_file and all_reports:
            combined_report = {
                "total_objects": len(all_reports),
                "total_fields_masked": sum(
                    r["total_fields_masked"] for r in all_reports
                ),
                "objects": all_reports,
            }
            Path(report_file).write_text(
                json.dumps(combined_report, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            if not quiet:
                click.echo(f"Reporte guardado en {report_file}", err=True)

        if not quiet:
            total_masked = sum(
                r["total_fields_masked"] for r in all_reports
            ) if all_reports else "N/A"
            click.echo(f"✓ Completado. Campos enmascarados: {total_masked}", err=True)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except json.JSONDecodeError as e:
        click.echo(f"Error parseando JSON: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--rules", "-r",
    "rules_file",
    type=click.Path(exists=True),
    required=True,
    help="Archivo de reglas a validar",
)
def validate(rules_file: str) -> None:
    """Valida un archivo de reglas.

    Verifica que el archivo de reglas tenga sintaxis correcta
    y que todas las estrategias sean válidas.
    """
    try:
        rules = RulesParser.from_file(rules_file)
        click.echo(f"✓ Archivo válido: {len(rules)} regla(s) encontrada(s)")

        for i, rule in enumerate(rules, 1):
            click.echo(f"  {i}. path='{rule.path}' strategy='{rule.strategy_name}'")

    except Exception as e:
        click.echo(f"✗ Error de validación: {e}", err=True)
        sys.exit(1)


@cli.command()
def list_strategies() -> None:
    """Lista las estrategias de enmascarado disponibles."""
    from .strategies import STRATEGY_REGISTRY

    click.echo("Estrategias disponibles:\n")

    descriptions = {
        "redact": "Reemplaza el valor completo con '****'",
        "replace": "Reemplaza con un valor literal especificado",
        "hash": "Aplica SHA256 y muestra un prefijo del hash",
        "partial": "Mantiene inicio/fin, enmascara el medio",
        "regex": "Aplica expresión regular con reemplazo",
        "entropy": "Detecta alta entropía y enmascara",
    }

    for name in STRATEGY_REGISTRY:
        desc = descriptions.get(name, "Sin descripción")
        click.echo(f"  • {name}: {desc}")


@cli.command()
def generate_rules() -> None:
    """Genera un archivo de reglas de ejemplo."""
    example_rules = {
        "rules": [
            {
                "path": "user.email",
                "strategy": "redact",
                "replace_with": "****",
            },
            {
                "path": "cards.*.number",
                "strategy": "partial",
                "keep_start": 4,
                "keep_end": 4,
                "mask_char": "*",
            },
            {
                "path": "headers.authorization",
                "strategy": "regex",
                "pattern": "Bearer\\s+(.+)",
                "replace_with": "Bearer ****",
            },
            {
                "path": "token",
                "strategy": "hash",
                "hash_prefix_length": 8,
            },
        ]
    }

    click.echo(yaml.dump(example_rules, default_flow_style=False, allow_unicode=True))


def main() -> None:
    """Entry point principal."""
    cli()


if __name__ == "__main__":
    main()
