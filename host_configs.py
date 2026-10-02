import logging
import platform
import socket
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from database import Database

logger = logging.getLogger(__name__)

LOCAL_HOST_FILE = Path(__file__).parent / ".local_host"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def detect_system_hardware() -> dict:
    """Detects current machine hardware without external dependencies."""
    system = platform.system()
    hostname = socket.gethostname()
    cpu_name = ""
    ram_gb = 0

    if system == "Windows":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            )
            cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            cpu_name = cpu_name.strip()
        except Exception:
            cpu_name = platform.processor()

        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            raw_gb = stat.ullTotalPhys / (1024**3)
            ram_gb = round(raw_gb)
            if 28 <= ram_gb <= 31:
                ram_gb = 32
            elif 14 <= ram_gb <= 15:
                ram_gb = 16
        except Exception:
            pass

    elif system == "Darwin":
        try:
            cpu_name = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
        except Exception:
            cpu_name = "Apple Silicon"

        try:
            mem_bytes = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]).decode().strip())
            ram_gb = round(mem_bytes / (1024**3))
        except Exception:
            pass

    elif system == "Linux":
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        cpu_name = line.split(":", 1)[1].strip()
                        break
        except Exception:
            cpu_name = platform.processor()

        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if "MemTotal" in line:
                        kb = int(line.split()[1])
                        ram_gb = round(kb / (1024 * 1024))
                        break
        except Exception:
            pass

    return {
        "system": system,
        "hostname": hostname,
        "cpu": cpu_name or platform.processor(),
        "ram": ram_gb,
    }


def build_hardware_label(info: dict) -> str:
    parts = []
    cpu = info.get("cpu", "")
    if cpu:
        parts.append(cpu.replace("with Radeon Graphics", "Radeon iGPU"))
    if info.get("ram", 0) > 0:
        parts.append(f"{info['ram']} GB")
    parts.append(info.get("system", ""))
    return " | ".join(parts) if parts else info.get("hostname", "Local Machine")


def match_existing_host(info: dict, existing_hosts: list["HostConfig"]) -> "HostConfig | None":
    """Intelligently matches existing profile in database for current hardware."""
    cpu = info.get("cpu", "").lower()
    system = info.get("system", "").lower()

    for h in existing_hosts:
        lbl = h.label.lower()

        # 1. Apple Silicon (M4, M3, M2, M1)
        if "darwin" in system:
            for m in ["m4", "m3", "m2", "m1"]:
                if m in cpu and m in lbl:
                    return h

        # 2. AMD Ryzen and Intel Core models (250, 7735hs, 1235u, etc.)
        for token in ["250", "7735hs", "1235u", "7735", "7840", "8840", "13700", "14700", "9950"]:
            if token in cpu and token in lbl:
                return h

        # 3. Full CPU name match
        if cpu and (
            cpu in lbl
            or any(part in lbl for part in cpu.split() if len(part) >= 4 and part not in ("intel", "amd", "core"))
        ):
            return h

    return None


@dataclass
class HostConfig:
    id: str
    label: str
    created_at: str

    @classmethod
    def create(cls, label: str) -> "HostConfig":
        return cls(id=uuid.uuid4().hex[:12], label=label.strip(), created_at=now_str())


class HostConfigStore:
    def __init__(self, db: Database):
        self.db = db

    def load_all(self) -> list[HostConfig]:
        rows = self.db.conn.execute("SELECT id, label, created_at FROM hosts ORDER BY created_at").fetchall()
        return [HostConfig(id=row["id"], label=row["label"], created_at=row["created_at"]) for row in rows]

    def add(self, host: HostConfig) -> HostConfig:
        self.db.conn.execute(
            "INSERT OR REPLACE INTO hosts (id, label, created_at) VALUES (?, ?, ?)",
            (host.id, host.label, host.created_at),
        )
        self.db.conn.commit()

        # Persist to records/ for Git versioning
        try:
            import json

            records_dir = Path(__file__).parent / "records" / "hosts"
            records_dir.mkdir(parents=True, exist_ok=True)
            path = records_dir / f"{host.id}.json"
            path.write_text(
                json.dumps(
                    {"id": host.id, "label": host.label, "created_at": host.created_at}, ensure_ascii=False, indent=2
                ),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("Failed to persist host config record to %s: %s", path, e)

        return host

    def get(self, host_id: str) -> HostConfig | None:
        row = self.db.conn.execute("SELECT id, label, created_at FROM hosts WHERE id = ?", (host_id,)).fetchone()
        if row is None:
            return None
        return HostConfig(id=row["id"], label=row["label"], created_at=row["created_at"])

    def setup_local_device(self) -> HostConfig:
        """Initial host setup for a new machine.

        Detects system hardware and prompts the user only ONCE.
        The choice is persisted to .local_host and will not be asked again.
        """
        import questionary
        from questionary import Choice

        info = detect_system_hardware()
        detected_label = build_hardware_label(info)
        existing = self.load_all()

        exact_match = match_existing_host(info, existing)

        # Non-interactive environment (CI / headless)
        if not sys.stdin.isatty():
            if exact_match:
                host = exact_match
            else:
                host = HostConfig.create(detected_label)
                self.add(host)
            LOCAL_HOST_FILE.write_text(host.id, encoding="utf-8")
            return host

        print("\n" + "=" * 62)
        print("🔍 New device detected (first run on this machine)")
        print(f"   Hardware: {detected_label}")
        print(f"   Hostname: {info.get('hostname')}")
        print("=" * 62)

        choices = []
        if exact_match:
            choices.append(Choice(f"🔗 Link to detected profile: '{exact_match.label}'", value=exact_match.id))

        choices.append(Choice(f"✨ Create new profile: '{detected_label}'", value="new"))

        # Other profiles
        for h in existing:
            if exact_match and h.id == exact_match.id:
                continue
            choices.append(Choice(f"🔗 Link to existing profile: '{h.label}'", value=h.id))

        choices.append(Choice("✏️  Enter custom profile name", value="custom"))

        chosen = questionary.select(
            "How should speed benchmark results be recorded from this machine?",
            choices=choices,
        ).ask()

        if chosen == "new":
            host = HostConfig.create(detected_label)
            self.add(host)
        elif chosen == "custom":
            custom_lbl = questionary.text("Enter profile name:").ask()
            label = custom_lbl.strip() if custom_lbl and custom_lbl.strip() else detected_label
            host = HostConfig.create(label)
            self.add(host)
        elif chosen:
            host = self.get(chosen) or HostConfig.create(detected_label)
            if not self.get(host.id):
                self.add(host)
        else:
            host = exact_match or HostConfig.create(detected_label)
            if not self.get(host.id):
                self.add(host)

        LOCAL_HOST_FILE.write_text(host.id, encoding="utf-8")
        print(f"✔ Device profile bound: {host.label}")
        print("✔ Saved to .local_host (will not be prompted again).\n")
        return host

    def get_active(self) -> HostConfig:
        """Returns the active host for the CURRENT machine.

        Uses the local .local_host file (not committed to git),
        guaranteeing that git pull from another laptop will not overwrite configuration.
        """
        if LOCAL_HOST_FILE.exists():
            try:
                host_id = LOCAL_HOST_FILE.read_text(encoding="utf-8").strip()
                if host_id:
                    host = self.get(host_id)
                    if host:
                        return host
            except Exception:
                pass

        # If file is missing, configure device once
        return self.setup_local_device()

    def set_active(self, host_id: str) -> None:
        """Switches active host ONLY on the current local machine."""
        LOCAL_HOST_FILE.write_text(host_id, encoding="utf-8")
        # Also update in DB for backward compatibility
        try:
            self.db.conn.execute("UPDATE hosts SET is_active = 0")
            self.db.conn.execute("UPDATE hosts SET is_active = 1 WHERE id = ?", (host_id,))
            self.db.conn.commit()
        except Exception:
            pass
