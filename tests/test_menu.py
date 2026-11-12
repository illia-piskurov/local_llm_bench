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


def _ollama_prompts(monkeypatch, texts, selects):
    """Feeds questionary.text / questionary.select answers; records the defaults each prompt offered."""
    text_queue, select_queue, offered = list(texts), list(selects), []

    def text(message, default="", **kwargs):
        offered.append(default)
        return _Answer(text_queue.pop(0))

    def select(message, choices=None, default=None, **kwargs):
        offered.append(default)
        return _Answer(select_queue.pop(0))

    monkeypatch.setattr(main.questionary, "text", text)
    monkeypatch.setattr(main.questionary, "select", select)
    return offered


@pytest.fixture
def ollama_server(monkeypatch):
    monkeypatch.setenv("LM_STUDIO_URL", "http://127.0.0.1:11434/v1")
    for var in ("OLLAMA_THINK", "OLLAMA_NUM_CTX", "OLLAMA_THINK_BUDGET"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(main, "_last_ollama_settings", None)


def test_lm_studio_run_asks_nothing_and_sets_nothing(monkeypatch):
    monkeypatch.setattr(main.questionary, "text", lambda *a, **kw: pytest.fail("LM Studio must not be asked"))
    cfg = main.prompt_generation_config()
    assert cfg.to_dict().keys() == {"seed", "timeout_seconds"}
    assert cfg.think is None


def test_ollama_run_asks_for_budgets_and_thinking(monkeypatch, ollama_server):
    offered = _ollama_prompts(monkeypatch, texts=["6000", "2048", "8192"], selects=["high"])
    cfg = main.prompt_generation_config()
    assert offered == [str(lmstudio.DEFAULT_MAX_TOKENS), "medium", "8192", str(lmstudio.OLLAMA_DEFAULT_NUM_CTX)]
    assert (cfg.max_tokens, cfg.think, cfg.think_budget, cfg.context_length) == (6000, "high", 2048, 8192)


def test_ollama_run_skips_the_thinking_budget_when_thinking_is_off(monkeypatch, ollama_server):
    _ollama_prompts(monkeypatch, texts=["4000", "16384"], selects=["off"])
    cfg = main.prompt_generation_config()
    assert cfg.think == "off"
    assert cfg.think_budget == lmstudio.OLLAMA_DEFAULT_THINK_BUDGET


def test_ollama_prompts_remember_the_previous_answers(monkeypatch, ollama_server):
    _ollama_prompts(monkeypatch, texts=["6000", "0", "8192"], selects=["low"])
    main.prompt_generation_config()
    offered = _ollama_prompts(monkeypatch, texts=["6000", "0", "8192"], selects=["low"])
    main.prompt_generation_config()
    assert offered == ["6000", "low", "0", "8192"]


def test_cancelled_ollama_prompt_cancels_the_run(monkeypatch, ollama_server):
    _ollama_prompts(monkeypatch, texts=["6000", None], selects=["on"])
    ran: list = []
    monkeypatch.setattr(main, "run_queue", lambda *a, **kw: ran.append(kw))
    main.start_run(Model("llm", "m"), [], None, force=False)
    assert ran == []


def test_start_run_passes_the_chosen_settings_to_run_queue(monkeypatch, ollama_server):
    _ollama_prompts(monkeypatch, texts=["5000", "1000", "8192"], selects=["low"])
    ran: list = []
    monkeypatch.setattr(main, "run_queue", lambda *a, **kw: ran.append(kw))
    main.start_run(Model("llm", "m"), [], None, force=True)
    assert ran[0]["gen_config"].max_tokens == 5000 and ran[0]["force"] is True
