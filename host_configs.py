import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class HostConfig:
    id: str
    label: str
    created_at: str

    @classmethod
    def create(cls, label: str) -> "HostConfig":
        return cls(id=uuid.uuid4().hex[:12], label=label.strip(), created_at=now_str())

    def to_dict(self) -> dict:
        return {"id": self.id, "label": self.label, "created_at": self.created_at}

    @classmethod
    def from_dict(cls, data: dict) -> "HostConfig":
        return cls(id=data["id"], label=data.get("label", ""), created_at=data.get("created_at", ""))


class HostConfigStore:
    def __init__(self, hosts_path: Path, active_path: Path):
        self.hosts_path = hosts_path
        self.active_path = active_path

    def load_all(self) -> list[HostConfig]:
        if not self.hosts_path.exists():
            return []
        try:
            data = json.loads(self.hosts_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        hosts = []
        for item in data:
            try:
                hosts.append(HostConfig.from_dict(item))
            except (KeyError, TypeError):
                continue
        return hosts

    def save_all(self, hosts: list[HostConfig]) -> None:
        self.hosts_path.write_text(
            json.dumps([host.to_dict() for host in hosts], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(self, host: HostConfig) -> HostConfig:
        hosts = [item for item in self.load_all() if item.id != host.id]
        hosts.append(host)
        self.save_all(hosts)
        return host

    def get(self, host_id: str) -> HostConfig | None:
        for host in self.load_all():
            if host.id == host_id:
                return host
        return None

    def load_active_id(self) -> str | None:
        if not self.active_path.exists():
            return None
        try:
            data = json.loads(self.active_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        return data.get("host_id")

    def set_active(self, host_id: str) -> None:
        self.active_path.write_text(json.dumps({"host_id": host_id}, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_active(self) -> HostConfig | None:
        active_id = self.load_active_id()
        if not active_id:
            return None
        return self.get(active_id)