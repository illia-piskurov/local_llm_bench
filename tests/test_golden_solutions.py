"""Golden and negative regression tests for benchmark evaluators."""

import pytest

from benchmarks import REGISTRY
from benchmarks.c_framing import CFramingBenchmark
from benchmarks.js_async import JSAsyncBenchmark
from benchmarks.kv import KVBenchmark
from benchmarks.lua_game_ai import LuaGameAIBenchmark
from benchmarks.priority_scheduler import PrioritySchedulerBenchmark
from benchmarks.scheduler import SchedulerBenchmark
from benchmarks.sql import SQLBenchmark
from benchmarks.vm import VMBenchmark

SCHEDULER_SOLUTION = """
def topo_sort(tasks):
    indegree = {name: len(deps) for name, deps in tasks.items()}
    dependents = {name: [] for name in tasks}
    for name, deps in tasks.items():
        for dep in deps:
            if dep not in tasks:
                return None
            dependents[dep].append(name)
    ready = sorted(name for name in tasks if indegree[name] == 0)
    result = []
    while ready:
        name = ready.pop(0)
        result.append(name)
        for child in dependents[name]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
        ready.sort()
    return result if len(result) == len(tasks) else None


def critical_path(tasks):
    visiting = set()
    memo = {}

    def visit(name):
        if name in visiting:
            return None
        if name in memo:
            return memo[name]
        if name not in tasks:
            return None
        visiting.add(name)
        duration, deps = tasks[name]
        longest = 0
        for dep in deps:
            value = visit(dep)
            if value is None:
                return None
            longest = max(longest, value)
        visiting.remove(name)
        memo[name] = duration + longest
        return memo[name]

    values = []
    for name in tasks:
        value = visit(name)
        if value is None:
            return None
        values.append(value)
    return max(values) if values else 0
"""


PRIORITY_SCHEDULER_SOLUTION = """
def _key(name, tasks):
    duration, deps, priority = tasks[name]
    return (-priority, duration, name)


def _schedule(tasks, workers):
    if workers <= 0:
        return None
    indegree = {name: len(spec[1]) for name, spec in tasks.items()}
    dependents = {name: [] for name in tasks}
    for name, spec in tasks.items():
        for dep in spec[1]:
            if dep not in tasks:
                return None
            dependents[dep].append(name)

    ready = [name for name in tasks if indegree[name] == 0]
    running = []
    started = []
    time = 0
    latest_end = 0
    while len(started) < len(tasks):
        ready.sort(key=lambda name: _key(name, tasks))
        while ready and len(running) < workers:
            name = ready.pop(0)
            started.append(name)
            end = time + tasks[name][0]
            latest_end = max(latest_end, end)
            running.append((end, name))
        if not running:
            return None
        time = min(end for end, name in running)
        finished = [name for end, name in running if end == time]
        running = [(end, name) for end, name in running if end != time]
        for name in finished:
            for child in dependents[name]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
    return started, latest_end


def plan_order(tasks, workers):
    result = _schedule(tasks, workers)
    return None if result is None else result[0]


def makespan(tasks, workers):
    result = _schedule(tasks, workers)
    return None if result is None else result[1]


def critical_path(tasks):
    visiting = set()
    memo = {}

    def visit(name):
        if name in visiting or name not in tasks:
            return None
        if name in memo:
            return memo[name]
        visiting.add(name)
        duration, deps, priority = tasks[name]
        longest = 0
        for dep in deps:
            value = visit(dep)
            if value is None:
                return None
            longest = max(longest, value)
        visiting.remove(name)
        memo[name] = duration + longest
        return memo[name]

    values = []
    for name in tasks:
        value = visit(name)
        if value is None:
            return None
        values.append(value)
    return max(values) if values else 0
"""


C_FRAMING_SOLUTION = r"""
#include <stdint.h>

#define BUFFER_SIZE 512

static uint8_t buffer[BUFFER_SIZE];
static int head;
static int count;

void ringbuf_init(void) {
    head = 0;
    count = 0;
}

int ringbuf_push(uint8_t byte) {
    if (count == BUFFER_SIZE) return -1;
    buffer[(head + count) % BUFFER_SIZE] = byte;
    count++;
    return 0;
}

int ringbuf_pop(void) {
    int value;
    if (count == 0) return -1;
    value = buffer[head];
    head = (head + 1) % BUFFER_SIZE;
    count--;
    return value;
}

int ringbuf_available(void) { return count; }
int ringbuf_free_space(void) { return BUFFER_SIZE - count; }

static int packet_at(const uint8_t *data, int available, uint8_t *payload, int *out_type) {
    int length;
    int i;
    uint8_t checksum = 0;
    if (available < 4 || data[0] != 0xAA) return -1;
    length = data[2];
    if (available < length + 4) return -1;
    for (i = 0; i < length; i++) checksum ^= data[3 + i];
    if (checksum != data[3 + length]) return -1;
    for (i = 0; i < length; i++) payload[i] = data[3 + i];
    *out_type = data[1];
    return length;
}

int decode_packet(const uint8_t *stream, int stream_len, uint8_t *out_payload, int *out_type) {
    int i;
    int result;
    for (i = 0; i < stream_len; i++) {
        if (stream[i] != 0xAA) continue;
        result = packet_at(stream + i, stream_len - i, out_payload, out_type);
        if (result >= 0) return result;
    }
    return -1;
}

void feed_bytes(const uint8_t *data, int length) {
    int i;
    for (i = 0; i < length; i++) ringbuf_push(data[i]);
}

static uint8_t peek(int offset) {
    return buffer[(head + offset) % BUFFER_SIZE];
}

int get_next_packet(uint8_t *out_payload, int *out_type) {
    int length;
    int total;
    int i;
    uint8_t checksum;
    while (count > 0) {
        if (peek(0) != 0xAA) {
            ringbuf_pop();
            continue;
        }
        if (count < 3) return -1;
        length = peek(2);
        total = length + 4;
        if (count < total) return -1;
        checksum = 0;
        for (i = 0; i < length; i++) checksum ^= peek(3 + i);
        if (checksum != peek(3 + length)) {
            ringbuf_pop();
            continue;
        }
        *out_type = peek(1);
        for (i = 0; i < length; i++) out_payload[i] = peek(3 + i);
        for (i = 0; i < total; i++) ringbuf_pop();
        return length;
    }
    return -1;
}
"""


LUA_GAME_AI_SOLUTION = r"""
BT = {}
BT.SUCCESS = "SUCCESS"
BT.FAILURE = "FAILURE"
BT.RUNNING = "RUNNING"

local function normalize(value)
    if value == true or value == BT.SUCCESS then return BT.SUCCESS end
    if value == false or value == BT.FAILURE then return BT.FAILURE end
    return value
end

function BT.Action(fn)
    local node = {}
    function node:tick(ctx)
        return normalize(fn(ctx))
    end
    function node:reset() end
    return node
end

function BT.Condition(predicate)
    local node = {}
    function node:tick(ctx)
        return predicate(ctx) and BT.SUCCESS or BT.FAILURE
    end
    function node:reset() end
    return node
end

function BT.Sequence(children)
    local node = { children = children, index = 1 }
    function node:tick(ctx)
        while self.index <= #self.children do
            local result = self.children[self.index]:tick(ctx)
            if result == BT.RUNNING then return BT.RUNNING end
            if result == BT.FAILURE then
                self.index = 1
                return BT.FAILURE
            end
            self.index = self.index + 1
        end
        self.index = 1
        return BT.SUCCESS
    end
    function node:reset()
        self.index = 1
        for _, child in ipairs(self.children) do child:reset() end
    end
    return node
end

function BT.Selector(children)
    local node = { children = children, index = 1 }
    function node:tick(ctx)
        while self.index <= #self.children do
            local result = self.children[self.index]:tick(ctx)
            if result == BT.RUNNING then return BT.RUNNING end
            if result == BT.SUCCESS then
                self.index = 1
                return BT.SUCCESS
            end
            self.index = self.index + 1
        end
        self.index = 1
        return BT.FAILURE
    end
    function node:reset()
        self.index = 1
        for _, child in ipairs(self.children) do child:reset() end
    end
    return node
end

BT.Blackboard = {}
function BT.Blackboard.new()
    local board = { data = {}, watchers = {} }
    function board:get(key, default)
        local value = self.data[key]
        if value == nil then return default end
        return value
    end
    function board:set(key, value)
        local old_value = self.data[key]
        if old_value == value then return end
        self.data[key] = value
        local callbacks = self.watchers[key]
        if callbacks then
            for _, callback in ipairs(callbacks) do callback(key, value, old_value) end
        end
    end
    function board:watch(key, callback)
        if not self.watchers[key] then self.watchers[key] = {} end
        table.insert(self.watchers[key], callback)
    end
    return board
end

function BT.Inverter(child)
    local node = { child = child }
    function node:tick(ctx)
        local result = self.child:tick(ctx)
        if result == BT.SUCCESS then return BT.FAILURE end
        if result == BT.FAILURE then return BT.SUCCESS end
        return result
    end
    function node:reset() self.child:reset() end
    return node
end

function BT.Cooldown(child, ticks)
    local node = { child = child, ticks = ticks, remaining = 0 }
    function node:tick(ctx)
        if self.remaining > 0 then
            self.remaining = self.remaining - 1
            return BT.FAILURE
        end
        local result = self.child:tick(ctx)
        if result == BT.SUCCESS then self.remaining = self.ticks end
        return result
    end
    function node:reset()
        self.remaining = 0
        self.child:reset()
    end
    return node
end

function BT.AsyncAction(fn)
    local node = { fn = fn, coroutine = nil, wait = 0 }
    function node:tick(ctx)
        if self.wait > 0 then
            self.wait = self.wait - 1
            if self.wait > 0 then return BT.RUNNING end
        end
        if self.coroutine == nil then self.coroutine = coroutine.create(self.fn) end
        local ok, value, amount = coroutine.resume(self.coroutine, ctx)
        if not ok then
            self.coroutine = nil
            return BT.FAILURE
        end
        if coroutine.status(self.coroutine) == "dead" then
            self.coroutine = nil
            return normalize(value)
        end
        if value == "WAIT_TICKS" then self.wait = amount or 0 end
        return BT.RUNNING
    end
    function node:reset()
        self.coroutine = nil
        self.wait = 0
    end
    return node
end
"""


JS_ASYNC_SOLUTION = r"""
async function pMap(items, mapper, options) {
    const opts = typeof options === "number" ? { concurrency: options } : (options || {});
    const signal = opts.signal;
    if (signal && signal.aborted) {
        return Promise.reject(signal.reason || new Error("Aborted"));
    }

    if (!items || items.length === 0) {
        return [];
    }

    const concurrency = Math.max(1, Number(opts.concurrency) || 1);
    const retries = Math.max(0, Number(opts.retries) || 0);
    const backoffMs = Math.max(0, Number(opts.backoffMs) || 0);
    const timeoutMs = Math.max(0, Number(opts.timeoutMs) || 0);
    const isSettled = Boolean(opts.settled);

    return new Promise((resolve, reject) => {
        const results = new Array(items.length);
        let nextIndex = 0;
        let completedCount = 0;
        let isDone = false;

        function cleanup() {
            if (signal && onAbort) {
                signal.removeEventListener("abort", onAbort);
            }
        }

        function fail(err) {
            if (isDone) return;
            isDone = true;
            cleanup();
            reject(err);
        }

        const onAbort = () => {
            fail(signal.reason || new Error("Aborted"));
        };

        if (signal) {
            signal.addEventListener("abort", onAbort);
        }

        function sleep(ms) {
            return new Promise((res) => setTimeout(res, ms));
        }

        async function executeWithTimeout(item, index) {
            if (timeoutMs <= 0) {
                return await mapper(item, index);
            }
            return await new Promise((res, rej) => {
                let timer = setTimeout(() => {
                    timer = null;
                    rej(new Error("Timeout"));
                }, timeoutMs);

                Promise.resolve()
                    .then(() => mapper(item, index))
                    .then(
                        (val) => {
                            if (timer !== null) {
                                clearTimeout(timer);
                                timer = null;
                            }
                            res(val);
                        },
                        (err) => {
                            if (timer !== null) {
                                clearTimeout(timer);
                                timer = null;
                            }
                            rej(err);
                        }
                    );
            });
        }

        async function runTask(index) {
            const item = items[index];
            let lastError = null;
            let success = false;
            let value = undefined;

            for (let attempt = 0; attempt <= retries; attempt++) {
                if (isDone) return;
                if (attempt > 0 && backoffMs > 0) {
                    const delay = backoffMs * Math.pow(2, attempt - 1);
                    await sleep(delay);
                    if (isDone) return;
                }

                try {
                    value = await executeWithTimeout(item, index);
                    success = true;
                    break;
                } catch (err) {
                    lastError = err;
                }
            }

            if (isDone) return;

            if (success) {
                results[index] = isSettled ? { status: "fulfilled", value } : value;
            } else {
                if (isSettled) {
                    const reason = (lastError && lastError.message) ? lastError.message : String(lastError);
                    results[index] = { status: "rejected", reason };
                } else {
                    fail(lastError);
                    return;
                }
            }

            completedCount++;
            if (completedCount === items.length) {
                isDone = true;
                cleanup();
                resolve(results);
            }
        }

        async function worker() {
            while (nextIndex < items.length && !isDone) {
                const currentIndex = nextIndex++;
                await runTask(currentIndex);
            }
        }

        const workerCount = Math.min(concurrency, items.length);
        for (let i = 0; i < workerCount; i++) {
            worker();
        }
    });
}
"""


VM_SOLUTION = r"""
def run(program: str) -> list[str]:
    lines = program.splitlines()
    instructions = []
    labels = {}

    for line_no, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        op = parts[0]
        arg = parts[1] if len(parts) > 1 else None
        if op == "LABEL":
            if not arg:
                raise ValueError(f"Line {line_no}: LABEL requires a name")
            labels[arg] = len(instructions)
        instructions.append((op, arg, line_no))

    stack: list[int] = []
    call_stack: list[int] = []
    variables: dict[str, int] = {}
    output: list[str] = []
    ip = 0
    max_steps = 1000000
    steps = 0

    while ip < len(instructions):
        steps += 1
        if steps > max_steps:
            raise RuntimeError("Execution step limit exceeded")

        op, arg, line_no = instructions[ip]

        if op == "LABEL":
            ip += 1
        elif op == "PUSH":
            if arg is None:
                raise ValueError(f"Line {line_no}: PUSH requires an argument")
            stack.append(int(arg))
            ip += 1
        elif op == "POP":
            if not stack:
                raise IndexError(f"Line {line_no}: Stack underflow on POP")
            stack.pop()
            ip += 1
        elif op == "PRINT":
            if not stack:
                raise IndexError(f"Line {line_no}: Stack underflow on PRINT")
            output.append(str(stack[-1]))
            ip += 1
        elif op == "DUP":
            if not stack:
                raise IndexError(f"Line {line_no}: Stack underflow on DUP")
            stack.append(stack[-1])
            ip += 1
        elif op == "SWAP":
            if len(stack) < 2:
                raise IndexError(f"Line {line_no}: Stack underflow on SWAP")
            stack[-1], stack[-2] = stack[-2], stack[-1]
            ip += 1
        elif op in ("ADD", "SUB", "MUL", "DIV", "EQ", "GT", "LT"):
            if len(stack) < 2:
                raise IndexError(f"Line {line_no}: Stack underflow on {op}")
            b = stack.pop()
            a = stack.pop()
            if op == "ADD":
                stack.append(a + b)
            elif op == "SUB":
                stack.append(a - b)
            elif op == "MUL":
                stack.append(a * b)
            elif op == "DIV":
                if b == 0:
                    raise ZeroDivisionError(f"Line {line_no}: Division by zero")
                stack.append(int(a / b))
            elif op == "EQ":
                stack.append(1 if a == b else 0)
            elif op == "GT":
                stack.append(1 if a > b else 0)
            elif op == "LT":
                stack.append(1 if a < b else 0)
            ip += 1
        elif op == "JMP":
            if arg not in labels:
                raise KeyError(f"Line {line_no}: Undefined label {arg}")
            ip = labels[arg]
        elif op == "JZ":
            if not stack:
                raise IndexError(f"Line {line_no}: Stack underflow on JZ")
            if arg not in labels:
                raise KeyError(f"Line {line_no}: Undefined label {arg}")
            val = stack.pop()
            if val == 0:
                ip = labels[arg]
            else:
                ip += 1
        elif op == "JNZ":
            if not stack:
                raise IndexError(f"Line {line_no}: Stack underflow on JNZ")
            if arg not in labels:
                raise KeyError(f"Line {line_no}: Undefined label {arg}")
            val = stack.pop()
            if val != 0:
                ip = labels[arg]
            else:
                ip += 1
        elif op == "CALL":
            if arg not in labels:
                raise KeyError(f"Line {line_no}: Undefined label {arg}")
            call_stack.append(ip + 1)
            ip = labels[arg]
        elif op == "RET":
            if not call_stack:
                raise IndexError(f"Line {line_no}: Call stack underflow on RET")
            ip = call_stack.pop()
        elif op == "STORE":
            if not stack:
                raise IndexError(f"Line {line_no}: Stack underflow on STORE")
            variables[arg] = stack.pop()
            ip += 1
        elif op == "LOAD":
            if arg not in variables:
                raise KeyError(f"Line {line_no}: Undefined variable {arg}")
            stack.append(variables[arg])
            ip += 1
        else:
            raise ValueError(f"Line {line_no}: Unknown instruction {op}")

    return output
"""


KV_SOLUTION = r"""
def run(program: str) -> list[str]:
    global_store = {}
    transactions = []
    watched_keys = set()
    snapshots = {}
    output = []

    def get_val(key: str) -> str | None:
        for tx in reversed(transactions):
            if key in tx:
                return tx[key]
        return global_store.get(key)

    for raw_line in program.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        cmd = parts[0]

        if cmd == "SET":
            key, val = parts[1], parts[2]
            old_val = get_val(key) if key in watched_keys else None
            if transactions:
                transactions[-1][key] = val
            else:
                global_store[key] = val
            if key in watched_keys:
                new_val = get_val(key)
                if old_val != new_val:
                    o_str = "NULL" if old_val is None else old_val
                    n_str = "NULL" if new_val is None else new_val
                    output.append(f"WATCH {key} {o_str} -> {n_str}")

        elif cmd == "GET":
            key = parts[1]
            val = get_val(key)
            output.append("NULL" if val is None else val)

        elif cmd == "DELETE":
            key = parts[1]
            old_val = get_val(key) if key in watched_keys else None
            if transactions:
                transactions[-1][key] = None
            else:
                global_store.pop(key, None)
            if key in watched_keys:
                new_val = get_val(key)
                if old_val != new_val:
                    o_str = "NULL" if old_val is None else old_val
                    n_str = "NULL" if new_val is None else new_val
                    output.append(f"WATCH {key} {o_str} -> {n_str}")

        elif cmd == "BEGIN":
            transactions.append({})

        elif cmd == "COMMIT":
            if not transactions:
                output.append("NO TRANSACTION")
            else:
                top = transactions.pop()
                if transactions:
                    transactions[-1].update(top)
                else:
                    for k, v in top.items():
                        if v is None:
                            global_store.pop(k, None)
                        else:
                            global_store[k] = v

        elif cmd == "ROLLBACK":
            if not transactions:
                output.append("NO TRANSACTION")
            else:
                transactions.pop()

        elif cmd == "COUNT":
            target_val = parts[1]
            visible = dict(global_store)
            for tx in transactions:
                for k, v in tx.items():
                    if v is None:
                        visible.pop(k, None)
                    else:
                        visible[k] = v
            c = sum(1 for v in visible.values() if v == target_val)
            output.append(str(c))

        elif cmd == "WATCH":
            key = parts[1]
            watched_keys.add(key)

        elif cmd == "SNAPSHOT":
            name = parts[1]
            snapshots[name] = (
                dict(global_store),
                [dict(tx) for tx in transactions],
                set(watched_keys),
            )

        elif cmd == "RESTORE":
            name = parts[1]
            if name in snapshots:
                g, txs, w = snapshots[name]
                global_store = dict(g)
                transactions = [dict(tx) for tx in txs]
                watched_keys = set(w)

    return output
"""


SQL_SOLUTION = r"""
def compile_query(query: dict) -> dict:
    params = []

    def _compile_cond(cond: dict) -> str:
        if "AND" in cond:
            subs = [_compile_cond(c) for c in cond["AND"]]
            return f"({' AND '.join(subs)})" if len(subs) > 1 else subs[0]
        if "OR" in cond:
            subs = [_compile_cond(c) for c in cond["OR"]]
            return f"({' OR '.join(subs)})" if len(subs) > 1 else subs[0]
        field = cond["field"]
        op = cond.get("op", "=")
        if op == "IS NULL":
            return f"{field} IS NULL"
        if op == "IS NOT NULL":
            return f"{field} IS NOT NULL"
        if op == "IN":
            if "query" in cond:
                sub = _compile_query(cond["query"])
                return f"{field} IN ({sub})"
            vals = cond.get("value", [])
            ph = []
            for v in vals:
                params.append(v)
                ph.append(f"${len(params)}")
            return f"{field} IN ({', '.join(ph)})"
        val = cond.get("value")
        params.append(val)
        return f"{field} {op} ${len(params)}"

    def _compile_query(q: dict) -> str:
        select_items = q.get("select", ["*"])
        select_parts = []
        for item in select_items:
            if isinstance(item, dict):
                select_parts.append(f"{item['expr']} AS {item['as']}")
            else:
                select_parts.append(str(item))
        parts = [f"SELECT {', '.join(select_parts)} FROM {q['table']}"]

        if "joins" in q:
            for j in q["joins"]:
                j_type = j.get("type", "INNER")
                on_str = " AND ".join(f"{k} = {v}" for k, v in j["on"].items())
                parts.append(f"{j_type} JOIN {j['table']} ON {on_str}")

        if "where" in q:
            parts.append(f"WHERE {_compile_cond(q['where'])}")

        if "groupBy" in q:
            parts.append(f"GROUP BY {', '.join(q['groupBy'])}")

        if "having" in q:
            parts.append(f"HAVING {_compile_cond(q['having'])}")

        if "orderBy" in q:
            ob_parts = [f"{ob['field']} {ob.get('dir', 'ASC')}" for ob in q["orderBy"]]
            parts.append(f"ORDER BY {', '.join(ob_parts)}")

        if "limit" in q:
            parts.append(f"LIMIT {q['limit']}")

        if "offset" in q:
            parts.append(f"OFFSET {q['offset']}")

        return " ".join(parts)

    sql = _compile_query(query)
    return {"sql": sql, "params": params}
"""


@pytest.mark.parametrize("benchmark", REGISTRY, ids=lambda benchmark: benchmark.id)
def test_every_benchmark_rejects_an_empty_solution(benchmark, tmp_path):
    answer_path = tmp_path / f"empty.{benchmark.file_ext}"
    answer_path.write_text("", encoding="utf-8")

    result = benchmark.run_tests(benchmark.level_order[0], answer_path)

    assert result.passed == 0
    assert result.total > 0


@pytest.mark.parametrize(
    ("benchmark", "level_id", "source"),
    [
        (SchedulerBenchmark(), "level1", SCHEDULER_SOLUTION),
        (SchedulerBenchmark(), "level2", SCHEDULER_SOLUTION),
        (PrioritySchedulerBenchmark(), "level1", PRIORITY_SCHEDULER_SOLUTION),
        (PrioritySchedulerBenchmark(), "level2", PRIORITY_SCHEDULER_SOLUTION),
        (CFramingBenchmark(), "level1", C_FRAMING_SOLUTION),
        (CFramingBenchmark(), "level2", C_FRAMING_SOLUTION),
        (CFramingBenchmark(), "level3", C_FRAMING_SOLUTION),
        (LuaGameAIBenchmark(), "level1", LUA_GAME_AI_SOLUTION),
        (LuaGameAIBenchmark(), "level2", LUA_GAME_AI_SOLUTION),
        (LuaGameAIBenchmark(), "level3", LUA_GAME_AI_SOLUTION),
        (JSAsyncBenchmark(), "level1", JS_ASYNC_SOLUTION),
        (JSAsyncBenchmark(), "level2", JS_ASYNC_SOLUTION),
        (JSAsyncBenchmark(), "level3", JS_ASYNC_SOLUTION),
        (VMBenchmark(), "level1", VM_SOLUTION),
        (VMBenchmark(), "level2", VM_SOLUTION),
        (VMBenchmark(), "level3", VM_SOLUTION),
        (KVBenchmark(), "level1", KV_SOLUTION),
        (KVBenchmark(), "level2", KV_SOLUTION),
        (KVBenchmark(), "level3", KV_SOLUTION),
        (SQLBenchmark(), "level1", SQL_SOLUTION),
        (SQLBenchmark(), "level2", SQL_SOLUTION),
        (SQLBenchmark(), "level3", SQL_SOLUTION),
    ],
)
def test_golden_solutions_pass_every_case(benchmark, level_id, source, tmp_path):
    answer_path = tmp_path / f"solution.{benchmark.file_ext}"
    answer_path.write_text(source, encoding="utf-8")

    result = benchmark.run_tests(level_id, answer_path)

    assert result.passed == result.total, result.failures
