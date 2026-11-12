import json

import pytest
import requests

import lmstudio
from lmstudio import GenerationConfig


class _Stream:
    """Stands in for a streaming requests.Response."""

    def __init__(self, chunks, error=None, status=200, text=""):
        self._lines = [json.dumps(c).encode() for c in chunks]
        self._error = error
        self.status_code = status
        self.text = text

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        pass

    def iter_lines(self):
        yield from self._lines
        if self._error:
            raise self._error


def _done(**extra):
    return {
        "message": {"role": "assistant", "content": ""},
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 10,
        "eval_count": 50,
        "eval_duration": 2_000_000_000,
        "prompt_eval_duration": 500_000_000,
        "load_duration": 1_000_000_000,
        **extra,
    }


@pytest.fixture
def ollama(monkeypatch):
    monkeypatch.setenv("LM_STUDIO_URL", "http://127.0.0.1:11434/v1")
    for var in ("OLLAMA_THINK", "OLLAMA_NUM_CTX", "OLLAMA_THINK_BUDGET"):
        monkeypatch.delenv(var, raising=False)
    calls: list[dict] = []

    def install(chunks, error=None, responses=None):
        """`responses` is an optional per-call list of ready _Stream objects, used instead of `chunks`."""
        queue = list(responses or [])

        def post(url, **kwargs):
            calls.append({"url": url, **kwargs, "json": json.loads(json.dumps(kwargs["json"]))})
            return queue.pop(0) if queue else _Stream(chunks, error)

        monkeypatch.setattr(requests, "post", post)
        return calls

    return install


def _chunks(content="print(1)", thinking="", **done):
    out = []
    if thinking:
        out.append({"message": {"role": "assistant", "content": "", "thinking": thinking}, "done": False})
    out.append({"message": {"role": "assistant", "content": content}, "done": False})
    out.append(_done(**done))
    return out


def test_streams_native_chat_and_maps_stats(ollama):
    calls = ollama(_chunks(thinking="hmm"))
    assert lmstudio.is_ollama()

    res = lmstudio.ask_model("qwen3:8b", [{"role": "user", "content": "solve"}])
    assert calls[0]["url"] == "http://127.0.0.1:11434/api/chat"
    assert calls[0]["json"]["stream"] is True
    assert calls[0]["json"]["messages"] == [{"role": "user", "content": "solve"}]
    assert calls[0]["json"]["think"] == "medium"  # the default thinking effort
    assert res.content == "print(1)"
    assert res.reasoning == "hmm"
    assert res.stats["tokens_per_second"] == 25.0
    assert res.stats["time_to_first_token_seconds"] == 0.5
    assert res.stats["input_tokens"] == 10
    assert res.truncated_reason is None


def test_reasoning_tokens_are_a_share_of_the_real_output_count(ollama):
    # 90 thinking chars vs 10 answer chars of 50 generated tokens -> 45 reasoning tokens, never more than the total
    ollama(_chunks(content="x" * 10, thinking="t" * 90))
    res = lmstudio.ask_model("m", [{"role": "user", "content": "q"}])
    assert res.stats["reasoning_output_tokens"] == 45
    assert res.stats["reasoning_output_tokens"] <= res.stats["total_output_tokens"]


def test_context_window_fits_prompt_and_answer(ollama):
    calls = ollama(_chunks())
    lmstudio.ask_model("m", [{"role": "user", "content": "x" * 24000}])  # ~8000 prompt tokens
    opts = calls[0]["json"]["options"]
    assert opts["num_ctx"] == lmstudio.OLLAMA_DEFAULT_NUM_CTX
    # the answer budget never reaches the window, otherwise Ollama would shift out the start of the prompt
    assert opts["num_predict"] <= opts["num_ctx"] - 8000
    assert opts["num_predict"] < lmstudio.DEFAULT_MAX_TOKENS


def test_large_max_tokens_grows_the_window(ollama):
    calls = ollama(_chunks())
    cfg = GenerationConfig(max_tokens=lmstudio.DEFAULT_MAX_TOKENS * 2)
    lmstudio.ask_model("m", [{"role": "user", "content": "q"}], config=cfg)
    opts = calls[0]["json"]["options"]
    assert opts["num_predict"] == cfg.max_tokens
    assert opts["num_ctx"] > cfg.max_tokens


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        (None, "medium"),
        ("", "medium"),
        ("off", False),
        ("false", False),
        ("on", True),
        ("high", "high"),
        ("auto", None),
    ],
)
def test_think_mode_from_environment(ollama, monkeypatch, env, expected):
    if env is not None:
        monkeypatch.setenv("OLLAMA_THINK", env)
    calls = ollama(_chunks())
    lmstudio.ask_model("m", [{"role": "user", "content": "q"}])
    if expected is None:
        assert "think" not in calls[0]["json"]
    else:
        assert calls[0]["json"]["think"] == expected


def _thinking_stream(tokens):
    chunks = [{"message": {"role": "assistant", "content": "", "thinking": "t"}, "done": False}] * tokens
    return _Stream([*chunks, *_chunks(content="late answer")])


def test_thinking_over_budget_is_dropped_and_asked_again_without_thinking(ollama, monkeypatch):
    monkeypatch.setenv("OLLAMA_THINK_BUDGET", "5")
    calls = ollama(None, responses=[_thinking_stream(50), _Stream(_chunks(content="direct answer"))])

    res = lmstudio.ask_model("m", [{"role": "user", "content": "q"}])
    assert len(calls) == 2
    assert calls[0]["json"]["think"] == "medium"
    assert calls[1]["json"]["think"] is False
    assert res.content == "direct answer"
    assert res.reasoning is None
    assert res.raw["think_budget"] == {"limit": 5, "discarded_thinking_tokens": 6}


def test_thinking_within_budget_is_kept(ollama, monkeypatch):
    monkeypatch.setenv("OLLAMA_THINK_BUDGET", "5")
    calls = ollama(None, responses=[_thinking_stream(3)])
    res = lmstudio.ask_model("m", [{"role": "user", "content": "q"}])
    assert len(calls) == 1
    assert res.reasoning == "ttt"
    assert "think_budget" not in res.raw


def test_zero_budget_means_unlimited(ollama, monkeypatch):
    monkeypatch.setenv("OLLAMA_THINK_BUDGET", "0")
    calls = ollama(None, responses=[_thinking_stream(500)])
    res = lmstudio.ask_model("m", [{"role": "user", "content": "q"}])
    assert len(calls) == 1
    assert len(res.reasoning) == 500


def test_rejected_think_value_falls_back_to_the_model_default(ollama):
    rejected = _Stream([], status=400, text='{"error":"think value \\"low\\" is not supported for this model"}')
    calls = ollama(None, responses=[rejected, _Stream(_chunks())])
    res = lmstudio.ask_model("m", [{"role": "user", "content": "q"}])
    assert "think" in calls[0]["json"]
    assert "think" not in calls[1]["json"]
    assert res.content == "print(1)"


def test_budget_overflow_on_a_model_that_cannot_skip_thinking_lets_it_finish(ollama, monkeypatch):
    monkeypatch.setenv("OLLAMA_THINK_BUDGET", "2")
    rejected = _Stream([], status=400, text='{"error":"model does not support think=false"}')
    calls = ollama(None, responses=[_thinking_stream(10), rejected, _thinking_stream(10)])
    res = lmstudio.ask_model("m", [{"role": "user", "content": "q"}])
    assert len(calls) == 3
    assert "think" not in calls[2]["json"]
    assert res.content == "late answer"
    assert len(res.reasoning) == 10


def test_backend_generation_params_are_recorded_only_for_ollama(ollama, monkeypatch):
    assert lmstudio.backend_generation_params() == {"think": "medium", "think_budget": 8192}
    monkeypatch.setenv("OLLAMA_THINK", "auto")
    monkeypatch.setenv("OLLAMA_THINK_BUDGET", "0")
    assert lmstudio.backend_generation_params() == {"think": "auto", "think_budget": 0}
    monkeypatch.setenv("LM_STUDIO_URL", "http://127.0.0.1:1234")
    assert lmstudio.backend_generation_params() == {}


def test_stalled_stream_is_a_timeout_not_a_generic_failure(ollama):
    ollama(_chunks()[:1], error=requests.exceptions.ConnectionError("Read timed out."))
    with pytest.raises(TimeoutError):
        lmstudio.ask_model("m", [{"role": "user", "content": "q"}])


def test_stream_without_final_chunk_is_an_error(ollama):
    ollama(_chunks()[:-1])
    with pytest.raises(RuntimeError, match="final chunk"):
        lmstudio.ask_model("m", [{"role": "user", "content": "q"}])


def test_run_settings_override_the_environment(ollama, monkeypatch):
    monkeypatch.setenv("OLLAMA_THINK", "high")
    monkeypatch.setenv("OLLAMA_THINK_BUDGET", "5")
    calls = ollama(_chunks())
    cfg = GenerationConfig(think="low", think_budget=0, context_length=8192)
    lmstudio.ask_model("m", [{"role": "user", "content": "q"}], config=cfg)
    assert calls[0]["json"]["think"] == "low"
    assert calls[0]["json"]["options"]["num_ctx"] == 8192
    assert lmstudio.backend_generation_params(cfg) == {"think": "low", "think_budget": 0}
    assert lmstudio.backend_generation_params() == {"think": "high", "think_budget": 5}


def test_run_can_turn_thinking_off(ollama):
    calls = ollama(_chunks())
    lmstudio.ask_model("m", [{"role": "user", "content": "q"}], config=GenerationConfig(think="off"))
    assert calls[0]["json"]["think"] is False


def test_sampling_is_left_to_the_model_unless_set(ollama):
    calls = ollama(_chunks())
    lmstudio.ask_model("m", [{"role": "user", "content": "q"}])
    options = calls[0]["json"]["options"]
    assert "temperature" not in options and "top_p" not in options
    assert {"seed", "num_predict", "num_ctx"} <= options.keys()

    calls = ollama(_chunks())
    lmstudio.ask_model("m", [{"role": "user", "content": "q"}], config=GenerationConfig(temperature=0.6, top_p=0.9))
    assert calls[-1]["json"]["options"]["temperature"] == 0.6
    assert calls[-1]["json"]["options"]["top_p"] == 0.9
