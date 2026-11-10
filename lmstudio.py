import json
import os
import re
import threading
from dataclasses import dataclass, replace
from pathlib import Path

import requests

UNLOAD_TIMEOUT_SECONDS = 30
OLLAMA_DEFAULT_NUM_CTX = 16384
OLLAMA_CTX_MARGIN = 256
OLLAMA_DEFAULT_THINK = "medium"
OLLAMA_DEFAULT_THINK_BUDGET = 8192
LOCAL_SERVER_FILE = Path(__file__).parent / ".local_server"


def get_base_url() -> str:
    """Returns the current inference server URL (LM Studio / Ollama / Remote)."""
    if "LM_STUDIO_URL" in os.environ and os.environ["LM_STUDIO_URL"].strip():
        return os.environ["LM_STUDIO_URL"].strip().rstrip("/")
    if "OPENAI_BASE_URL" in os.environ and os.environ["OPENAI_BASE_URL"].strip():
        return os.environ["OPENAI_BASE_URL"].strip().rstrip("/")
    if LOCAL_SERVER_FILE.exists():
        try:
            val = LOCAL_SERVER_FILE.read_text(encoding="utf-8").strip()
            if val:
                return val.rstrip("/")
        except Exception:
            pass
    return "http://127.0.0.1:1234"


def set_base_url(url: str) -> str:
    """Saves the local inference server URL to .local_server."""
    cleaned = url.strip().rstrip("/")
    if not cleaned.startswith("http://") and not cleaned.startswith("https://"):
        cleaned = f"http://{cleaned}"
    LOCAL_SERVER_FILE.write_text(cleaned, encoding="utf-8")
    return cleaned


def _ollama_root() -> str:
    """Returns the server root without a trailing /v1 or /api segment."""
    return re.sub(r"/(?:v1|api)/?$", "", get_base_url())


def is_ollama() -> bool:
    """True when the configured server is Ollama (default port 11434 or 'ollama' in the host name)."""
    root = _ollama_root().lower()
    return ":11434" in root or "ollama" in root


@dataclass
class Model:
    type: str
    key: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(type=str(data.get("type") or "llm"), key=str(data.get("key") or ""))


@dataclass
class ModelResponse:
    content: str
    stats: dict | None
    raw: dict
    reasoning: str | None = None
    truncated_reason: str | None = None

    @property
    def truncated(self) -> bool:
        return self.truncated_reason is not None


# Reasoning models spend a large share of the budget on thoughts, so the defaults are generous.
# They only apply to Ollama, which has no sampling presets: LM Studio gets no sampling or length parameters
# unless they are set explicitly, so the model's own LM Studio preset (temperature, max tokens, context) governs.
DEFAULT_MAX_TOKENS = 16384
DEFAULT_TEMPERATURE = 0.0
DEFAULT_TOP_P = 1.0
DEFAULT_TIMEOUT_SECONDS = 600.0


@dataclass
class GenerationConfig:
    temperature: float | None = None
    seed: int = 42
    top_p: float | None = None
    max_tokens: int | None = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    context_length: int | None = None
    repeat_penalty: float | None = None

    def to_dict(self) -> dict:
        d: dict = {"seed": self.seed, "timeout_seconds": self.timeout_seconds}
        if self.temperature is not None:
            d["temperature"] = self.temperature
        if self.top_p is not None:
            d["top_p"] = self.top_p
        if self.max_tokens is not None:
            d["max_tokens"] = self.max_tokens
        if self.context_length is not None:
            d["context_length"] = self.context_length
        if self.repeat_penalty is not None:
            d["repeat_penalty"] = self.repeat_penalty
        return d

    @classmethod
    def from_dict(cls, data: dict | None) -> "GenerationConfig":
        if not data:
            return cls()
        return cls(
            temperature=float(data["temperature"]) if data.get("temperature") is not None else None,
            seed=int(data.get("seed", 42)),
            top_p=float(data["top_p"]) if data.get("top_p") is not None else None,
            max_tokens=int(data["max_tokens"]) if data.get("max_tokens") is not None else None,
            timeout_seconds=float(data.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)),
            context_length=data.get("context_length"),
            repeat_penalty=data.get("repeat_penalty"),
        )


def resolve_for_backend(cfg: GenerationConfig) -> GenerationConfig:
    """Fills the defaults a backend cannot do without; LM Studio keeps every unset parameter unset."""
    if not is_ollama():
        return cfg
    return replace(
        cfg,
        temperature=DEFAULT_TEMPERATURE if cfg.temperature is None else cfg.temperature,
        top_p=DEFAULT_TOP_P if cfg.top_p is None else cfg.top_p,
        max_tokens=DEFAULT_MAX_TOKENS if cfg.max_tokens is None else cfg.max_tokens,
    )


@dataclass
class ModelArtifactInfo:
    key: str
    display_name: str | None = None
    architecture: str | None = None
    quantization: str | None = None
    quantization_bits: int | None = None
    size_bytes: int | None = None
    params_string: str | None = None
    max_context_length: int | None = None
    format: str | None = None
    publisher: str | None = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "architecture": self.architecture,
            "quantization": self.quantization,
            "quantization_bits": self.quantization_bits,
            "size_bytes": self.size_bytes,
            "params_string": self.params_string,
            "max_context_length": self.max_context_length,
            "format": self.format,
            "publisher": self.publisher,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "ModelArtifactInfo":
        if not data:
            return cls(key="unknown")
        return cls(
            key=data.get("key", "unknown"),
            display_name=data.get("display_name"),
            architecture=data.get("architecture"),
            quantization=data.get("quantization"),
            quantization_bits=data.get("quantization_bits"),
            size_bytes=data.get("size_bytes"),
            params_string=data.get("params_string"),
            max_context_length=data.get("max_context_length"),
            format=data.get("format"),
            publisher=data.get("publisher"),
        )


def _ollama_artifact_info(model_key: str) -> ModelArtifactInfo:
    root = _ollama_root()
    info = ModelArtifactInfo(key=model_key)
    try:
        resp = requests.post(f"{root}/api/show", json={"model": model_key}, timeout=5)
        if resp.status_code != 200:
            return info
        data = resp.json()
        details = data.get("details") or {}
        arch = details.get("family")
        max_ctx = None
        for k, v in (data.get("model_info") or {}).items():
            if k.endswith(".context_length") and isinstance(v, int):
                max_ctx = v
                break
        tags = requests.get(f"{root}/api/tags", timeout=5).json().get("models", [])
        size = next((m.get("size") for m in tags if model_key in (m.get("name"), m.get("model"))), None)
        return ModelArtifactInfo(
            key=model_key,
            display_name=model_key,
            architecture=arch,
            quantization=details.get("quantization_level"),
            size_bytes=size,
            params_string=details.get("parameter_size"),
            max_context_length=max_ctx,
            format=details.get("format"),
        )
    except Exception:
        return info


def get_model_artifact_info(model_key: str) -> ModelArtifactInfo:
    if is_ollama():
        return _ollama_artifact_info(model_key)
    try:
        resp = requests.get(f"{get_base_url()}/api/v1/models", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            for m in models:
                if m.get("key") == model_key or model_key in m.get("variants", []):
                    q = m.get("quantization")
                    q_name = q.get("name") if isinstance(q, dict) else (q or None)
                    q_bits = q.get("bits_per_weight") if isinstance(q, dict) else None
                    return ModelArtifactInfo(
                        key=m.get("key", model_key),
                        display_name=m.get("display_name"),
                        architecture=m.get("architecture"),
                        quantization=q_name,
                        quantization_bits=q_bits,
                        size_bytes=m.get("size_bytes"),
                        params_string=m.get("params_string"),
                        max_context_length=m.get("max_context_length"),
                        format=m.get("format"),
                        publisher=m.get("publisher"),
                    )
    except Exception:
        pass
    return ModelArtifactInfo(key=model_key)


def _render_transcript(messages: list[dict]) -> tuple[str | None, str]:
    if not messages:
        return None, ""

    if len(messages) == 1 and messages[0].get("role") == "user":
        return None, messages[0].get("content", "")

    system_prompt = None
    chunks: list[str] = []
    last_role = None

    for message in messages:
        role = (message.get("role") or "user").lower()
        content = message.get("content", "")

        if role == "system":
            system_prompt = content
            continue

        label = "User" if role == "user" else "Assistant" if role == "assistant" else role.capitalize()
        chunks.append(f"### {label}:\n{content.strip()}")
        last_role = role

    # Append terminal assistant cue so the model recognizes its turn to respond as Assistant
    if last_role != "assistant":
        chunks.append("### Assistant:\n")

    return system_prompt, "\n\n".join(chunks)


def list_llm_models() -> list[Model]:
    if is_ollama():
        try:
            resp = requests.get(f"{_ollama_root()}/api/tags", timeout=10).json()
            return [Model(type="llm", key=str(m.get("name") or "")) for m in resp.get("models", []) if m.get("name")]
        except Exception:
            return []
    try:
        resp = requests.get(f"{get_base_url()}/api/v1/models", timeout=10).json()
        models = resp.get("models", []) if isinstance(resp, dict) else []
        return [Model.from_dict(m) for m in models if isinstance(m, dict) and m.get("type") == "llm"]
    except Exception:
        return []


_FENCE_LINE_RE = re.compile(r"^[ \t]*```", re.MULTILINE)
_OPEN_THINK_RE = re.compile(r"<(think|thought|reasoning|reflection)>", re.IGNORECASE)
_CLOSE_THINK_RE = re.compile(r"</(think|thought|reasoning|reflection)>", re.IGNORECASE)


def detect_truncation(
    payload: dict, raw_content: str, max_tokens: int | None, has_reasoning: bool = False
) -> str | None:
    """Returns a human-readable reason if the generation was cut off, otherwise None.

    LM Studio's native API does not always report a finish reason, so several signals are combined:
    an explicit server-side status, the output token count reaching the budget, a reply made of reasoning only
    (the context window or token limit ran out before the final answer), and structural damage in the text
    (unclosed reasoning tag or unclosed code fence).
    """
    finish = payload.get("finish_reason") or payload.get("stop_reason")
    if isinstance(finish, str) and finish.lower() in {"length", "max_tokens", "max_output_tokens"}:
        return f"server reported finish_reason={finish}"
    if payload.get("status") == "incomplete":
        return "server reported status=incomplete"

    stats = payload.get("stats") or {}
    total = stats.get("total_output_tokens")
    if isinstance(total, int) and max_tokens and total >= max_tokens:
        return f"output reached the token limit ({total}/{max_tokens})"

    if has_reasoning and not raw_content.strip():
        return (
            f"no final answer: the output is reasoning only ({total} tokens), the context window or token limit ran out"
        )

    if len(_OPEN_THINK_RE.findall(raw_content)) > len(_CLOSE_THINK_RE.findall(raw_content)):
        return "unclosed reasoning tag in the response"
    if len(_FENCE_LINE_RE.findall(raw_content)) % 2 == 1:
        return "unclosed code fence in the response"
    return None


def _ollama_think() -> bool | str | None:
    """Thinking mode from OLLAMA_THINK: low | medium (default) | high | on | off | auto (the model's own default)."""
    raw = (os.environ.get("OLLAMA_THINK") or OLLAMA_DEFAULT_THINK).strip().lower()
    if raw in ("off", "false", "0", "no"):
        return False
    if raw in ("on", "true", "1", "yes"):
        return True
    if raw in ("low", "medium", "high"):
        return raw
    return None


def _ollama_think_budget() -> int:
    """Max thinking tokens per answer from OLLAMA_THINK_BUDGET (0 disables the limit)."""
    raw = os.environ.get("OLLAMA_THINK_BUDGET")
    return max(0, int(raw)) if raw and raw.strip().isdigit() else OLLAMA_DEFAULT_THINK_BUDGET


def backend_generation_params() -> dict:
    """Backend settings that change the results, so they are recorded together with the run's parameters."""
    if not is_ollama():
        return {}
    think = _ollama_think()
    return {"think": "auto" if think is None else think, "think_budget": _ollama_think_budget()}


def _ollama_context_plan(messages: list[dict], cfg: GenerationConfig) -> tuple[int, int]:
    """Returns (num_ctx, num_predict) so the prompt and the answer always fit the window.

    Without an explicit num_ctx Ollama uses the model's baked-in default (up to 256k), which allocates a huge
    KV cache, so a bounded default is used. When the output hits the window Ollama shifts the context and drops
    the start of the prompt, hence num_predict is clamped to the room left. A truncation retry asks for a larger
    max_tokens, so the window grows with it instead of repeating the same cut-off.
    """
    prompt_tokens = sum(len(m.get("content") or "") for m in messages) // 3 + 1
    ctx = cfg.context_length or int(os.environ.get("OLLAMA_NUM_CTX") or OLLAMA_DEFAULT_NUM_CTX)
    if cfg.max_tokens > DEFAULT_MAX_TOKENS:
        ctx = max(ctx, prompt_tokens + cfg.max_tokens + OLLAMA_CTX_MARGIN)
    return ctx, max(1, min(cfg.max_tokens, ctx - prompt_tokens - OLLAMA_CTX_MARGIN))


class _ThinkRejected(Exception):
    """The server does not accept the requested `think` value for this model (older Ollama or a non-thinking model)."""


def _stream_chat(body: dict, idle_timeout: float, think_budget: int) -> tuple[dict, str, str, int | None]:
    """Streams /api/chat; returns (final chunk, content, thinking, thinking tokens when the budget was exceeded).

    The reply is streamed so the timeout means "no tokens for N seconds" rather than a wall-clock limit on the
    whole answer, which would fail slow reasoning models that are still producing output. Every streamed chunk is
    about one token, so counting thinking chunks enforces the thinking budget; on overflow the stream is dropped
    and the final chunk is empty.
    """
    content_parts: list[str] = []
    thinking_parts: list[str] = []
    final: dict = {}
    try:
        with requests.post(
            f"{_ollama_root()}/api/chat", json=body, stream=True, timeout=(10.0, idle_timeout)
        ) as response:
            if response.status_code == 400 and "think" in response.text.lower():
                raise _ThinkRejected(response.text)
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                if chunk.get("error"):
                    raise RuntimeError(f"Ollama error: {chunk['error']}")
                msg = chunk.get("message") or {}
                content_parts.append(msg.get("content") or "")
                if msg.get("thinking"):
                    thinking_parts.append(msg["thinking"])
                    if think_budget and len(thinking_parts) > think_budget:
                        return {}, "".join(content_parts), "".join(thinking_parts), len(thinking_parts)
                if chunk.get("done"):
                    final = chunk
    except requests.exceptions.RequestException as e:
        # A stalled stream surfaces as a ConnectionError wrapping the read timeout, not as a Timeout.
        if isinstance(e, requests.exceptions.Timeout) or "timed out" in str(e).lower():
            raise TimeoutError(f"No output from the model for {idle_timeout}s: {e}") from e
        raise RuntimeError(f"Inference request failed: {e}") from e

    if not final:
        raise RuntimeError("Ollama stream ended before the final chunk")
    return final, "".join(content_parts), "".join(thinking_parts), None


def _ask_ollama(model_key: str, messages: list[dict], cfg: GenerationConfig) -> ModelResponse:
    """Runs a chat completion through Ollama's native /api/chat and maps its stats to the LM Studio shape."""
    cfg = resolve_for_backend(cfg)
    num_ctx, num_predict = _ollama_context_plan(messages, cfg)
    options: dict = {
        "temperature": cfg.temperature,
        "seed": cfg.seed,
        "top_p": cfg.top_p,
        "num_predict": num_predict,
        "num_ctx": num_ctx,
    }
    if cfg.repeat_penalty is not None:
        options["repeat_penalty"] = cfg.repeat_penalty

    body: dict = {"model": model_key, "messages": messages, "stream": True, "options": options}
    think = _ollama_think()
    if think is not None:
        body["think"] = think
    budget = _ollama_think_budget()

    def stream(limit: int):
        try:
            return _stream_chat(body, cfg.timeout_seconds, limit)
        except _ThinkRejected:
            # Older Ollama or a model without the requested thinking mode: fall back to the model's default.
            body.pop("think", None)
            return _stream_chat(body, cfg.timeout_seconds, limit)

    final, raw_content, reasoning_text, exceeded = stream(budget)
    discarded = None
    if exceeded is not None:
        # Thinking ran past the budget: drop that attempt and ask again without thinking (or, when the model
        # cannot skip it, let it finish unrestricted).
        discarded = exceeded
        body["think"] = False
        final, raw_content, reasoning_text, _ = stream(0)
    reasoning_text = reasoning_text or None
    data = {**final, "message": {"role": "assistant", "content": raw_content, "thinking": reasoning_text or ""}}

    eval_count = final.get("eval_count") or 0
    eval_ns = final.get("eval_duration") or 0
    stats: dict = {
        "input_tokens": final.get("prompt_eval_count"),
        "total_output_tokens": eval_count,
        "tokens_per_second": eval_count / (eval_ns / 1e9) if eval_count and eval_ns else None,
        "time_to_first_token_seconds": (final.get("prompt_eval_duration") or 0) / 1e9,
        "model_load_time_seconds": (final.get("load_duration") or 0) / 1e9,
    }
    payload = {**data, "finish_reason": final.get("done_reason"), "stats": stats}
    if discarded is not None:
        payload["think_budget"] = {"limit": budget, "discarded_thinking_tokens": discarded}

    from benchmarks.base import strip_reasoning_blocks

    cleaned_content, inline_reasoning = strip_reasoning_blocks(raw_content)
    if inline_reasoning:
        reasoning_text = f"{reasoning_text}\n\n{inline_reasoning}" if reasoning_text else inline_reasoning
        content = cleaned_content
    else:
        content = raw_content

    # Ollama does not report reasoning tokens separately: split the real output count by the text share.
    if reasoning_text:
        think_chars = len(reasoning_text)
        share = think_chars / (think_chars + len(content)) if think_chars + len(content) else 1.0
        estimate = eval_count * share if eval_count else think_chars / 3.8
        stats["reasoning_output_tokens"] = max(1, round(estimate))

    return ModelResponse(
        content=content,
        stats=stats,
        raw=payload,
        reasoning=reasoning_text,
        truncated_reason=detect_truncation(payload, raw_content, cfg.max_tokens, bool(reasoning_text)),
    )


def ask_model(
    model_key: str,
    messages: list[dict],
    temperature: float | None = None,
    config: GenerationConfig | None = None,
) -> ModelResponse:
    # Work on a copy so the caller's shared config is never mutated.
    cfg = replace(config) if config is not None else GenerationConfig()
    if temperature is not None:
        cfg = replace(cfg, temperature=temperature)

    if is_ollama():
        return _ask_ollama(model_key, messages, cfg)

    system_prompt, input_text = _render_transcript(messages)

    payload = {
        "model": model_key,
        "input": input_text,
        "store": False,
    }
    if cfg.temperature is not None:
        payload["temperature"] = cfg.temperature
    if cfg.top_p is not None:
        payload["top_p"] = cfg.top_p
    if cfg.max_tokens is not None:
        payload["max_output_tokens"] = cfg.max_tokens
    if cfg.context_length:
        payload["context_length"] = cfg.context_length
    if cfg.repeat_penalty is not None:
        payload["repeat_penalty"] = cfg.repeat_penalty
    if system_prompt:
        payload["system_prompt"] = system_prompt

    timeout = (10.0, cfg.timeout_seconds)
    try:
        response = requests.post(
            f"{get_base_url()}/api/v1/chat",
            json=payload,
            timeout=timeout,
        )
    except requests.exceptions.Timeout as e:
        raise TimeoutError(f"Inference request timed out after {cfg.timeout_seconds}s: {e}") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Inference request failed: {e}") from e

    response.raise_for_status()
    payload = response.json()
    output = payload.get("output", [])

    # 1. Extract message and reasoning blocks from LM Studio API
    message_parts = [item.get("content", "") for item in output if item.get("type") == "message"]
    reasoning_parts = [item.get("content", "") for item in output if item.get("type") == "reasoning"]

    raw_content = "\n".join(message_parts)
    reasoning_text = "\n\n".join(reasoning_parts) if reasoning_parts else None

    # 2. If message_content contained inline <think>...</think> tags
    from benchmarks.base import strip_reasoning_blocks

    cleaned_content, inline_reasoning = strip_reasoning_blocks(raw_content)

    if inline_reasoning:
        if reasoning_text:
            reasoning_text = reasoning_text + "\n\n" + inline_reasoning
        else:
            reasoning_text = inline_reasoning
        content = cleaned_content
    else:
        content = raw_content

    # 3. If content is empty (e.g. model output only reasoning), do not fall back to reasoning
    # This prevents extracting draft code from thought chains (draft shielding)
    stats = payload.get("stats") or {}
    # If reasoning_output_tokens not reported by API but thoughts occurred, estimate tokens (~3.8 chars/tok)
    if reasoning_text and not stats.get("reasoning_output_tokens"):
        stats["reasoning_output_tokens"] = max(1, round(len(reasoning_text) / 3.8))

    return ModelResponse(
        content=content,
        stats=stats,
        raw=payload,
        reasoning=reasoning_text,
        truncated_reason=detect_truncation(payload, raw_content, cfg.max_tokens, bool(reasoning_text)),
    )


def loaded_instance_ids(model_key: str) -> list[str]:
    try:
        resp = requests.get(f"{get_base_url()}/api/v1/models", timeout=30).json()
        models = resp.get("models", []) if isinstance(resp, dict) else []
        for m in models:
            if isinstance(m, dict) and m.get("key") == model_key:
                return [
                    instance["id"]
                    for instance in m.get("loaded_instances", [])
                    if isinstance(instance, dict) and "id" in instance
                ]
    except Exception:
        pass
    return []


def unload_model(model_key: str, console=None, timeout: int = UNLOAD_TIMEOUT_SECONDS) -> None:
    if is_ollama():
        try:
            requests.post(f"{_ollama_root()}/api/generate", json={"model": model_key, "keep_alive": 0}, timeout=timeout)
        except Exception as e:
            msg = f"failed to unload {model_key}: {e}"
            if console is not None:
                console.print(f"  [yellow]warn:[/yellow] {msg}")
            else:
                print(f"  warn: {msg}")
        return

    def warn(message: str) -> None:
        if console is not None:
            console.print(f"  [yellow]warn:[/yellow] {message}")
        else:
            print(f"  warn: {message}")

    def _do_unload() -> None:
        try:
            instance_ids = loaded_instance_ids(model_key)
        except Exception as e:
            warn(f"failed to retrieve loaded_instances: {e}")
            return

        if not instance_ids:
            return

        for instance_id in instance_ids:
            try:
                requests.post(
                    f"{get_base_url()}/api/v1/models/unload",
                    json={"instance_id": instance_id},
                    timeout=timeout,
                )
            except Exception as e:
                warn(f"failed to unload instance {instance_id}: {e}")

    thread = threading.Thread(target=_do_unload, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    if thread.is_alive():
        warn(f"model unload timed out (>{timeout}s) - continuing without waiting")


def is_server_online() -> bool:
    if is_ollama():
        try:
            return requests.get(f"{_ollama_root()}/api/version", timeout=2).status_code == 200
        except Exception:
            return False
    try:
        r = requests.get(f"{get_base_url()}/api/v1/models", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def get_loaded_models() -> list[Model]:
    if is_ollama():
        try:
            resp = requests.get(f"{_ollama_root()}/api/ps", timeout=5).json()
            return [Model(type="llm", key=str(m.get("name") or "")) for m in resp.get("models", []) if m.get("name")]
        except Exception:
            return []
    try:
        resp = requests.get(f"{get_base_url()}/api/v1/models", timeout=5).json()
        models = resp.get("models", [])
        loaded = []
        for m in models:
            if m.get("type") == "llm" and m.get("loaded_instances"):
                loaded.append(Model.from_dict(m))
        return loaded
    except Exception:
        return []
