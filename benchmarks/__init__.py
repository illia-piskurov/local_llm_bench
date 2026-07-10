from benchmarks.base import Benchmark
from benchmarks.kv import KVBenchmark
from benchmarks.scheduler import SchedulerBenchmark
from benchmarks.snake import SnakeBenchmark
from benchmarks.vm import VMBenchmark

REGISTRY: list[Benchmark] = [VMBenchmark(), SchedulerBenchmark(), KVBenchmark(), SnakeBenchmark()]
BY_ID: dict[str, Benchmark] = {b.id: b for b in REGISTRY}
