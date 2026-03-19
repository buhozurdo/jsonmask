"""Tests para la CLI."""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from jsonmask.cli import cli


class TestMaskCommand:
    """Tests para el comando mask."""

    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def rules_file(self):
        """Archivo de reglas temporal."""
        content = """
rules:
  - path: "email"
    strategy: "redact"
  - path: "password"
    strategy: "redact"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(content)
            f.flush()
            yield f.name
            Path(f.name).unlink()

    @pytest.fixture
    def json_file(self):
        """Archivo JSON temporal."""
        data = {"email": "test@example.com", "name": "Test User"}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            f.flush()
            yield f.name
            Path(f.name).unlink()

    def test_mask_file(self, runner, rules_file, json_file):
        """Enmascara archivo JSON."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as output_file:
            result = runner.invoke(
                cli,
                ["mask", "-i", json_file, "-r", rules_file, "-o", output_file.name, "-q"]
            )

            assert result.exit_code == 0

            output_data = json.loads(Path(output_file.name).read_text())
            assert output_data["email"] == "****"
            assert output_data["name"] == "Test User"

            Path(output_file.name).unlink()

    def test_mask_stdin_stdout(self, runner, rules_file):
        """Enmascara desde stdin a stdout."""
        input_data = json.dumps({"password": "secret123", "user": "ana"})

        result = runner.invoke(
            cli,
            ["mask", "-r", rules_file, "-q"],
            input=input_data
        )

        assert result.exit_code == 0
        output = json.loads(result.output.strip())
        assert output["password"] == "****"
        assert output["user"] == "ana"

    def test_mask_with_report(self, runner, rules_file, json_file):
        """Genera reporte de enmascarado."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as report_file:
            result = runner.invoke(
                cli,
                ["mask", "-i", json_file, "-r", rules_file,
                 "--report", report_file.name, "-q"]
            )

            assert result.exit_code == 0

            report = json.loads(Path(report_file.name).read_text())
            assert "total_fields_masked" in report
            assert "objects" in report

            Path(report_file.name).unlink()

    def test_mask_rules_not_found(self, runner, json_file):
        """Error cuando archivo de reglas no existe."""
        result = runner.invoke(
            cli,
            ["mask", "-i", json_file, "-r", "/nonexistent/rules.yaml"]
        )

        assert result.exit_code != 0
        assert "Error" in result.output or result.exit_code == 2


class TestValidateCommand:
    """Tests para el comando validate."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_validate_valid_rules(self, runner):
        """Valida archivo de reglas válido."""
        content = """
rules:
  - path: "email"
    strategy: "redact"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(content)
            f.flush()

            result = runner.invoke(cli, ["validate", "-r", f.name])

            assert result.exit_code == 0
            assert "válido" in result.output or "1" in result.output

            Path(f.name).unlink()

    def test_validate_invalid_rules(self, runner):
        """Detecta reglas inválidas."""
        content = """
rules:
  - path: "email"
    strategy: "invalid_strategy"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(content)
            f.flush()

            result = runner.invoke(cli, ["validate", "-r", f.name])

            assert result.exit_code == 1
            assert "Error" in result.output

            Path(f.name).unlink()


class TestListStrategiesCommand:
    """Tests para el comando list-strategies."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_list_strategies(self, runner):
        """Lista todas las estrategias."""
        result = runner.invoke(cli, ["list-strategies"])

        assert result.exit_code == 0
        assert "redact" in result.output
        assert "hash" in result.output
        assert "partial" in result.output


class TestGenerateRulesCommand:
    """Tests para el comando generate-rules."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_generate_rules(self, runner):
        """Genera reglas de ejemplo."""
        result = runner.invoke(cli, ["generate-rules"])

        assert result.exit_code == 0
        assert "rules:" in result.output
        assert "path:" in result.output
        assert "strategy:" in result.output
