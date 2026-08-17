"""Benchmark base classes and registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TestCase:
    """A single assertion to run against generated code."""
    code: str  # exec'd in the same namespace as the generated code


@dataclass
class BenchmarkTask:
    """One problem for the LLM to solve."""
    id: str
    level: str                      # 'l1' | 'l2' | 'l3'
    prompt: str
    tests: list[TestCase]
    description: str = ""


class Benchmark(ABC):
    """Base class for all benchmark types."""

    id: str                         # e.g. 'bug_hunt'
    name: str                       # human-readable
    levels: list[str] = field(default_factory=lambda: ["l1", "l2", "l3"])  # type: ignore[misc]

    @abstractmethod
    def load_tasks(self, level: str) -> list[BenchmarkTask]:
        """Load all tasks for a given difficulty level."""
        ...

    def available_levels(self) -> list[str]:
        return ["l1", "l2", "l3"]
