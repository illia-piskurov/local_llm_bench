"""Bug Hunt benchmark — find and fix bugs in broken Python code."""

from llm_probe.benchmarks.base import Benchmark, BenchmarkTask, TestCase

PROMPT_TEMPLATE = """\
The following Python function has a bug. Find and fix it.
Return ONLY the corrected Python code in a ```python``` block, no explanations.

```python
{buggy_code}
```
"""


class BugHuntBenchmark(Benchmark):
    id = "bug_hunt"
    name = "Bug Hunt"

    def load_tasks(self, level: str) -> list[BenchmarkTask]:
        return _get_tasks(level)


def _get_tasks(level: str) -> list[BenchmarkTask]:
    if level == "l1":
        return [
            BenchmarkTask(
                id="bug_l1_off_by_one",
                level="l1",
                description="Off-by-one in loop",
                prompt=PROMPT_TEMPLATE.format(buggy_code="""\
def sum_to_n(n: int) -> int:
    total = 0
    for i in range(n):   # Bug: should be range(n+1)
        total += i
    return total"""),
                tests=[
                    TestCase("assert sum_to_n(0) == 0"),
                    TestCase("assert sum_to_n(1) == 1"),
                    TestCase("assert sum_to_n(5) == 15"),
                    TestCase("assert sum_to_n(10) == 55"),
                    TestCase("assert sum_to_n(100) == 5050"),
                ],
            ),
            BenchmarkTask(
                id="bug_l1_wrong_operator",
                level="l1",
                description="Wrong comparison operator",
                prompt=PROMPT_TEMPLATE.format(buggy_code="""\
def is_even(n: int) -> bool:
    return n % 2 == 1  # Bug: should be == 0"""),
                tests=[
                    TestCase("assert is_even(0) == True"),
                    TestCase("assert is_even(2) == True"),
                    TestCase("assert is_even(1) == False"),
                    TestCase("assert is_even(-4) == True"),
                    TestCase("assert is_even(7) == False"),
                ],
            ),
            BenchmarkTask(
                id="bug_l1_wrong_return",
                level="l1",
                description="Returns wrong accumulator",
                prompt=PROMPT_TEMPLATE.format(buggy_code="""\
def factorial(n: int) -> int:
    result = 0  # Bug: should be 1
    for i in range(1, n + 1):
        result *= i
    return result"""),
                tests=[
                    TestCase("assert factorial(0) == 1"),
                    TestCase("assert factorial(1) == 1"),
                    TestCase("assert factorial(5) == 120"),
                    TestCase("assert factorial(6) == 720"),
                    TestCase("assert factorial(3) == 6"),
                ],
            ),
        ]

    if level == "l2":
        return [
            BenchmarkTask(
                id="bug_l2_missing_base_case",
                level="l2",
                description="Missing base case in recursion",
                prompt=PROMPT_TEMPLATE.format(buggy_code="""\
def fibonacci(n: int) -> int:
    if n == 0:   # Bug: missing 'if n == 1: return 1'
        return 0
    return fibonacci(n - 1) + fibonacci(n - 2)"""),
                tests=[
                    TestCase("assert fibonacci(0) == 0"),
                    TestCase("assert fibonacci(1) == 1"),
                    TestCase("assert fibonacci(5) == 5"),
                    TestCase("assert fibonacci(7) == 13"),
                    TestCase("assert fibonacci(10) == 55"),
                ],
            ),
            BenchmarkTask(
                id="bug_l2_none_check",
                level="l2",
                description="Missing None guard",
                prompt=PROMPT_TEMPLATE.format(buggy_code="""\
def safe_divide(a: float, b: float | None) -> float:
    return a / b  # Bug: b could be None"""),
                tests=[
                    TestCase("assert safe_divide(10, 2) == 5.0"),
                    TestCase("assert safe_divide(10, None) == 0.0"),
                    TestCase("assert safe_divide(0, 5) == 0.0"),
                    TestCase("assert safe_divide(-6, 3) == -2.0"),
                    TestCase("import math; assert math.isnan(safe_divide(10, None)) or safe_divide(10, None) == 0.0"),
                ],
            ),
        ]

    # l3
    return [
        BenchmarkTask(
            id="bug_l3_mutable_default",
            level="l3",
            description="Mutable default argument bug",
            prompt=PROMPT_TEMPLATE.format(buggy_code="""\
def append_to(item: int, lst: list[int] = []) -> list[int]:
    # Bug: mutable default argument shared across calls
    lst.append(item)
    return lst"""),
            tests=[
                TestCase("r1 = append_to(1); r2 = append_to(2); assert r1 != r2"),
                TestCase("assert append_to(5) == [5]"),
                TestCase("assert append_to(5, [1,2]) == [1,2,5]"),
                TestCase("a = append_to(10); b = append_to(20); assert 10 not in b"),
                TestCase("assert len(append_to(99)) == 1"),
            ],
        ),
    ]
