import logging
import platform
import re
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


# Vendor boilerplate that carries no information about the exact CPU model.
_CPU_NOISE_RE = re.compile(
    r"\(r\)|\(tm\)|®|™|@\s*[\d.]+\s*ghz|\b\d+-core\b|\bwith\s+radeon\s+graphics\b|\b(?:cpu|processor)\b"
)
# Tokens that contain digits but describe a CPU generation or clock, not a specific model.
_GENERIC_ID_RE = re.compile(r"^(?:\d+(?:st|nd|rd|th)|\d*ghz|\d+mhz|\d+nm|\d+cores?|\d+threads?)$")
_APPLE_CHIP_RE = re.compile(r"\bm([1-9])(?:\s+(pro|max|ultra))?\b")
_RAM_RE = re.compile(r"(\d+)\s*gb\b")


def _cpu_model_ids(text: str) -> set[str]:
    """Extracts distinctive CPU model identifiers (e.g. ``i71235u``, ``1235u``, ``7735hs``) from free text.

    Only whole identifiers that contain a digit and are at least 4 characters long are kept, so generic
    words (``intel``, ``core``, ``ryzen``) and short family markers (``i7``, ``7``) never produce a match.
    """
    cleaned = _CPU_NOISE_RE.sub(" ", text.lower())
    ids: set[str] = set()
    for token in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", cleaned):
        for part in (token, *token.split("-")):
            part = part.replace("-", "")
            if len(part) >= 4 and any(ch.isdigit() for ch in part) and not _GENERIC_ID_RE.match(part):
                ids.add(part)
    return ids


def _apple_chip(text: str) -> str | None:
    """Returns the full Apple Silicon chip name (``m3``, ``m3 max``) or None."""
    match = _APPLE_CHIP_RE.search(text.lower())
    if not match:
        return None
    return f"m{match.group(1)}" + (f" {match.group(2)}" if match.group(2) else "")


def match_existing_host(info: dict, existing_hosts: list["HostConfig"]) -> "HostConfig | None":
    """Finds the single existing profile that describes the current hardware.

    The match is deliberately conservative because a wrong link silently mixes speed metrics from
    different machines: a profile matches only when it names the exact CPU model (whole identifier,
    not a substring) and, if it states a RAM size, that size agrees. When several profiles match,
    the result is ambiguous and None is returned so the caller creates a new profile or asks the user.
    """
    cpu = info.get("cpu", "") or ""
    system = (info.get("system", "") or "").lower()
    ram = info.get("ram", 0) or 0

    is_apple = "darwin" in system
    cpu_chip = _apple_chip(cpu) if is_apple else None
    cpu_ids = _cpu_model_ids(cpu)
    if not cpu_chip and not cpu_ids:
        return None

    matches: list[HostConfig] = []
    for host in existing_hosts:
        label = host.label.lower()

        if cpu_chip:
            if _apple_chip(label) != cpu_chip:
                continue
        elif not (cpu_ids & _cpu_model_ids(label)):
            continue

        stated_ram = _RAM_RE.search(label)
        if stated_ram and ram and int(stated_ram.group(1)) != ram:
            continue

        matches.append(host)

    return matches[0] if len(matches) == 1 else None


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
        records_dir = Path(__file__).parent / "records" / "hosts"
        try:
            import json

            records_dir.mkdir(parents=True, exist_ok=True)
            path = records_dir / f"{host.id}.json"
            path.write_text(
                json.dumps(
                    {"id": host.id, "label": host.label, "created_at": host.created_at}, ensure_ascii=False, indent=2
                ),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("Failed to persist host config record in %s: %s", records_dir, e)

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
