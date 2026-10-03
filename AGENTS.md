# AGENTS.md - Instructions for Autonomous Coding Agents

> **MANDATORY POLICY**:
> All documentation files (`*.md`), code comments, docstrings, and commit messages in this repository **MUST be written strictly and exclusively in English**.

---

## Canonical Guide

For the complete architectural reference, benchmark contracts, directory layout, and workflow commands, refer to:
👉 **[`AGENT.md`](./AGENT.md)**

---

## Critical Context: MicroPython WASI & Compatibility Shim Layer

When working on benchmarks, tests, or sandboxes in this repository, agents must understand the Python execution architecture:

1. **Zero Native Execution**:
   - Model-generated Python code **never** runs directly on the host machine.
   - It executes inside **MicroPython WASI** with instruction-level fuel metering for strict timeout and resource protection.

2. **The CPython Compatibility Layer (`sandboxes/mpy_compat.py`)**:
   - Modern LLMs write idiomatic CPython 3.10+ solutions utilizing standard library modules such as `typing`, `collections`, `itertools`, `heapq`, `functools`, `bisect`, `copy`, and `abc`.
   - MicroPython lacks most of these modules out-of-the-box.
   - Rather than forcing models to write primitive MicroPython or compromising sandbox security, `local_llm_bench` injects an AST-driven **pure-Python compatibility layer** on top of MicroPython.
   - The sandbox inspects the guest code's AST and selectively prepends shims **only** for the modules the guest code actually imports.

3. **Supported Shimmed Modules**:
   - `typing`: `Any`, `Optional`, `Union`, `List`, `Dict`, `Set`, `Tuple`, `Callable`, `Iterable`, `Sequence`, `Mapping`, `TypeVar`, `Generic`, `Protocol`, `cast`, `overload`.
   - `copy`: `copy`, `deepcopy`.
   - `collections`: `deque` (full deque API with `maxlen`), `defaultdict`, `Counter`, `OrderedDict`, `namedtuple`.
   - `functools`: `lru_cache`, `cache`, `wraps`, `reduce`, `partial`, `total_ordering`.
   - `itertools`: `chain`, `combinations`, `permutations`, `product`, `islice`, `cycle`, `repeat`, `accumulate`, `groupby`, `takewhile`, `dropwhile`.
   - `bisect`: `bisect_left`, `bisect_right`, `bisect`, `insort_left`, `insort_right`, `insort`.
   - `abc`: `ABC`, `abstractmethod`.
   - `heapq`: CPython extensions (`nlargest`, `nsmallest`, `heappushpop`, `heapreplace`).

4. **Architectural Invariants & Limitations**:
   - **Do not remove or weaken `sandboxes/mpy_compat.py`**: Shims allow real-world models to be fairly evaluated on their algorithmic logic rather than MicroPython-specific quirks.
   - **MicroPython constraints**: Recursion limit is ~100 frames; no native `dataclasses` or `enum.Enum`; dict iteration order is not guaranteed; 32-bit signed integers in certain math operations.
   - **Testing**: When updating shims, always verify parity with standard CPython using `uv run pytest tests/test_mpy_shims.py`.
