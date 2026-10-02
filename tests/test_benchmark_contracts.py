"""Regression tests for benchmark-runner contracts.

These tests target the evaluators themselves, not a particular model answer.
"""

from benchmarks import BY_ID, REGISTRY, priority_scheduler
from sandboxes import process


def test_registry_ids_and_level_dependencies_are_valid():
    assert len(BY_ID) == len(REGISTRY)
    assert len({benchmark.id for benchmark in REGISTRY}) == len(REGISTRY)

    for benchmark in REGISTRY:
        level_ids = benchmark.level_order
        assert level_ids
        assert len(level_ids) == len(set(level_ids))
        for level in benchmark.levels:
            assert level.requires is None or level.requires in level_ids


def test_priority_level2_rechecks_plan_order(monkeypatch, tmp_path):
    """A level-2 answer must retain a correct level-1 implementation."""
    expected = {
        repr(tasks): (expected_order, expected_makespan, expected_cp)
        for _name, tasks, _workers, expected_order, expected_makespan, expected_cp in priority_scheduler.LEVEL2_TESTS
    }

    def fake_call(_path, function_name, args):
        tasks = args[0]
        expected_order, expected_makespan, expected_cp = expected[repr(tasks)]
        if function_name == "plan_order":
            return True, [] if expected_order is not None else None
        if function_name == "critical_path":
            return True, expected_cp
        if function_name == "makespan":
            return True, expected_makespan
        raise AssertionError(f"Unexpected function: {function_name}")

    monkeypatch.setattr(priority_scheduler, "call_with_timeout", fake_call)
    passed, total, failures = priority_scheduler.run_priority_level2(tmp_path / "solution.py")

    assert passed == 1  # Only the cyclic case may return None for plan_order.
    assert total == len(priority_scheduler.LEVEL2_TESTS)
    assert len(failures) == total - passed


def test_python_runner_never_falls_back_to_native_execution(monkeypatch, tmp_path):
    monkeypatch.setattr(process, "WASM_AVAILABLE", False)

    success, result = process.call_with_timeout(tmp_path / "solution.py", "solution", ())

    assert success is False
    assert "native execution is disabled" in str(result)
