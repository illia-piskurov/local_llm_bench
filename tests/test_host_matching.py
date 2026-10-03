"""Tests for conservative hardware-profile matching in host_configs."""

from host_configs import HostConfig, match_existing_host


def _host(host_id: str, label: str) -> HostConfig:
    return HostConfig(id=host_id, label=label, created_at="2026-01-01 00:00:00")


def _info(cpu: str, ram: int = 16, system: str = "Windows") -> dict:
    return {"cpu": cpu, "ram": ram, "system": system, "hostname": "box"}


def test_different_intel_cpus_do_not_match():
    hosts = [_host("a", "Intel(R) Core(TM) i7-1235U | 16 GB | Windows")]
    info = _info("Intel(R) Core(TM) i9-13900H")
    assert match_existing_host(info, hosts) is None


def test_same_intel_cpu_matches_across_label_formats():
    hosts = [_host("a", "ThinkPad i7-1235U | 16 GB | Linux")]
    info = _info("12th Gen Intel(R) Core(TM) i7-1235U", system="Linux")
    assert match_existing_host(info, hosts) is hosts[0]


def test_generation_and_clock_tokens_are_not_identifiers():
    hosts = [_host("a", "12th Gen Intel(R) Core(TM) i5-1235U @ 3.30GHz | 16 GB | Windows")]
    info = _info("12th Gen Intel(R) Core(TM) i7-1255U @ 3.30GHz")
    assert match_existing_host(info, hosts) is None


def test_amd_models_must_match_exactly():
    hosts = [_host("a", "AMD Ryzen 7 7735HS Radeon iGPU | 32 GB | Windows")]
    assert match_existing_host(_info("AMD Ryzen 7 7735HS with Radeon Graphics", ram=32), hosts) is hosts[0]
    assert match_existing_host(_info("AMD Ryzen 7 7840HS with Radeon Graphics", ram=32), hosts) is None
    # Same family word "ryzen" alone must never link two machines.
    assert match_existing_host(_info("AMD Ryzen 9 9950X", ram=32), hosts) is None


def test_ram_mismatch_prevents_match():
    hosts = [_host("a", "AMD Ryzen 7 7735HS | 16 GB | Windows")]
    assert match_existing_host(_info("AMD Ryzen 7 7735HS", ram=32), hosts) is None
    assert match_existing_host(_info("AMD Ryzen 7 7735HS", ram=16), hosts) is hosts[0]


def test_label_without_ram_still_matches_on_cpu():
    hosts = [_host("a", "Workstation Ryzen 9 9950X")]
    assert match_existing_host(_info("AMD Ryzen 9 9950X 16-Core Processor", ram=64), hosts) is hosts[0]


def test_ambiguous_match_returns_none():
    hosts = [
        _host("a", "Desktop i7-1235U | 16 GB"),
        _host("b", "Laptop i7-1235U | 16 GB"),
    ]
    assert match_existing_host(_info("Intel(R) Core(TM) i7-1235U"), hosts) is None


def test_apple_silicon_variants_are_distinct():
    hosts = [_host("a", "MacBook M3 Max | 64 GB | Darwin")]
    assert match_existing_host(_info("Apple M3", ram=64, system="Darwin"), hosts) is None
    assert match_existing_host(_info("Apple M3 Pro", ram=64, system="Darwin"), hosts) is None
    assert match_existing_host(_info("Apple M3 Max", ram=64, system="Darwin"), hosts) is hosts[0]


def test_apple_m1_does_not_match_m1_pro_or_other_generation():
    hosts = [_host("a", "Apple M1 Pro | 16 GB | Darwin")]
    assert match_existing_host(_info("Apple M1", system="Darwin"), hosts) is None
    assert match_existing_host(_info("Apple M2 Pro", system="Darwin"), hosts) is None
    assert match_existing_host(_info("Apple M1 Pro", system="Darwin"), hosts) is hosts[0]


def test_empty_or_unknown_cpu_never_matches():
    hosts = [_host("a", "Some Host | 16 GB")]
    assert match_existing_host(_info(""), hosts) is None
    assert match_existing_host(_info("Generic CPU"), hosts) is None
    assert match_existing_host(_info("Intel(R) Core(TM) i7-1235U"), []) is None
