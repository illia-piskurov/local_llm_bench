"""Isolated eval sandbox using multiprocessing.

The generated LLM code runs in a child process so that:
- infinite loops → killed by timeout
- sys.exit() / os._exit() → affects only the child
- segfaults / OOM → caught via exit code
- exceptions → reported via Queue, don't crash the parent
"""

import multiprocessing as mp
import queue
from dataclasses import dataclass, field


@dataclass
class SandboxResult:
    passed: int
    total: int
    errors: list[str] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return self.passed == self.total and self.total > 0


def _worker(code: str, tests: list[dict[str, str]], result_queue: "mp.Queue[SandboxResult]") -> None:
    """Runs inside the child process. Parent never sees exceptions from here."""
    namespace: dict[str, object] = {}
    errors: list[str] = []
    passed = 0

    try:
        exec(code, namespace)  # noqa: S102
    except Exception as exc:
        result_queue.put(SandboxResult(0, len(tests), [f"Compilation error: {exc}"]))
        return

    for test in tests:
        try:
            exec(test["code"], namespace.copy())  # noqa: S102 — copy: tests don't pollute each other
            passed += 1
        except AssertionError as exc:
            errors.append(f"AssertionError: {exc}")
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")

    result_queue.put(SandboxResult(passed, len(tests), errors))


def evaluate(
    code: str,
    tests: list[dict[str, str]],
    *,
    timeout: float = 5.0,
) -> SandboxResult:
    """Run code against tests in an isolated child process.

    Always returns a SandboxResult — never raises.
    """
    if not code.strip():
        return SandboxResult(0, len(tests), ["No code to evaluate"])

    ctx = mp.get_context("spawn")  # safer than fork on all platforms
    result_queue: "mp.Queue[SandboxResult]" = ctx.Queue()
    proc = ctx.Process(target=_worker, args=(code, tests, result_queue), daemon=True)

    try:
        proc.start()
        proc.join(timeout)
    except Exception as exc:
        return SandboxResult(0, len(tests), [f"Sandbox start error: {exc}"])

    if proc.is_alive():
        proc.kill()
        proc.join(2.0)  # wait for real termination after kill
        return SandboxResult(0, len(tests), [f"Timeout after {timeout}s"])

    # Child crashed (segfault, OOM, os._exit, etc.)
    if proc.exitcode != 0 and result_queue.empty():
        return SandboxResult(
            0, len(tests), [f"Process crashed with exit code {proc.exitcode}"]
        )

    try:
        return result_queue.get_nowait()
    except queue.Empty:
        return SandboxResult(0, len(tests), ["No result returned from sandbox"])
