from benchmarks.base import Benchmark
from benchmarks.brackets import BracketsBenchmark
from benchmarks.cron import CronBenchmark
from benchmarks.kv import KVBenchmark
from benchmarks.priority_scheduler import PrioritySchedulerBenchmark
from benchmarks.scheduler import SchedulerBenchmark
from benchmarks.snake import SnakeBenchmark
from benchmarks.sql import SQLBenchmark
from benchmarks.vm import VMBenchmark

REGISTRY: list[Benchmark] = [
    VMBenchmark(),
    BracketsBenchmark(),
    SchedulerBenchmark(),
    PrioritySchedulerBenchmark(),
    KVBenchmark(),
    CronBenchmark(),
    SQLBenchmark(),
    SnakeBenchmark(),
]
BY_ID: dict[str, Benchmark] = {b.id: b for b in REGISTRY}
