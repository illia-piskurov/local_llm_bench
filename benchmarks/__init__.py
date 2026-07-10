from benchmarks.base import Benchmark
from benchmarks.brackets import BracketsBenchmark
from benchmarks.kv import KVBenchmark
from benchmarks.scheduler import SchedulerBenchmark
from benchmarks.snake import SnakeBenchmark
from benchmarks.vm import VMBenchmark

REGISTRY: list[Benchmark] = [
    VMBenchmark(),
    BracketsBenchmark(),
    SchedulerBenchmark(),
    KVBenchmark(),
    SnakeBenchmark(),
]
BY_ID: dict[str, Benchmark] = {b.id: b for b in REGISTRY}
