from dataclasses import dataclass

import requests

BASE_URL = "http://127.0.0.1:1234"


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
    models = requests.get(f"{BASE_URL}/api/v1/models").json()
    return [Model.from_dict(m) for m in models["models"] if m["type"] == "llm"]


def ask_model(model_key: str, messages: list[dict]) -> ModelResponse:
    system_prompt, input_text = _render_transcript(messages)

    payload = {
        "model": model_key,
        "input": input_text,
        "temperature": 0.2,
        "store": True,
    }
    if system_prompt:
        payload["system_prompt"] = system_prompt

    response = requests.post(
        f"{BASE_URL}/api/v1/chat",
        json=payload,
        timeout=None,
    )
    response.raise_for_status()
    payload = response.json()
    output = payload.get("output", [])
    content = "\n".join(item.get("content", "") for item in output if item.get("type") == "message")
    return ModelResponse(
        content=content,
        stats=payload.get("stats"),
        raw=payload,
    )


def loaded_instance_ids(model_key: str) -> list[str]:
    models = requests.get(f"{BASE_URL}/api/v1/models", timeout=30).json()["models"]
    for m in models:
        if m["key"] == model_key:
            return [instance["id"] for instance in m.get("loaded_instances", [])]
    return []


def unload_model(model_key: str, console=None) -> None:
    def warn(message: str) -> None:
        if console is not None:
            console.print(f"  [yellow]warn:[/yellow] {message}")
        else:
            print(f"  warn: {message}")

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
                f"{BASE_URL}/api/v1/models/unload",
                json={"instance_id": instance_id},
                timeout=60,
            )
        except Exception as e:
            warn(f"не удалось выгрузить инстанс {instance_id}: {e}")
