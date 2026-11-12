"""Runs sandboxed test cases (QuickJS, Lua) in a child process that the parent can kill.

In-process limits are not a hard guarantee. The QuickJS time limit is swallowed by a Promise executor, so guest
code such as ``new Promise(() => { while (executing.size) asyncFn(); })`` can spin forever inside ``ctx.eval``;
the Lua instruction hook cannot interrupt a long native call such as a pathological ``string.find``. No
in-process limit can stop that, so every case runs in a worker and the parent enforces a wall-clock timeout per
case by killing the worker and continuing with the remaining cases in a fresh one.

Protocol: the parent writes one JSON request line to the worker's stdin, the worker answers with one JSON line
per finished case.
"""

import importlib
import json
import queue
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASE_TIMEOUT_SECONDS = 10.0

# (status, detail): status is "pass", "fail", "error" (the case raised) or "timeout".
CaseOutcome = tuple[str, str]


def _resolve(ref: str) -> Callable:
    module, _, name = ref.partition(":")
    return getattr(importlib.import_module(module), name)


def _ref(function: Callable) -> str:
    return f"{function.__module__}:{function.__qualname__}"


def _call_case(case: Callable, solution: str) -> bool:
    return case(solution)


def _worker_main() -> None:
    request = json.loads(sys.stdin.readline())
    runner = _resolve(request["runner"])
    for index in range(request["start"], len(request["cases"])):
        try:
            reply = {"index": index, "ok": bool(runner(_resolve(request["cases"][index]), request["solution"]))}
        except Exception as error:
            reply = {"index": index, "error": str(error)}
        sys.stdout.write(json.dumps(reply) + "\n")
        sys.stdout.flush()


def run_cases_isolated(
    cases: list[tuple[str, Callable]],
    solution: str,
    runner: Callable[[Callable, str], bool] = _call_case,
    case_timeout: float | None = None,
) -> list[CaseOutcome]:
    """Runs importable module-level case functions in worker processes; returns one outcome per case.

    ``runner(case, solution)`` executes one case inside the worker; by default the case receives the solution
    source. Cases and the runner are passed by reference, so they must be module-level functions.
    """
    case_timeout = CASE_TIMEOUT_SECONDS if case_timeout is None else case_timeout
    refs = [_ref(case) for _, case in cases]
    runner_ref = _ref(runner)
    outcomes: list[CaseOutcome] = [("error", "not run")] * len(cases)
    index = 0
    while index < len(cases):
        worker = subprocess.Popen(
            [sys.executable, "-m", "sandboxes.case_worker"],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        lines: queue.Queue[str | None] = queue.Queue()

        def pump(stdout=worker.stdout, sink=lines) -> None:
            for line in stdout:
                sink.put(line)
            sink.put(None)

        threading.Thread(target=pump, daemon=True).start()
        try:
            assert worker.stdin is not None
            worker.stdin.write(
                json.dumps({"cases": refs, "runner": runner_ref, "solution": solution, "start": index}) + "\n"
            )
            worker.stdin.close()
            while index < len(cases):
                try:
                    line = lines.get(timeout=case_timeout)
                except queue.Empty:
                    outcomes[index] = ("timeout", f"timed out after {case_timeout:g}s (runaway JavaScript)")
                    index += 1
                    break
                if line is None:
                    outcomes[index] = ("error", "sandbox worker exited unexpectedly")
                    index += 1
                    break
                try:
                    reply = json.loads(line)
                    index = int(reply["index"])
                except (ValueError, KeyError, TypeError):
                    continue
                if "error" in reply:
                    outcomes[index] = ("error", str(reply["error"]))
                else:
                    outcomes[index] = ("pass", "") if reply["ok"] else ("fail", "assertion returned False")
                index += 1
        finally:
            worker.kill()
            worker.wait()
    return outcomes


if __name__ == "__main__":
    _worker_main()
