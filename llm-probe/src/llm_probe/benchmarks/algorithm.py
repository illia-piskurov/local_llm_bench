"""Algorithm benchmark — classic coding problems at 3 difficulty levels."""

import json
from pathlib import Path

from llm_probe.benchmarks.base import Benchmark, BenchmarkTask, TestCase

_DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "benchmarks" / "algorithm"

PROMPT_TEMPLATE = """\
Implement the following function in Python.
Return ONLY the Python code in a ```python``` block, no explanations.

Task: {description}

Function signature:
{signature}
"""


class AlgorithmBenchmark(Benchmark):
    id = "algorithm"
    name = "Algorithm"

    def load_tasks(self, level: str) -> list[BenchmarkTask]:
        path = _DATA_DIR / f"{level}_cases.json"
        if not path.exists():
            return _get_hardcoded_tasks(level)
        with path.open(encoding="utf-8") as f:
            raw = json.load(f)
        return [
            BenchmarkTask(
                id=item["id"],
                level=level,
                prompt=PROMPT_TEMPLATE.format(
                    description=item["description"],
                    signature=item["signature"],
                ),
                tests=[TestCase(code=t) for t in item["tests"]],
                description=item["description"],
            )
            for item in raw
        ]


def _get_hardcoded_tasks(level: str) -> list[BenchmarkTask]:
    """Built-in tasks so the tool works without external JSON files."""
    if level == "l1":
        return [
            BenchmarkTask(
                id="algo_l1_binary_search",
                level="l1",
                description="Binary search in sorted list",
                prompt=PROMPT_TEMPLATE.format(
                    description="Implement binary search. Return the index of target in sorted list, or -1 if not found.",
                    signature="def binary_search(arr: list[int], target: int) -> int:",
                ),
                tests=[
                    TestCase("assert binary_search([1,3,5,7,9], 5) == 2"),
                    TestCase("assert binary_search([1,3,5,7,9], 1) == 0"),
                    TestCase("assert binary_search([1,3,5,7,9], 9) == 4"),
                    TestCase("assert binary_search([1,3,5,7,9], 4) == -1"),
                    TestCase("assert binary_search([], 1) == -1"),
                ],
            ),
            BenchmarkTask(
                id="algo_l1_two_sum",
                level="l1",
                description="Two sum — find indices of two numbers that add up to target",
                prompt=PROMPT_TEMPLATE.format(
                    description="Return indices of two numbers in nums that add up to target. Exactly one solution exists.",
                    signature="def two_sum(nums: list[int], target: int) -> tuple[int, int]:",
                ),
                tests=[
                    TestCase("assert set(two_sum([2,7,11,15], 9)) == {0,1}"),
                    TestCase("assert set(two_sum([3,2,4], 6)) == {1,2}"),
                    TestCase("assert set(two_sum([3,3], 6)) == {0,1}"),
                    TestCase("r = two_sum([1,2,3,4], 7); assert set(r) == {2,3}"),
                    TestCase("r = two_sum([0,4,3,0], 0); assert set(r) == {0,3}"),
                ],
            ),
            BenchmarkTask(
                id="algo_l1_fizzbuzz",
                level="l1",
                description="FizzBuzz — return list of strings for 1..n",
                prompt=PROMPT_TEMPLATE.format(
                    description="Return a list of strings 1..n: 'FizzBuzz' for multiples of 15, 'Fizz' for 3, 'Buzz' for 5, else the number as string.",
                    signature="def fizzbuzz(n: int) -> list[str]:",
                ),
                tests=[
                    TestCase("r = fizzbuzz(15); assert r[2] == 'Fizz'"),
                    TestCase("r = fizzbuzz(15); assert r[4] == 'Buzz'"),
                    TestCase("r = fizzbuzz(15); assert r[14] == 'FizzBuzz'"),
                    TestCase("r = fizzbuzz(5); assert r == ['1','2','Fizz','4','Buzz']"),
                    TestCase("assert len(fizzbuzz(10)) == 10"),
                ],
            ),
        ]
    if level == "l2":
        return [
            BenchmarkTask(
                id="algo_l2_lcs",
                level="l2",
                description="Longest Common Subsequence length",
                prompt=PROMPT_TEMPLATE.format(
                    description="Return the length of the longest common subsequence of strings s1 and s2 using dynamic programming.",
                    signature="def lcs(s1: str, s2: str) -> int:",
                ),
                tests=[
                    TestCase("assert lcs('abcde', 'ace') == 3"),
                    TestCase("assert lcs('abc', 'abc') == 3"),
                    TestCase("assert lcs('abc', 'def') == 0"),
                    TestCase("assert lcs('', 'abc') == 0"),
                    TestCase("assert lcs('AGGTAB', 'GXTXAYB') == 4"),
                ],
            ),
            BenchmarkTask(
                id="algo_l2_coin_change",
                level="l2",
                description="Coin change — minimum number of coins",
                prompt=PROMPT_TEMPLATE.format(
                    description="Return the minimum number of coins to make amount. Use coins from the given list. Return -1 if not possible.",
                    signature="def coin_change(coins: list[int], amount: int) -> int:",
                ),
                tests=[
                    TestCase("assert coin_change([1,5,11], 15) == 3"),
                    TestCase("assert coin_change([2], 3) == -1"),
                    TestCase("assert coin_change([1,2,5], 11) == 3"),
                    TestCase("assert coin_change([1], 0) == 0"),
                    TestCase("assert coin_change([186,419,83,408], 6249) == 20"),
                ],
            ),
        ]
    # l3
    return [
        BenchmarkTask(
            id="algo_l3_interval_scheduling",
            level="l3",
            description="Interval scheduling maximization",
            prompt=PROMPT_TEMPLATE.format(
                description=(
                    "Given a list of intervals (start, end), return the maximum number of "
                    "non-overlapping intervals you can select. Intervals that touch at endpoints are considered overlapping."
                ),
                signature="def max_non_overlapping(intervals: list[tuple[int,int]]) -> int:",
            ),
            tests=[
                TestCase("assert max_non_overlapping([(1,3),(2,4),(3,5)]) == 2"),
                TestCase("assert max_non_overlapping([(1,2),(2,3),(3,4),(1,3)]) == 3"),
                TestCase("assert max_non_overlapping([]) == 0"),
                TestCase("assert max_non_overlapping([(1,10)]) == 1"),
                TestCase("assert max_non_overlapping([(1,2),(3,4),(5,6),(7,8)]) == 4"),
            ],
        ),
    ]
