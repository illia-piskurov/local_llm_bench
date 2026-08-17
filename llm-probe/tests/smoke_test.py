"""Quick smoke test for the full stack."""

from llm_probe.db.engine import init_db, get_session
from llm_probe.db.crud import get_leaderboard, save_run
from llm_probe.runner.sandbox import evaluate
from llm_probe.runner.extractor import extract_code
from llm_probe.benchmarks.registry import all_bench_ids, get_benchmark
from llm_probe.runner.runner import build_jobs
from llm_probe.models.run import Run


def test_db() -> None:
    init_db()
    with get_session() as s:
        rows = get_leaderboard(s)
    print(f"[1] DB init OK, leaderboard rows: {len(rows)}")

    with get_session() as s:
        run = Run(
            model_id="test-model",
            bench_id="algorithm",
            level_id="l1",
            attempt=1,
            temperature=0.2,
            passed=5,
            total=5,
            tok_per_sec=12.5,
            status="ok",
        )
        saved = save_run(s, run)
    print(f"[2] Save run OK: {saved.id}")

    with get_session() as s:
        rows = get_leaderboard(s)
    r = rows[0]
    print(f"[3] Leaderboard OK: pass@1={r['pass_at_1']}, avg={r['avg_accuracy']:.2f}, attempts={r['attempts']}")



def test_extractor() -> None:
    code = extract_code("```python\ndef add(a, b):\n    return a + b\n```")
    assert "def add" in code
    code2 = extract_code("``` python\ndef foo(): return 1\n```")
    assert "def foo" in code2
    print("[4] Extractor OK")


def test_sandbox() -> None:
    r = evaluate(
        "def f(x): return x*2",
        [{"code": "assert f(3)==6"}, {"code": "assert f(0)==0"}],
    )
    assert r.passed == 2 and r.total == 2
    print(f"[5] Sandbox pass OK: {r.passed}/{r.total}")

    r2 = evaluate("while True: pass", [{"code": "assert True"}], timeout=1.0)
    assert "Timeout" in r2.errors[0]
    print(f"[6] Sandbox timeout OK: {r2.errors[0]}")

    r3 = evaluate("import sys; sys.exit(42)", [{"code": "assert True"}])
    assert r3.passed == 0
    print(f"[7] Sandbox crash OK: {r3.errors}")


def test_benchmarks() -> None:
    bench = get_benchmark("algorithm")
    tasks = bench.load_tasks("l1")
    assert len(tasks) >= 1
    print(f"[8] Algorithm L1: {len(tasks)} tasks, first: {tasks[0].id}")

    bench2 = get_benchmark("bug_hunt")
    tasks2 = bench2.load_tasks("l2")
    assert len(tasks2) >= 1
    print(f"[9] BugHunt L2: {len(tasks2)} tasks")

    jobs = build_jobs("test-model", ["algorithm", "bug_hunt"], ["l1"], k=2)
    assert len(jobs) > 0
    print(f"[10] Jobs built: {len(jobs)}")


if __name__ == "__main__":
    test_db()
    test_extractor()
    test_sandbox()
    test_benchmarks()
    print()
    print("=== ALL TESTS PASSED ===")
