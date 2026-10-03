"""Lua: Game AI (Behavior Trees & Coroutines) benchmark.

Tests game AI development capabilities in Lua (5.3+ / 5.4+):
- Level 1: Core behavior tree nodes (Action, Condition, Sequence, Selector).
- Level 2: Reactive shared memory (Blackboard with watchers) and decorators (Inverter, Cooldown).
- Level 3: Asynchronous actions on coroutines (AsyncAction with WAIT_TICKS pauses) and cascading tree reset.

Code executes inside an isolated Lupa Lua sandbox with revoked OS and file system access.
"""

from collections.abc import Callable
from pathlib import Path

from lupa import LuaError, LuaRuntime

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes.lua_runtime import create_lua_sandbox as _create_sandbox

LEVEL1_PROMPT = """\
Implement the core of a Behavior Tree engine for game AI in Lua (5.3+ / 5.4+).

Define a global table `BT = {}`:
- Execution statuses:
  BT.SUCCESS = "SUCCESS"
  BT.FAILURE = "FAILURE"
  BT.RUNNING = "RUNNING"

Nodes to implement:
1. `BT.Action(fn)` — action node:
   - When calling `node:tick(ctx)`, invokes `fn(ctx)`.
   - If `fn` returns `true` or `BT.SUCCESS` — returns `BT.SUCCESS`.
   - If `fn` returns `false` or `BT.FAILURE` — returns `BT.FAILURE`.
   - If `fn` returns `BT.RUNNING` — returns `BT.RUNNING`.
   - Method `node:reset()`.

2. `BT.Condition(predicate)` — condition check node:
   - When calling `node:tick(ctx)`, invokes `predicate(ctx)`.
   - If predicate evaluates to true — returns `BT.SUCCESS`, otherwise `BT.FAILURE`.
   - Method `node:reset()`.

3. `BT.Sequence(children)` — composite sequence node (logical AND):
   - Executes child nodes in order.
   - If a child returns `BT.FAILURE` — halts execution and returns `BT.FAILURE`.
   - If a child returns `BT.RUNNING` — remembers current node index and returns `BT.RUNNING`. On next `tick`, resumes from that node without re-executing previously succeeded children!
   - If all children return `BT.SUCCESS` — returns `BT.SUCCESS`.
   - Method `node:reset()` resets remembered child index to 1.

4. `BT.Selector(children)` — composite selector node (logical OR / Fallback):
   - Executes child nodes in order.
   - If a child returns `BT.SUCCESS` — halts execution and returns `BT.SUCCESS`.
   - If a child returns `BT.RUNNING` — remembers node index and returns `BT.RUNNING`. On next `tick`, resumes from it.
   - If all children return `BT.FAILURE` — returns `BT.FAILURE`.
   - Method `node:reset()` resets remembered child index to 1.

Return only clean Lua code in a single ```lua ... ``` code block, with no explanations outside the block.
"""

LEVEL2_PROMPT = """\
Extend your Behavior Tree implementation with a shared memory Blackboard and decorators:

1. Reactive memory board `BT.Blackboard`:
   - `BT.Blackboard.new()` — creates a new blackboard instance:
     - `bb:get(key, default)` — returns value for key, or `default` if nil.
     - `bb:set(key, value)` — stores value. If value changed, invokes all registered watchers for this key.
     - `bb:watch(key, callback)` — registers callback `callback(key, new_value, old_value)` triggered when value changes.

2. Decorators (single-child nodes):
   - `BT.Inverter(child)`:
     - Inverts child result: `BT.SUCCESS` -> `BT.FAILURE`, `BT.FAILURE` -> `BT.SUCCESS`.
     - Status `BT.RUNNING` is passed through unchanged.
     - Method `reset()` delegates to child.
   - `BT.Cooldown(child, ticks)`:
     - After successful child execution (`BT.SUCCESS`), enters cooldown for `ticks` ticks.
     - During cooldown, immediately returns `BT.FAILURE` without invoking child.
     - Once cooldown expires, child can execute again.
     - Method `reset()` resets cooldown counter and calls `child:reset()`.

Preserve Level 1 node behavior.

Return only clean Lua code in a single ```lua ... ``` code block, with no explanations outside the block.
"""

LEVEL3_PROMPT = """\
Extend your implementation with coroutine-based async actions and cascading tree resets:

1. Asynchronous action `BT.AsyncAction(coroutine_fn)`:
   - Enables multi-tick actions without blocking the main game loop, using Lua coroutines (`coroutine.create`, `coroutine.resume`, `coroutine.yield`).
   - Function `coroutine_fn(ctx)` may yield `coroutine.yield("WAIT_TICKS", n)` to wait for `n` ticks.
   - When calling `node:tick(ctx)`:
     - If coroutine is not yet created or dead — create new coroutine.
     - If node is in wait ticks mode — decrement ticks counter and return `BT.RUNNING`.
     - Resume coroutine (`coroutine.resume(co, ctx)`).
     - If coroutine yields `("WAIT_TICKS", n)` — set wait ticks to `n` and return `BT.RUNNING`.
     - When coroutine finishes — return its final result (`BT.SUCCESS`, `BT.FAILURE` or `true`/`false`).
   - Method `node:reset()`: clears coroutine and wait timer.

2. Cascading tree reset:
   - When calling `node:reset()` on composite nodes (`Sequence`, `Selector`), recursively call `reset()` on all child nodes.

Preserve Level 1 and Level 2 functionality.

Return only clean Lua code in a single ```lua ... ``` code block, with no explanations outside the block.
"""


def _load_solution(runtime: LuaRuntime, lua_code: str) -> None:
    runtime.execute(lua_code)


# ── LEVEL 1 TESTS ──
def test_action_and_condition(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local a_succ = BT.Action(function() return BT.SUCCESS end)
    local a_fail = BT.Action(function() return BT.FAILURE end)
    local a_bool_t = BT.Action(function() return true end)
    local a_bool_f = BT.Action(function() return false end)

    if a_succ:tick({}) ~= BT.SUCCESS then return false end
    if a_fail:tick({}) ~= BT.FAILURE then return false end
    if a_bool_t:tick({}) ~= BT.SUCCESS then return false end
    if a_bool_f:tick({}) ~= BT.FAILURE then return false end

    local c_t = BT.Condition(function(ctx) return ctx.val > 10 end)
    local c_f = BT.Condition(function(ctx) return ctx.val > 50 end)
    if c_t:tick({ val = 20 }) ~= BT.SUCCESS then return false end
    if c_f:tick({ val = 20 }) ~= BT.FAILURE then return false end

    return true
    """
    return bool(rt.execute(script))


def test_sequence_all_success(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local count = 0
    local seq = BT.Sequence({
        BT.Action(function() count = count + 1; return BT.SUCCESS end),
        BT.Action(function() count = count + 1; return BT.SUCCESS end),
        BT.Action(function() count = count + 1; return BT.SUCCESS end),
    })
    local res = seq:tick({})
    return res == BT.SUCCESS and count == 3
    """
    return bool(rt.execute(script))


def test_sequence_short_circuit_failure(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local count = 0
    local seq = BT.Sequence({
        BT.Action(function() count = count + 1; return BT.SUCCESS end),
        BT.Action(function() count = count + 1; return BT.FAILURE end),
        BT.Action(function() count = count + 1; return BT.SUCCESS end),
    })
    local res = seq:tick({})
    return res == BT.FAILURE and count == 2
    """
    return bool(rt.execute(script))


def test_sequence_resumes_running_child(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local node1_count = 0
    local node2_step = 0
    local seq = BT.Sequence({
        BT.Action(function() node1_count = node1_count + 1; return BT.SUCCESS end),
        BT.Action(function()
            node2_step = node2_step + 1
            if node2_step == 1 then return BT.RUNNING end
            return BT.SUCCESS
        end),
        BT.Action(function() return BT.SUCCESS end),
    })

    local r1 = seq:tick({})
    if r1 ~= BT.RUNNING then return false end
    if node1_count ~= 1 then return false end

    local r2 = seq:tick({})
    if r2 ~= BT.SUCCESS then return false end
    if node1_count ~= 1 then return false end

    return true
    """
    return bool(rt.execute(script))


def test_selector_first_success(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local count = 0
    local sel = BT.Selector({
        BT.Action(function() count = count + 1; return BT.FAILURE end),
        BT.Action(function() count = count + 1; return BT.SUCCESS end),
        BT.Action(function() count = count + 1; return BT.SUCCESS end),
    })
    local res = sel:tick({})
    return res == BT.SUCCESS and count == 2
    """
    return bool(rt.execute(script))


def test_selector_all_failure(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local count = 0
    local sel = BT.Selector({
        BT.Action(function() count = count + 1; return BT.FAILURE end),
        BT.Action(function() count = count + 1; return BT.FAILURE end),
    })
    local res = sel:tick({})
    return res == BT.FAILURE and count == 2
    """
    return bool(rt.execute(script))


def test_selector_resumes_running_child(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local node1_count = 0
    local node2_step = 0
    local sel = BT.Selector({
        BT.Action(function() node1_count = node1_count + 1; return BT.FAILURE end),
        BT.Action(function()
            node2_step = node2_step + 1
            if node2_step == 1 then return BT.RUNNING end
            return BT.SUCCESS
        end),
        BT.Action(function() return BT.FAILURE end),
    })

    local r1 = sel:tick({})
    if r1 ~= BT.RUNNING then return false end
    if node1_count ~= 1 then return false end

    local r2 = sel:tick({})
    if r2 ~= BT.SUCCESS then return false end
    if node1_count ~= 1 then return false end

    return true
    """
    return bool(rt.execute(script))


LEVEL1_CASES: list[tuple[str, Callable[[LuaRuntime], bool]]] = [
    ("action_and_condition", test_action_and_condition),
    ("sequence_all_success", test_sequence_all_success),
    ("sequence_short_circuit_failure", test_sequence_short_circuit_failure),
    ("sequence_resumes_running_child", test_sequence_resumes_running_child),
    ("selector_first_success", test_selector_first_success),
    ("selector_all_failure", test_selector_all_failure),
    ("selector_resumes_running_child", test_selector_resumes_running_child),
]


# ── LEVEL 2 TESTS: Blackboard & Decorators ──
def test_blackboard_get_set(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local bb = BT.Blackboard.new()
    if bb:get("missing", 42) ~= 42 then return false end
    if bb:get("missing") ~= nil then return false end

    bb:set("mana", 100)
    if bb:get("mana") ~= 100 then return false end

    bb:set("target", { x = 10, y = 20 })
    local t = bb:get("target")
    if not t or t.x ~= 10 or t.y ~= 20 then return false end

    return true
    """
    return bool(rt.execute(script))


def test_blackboard_watchers(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local bb = BT.Blackboard.new()
    local log = {}

    bb:watch("hp", function(k, new_v, old_v)
        table.insert(log, { k = k, new_v = new_v, old_v = old_v })
    end)

    bb:set("hp", 100)
    bb:set("hp", 80)
    bb:set("hp", 80)

    if #log ~= 2 then return false end
    if log[1].new_v ~= 100 or log[1].old_v ~= nil then return false end
    if log[2].new_v ~= 80 or log[2].old_v ~= 100 then return false end

    return true
    """
    return bool(rt.execute(script))


def test_inverter_decorator(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local inv1 = BT.Inverter(BT.Action(function() return BT.SUCCESS end))
    local inv2 = BT.Inverter(BT.Action(function() return BT.FAILURE end))
    local inv3 = BT.Inverter(BT.Action(function() return BT.RUNNING end))

    if inv1:tick({}) ~= BT.FAILURE then return false end
    if inv2:tick({}) ~= BT.SUCCESS then return false end
    if inv3:tick({}) ~= BT.RUNNING then return false end

    return true
    """
    return bool(rt.execute(script))


def test_cooldown_decorator(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local calls = 0
    local cd = BT.Cooldown(BT.Action(function()
        calls = calls + 1
        return BT.SUCCESS
    end), 2)

    if cd:tick({}) ~= BT.SUCCESS or calls ~= 1 then return false end
    if cd:tick({}) ~= BT.FAILURE or calls ~= 1 then return false end
    if cd:tick({}) ~= BT.FAILURE or calls ~= 1 then return false end
    if cd:tick({}) ~= BT.SUCCESS or calls ~= 2 then return false end

    return true
    """
    return bool(rt.execute(script))


def test_composite_ai_tree(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local bb = BT.Blackboard.new()
    bb:set("ammo", 0)

    local tree = BT.Selector({
        BT.Sequence({
            BT.Condition(function(ctx) return ctx.bb:get("ammo", 0) > 0 end),
            BT.Action(function(ctx)
                local a = ctx.bb:get("ammo")
                ctx.bb:set("ammo", a - 1)
                return BT.SUCCESS
            end),
        }),
        BT.Action(function(ctx)
            ctx.bb:set("ammo", 5)
            return BT.SUCCESS
        end)
    })

    local r1 = tree:tick({ bb = bb })
    if r1 ~= BT.SUCCESS or bb:get("ammo") ~= 5 then return false end

    local r2 = tree:tick({ bb = bb })
    if r2 ~= BT.SUCCESS or bb:get("ammo") ~= 4 then return false end

    return true
    """
    return bool(rt.execute(script))


LEVEL2_CASES: list[tuple[str, Callable[[LuaRuntime], bool]]] = [
    ("blackboard_get_set", test_blackboard_get_set),
    ("blackboard_watchers", test_blackboard_watchers),
    ("inverter_decorator", test_inverter_decorator),
    ("cooldown_decorator", test_cooldown_decorator),
    ("composite_ai_tree", test_composite_ai_tree),
]


# ── LEVEL 3 TESTS: Coroutine Async Action & Reset ──
def test_async_action_wait_ticks(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local finished = false
    local spell = BT.AsyncAction(function(ctx)
        coroutine.yield("WAIT_TICKS", 2)
        finished = true
        return BT.SUCCESS
    end)

    if spell:tick({}) ~= BT.RUNNING then return false end
    if finished then return false end

    if spell:tick({}) ~= BT.RUNNING then return false end
    if finished then return false end

    if spell:tick({}) ~= BT.SUCCESS then return false end
    if not finished then return false end

    return true
    """
    return bool(rt.execute(script))


def test_async_action_state_mutation(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local build_progress = 0
    local builder = BT.AsyncAction(function(ctx)
        for i = 1, 3 do
            build_progress = build_progress + 30
            coroutine.yield("WAIT_TICKS", 1)
        end
        build_progress = 100
        return BT.SUCCESS
    end)

    local ctx = {}
    if builder:tick(ctx) ~= BT.RUNNING or build_progress ~= 30 then return false end
    if builder:tick(ctx) ~= BT.RUNNING or build_progress ~= 60 then return false end
    if builder:tick(ctx) ~= BT.RUNNING or build_progress ~= 90 then return false end
    if builder:tick(ctx) ~= BT.SUCCESS or build_progress ~= 100 then return false end

    return true
    """
    return bool(rt.execute(script))


def test_tree_reset_interrupt(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local steps = 0
    local async_task = BT.AsyncAction(function(ctx)
        steps = steps + 1
        coroutine.yield("WAIT_TICKS", 5)
        steps = steps + 100
        return BT.SUCCESS
    end)

    local seq = BT.Sequence({ async_task })

    if seq:tick({}) ~= BT.RUNNING then return false end
    if steps ~= 1 then return false end

    seq:reset()

    if seq:tick({}) ~= BT.RUNNING then return false end
    if steps ~= 2 then return false end

    return true
    """
    return bool(rt.execute(script))


def test_full_npc_game_loop(rt: LuaRuntime) -> bool:
    script = """
    local BT = BT
    local bb = BT.Blackboard.new()
    bb:set("enemy_spotted", false)
    bb:set("attack_performed", 0)

    local patrol_ticks = 0

    local npc_tree = BT.Selector({
        BT.Sequence({
            BT.Condition(function(ctx) return ctx.bb:get("enemy_spotted") == true end),
            BT.Cooldown(
                BT.AsyncAction(function(ctx)
                    coroutine.yield("WAIT_TICKS", 1)
                    local count = ctx.bb:get("attack_performed")
                    ctx.bb:set("attack_performed", count + 1)
                    return BT.SUCCESS
                end),
                2
            )
        }),
        BT.Action(function(ctx)
            patrol_ticks = patrol_ticks + 1
            return BT.SUCCESS
        end)
    })

    local ctx = { bb = bb }

    if npc_tree:tick(ctx) ~= BT.SUCCESS or patrol_ticks ~= 1 then return false end
    if npc_tree:tick(ctx) ~= BT.SUCCESS or patrol_ticks ~= 2 then return false end

    bb:set("enemy_spotted", true)

    if npc_tree:tick(ctx) ~= BT.RUNNING then return false end
    if bb:get("attack_performed") ~= 0 then return false end

    if npc_tree:tick(ctx) ~= BT.SUCCESS then return false end
    if bb:get("attack_performed") ~= 1 then return false end

    return true
    """
    return bool(rt.execute(script))


LEVEL3_CASES: list[tuple[str, Callable[[LuaRuntime], bool]]] = [
    ("async_action_wait_ticks", test_async_action_wait_ticks),
    ("async_action_state_mutation", test_async_action_state_mutation),
    ("tree_reset_interrupt", test_tree_reset_interrupt),
    ("full_npc_game_loop", test_full_npc_game_loop),
]


def run_lua_suite(cases: list[tuple[str, Callable[[LuaRuntime], bool]]], lua_path: Path) -> tuple[int, int, list[str]]:
    if not lua_path.exists():
        return 0, len(cases), [f"File {lua_path} not found"]

    try:
        solution_lua = lua_path.read_text(encoding="utf-8")
    except Exception as e:
        return 0, len(cases), [f"Error reading file {lua_path}: {e}"]

    rt = _create_sandbox()
    try:
        _load_solution(rt, solution_lua)
    except LuaError as e:
        return 0, len(cases), [f"Lua syntax error: {e}"]

    passed = 0
    failures: list[str] = []
    for test_name, test_fn in cases:
        try:
            test_rt = _create_sandbox()
            _load_solution(test_rt, solution_lua)
            ok = test_fn(test_rt)
            if ok:
                passed += 1
            else:
                failures.append(f"{test_name}: assertion returned false")
        except Exception as e:
            failures.append(f"{test_name}: exception {e}")

    return passed, len(cases), failures


class LuaGameAIBenchmark(Benchmark):
    id = "lua_game_ai"
    name = "Lua: Game AI (Behavior Trees & Coroutines)"
    short = "Lua BT"
    file_ext = "lua"
    code_lang = "lua"
    levels = [
        Level(id="level1", name="Level 1 (Core Behavior Tree)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (Blackboard & Decorators)", prompt=LEVEL2_PROMPT, requires="level1"),
        Level(id="level3", name="Level 3 (Async Coroutines & Reset)", prompt=LEVEL3_PROMPT, requires="level2"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        if level_id == "level1":
            cases = LEVEL1_CASES
        elif level_id == "level2":
            cases = LEVEL1_CASES + LEVEL2_CASES
        else:
            cases = LEVEL1_CASES + LEVEL2_CASES + LEVEL3_CASES

        passed, total, failures = run_lua_suite(cases, answer_path)
        return TestResult(passed, total, failures)
