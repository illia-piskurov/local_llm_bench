import re
from pathlib import Path

import pytest
from questionary import Choice

import lmstudio
import main
from lmstudio import Model


class _Answer:
    def __init__(self, value):
        self._value = value

    def ask(self):
        return self._value


def _answers(monkeypatch, *values):
    """Makes successive questionary.select(...).ask() calls return the given values."""
    queue = list(values)
    monkeypatch.setattr(main.questionary, "select", lambda *a, **kw: _Answer(queue.pop(0)))


def test_choice_with_none_value_would_return_its_title():
    # The root cause of the menu crashes: questionary replaces value=None with the title.
    assert Choice("🔙 Back", value=None).value == "🔙 Back"
    assert Choice("🔙 Back", value=main.BACK).value == main.BACK


def test_no_menu_choice_relies_on_a_none_value():
    source = (Path(main.__file__)).read_text(encoding="utf-8")
    assert not re.search(r"Choice\([^)]*value=None", source)


@pytest.mark.parametrize("raw", [main.BACK, None])
def test_select_choice_maps_back_and_cancel_to_none(monkeypatch, raw):
    _answers(monkeypatch, raw)
    assert main.select_choice("?", [Choice("x", value="x")]) is None


def test_select_choice_passes_values_through(monkeypatch):
    model = Model(type="llm", key="m")
    _answers(monkeypatch, model, "other", ("bench", "level1"))
    assert main.select_choice("?", []) is model
    assert main.select_choice("?", []) == "other"
    assert main.select_choice("?", []) == ("bench", "level1")


def test_model_picker_back_returns_none_instead_of_a_string(monkeypatch):
    monkeypatch.setattr(lmstudio, "is_server_online", lambda: True)
    monkeypatch.setattr(lmstudio, "get_loaded_models", lambda: [Model("llm", "a"), Model("llm", "b")])
    _answers(monkeypatch, main.BACK)
    assert main.detect_or_select_model() is None

    monkeypatch.setattr(lmstudio, "get_loaded_models", lambda: [])
    monkeypatch.setattr(lmstudio, "list_llm_models", lambda: [Model("llm", "a")])
    _answers(monkeypatch, main.BACK)
    assert main.detect_or_select_model() is None


def test_server_url_back_does_not_overwrite_the_saved_address(monkeypatch):
    saved: list[str] = []
    monkeypatch.setattr(lmstudio, "set_base_url", lambda url: saved.append(url) or url)
    monkeypatch.setattr(lmstudio, "get_base_url", lambda: "http://127.0.0.1:1234")
    _answers(monkeypatch, main.BACK)
    assert main.configure_server_url() == "http://127.0.0.1:1234"
    assert saved == []
