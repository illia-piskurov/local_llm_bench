"""Benchmark registry — maps bench_id strings to Benchmark instances."""

from llm_probe.benchmarks.algorithm import AlgorithmBenchmark
from llm_probe.benchmarks.base import Benchmark
from llm_probe.benchmarks.bug_hunt import BugHuntBenchmark

_REGISTRY: dict[str, Benchmark] = {
    b.id: b  # type: ignore[attr-defined]
    for b in [
        AlgorithmBenchmark(),
        BugHuntBenchmark(),
        # completion, refactor, test_writer — TODO Phase 3
    ]
}


def get_benchmark(bench_id: str) -> Benchmark:
    if bench_id not in _REGISTRY:
        raise KeyError(f"Unknown benchmark: {bench_id!r}. Available: {list(_REGISTRY)}")
    return _REGISTRY[bench_id]


def list_benchmarks() -> list[dict[str, str]]:
    return [
        {"id": b.id, "name": b.name, "levels": ",".join(b.available_levels())}  # type: ignore[attr-defined]
        for b in _REGISTRY.values()
    ]


def all_bench_ids() -> list[str]:
    return list(_REGISTRY)
