from benchmarks.base import Benchmark
from benchmarks.c_framing import CFramingBenchmark
from benchmarks.js_async import JSAsyncBenchmark
from benchmarks.kv import KVBenchmark
from benchmarks.lua_game_ai import LuaGameAIBenchmark
from benchmarks.priority_scheduler import PrioritySchedulerBenchmark
from benchmarks.scheduler import SchedulerBenchmark
from benchmarks.sql import SQLBenchmark
from benchmarks.vm import VMBenchmark

REGISTRY: list[Benchmark] = [
    VMBenchmark(),
    SchedulerBenchmark(),
    PrioritySchedulerBenchmark(),
    KVBenchmark(),
    SQLBenchmark(),
    CFramingBenchmark(),
    JSAsyncBenchmark(),
    LuaGameAIBenchmark(),
]
BY_ID: dict[str, Benchmark] = {b.id: b for b in REGISTRY}
