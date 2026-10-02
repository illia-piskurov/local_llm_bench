import os
import threading
from dataclasses import dataclass
from pathlib import Path

import requests

UNLOAD_TIMEOUT_SECONDS = 30
LOCAL_SERVER_FILE = Path(__file__).parent / ".local_server"


def get_base_url() -> str:
    """Возвращает текущий URL сервера инференса (LM Studio / Ollama / Remote)."""
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
    """Сохраняет локальный адрес сервера инференса в .local_server."""
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


def _render_transcript(messages: list[dict]) -> tuple[str | None, str]:
    system_prompt = None
    chunks: list[str] = []

    for message in messages:
        role = message.get("role")
        content = message.get("content", "")

        if role == "system":
            system_prompt = content
            continue

        label = "User" if role == "user" else "Assistant" if role == "assistant" else str(role or "message")
        chunks.append(f"{label}: {content}")

    return system_prompt, "\n\n".join(chunks)


def list_llm_models() -> list[Model]:
    models = requests.get(f"{get_base_url()}/api/v1/models").json()
    return [Model.from_dict(m) for m in models["models"] if m["type"] == "llm"]


def ask_model(model_key: str, messages: list[dict], temperature: float | None = None) -> ModelResponse:
    system_prompt, input_text = _render_transcript(messages)

    payload = {
        "model": model_key,
        "input": input_text,
        "store": True,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if system_prompt:
        payload["system_prompt"] = system_prompt

    response = requests.post(
        f"{get_base_url()}/api/v1/chat",
        json=payload,
        timeout=None,
    )

    response.raise_for_status()
    payload = response.json()
    output = payload.get("output", [])

    # 1. Извлекаем блоки message и reasoning из API LM Studio
    message_parts = [item.get("content", "") for item in output if item.get("type") == "message"]
    reasoning_parts = [item.get("content", "") for item in output if item.get("type") == "reasoning"]

    raw_content = "\n".join(message_parts)
    reasoning_text = "\n\n".join(reasoning_parts) if reasoning_parts else None

    # 2. Если в message_content содержались встроенные теги <think>...</think>
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

    # 3. Если content пуст (модель выдала всё внутри reasoning), используем reasoning
    if not content.strip() and reasoning_text:
        content = reasoning_text

    stats = payload.get("stats") or {}
    # Если reasoning_output_tokens не заполнено API, но мысли были — оцениваем токены (~3.8 символа/токен)
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
            warn(f"не удалось получить loaded_instances: {e}")
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
                warn(f"не удалось выгрузить инстанс {instance_id}: {e}")

    thread = threading.Thread(target=_do_unload, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    if thread.is_alive():
        warn(f"выгрузка модели зависла (>{timeout}с) — продолжаем без ожидания")


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
