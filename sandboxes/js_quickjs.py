"""JavaScript Sandbox powered by QuickJS.

QuickJS is a bare ECMAScript engine: it ships none of the host APIs that solutions written for Node.js or
a browser take for granted. This module provides a deterministic environment on top of it:
- Virtual clock: setTimeout/setInterval/setImmediate fire instantly in timestamp order, and
  Date.now()/performance.now() follow the same virtual time.
- Standards-conformant EventTarget, Event, DOMException, AbortController and AbortSignal
  (including AbortSignal.abort/timeout/any and throwIfAborted).
- console (captured, never printed), queueMicrotask, structuredClone, a CommonJS-style
  `module`/`exports` stub and a minimal `process`.
- Small ES2022+ built-ins QuickJS lacks (Array#at, Object.hasOwn, findLast, toSorted, ...).
- Configurable QuickJS memory and execution limits.

Polyfill classes live inside an IIFE so they never become global lexical bindings: a solution that
declares its own `class EventTarget` or `const console` must not hit a redeclaration SyntaxError.
"""

import quickjs

PRELUDE = """
(function () {
    const g = globalThis;

    function define(target, name, value, enumerable = false) {
        Object.defineProperty(target, name, {
            value,
            writable: true,
            configurable: true,
            enumerable,
        });
    }

    // ── Virtual timer system for deterministic, zero-latency async testing ──
    const timerQueue = [];
    let currentTime = 0;
    // Monotonic id source: ids must stay unique after fired timers are removed from the queue.
    let timerSeq = 0;
    // Ids cancelled while their callback is running (an interval that clears itself).
    const cancelledIds = new Set();

    function schedule(fn, delay, args, interval) {
        const id = ++timerSeq;
        timerQueue.push({
            id,
            fn,
            time: currentTime + Math.max(0, Number(delay) || 0),
            args,
            interval,
            cancelled: false,
        });
        // Array#sort is stable, so timers due at the same instant fire in creation order.
        timerQueue.sort((a, b) => a.time - b.time);
        return id;
    }

    function setTimeout(fn, delay = 0, ...args) {
        return schedule(fn, delay, args, null);
    }

    function setInterval(fn, delay = 0, ...args) {
        return schedule(fn, delay, args, Math.max(1, Number(delay) || 0));
    }

    function setImmediate(fn, ...args) {
        return schedule(fn, 0, args, null);
    }

    function clearTimeout(id) {
        const t = timerQueue.find((x) => x.id === id);
        if (t) t.cancelled = true;
        cancelledIds.add(id);
    }

    const clearInterval = clearTimeout;
    const clearImmediate = clearTimeout;

    function advanceNextTimer() {
        while (timerQueue.length > 0) {
            const t = timerQueue.shift();
            if (!t.cancelled) {
                currentTime = t.time;
                cancelledIds.delete(t.id);
                try {
                    t.fn(...t.args);
                } catch (err) {
                    if (typeof g.console !== 'undefined' && g.console.error) {
                        try { g.console.error(err); } catch (_) {}
                    }
                } finally {
                    if (t.interval !== null && !cancelledIds.has(t.id)) {
                        t.time = currentTime + t.interval;
                        timerQueue.push(t);
                        timerQueue.sort((a, b) => a.time - b.time);
                    }
                }
                return true;
            }
        }
        return false;
    }

    define(g, 'setTimeout', setTimeout, true);
    define(g, 'setInterval', setInterval, true);
    define(g, 'setImmediate', setImmediate, true);
    define(g, 'clearTimeout', clearTimeout, true);
    define(g, 'clearInterval', clearInterval, true);
    define(g, 'clearImmediate', clearImmediate, true);

    define(g, '__hasPendingTimers', () => timerQueue.length > 0);
    define(g, '__advanceNextTimer', advanceNextTimer);
    Object.defineProperty(g, '__currentTime', {
        get: () => currentTime,
        set: (v) => { currentTime = v; },
        configurable: true,
        enumerable: false,
    });
    Object.defineProperty(g, '__timers', {
        get: () => timerQueue,
        set: () => {},
        configurable: true,
        enumerable: false,
    });

    // ── ES2022+ built-ins missing from QuickJS ──
    const toIndex = (i, len) => { i = Math.trunc(Number(i)) || 0; return i < 0 ? len + i : i; };
    define(Array.prototype, 'at', function (i) { const k = toIndex(i, this.length); return this[k]; });
    define(String.prototype, 'at', function (i) { const k = toIndex(i, this.length); return k >= 0 && k < this.length ? this[k] : undefined; });
    define(Object, 'hasOwn', function (o, k) { return Object.prototype.hasOwnProperty.call(o, k); }, true);
    define(Array.prototype, 'findLast', function (fn, thisArg) {
        for (let i = this.length - 1; i >= 0; i--) if (fn.call(thisArg, this[i], i, this)) return this[i];
        return undefined;
    });
    define(Array.prototype, 'findLastIndex', function (fn, thisArg) {
        for (let i = this.length - 1; i >= 0; i--) if (fn.call(thisArg, this[i], i, this)) return i;
        return -1;
    });
    define(Array.prototype, 'toSorted', function (cmp) { return this.slice().sort(cmp); });
    define(Array.prototype, 'toReversed', function () { return this.slice().reverse(); });
    define(Promise, 'withResolvers', function () {
        let resolve, reject;
        const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
        return { promise, resolve, reject };
    }, true);
    define(g, 'WeakRef', class WeakRef {
        constructor(target) { this._t = target; }
        deref() { return this._t; }
    }, true);
    define(g, 'FinalizationRegistry', class FinalizationRegistry {
        register() {}
        unregister() { return false; }
    }, true);
    define(g, 'globalThis', g, true);

    // ── Virtual clock for Date.now() / performance.now() / new Date() ──
    const EPOCH = 1700000000000;
    const OrigDate = Date;
    function CustomDate(...args) {
        if (!new.target) return new OrigDate(CustomDate.now()).toString();
        if (args.length === 0) return new OrigDate(CustomDate.now());
        return new OrigDate(...args);
    }
    CustomDate.prototype = OrigDate.prototype;
    CustomDate.now = () => EPOCH + currentTime;
    CustomDate.parse = OrigDate.parse;
    CustomDate.UTC = OrigDate.UTC;
    define(g, 'Date', CustomDate, true);

    define(g, 'performance', { now: () => currentTime, timeOrigin: EPOCH }, true);
    define(g, 'queueMicrotask', function (fn) {
        if (typeof fn !== 'function') {
            throw new TypeError('The argument to queueMicrotask must be a function');
        }
        Promise.resolve().then(fn);
    }, true);

    // ── console (captured, never printed) ──
    const consoleLog = [];
    const record = (level) => (...args) => {
        if (consoleLog.length < 500) {
            consoleLog.push(level + ': ' + args.map((a) => { try { return String(a); } catch (_) { return '[unprintable]'; } }).join(' '));
        }
    };
    define(g, 'console', {
        log: record('log'), info: record('info'), warn: record('warn'), error: record('error'),
        debug: record('debug'), trace: record('trace'), dir: record('dir'), table: record('table'),
        group() {}, groupEnd() {}, time() {}, timeEnd() {}, assert() {}, count() {},
    }, true);
    define(g, '__consoleLog', consoleLog);

    // ── CommonJS / Node stubs ──
    define(g, 'module', { exports: {} }, true);
    define(g, 'exports', g.module.exports, true);
    define(g, 'process', {
        env: {},
        platform: 'quickjs',
        argv: [],
        nextTick: (fn, ...args) => { Promise.resolve().then(() => fn(...args)); },
        hrtime: Object.assign(() => [Math.floor(currentTime / 1000), (currentTime % 1000) * 1e6], {
            bigint: () => BigInt(Math.round(currentTime * 1e6)),
        }),
    }, true);

    // ── structuredClone ──
    class DOMException extends Error {
        constructor(message = '', name = 'Error') {
            super(message);
            Object.defineProperty(this, 'name', { value: name, writable: true, configurable: true });
            const codes = {
                IndexSizeError: 1, NotFoundError: 8, NotSupportedError: 9, InvalidStateError: 11,
                SyntaxError: 12, InvalidAccessError: 15, TimeoutError: 23, DataCloneError: 25, AbortError: 20,
            };
            this.code = codes[name] || 0;
        }
    }
    define(g, 'DOMException', DOMException, true);

    define(g, 'structuredClone', function structuredClone(value) {
        const seen = new Map();
        const clone = (v) => {
            if (v === null || (typeof v !== 'object' && typeof v !== 'function')) {
                if (typeof v === 'symbol') throw new DOMException('Symbol could not be cloned.', 'DataCloneError');
                return v;
            }
            if (typeof v === 'function') throw new DOMException(String(v) + ' could not be cloned.', 'DataCloneError');
            if (seen.has(v)) return seen.get(v);
            let out;
            if (Array.isArray(v)) {
                out = []; seen.set(v, out);
                for (let i = 0; i < v.length; i++) out[i] = clone(v[i]);
            } else if (v instanceof Date) {
                out = new CustomDate(v.getTime()); seen.set(v, out);
            } else if (v instanceof Map) {
                out = new Map(); seen.set(v, out);
                for (const [k, x] of v) out.set(clone(k), clone(x));
            } else if (v instanceof Set) {
                out = new Set(); seen.set(v, out);
                for (const x of v) out.add(clone(x));
            } else if (v instanceof RegExp) {
                out = new RegExp(v.source, v.flags); seen.set(v, out);
            } else if (v instanceof Error) {
                out = new Error(v.message); out.name = v.name; seen.set(v, out);
            } else {
                out = {}; seen.set(v, out);
                for (const k of Object.keys(v)) out[k] = clone(v[k]);
            }
            return out;
        };
        return clone(value);
    }, true);

    // ── EventTarget / Event ──
    class Event {
        constructor(type, init = {}) {
            this.type = String(type);
            this.target = null;
            this.currentTarget = null;
            this.cancelable = !!init.cancelable;
            this.bubbles = !!init.bubbles;
            this.defaultPrevented = false;
            this.timeStamp = currentTime;
            Object.defineProperty(this, '_stop', { value: false, writable: true });
        }
        preventDefault() { if (this.cancelable) this.defaultPrevented = true; }
        stopPropagation() {}
        stopImmediatePropagation() { this._stop = true; }
    }
    define(g, 'Event', Event, true);

    class EventTarget {
        constructor() {
            Object.defineProperty(this, '_listeners', { value: {}, writable: true });
        }
        addEventListener(type, fn, options) {
            if (!fn) return;
            const once = typeof options === 'object' && options !== null && !!options.once;
            const list = this._listeners[type] || (this._listeners[type] = []);
            if (list.some((e) => e.fn === fn)) return;
            list.push({ fn, once });
        }
        removeEventListener(type, fn) {
            const list = this._listeners[type];
            if (list) this._listeners[type] = list.filter((e) => e.fn !== fn);
        }
        dispatchEvent(event) {
            event.target = this;
            event.currentTarget = this;
            const onHandler = this['on' + event.type];
            if (typeof onHandler === 'function') {
                try { onHandler.call(this, event); } catch (_) {}
            }
            for (const entry of (this._listeners[event.type] || []).slice()) {
                if (entry.once) this.removeEventListener(event.type, entry.fn);
                try {
                    if (typeof entry.fn === 'function') entry.fn.call(this, event);
                    else if (entry.fn && typeof entry.fn.handleEvent === 'function') entry.fn.handleEvent(event);
                } catch (_) { /* a throwing listener must not stop the others */ }
                if (event._stop) break;
            }
            return !event.defaultPrevented;
        }
    }
    define(g, 'EventTarget', EventTarget, true);

    // ── AbortSignal / AbortController (WHATWG semantics) ──
    const KEY = Symbol('AbortSignal.create');

    function createAbortError() {
        return new DOMException('This operation was aborted', 'AbortError');
    }

    function abortSignal(signal, reason) {
        if (signal.aborted) return;
        signal.aborted = true;
        signal.reason = reason === undefined ? createAbortError() : reason;
        const event = new Event('abort');
        signal.dispatchEvent(event);
    }

    class AbortSignal extends EventTarget {
        constructor(key) {
            if (key !== KEY) throw new TypeError('Illegal constructor');
            super();
            this.aborted = false;
            this.reason = undefined;
            this._onabort = null;
        }
        get onabort() {
            return this._onabort;
        }
        set onabort(fn) {
            this._onabort = typeof fn === 'function' ? fn : null;
        }
        throwIfAborted() {
            if (this.aborted) throw this.reason;
        }
        static abort(reason) {
            const signal = new AbortSignal(KEY);
            abortSignal(signal, reason);
            return signal;
        }
        static timeout(ms) {
            const signal = new AbortSignal(KEY);
            const delay = Math.max(0, Number(ms) || 0);
            setTimeout(() => {
                abortSignal(signal, new DOMException('The operation was aborted due to timeout', 'TimeoutError'));
            }, delay);
            return signal;
        }
        static any(signals) {
            const signal = new AbortSignal(KEY);
            for (const s of signals) {
                if (s && s.aborted) {
                    abortSignal(signal, s.reason);
                    return signal;
                }
            }
            for (const s of signals) {
                if (s && typeof s.addEventListener === 'function') {
                    s.addEventListener('abort', () => abortSignal(signal, s.reason), { once: true });
                }
            }
            return signal;
        }
    }
    define(g, 'AbortSignal', AbortSignal, true);

    class AbortController {
        constructor() {
            this.signal = new AbortSignal(KEY);
        }
        abort(reason) {
            abortSignal(this.signal, reason);
        }
    }
    define(g, 'AbortController', AbortController, true);
})();
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
        while True:
            try:
                if not ctx.execute_pending_job():
                    break
            except Exception:
                pass
        try:
            has_pending = bool(
                ctx.eval(
                    "Boolean(globalThis.__hasPendingTimers ? globalThis.__hasPendingTimers() : (globalThis.__timers && globalThis.__timers.length > 0))"
                )
            )
        except Exception:
            break
        if not has_pending:
            break
        try:
            advanced = bool(ctx.eval("Boolean(globalThis.__advanceNextTimer && globalThis.__advanceNextTimer())"))
            if not advanced:
                break
        except Exception:
            break
