import os
import threading
from dataclasses import dataclass
from pathlib import Path

import requests

UNLOAD_TIMEOUT_SECONDS = 30
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


@dataclass
class Model:
    type: str
    key: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(type=data.get("type"), key=data.get("key"))


@dataclass
class ModelResponse:
    content: str
    stats: dict | None
    raw: dict
    reasoning: str | None = None


@dataclass
class GenerationConfig:
    temperature: float = 0.0
    seed: int = 42
    top_p: float = 1.0
    max_tokens: int = 4096
    timeout_seconds: float = 180.0
    context_length: int | None = None
    repeat_penalty: float | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "temperature": self.temperature,
            "seed": self.seed,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "timeout_seconds": self.timeout_seconds,
        }
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
            temperature=float(data.get("temperature", 0.0)),
            seed=int(data.get("seed", 42)),
            top_p=float(data.get("top_p", 1.0)),
            max_tokens=int(data.get("max_tokens", 4096)),
            timeout_seconds=float(data.get("timeout_seconds", 180.0)),
            context_length=data.get("context_length"),
            repeat_penalty=data.get("repeat_penalty"),
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


def get_model_artifact_info(model_key: str) -> ModelArtifactInfo:
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
    if len(messages) == 1 and messages[0].get("role") == "user":
        return None, messages[0].get("content", "")

    system_prompt = None
    chunks: list[str] = []

    for message in messages:
        role = message.get("role")
        content = message.get("content", "")

        if role == "system":
            system_prompt = content
            continue

        label = "User" if role == "user" else "Assistant" if role == "assistant" else str(role or "message")
        chunks.append(f"{label}:\n{content}")

    return system_prompt, "\n\n".join(chunks)


def list_llm_models() -> list[Model]:
    models = requests.get(f"{get_base_url()}/api/v1/models", timeout=10).json()
    return [Model.from_dict(m) for m in models["models"] if m["type"] == "llm"]


def ask_model(
    model_key: str,
    messages: list[dict],
    temperature: float | None = None,
    config: GenerationConfig | None = None,
) -> ModelResponse:
    cfg = config or GenerationConfig()
    if temperature is not None:
        cfg.temperature = temperature

    system_prompt, input_text = _render_transcript(messages)

    payload = {
        "model": model_key,
        "input": input_text,
        "store": True,
        "temperature": cfg.temperature,
        "max_output_tokens": cfg.max_tokens,
        "top_p": cfg.top_p,
    }
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
    )


def loaded_instance_ids(model_key: str) -> list[str]:
    models = requests.get(f"{get_base_url()}/api/v1/models", timeout=30).json()["models"]
    for m in models:
        if m["key"] == model_key:
            return [instance["id"] for instance in m.get("loaded_instances", [])]
    return []


def unload_model(model_key: str, console=None, timeout: int = UNLOAD_TIMEOUT_SECONDS) -> None:
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
    try:
        r = requests.get(f"{get_base_url()}/api/v1/models", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def get_loaded_models() -> list[Model]:
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
