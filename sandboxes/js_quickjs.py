"""JavaScript Sandbox powered by QuickJS.

Provides a safe execution environment with virtual timers and polyfills:
- Virtual timer (setTimeout/clearTimeout) for deterministic, zero-latency async testing.
- AbortController and AbortSignal polyfills.
- Configurable QuickJS memory and execution limits.
"""

import quickjs

PRELUDE = """
// Virtual timer system for deterministic, zero-latency async testing
const __timers = [];
let __currentTime = 0;
// Monotonic id source: ids must stay unique after fired timers are removed from the queue.
let __timerSeq = 0;

function setTimeout(fn, delay = 0, ...args) {
    const id = ++__timerSeq;
    __timers.push({
        id,
        fn,
        time: __currentTime + Math.max(0, Number(delay) || 0),
        args,
        cancelled: false
    });
    __timers.sort((a, b) => a.time - b.time);
    return id;
}

function clearTimeout(id) {
    const t = __timers.find(x => x.id === id);
    if (t) t.cancelled = true;
}

function __advanceNextTimer() {
    while (__timers.length > 0) {
        const t = __timers.shift();
        if (!t.cancelled) {
            __currentTime = t.time;
            t.fn(...t.args);
            return true;
        }
    }
    return false;
}

// Standard AbortController / AbortSignal polyfill for QuickJS
class AbortSignal {
    constructor() {
        this.aborted = false;
        this.reason = undefined;
        this._listeners = [];
    }
    addEventListener(event, fn) {
        if (event === 'abort') {
            if (this.aborted) {
                fn();
            } else {
                this._listeners.push(fn);
            }
        }
    }
    removeEventListener(event, fn) {
        if (event === 'abort') {
            this._listeners = this._listeners.filter(f => f !== fn);
        }
    }
}

class AbortController {
    constructor() {
        this.signal = new AbortSignal();
    }
    abort(reason = new Error("Aborted")) {
        if (!this.signal.aborted) {
            this.signal.aborted = true;
            this.signal.reason = reason;
            for (const fn of this.signal._listeners) {
                try { fn(); } catch (_) {}
            }
        }
    }
}
"""


def create_js_context(solution_js: str, time_limit: int = 5, memory_limit_mb: int = 64) -> quickjs.Context:
    """Creates an isolated QuickJS context with embedded polyfills and solution code."""
    ctx = quickjs.Context()
    ctx.set_time_limit(time_limit)
    ctx.set_memory_limit(memory_limit_mb * 1024 * 1024)
    ctx.eval(PRELUDE)
    ctx.eval(solution_js)
    return ctx


def drain_js_jobs(ctx: quickjs.Context, max_steps: int = 1000) -> None:
    """Processes microtask and virtual timer queues until completion."""
    for _ in range(max_steps):
        while ctx.execute_pending_job():
            pass
        if not ctx.eval("__timers.length > 0"):
            break
        ctx.eval("__advanceNextTimer()")
