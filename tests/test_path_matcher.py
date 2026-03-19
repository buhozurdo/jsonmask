"""Tests para el módulo path_matcher."""

import pytest

from jsonmask.path_matcher import (
    PathMatcher,
    build_path,
    get_value_at_path,
    iter_paths,
    set_value_at_path,
)


class TestPathMatcher:
    """Tests para PathMatcher."""

    def test_simple_path_match(self):
        """Match de path simple."""
        matcher = PathMatcher("user.email")

        assert matcher.matches("user.email") is True
        assert matcher.matches("user.name") is False
        assert matcher.matches("other.email") is False

    def test_wildcard_match(self):
        """Match con wildcard."""
        matcher = PathMatcher("users.*.email")

        assert matcher.matches("users.john.email") is True
        assert matcher.matches("users.jane.email") is True
        assert matcher.matches("users.john.name") is False

    def test_index_match(self):
        """Match con índice específico."""
        matcher = PathMatcher("items[0].id")

        assert matcher.matches("items[0].id") is True
        assert matcher.matches("items[1].id") is False

    def test_index_wildcard_match(self):
        """Match con wildcard de índice."""
        matcher = PathMatcher("items[*].id")

        assert matcher.matches("items[0].id") is True
        assert matcher.matches("items[1].id") is True
        assert matcher.matches("items[99].id") is True

    def test_complex_path_match(self):
        """Match de path complejo."""
        matcher = PathMatcher("data.users.*.cards[*].number")

        assert matcher.matches("data.users.john.cards[0].number") is True
        assert matcher.matches("data.users.jane.cards[5].number") is True
        assert matcher.matches("data.users.john.cards[0].cvv") is False

    def test_different_lengths_no_match(self):
        """Paths de diferente longitud no coinciden."""
        matcher = PathMatcher("user.email")

        assert matcher.matches("user") is False
        assert matcher.matches("user.email.domain") is False

    def test_repr(self):
        """Representación string."""
        matcher = PathMatcher("test.path")
        assert "PathMatcher" in repr(matcher)
        assert "test.path" in repr(matcher)


class TestBuildPath:
    """Tests para build_path."""

    def test_simple_keys(self):
        """Construye path de claves simples."""
        result = build_path(["user", "email"])
        assert result == "user.email"

    def test_with_index(self):
        """Construye path con índice."""
        result = build_path(["users", 0, "email"])
        assert result == "users[0].email"

    def test_multiple_indices(self):
        """Construye path con múltiples índices."""
        result = build_path(["matrix", 0, 1])
        assert result == "matrix[0][1]"

    def test_empty_list(self):
        """Lista vacía retorna string vacío."""
        result = build_path([])
        assert result == ""


class TestIterPaths:
    """Tests para iter_paths."""

    def test_simple_dict(self):
        """Itera paths de dict simple."""
        data = {"name": "Ana", "age": 30}
        paths = list(iter_paths(data))

        assert len(paths) == 2
        path_strings = [p[0] for p in paths]
        assert "name" in path_strings
        assert "age" in path_strings

    def test_nested_dict(self):
        """Itera paths de dict anidado."""
        data = {"user": {"name": "Ana", "email": "a@b.com"}}
        paths = list(iter_paths(data))

        assert len(paths) == 2
        path_strings = [p[0] for p in paths]
        assert "user.name" in path_strings
        assert "user.email" in path_strings

    def test_with_list(self):
        """Itera paths con listas."""
        data = {"items": [{"id": 1}, {"id": 2}]}
        paths = list(iter_paths(data))

        assert len(paths) == 2
        path_strings = [p[0] for p in paths]
        assert "items[0].id" in path_strings
        assert "items[1].id" in path_strings

    def test_values_included(self):
        """Los valores están incluidos en el resultado."""
        data = {"secret": "password123"}
        paths = list(iter_paths(data))

        assert paths[0][1] == "password123"


class TestSetValueAtPath:
    """Tests para set_value_at_path."""

    def test_set_simple(self):
        """Establece valor en path simple."""
        data = {"email": "old@example.com"}
        set_value_at_path(data, ["email"], "****")

        assert data["email"] == "****"

    def test_set_nested(self):
        """Establece valor en path anidado."""
        data = {"user": {"email": "old@example.com"}}
        set_value_at_path(data, ["user", "email"], "****")

        assert data["user"]["email"] == "****"

    def test_set_in_list(self):
        """Establece valor en lista."""
        data = {"items": [{"id": 1}, {"id": 2}]}
        set_value_at_path(data, ["items", 0, "id"], "****")

        assert data["items"][0]["id"] == "****"
        assert data["items"][1]["id"] == 2  # No afectado

    def test_set_empty_keys(self):
        """No hace nada con keys vacíos."""
        data = {"x": 1}
        set_value_at_path(data, [], "new")
        assert data == {"x": 1}


class TestGetValueAtPath:
    """Tests para get_value_at_path."""

    def test_get_simple(self):
        """Obtiene valor en path simple."""
        data = {"name": "Ana"}
        found, value = get_value_at_path(data, ["name"])

        assert found is True
        assert value == "Ana"

    def test_get_nested(self):
        """Obtiene valor en path anidado."""
        data = {"user": {"email": "a@b.com"}}
        found, value = get_value_at_path(data, ["user", "email"])

        assert found is True
        assert value == "a@b.com"

    def test_get_from_list(self):
        """Obtiene valor de lista."""
        data = {"items": [{"id": "first"}, {"id": "second"}]}
        found, value = get_value_at_path(data, ["items", 1, "id"])

        assert found is True
        assert value == "second"

    def test_get_not_found(self):
        """Retorna False si no existe."""
        data = {"x": 1}
        found, value = get_value_at_path(data, ["y"])

        assert found is False
        assert value is None

    def test_get_index_out_of_range(self):
        """Retorna False si índice fuera de rango."""
        data = {"items": [1, 2, 3]}
        found, value = get_value_at_path(data, ["items", 99])

        assert found is False
