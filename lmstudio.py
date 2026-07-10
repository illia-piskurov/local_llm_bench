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


def list_llm_models() -> list[Model]:
    models = requests.get(f"{BASE_URL}/api/v1/models").json()
    return [Model.from_dict(m) for m in models["models"] if m["type"] == "llm"]


def ask_model(model_key: str, messages: list[dict]) -> str:
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={"model": model_key, "messages": messages, "temperature": 0.2},
        timeout=None,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


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
        warn(f"нет загруженных инстансов для {model_key}, выгружать нечего.")
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
