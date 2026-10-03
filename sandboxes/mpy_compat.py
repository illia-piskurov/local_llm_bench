"""CPython-compatibility shims for the MicroPython WASM sandbox.

Model-generated "Python" solutions are written for CPython, but they run inside MicroPython, whose
standard library is a small subset. Without help, perfectly correct answers score 0 simply because of
``import copy``, ``from typing import ...`` or ``collections.defaultdict`` (and ``deque([x])`` raises a
TypeError because MicroPython's deque demands a ``maxlen``).

This module supplies pure-Python replacements that are injected in front of the solution, and ONLY for
the modules the solution actually imports (found with ``ast`` on the host), so the extra parse/compile
cost in sandbox fuel is paid only when needed.

Shimmed: ``typing``, ``copy``, ``collections`` (``deque``, ``defaultdict``, ``Counter``; ``OrderedDict``
and ``namedtuple`` still come from MicroPython), ``collections.abc``, ``heapq`` (extra functions on top of
the native heap), ``functools``, ``itertools``, ``bisect``, ``abc``.

Known gaps that cannot be papered over (these still fail like they would on real MicroPython):
``dataclasses`` and ``enum`` (need class annotations / metaclasses), ``NamedTuple``, ``random``,
``datetime``, and two runtime quirks: ``dict(d)`` / ``{**d}`` on a *dict subclass* (so on a
``defaultdict`` or ``Counter``) raise TypeError, and dict iteration order is not insertion order.

The shim sources below are written in the MicroPython-compatible subset of Python (no ``__missing__``,
no ``__class_getitem__``, no function attributes, ``super().__init__()`` instead of
``dict.__init__(self)``) and are also executed under CPython in the test-suite, where their behaviour is
compared with the real standard library.
"""

import ast

# ── shared helpers ────────────────────────────────────────────────────────────────────────────

BASE_SOURCE = """
class _MpycModule:
    def __init__(self, name, fallback=None):
        self._fallback = fallback
        self.__name__ = name

    def __getattr__(self, name):
        fb = self._fallback
        if fb is None:
            raise AttributeError(name)
        return getattr(fb, name)


class _MpycAlias:
    def __init__(self, name):
        self._name = name

    def __getitem__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __or__(self, other):
        return self

    def __ror__(self, other):
        return self

    def __repr__(self):
        return 'typing.' + self._name


def _mpyc_module(name, fallback=None):
    return _MpycModule(name, fallback)
"""

# ── typing ────────────────────────────────────────────────────────────────────────────────────

TYPING_SOURCE = """
def _mpyc_install_typing(modules):
    names = (
        'Any Optional Union List Dict Set FrozenSet Tuple Callable Iterable Iterator Sequence Mapping '
        'MutableMapping MutableSequence MutableSet Deque DefaultDict OrderedDict Counter Type Literal Final '
        'ClassVar Hashable Generator Awaitable Coroutine NoReturn Self TypeAlias AnyStr Text Collection '
        'Container Reversible Sized AbstractSet Annotated Never LiteralString AsyncIterator AsyncGenerator'
    ).split()
    mod = _mpyc_module('typing')
    for n in names:
        setattr(mod, n, _MpycAlias(n))

    class _GenericBase:
        pass

    class _GenericFactory:
        def __getitem__(self, item):
            return _GenericBase

    class Protocol(_GenericBase):
        pass

    class TypedDict(dict):
        pass

    def TypeVar(name, *constraints, **kwargs):
        return _MpycAlias(name)

    def NewType(name, tp):
        return lambda x: x

    def cast(tp, value):
        return value

    def _identity(f):
        return f

    mod.Generic = _GenericFactory()
    mod.Protocol = Protocol
    mod.TypedDict = TypedDict
    mod.TypeVar = TypeVar
    mod.ParamSpec = TypeVar
    mod.TypeVarTuple = TypeVar
    mod.NewType = NewType
    mod.cast = cast
    mod.overload = _identity
    mod.final = _identity
    mod.runtime_checkable = _identity
    mod.no_type_check = _identity
    mod.TYPE_CHECKING = False
    modules['typing'] = mod
"""

# ── copy ──────────────────────────────────────────────────────────────────────────────────────

COPY_SOURCE = """
def _mpyc_install_copy(modules):
    atomic = (int, float, bool, str, bytes, type(None), type(len), type(lambda: None), type, range)

    class Error(Exception):
        pass

    def _make_like(x):
        cls = type(x)
        try:
            return cls()
        except TypeError:
            return object.__new__(cls)

    def _slot_names(cls):
        names = getattr(cls, '__slots__', ())
        if isinstance(names, str):
            names = (names,)
        return names

    def _copy_state(src, dst, memo):
        d = getattr(src, '__dict__', None)
        if d is not None:
            for k in list(d.keys()):
                v = d[k]
                setattr(dst, k, v if memo is None else deepcopy(v, memo))
        for k in _slot_names(type(src)):
            if hasattr(src, k):
                v = getattr(src, k)
                setattr(dst, k, v if memo is None else deepcopy(v, memo))

    def _fill(src, dst, memo):
        if isinstance(src, list):
            for e in src:
                dst.append(e if memo is None else deepcopy(e, memo))
        elif isinstance(src, dict):
            for k in src.keys():
                if memo is None:
                    dst[k] = src[k]
                else:
                    dst[deepcopy(k, memo)] = deepcopy(src[k], memo)
        elif isinstance(src, (set, frozenset)):
            for e in src:
                dst.add(e if memo is None else deepcopy(e, memo))

    def copy(x):
        if isinstance(x, atomic):
            return x
        hook = getattr(x, '__copy__', None)
        if hook is not None:
            return hook()
        cls = type(x)
        if cls is list:
            return list(x)
        if cls is dict:
            return x.copy()
        if cls is set:
            return set(x)
        if cls is frozenset or cls is tuple:
            return x
        if cls is bytearray:
            return bytearray(x)
        if isinstance(x, tuple):
            return x
        if isinstance(x, (list, dict, set)):
            y = _make_like(x)
        else:
            y = object.__new__(cls)
        _copy_state(x, y, None)
        _fill(x, y, None)
        return y

    def deepcopy(x, memo=None):
        if memo is None:
            memo = {}
        i = id(x)
        if i in memo:
            return memo[i]
        if isinstance(x, atomic):
            return x
        hook = getattr(x, '__deepcopy__', None)
        if hook is not None:
            y = hook(memo)
        elif isinstance(x, list):
            y = [] if type(x) is list else _make_like(x)
            memo[i] = y
            if type(x) is not list:
                _copy_state(x, y, memo)
            _fill(x, y, memo)
            return y
        elif isinstance(x, tuple):
            items = [deepcopy(e, memo) for e in x]
            same = True
            for a, b in zip(items, x):
                if a is not b:
                    same = False
                    break
            if same:
                y = x
            elif type(x) is tuple:
                y = tuple(items)
            else:
                y = type(x)(*items)
        elif isinstance(x, dict):
            y = {} if type(x) is dict else _make_like(x)
            memo[i] = y
            if type(x) is not dict:
                _copy_state(x, y, memo)
            _fill(x, y, memo)
            return y
        elif isinstance(x, (set, frozenset)):
            y = type(x)([deepcopy(e, memo) for e in x])
        elif isinstance(x, bytearray):
            y = bytearray(x)
        else:
            y = object.__new__(type(x))
            memo[i] = y
            _copy_state(x, y, memo)
            return y
        memo[i] = y
        return y

    mod = _mpyc_module('copy')
    mod.copy = copy
    mod.deepcopy = deepcopy
    mod.Error = Error
    mod.error = Error
    modules['copy'] = mod
"""

# ── collections (deque / defaultdict / Counter) ───────────────────────────────────────────────

COLLECTIONS_SOURCE = """
def _mpyc_install_collections(modules):
    import collections as real

    def _pairs(args):
        # MicroPython's dict()/update() mishandle mappings, so hand them a plain list of pairs.
        if len(args) == 1 and hasattr(args[0], 'keys'):
            m = args[0]
            return ([(k, m[k]) for k in m.keys()],)
        return args

    class deque:
        def __init__(self, iterable=(), maxlen=None):
            if maxlen is not None and maxlen < 0:
                raise ValueError('maxlen must be non-negative')
            self._a = []
            self._h = 0
            self.maxlen = maxlen
            for x in iterable:
                self.append(x)

        def __len__(self):
            return len(self._a) - self._h

        def __iter__(self):
            return iter(self._a[self._h:])

        def __reversed__(self):
            return iter(self._a[self._h:][::-1])

        def __contains__(self, x):
            for e in self._a[self._h:]:
                if e == x:
                    return True
            return False

        def _index(self, i):
            n = len(self._a) - self._h
            if i < 0:
                i += n
            if i < 0 or i >= n:
                raise IndexError('deque index out of range')
            return self._h + i

        def __getitem__(self, i):
            return self._a[self._index(i)]

        def __setitem__(self, i, v):
            self._a[self._index(i)] = v

        def __delitem__(self, i):
            self._a.pop(self._index(i))
            self._reset_if_empty()

        def _reset_if_empty(self):
            if len(self._a) == self._h:
                self._a = []
                self._h = 0

        def append(self, x):
            if self.maxlen is not None:
                if self.maxlen == 0:
                    return
                if len(self) >= self.maxlen:
                    self.popleft()
            self._a.append(x)

        def appendleft(self, x):
            if self.maxlen is not None:
                if self.maxlen == 0:
                    return
                if len(self) >= self.maxlen:
                    self.pop()
            if self._h > 0:
                self._h -= 1
                self._a[self._h] = x
            else:
                self._a.insert(0, x)

        def pop(self):
            if len(self._a) <= self._h:
                raise IndexError('pop from an empty deque')
            x = self._a.pop()
            self._reset_if_empty()
            return x

        def popleft(self):
            if len(self._a) <= self._h:
                raise IndexError('pop from an empty deque')
            x = self._a[self._h]
            self._a[self._h] = None
            self._h += 1
            if self._h > 32 and self._h * 2 > len(self._a):
                self._a = self._a[self._h:]
                self._h = 0
            self._reset_if_empty()
            return x

        def extend(self, iterable):
            for x in list(iterable):
                self.append(x)

        def extendleft(self, iterable):
            for x in list(iterable):
                self.appendleft(x)

        def clear(self):
            self._a = []
            self._h = 0

        def rotate(self, n=1):
            items = self._a[self._h:]
            if len(items) > 1:
                n = n % len(items)
                if n:
                    items = items[-n:] + items[:-n]
            self._a = items
            self._h = 0

        def reverse(self):
            self._a = self._a[self._h:][::-1]
            self._h = 0

        def count(self, x):
            c = 0
            for e in self._a[self._h:]:
                if e == x:
                    c += 1
            return c

        def index(self, x, start=0, stop=None):
            items = self._a[self._h:]
            if stop is None:
                stop = len(items)
            for i in range(start, min(stop, len(items))):
                if items[i] == x:
                    return i
            raise ValueError('%r is not in deque' % (x,))

        def remove(self, x):
            for i in range(self._h, len(self._a)):
                if self._a[i] == x:
                    self._a.pop(i)
                    self._reset_if_empty()
                    return
            raise ValueError('deque.remove(x): x not in deque')

        def insert(self, i, x):
            if self.maxlen is not None and len(self) >= self.maxlen:
                raise IndexError('deque already at its maximum size')
            items = self._a[self._h:]
            items.insert(i, x)
            self._a = items
            self._h = 0

        def copy(self):
            return deque(self._a[self._h:], self.maxlen)

        def __copy__(self):
            return self.copy()

        def __deepcopy__(self, memo):
            import copy as _copy

            y = deque((), self.maxlen)
            memo[id(self)] = y
            for x in self._a[self._h:]:
                y.append(_copy.deepcopy(x, memo))
            return y

        def __eq__(self, other):
            if not isinstance(other, deque):
                return False
            return list(self) == list(other)

        def __add__(self, other):
            y = self.copy()
            y.extend(other)
            return y

        def __iadd__(self, other):
            self.extend(other)
            return self

        def __repr__(self):
            if self.maxlen is None:
                return 'deque(%r)' % (list(self),)
            return 'deque(%r, maxlen=%d)' % (list(self), self.maxlen)

    class defaultdict(dict):
        def __init__(self, default_factory=None, *args, **kwargs):
            if default_factory is not None and not callable(default_factory):
                raise TypeError('first argument must be callable or None')
            super().__init__(*_pairs(args), **kwargs)
            self.default_factory = default_factory

        def __getitem__(self, key):
            try:
                return super().__getitem__(key)
            except KeyError:
                if self.default_factory is None:
                    raise
                value = self.default_factory()
                self[key] = value
                return value

        def copy(self):
            return defaultdict(self.default_factory, list(self.items()))

        def __copy__(self):
            return self.copy()

        def __deepcopy__(self, memo):
            import copy as _copy

            y = defaultdict(self.default_factory)
            memo[id(self)] = y
            for k in self.keys():
                y[_copy.deepcopy(k, memo)] = _copy.deepcopy(self[k], memo)
            return y

        def __repr__(self):
            body = ', '.join('%r: %r' % (k, self[k]) for k in self.keys())
            return 'defaultdict(%r, {%s})' % (self.default_factory, body)

    class Counter(dict):
        def __init__(self, iterable=None, **kwargs):
            super().__init__()
            self.update(iterable, **kwargs)

        def __getitem__(self, key):
            try:
                return super().__getitem__(key)
            except KeyError:
                return 0

        def __delitem__(self, key):
            self.pop(key, None)

        def update(self, iterable=None, **kwargs):
            if iterable is not None:
                if hasattr(iterable, 'keys'):
                    for k in iterable.keys():
                        self[k] = self.get(k, 0) + iterable[k]
                else:
                    for e in iterable:
                        self[e] = self.get(e, 0) + 1
            for k in kwargs:
                self[k] = self.get(k, 0) + kwargs[k]

        def subtract(self, iterable=None, **kwargs):
            if iterable is not None:
                if hasattr(iterable, 'keys'):
                    for k in iterable.keys():
                        self[k] = self.get(k, 0) - iterable[k]
                else:
                    for e in iterable:
                        self[e] = self.get(e, 0) - 1
            for k in kwargs:
                self[k] = self.get(k, 0) - kwargs[k]

        def most_common(self, n=None):
            items = sorted(self.items(), key=lambda kv: kv[1], reverse=True)
            return items if n is None else items[:n]

        def elements(self):
            for k, c in list(self.items()):
                for _ in range(c):
                    yield k

        def total(self):
            return sum(self.values())

        def copy(self):
            y = Counter()
            for k, v in self.items():
                y[k] = v
            return y

        def __copy__(self):
            return self.copy()

        def __deepcopy__(self, memo):
            import copy as _copy

            y = Counter()
            memo[id(self)] = y
            for k in self.keys():
                y[_copy.deepcopy(k, memo)] = self.get(k, 0)
            return y

        def __add__(self, other):
            y = Counter()
            for k in self.keys():
                v = self[k] + other[k]
                if v > 0:
                    y[k] = v
            for k in other.keys():
                if k not in self and other[k] > 0:
                    y[k] = other[k]
            return y

        def __sub__(self, other):
            y = Counter()
            for k in self.keys():
                v = self[k] - other[k]
                if v > 0:
                    y[k] = v
            for k in other.keys():
                if k not in self and other[k] < 0:
                    y[k] = -other[k]
            return y

        def __repr__(self):
            if len(self) == 0:
                return 'Counter()'
            body = ', '.join('%r: %r' % (k, v) for k, v in self.most_common())
            return 'Counter({%s})' % body

    mod = _mpyc_module('collections', real)
    mod.deque = deque
    mod.defaultdict = defaultdict
    mod.Counter = Counter
    modules['collections'] = mod

    abc = _mpyc_module('collections.abc')
    for n in (
        'Mapping MutableMapping Sequence MutableSequence Iterable Iterator Callable Hashable Set MutableSet '
        'Sized Container Collection Generator Awaitable Reversible'
    ).split():
        setattr(abc, n, _MpycAlias(n))
    mod.abc = abc
    modules['collections.abc'] = abc
"""

# ── heapq ─────────────────────────────────────────────────────────────────────────────────────

HEAPQ_SOURCE = """
def _mpyc_install_heapq(modules):
    import heapq as real

    def heappushpop(heap, item):
        real.heappush(heap, item)
        return real.heappop(heap)

    def heapreplace(heap, item):
        smallest = real.heappop(heap)
        real.heappush(heap, item)
        return smallest

    def nlargest(n, iterable, key=None):
        return sorted(iterable, key=key, reverse=True)[:n]

    def nsmallest(n, iterable, key=None):
        return sorted(iterable, key=key)[:n]

    def merge(*iterables, key=None, reverse=False):
        items = []
        for it in iterables:
            items.extend(it)
        for x in sorted(items, key=key, reverse=reverse):
            yield x

    mod = _mpyc_module('heapq', real)
    mod.heappushpop = heappushpop
    mod.heapreplace = heapreplace
    mod.nlargest = nlargest
    mod.nsmallest = nsmallest
    mod.merge = merge
    modules['heapq'] = mod
"""

# ── functools ─────────────────────────────────────────────────────────────────────────────────

FUNCTOOLS_SOURCE = """
def _mpyc_install_functools(modules):
    _missing = object()

    class partial:
        def __init__(self, func, *args, **keywords):
            self.func = func
            self.args = args
            self.keywords = keywords

        def __call__(self, *args, **keywords):
            kw = dict(self.keywords)
            kw.update(keywords)
            return self.func(*self.args, *args, **kw)

    def reduce(function, iterable, initial=_missing):
        it = iter(iterable)
        if initial is _missing:
            try:
                value = next(it)
            except StopIteration:
                raise TypeError('reduce() of empty iterable with no initial value')
        else:
            value = initial
        for element in it:
            value = function(value, element)
        return value

    def _make_cache(func, maxsize):
        cache = {}

        def wrapper(*args, **kwargs):
            if maxsize == 0:
                return func(*args, **kwargs)
            key = args if not kwargs else (args, tuple(sorted(kwargs.items())))
            if key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            cache[key] = result
            return result

        def cache_clear():
            cache.clear()

        try:
            wrapper.cache_clear = cache_clear
        except Exception:
            pass
        return wrapper

    def lru_cache(maxsize=128, typed=False):
        if callable(maxsize):
            return _make_cache(maxsize, 128)

        def decorator(func):
            return _make_cache(func, maxsize)

        return decorator

    def cache(func):
        return _make_cache(func, None)

    def wraps(wrapped, assigned=(), updated=()):
        def decorator(wrapper):
            try:
                wrapper.__name__ = wrapped.__name__
            except Exception:
                pass
            return wrapper

        return decorator

    def update_wrapper(wrapper, wrapped, assigned=(), updated=()):
        return wraps(wrapped)(wrapper)

    def cmp_to_key(mycmp):
        class K:
            def __init__(self, obj):
                self.obj = obj

            def __lt__(self, other):
                return mycmp(self.obj, other.obj) < 0

            def __gt__(self, other):
                return mycmp(self.obj, other.obj) > 0

            def __eq__(self, other):
                return mycmp(self.obj, other.obj) == 0

            def __le__(self, other):
                return mycmp(self.obj, other.obj) <= 0

            def __ge__(self, other):
                return mycmp(self.obj, other.obj) >= 0

        return K

    def total_ordering(cls):
        has = lambda name: name in cls.__dict__
        if has('__lt__'):
            if not has('__gt__'):
                cls.__gt__ = lambda a, b: not (a < b) and not (a == b)
            if not has('__le__'):
                cls.__le__ = lambda a, b: (a < b) or (a == b)
            if not has('__ge__'):
                cls.__ge__ = lambda a, b: not (a < b)
        elif has('__gt__'):
            if not has('__lt__'):
                cls.__lt__ = lambda a, b: not (a > b) and not (a == b)
            if not has('__ge__'):
                cls.__ge__ = lambda a, b: (a > b) or (a == b)
            if not has('__le__'):
                cls.__le__ = lambda a, b: not (a > b)
        elif has('__le__'):
            if not has('__lt__'):
                cls.__lt__ = lambda a, b: (a <= b) and not (a == b)
            if not has('__gt__'):
                cls.__gt__ = lambda a, b: not (a <= b)
            if not has('__ge__'):
                cls.__ge__ = lambda a, b: not (a <= b) or (a == b)
        elif has('__ge__'):
            if not has('__gt__'):
                cls.__gt__ = lambda a, b: (a >= b) and not (a == b)
            if not has('__lt__'):
                cls.__lt__ = lambda a, b: not (a >= b)
            if not has('__le__'):
                cls.__le__ = lambda a, b: not (a >= b) or (a == b)
        return cls

    mod = _mpyc_module('functools')
    mod.partial = partial
    mod.reduce = reduce
    mod.lru_cache = lru_cache
    mod.cache = cache
    mod.wraps = wraps
    mod.update_wrapper = update_wrapper
    mod.cmp_to_key = cmp_to_key
    mod.total_ordering = total_ordering
    modules['functools'] = mod
"""

# ── itertools ─────────────────────────────────────────────────────────────────────────────────

ITERTOOLS_SOURCE = """
def _mpyc_install_itertools(modules):
    class chain:
        def __init__(self, *iterables):
            self._its = iterables
            self._gen = None

        def __iter__(self):
            return self

        def __next__(self):
            if self._gen is None:
                self._gen = self._run()
            return next(self._gen)

        def _run(self):
            for it in self._its:
                for x in it:
                    yield x

        @classmethod
        def from_iterable(cls, iterables):
            c = cls()
            c._its = iterables
            return c

    def count(start=0, step=1):
        n = start
        while True:
            yield n
            n += step

    def cycle(iterable):
        saved = []
        for x in iterable:
            yield x
            saved.append(x)
        while saved:
            for x in saved:
                yield x

    def repeat(obj, times=None):
        if times is None:
            while True:
                yield obj
        else:
            for _ in range(times):
                yield obj

    def islice(iterable, *args):
        if len(args) == 1:
            start, stop, step = 0, args[0], 1
        elif len(args) == 2:
            start, stop, step = args[0], args[1], 1
        else:
            start, stop, step = args[0], args[1], args[2]
        start = 0 if start is None else start
        step = 1 if step is None else step
        nexti = start
        for i, element in enumerate(iterable):
            if stop is not None and i >= stop:
                return
            if i == nexti:
                yield element
                nexti += step

    def accumulate(iterable, func=None, initial=None):
        it = iter(iterable)
        total = initial
        if initial is None:
            try:
                total = next(it)
            except StopIteration:
                return
        yield total
        for element in it:
            total = func(total, element) if func is not None else total + element
            yield total

    def product(*iterables, repeat=1):
        pools = [tuple(p) for p in iterables] * repeat
        result = [[]]
        for pool in pools:
            result = [x + [y] for x in result for y in pool]
        for prod in result:
            yield tuple(prod)

    def permutations(iterable, r=None):
        pool = tuple(iterable)
        n = len(pool)
        r = n if r is None else r
        if r > n:
            return
        indices = list(range(n))
        cycles = list(range(n, n - r, -1))
        yield tuple([pool[k] for k in indices[:r]])
        while n:
            for i in range(r - 1, -1, -1):
                cycles[i] -= 1
                if cycles[i] == 0:
                    indices[i:] = indices[i + 1:] + indices[i:i + 1]
                    cycles[i] = n - i
                else:
                    j = cycles[i]
                    indices[i], indices[-j] = indices[-j], indices[i]
                    yield tuple([pool[k] for k in indices[:r]])
                    break
            else:
                return

    def combinations(iterable, r):
        pool = tuple(iterable)
        n = len(pool)
        if r > n:
            return
        indices = list(range(r))
        yield tuple([pool[k] for k in indices])
        while True:
            for i in range(r - 1, -1, -1):
                if indices[i] != i + n - r:
                    break
            else:
                return
            indices[i] += 1
            for j in range(i + 1, r):
                indices[j] = indices[j - 1] + 1
            yield tuple([pool[k] for k in indices])

    def combinations_with_replacement(iterable, r):
        pool = tuple(iterable)
        n = len(pool)
        if not n and r:
            return
        indices = [0] * r
        yield tuple([pool[k] for k in indices])
        while True:
            for i in range(r - 1, -1, -1):
                if indices[i] != n - 1:
                    break
            else:
                return
            indices[i:] = [indices[i] + 1] * (r - i)
            yield tuple([pool[k] for k in indices])

    def zip_longest(*iterables, fillvalue=None):
        lists = [list(it) for it in iterables]
        if not lists:
            return
        longest = max([len(items) for items in lists])
        for i in range(longest):
            yield tuple([items[i] if i < len(items) else fillvalue for items in lists])

    def groupby(iterable, key=None):
        keyfunc = (lambda x: x) if key is None else key
        group = None
        current = None
        for item in iterable:
            k = keyfunc(item)
            if group is None or k != current:
                if group is not None:
                    yield (current, iter(group))
                group = []
                current = k
            group.append(item)
        if group is not None:
            yield (current, iter(group))

    def starmap(function, iterable):
        for args in iterable:
            yield function(*args)

    def takewhile(predicate, iterable):
        for x in iterable:
            if predicate(x):
                yield x
            else:
                return

    def dropwhile(predicate, iterable):
        dropping = True
        for x in iterable:
            if dropping and predicate(x):
                continue
            dropping = False
            yield x

    def filterfalse(predicate, iterable):
        for x in iterable:
            if not (bool(x) if predicate is None else predicate(x)):
                yield x

    def compress(data, selectors):
        for d, s in zip(data, selectors):
            if s:
                yield d

    def pairwise(iterable):
        it = iter(iterable)
        try:
            a = next(it)
        except StopIteration:
            return
        for b in it:
            yield (a, b)
            a = b

    mod = _mpyc_module('itertools')
    mod.chain = chain
    mod.count = count
    mod.cycle = cycle
    mod.repeat = repeat
    mod.islice = islice
    mod.accumulate = accumulate
    mod.product = product
    mod.permutations = permutations
    mod.combinations = combinations
    mod.combinations_with_replacement = combinations_with_replacement
    mod.zip_longest = zip_longest
    mod.groupby = groupby
    mod.starmap = starmap
    mod.takewhile = takewhile
    mod.dropwhile = dropwhile
    mod.filterfalse = filterfalse
    mod.compress = compress
    mod.pairwise = pairwise
    modules['itertools'] = mod
"""

# ── bisect ────────────────────────────────────────────────────────────────────────────────────

BISECT_SOURCE = """
def _mpyc_install_bisect(modules):
    def bisect_left(a, x, lo=0, hi=None, key=None):
        if lo < 0:
            raise ValueError('lo must be non-negative')
        if hi is None:
            hi = len(a)
        while lo < hi:
            mid = (lo + hi) // 2
            item = a[mid] if key is None else key(a[mid])
            if item < x:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def bisect_right(a, x, lo=0, hi=None, key=None):
        if lo < 0:
            raise ValueError('lo must be non-negative')
        if hi is None:
            hi = len(a)
        while lo < hi:
            mid = (lo + hi) // 2
            item = a[mid] if key is None else key(a[mid])
            if x < item:
                hi = mid
            else:
                lo = mid + 1
        return lo

    def insort_left(a, x, lo=0, hi=None, key=None):
        k = x if key is None else key(x)
        a.insert(bisect_left(a, k, lo, hi, key), x)

    def insort_right(a, x, lo=0, hi=None, key=None):
        k = x if key is None else key(x)
        a.insert(bisect_right(a, k, lo, hi, key), x)

    mod = _mpyc_module('bisect')
    mod.bisect_left = bisect_left
    mod.bisect_right = bisect_right
    mod.bisect = bisect_right
    mod.insort_left = insort_left
    mod.insort_right = insort_right
    mod.insort = insort_right
    modules['bisect'] = mod
"""

# ── abc ───────────────────────────────────────────────────────────────────────────────────────

ABC_SOURCE = """
def _mpyc_install_abc(modules):
    class ABC:
        pass

    def abstractmethod(func):
        return func

    mod = _mpyc_module('abc')
    mod.ABC = ABC
    mod.ABCMeta = type
    mod.abstractmethod = abstractmethod
    mod.abstractproperty = property
    modules['abc'] = mod
"""

SHIM_SOURCES: dict[str, str] = {
    "typing": TYPING_SOURCE,
    "copy": COPY_SOURCE,
    "collections": COLLECTIONS_SOURCE,
    "heapq": HEAPQ_SOURCE,
    "functools": FUNCTOOLS_SOURCE,
    "itertools": ITERTOOLS_SOURCE,
    "bisect": BISECT_SOURCE,
    "abc": ABC_SOURCE,
}

# Modules MicroPython lacks entirely: any import of them needs the shim.
_ALWAYS_SHIMMED = frozenset({"typing", "copy", "functools", "itertools", "bisect", "abc"})
# Modules MicroPython has in a reduced form: shim only when the solution reaches for a missing name.
_PARTIALLY_SHIMMED: dict[str, frozenset[str]] = {
    "collections": frozenset({"deque", "defaultdict", "Counter", "abc"}),
    "heapq": frozenset({"nlargest", "nsmallest", "merge", "heappushpop", "heapreplace"}),
}


def required_shims(code: str) -> list[str]:
    """Returns the shim modules a solution needs, based on its import statements."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    needed: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in _ALWAYS_SHIMMED or top in _PARTIALLY_SHIMMED:
                    needed.add(top)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            top = node.module.split(".")[0]
            imported = {alias.name for alias in node.names}
            if top in _ALWAYS_SHIMMED:
                needed.add(top)
            elif top in _PARTIALLY_SHIMMED:
                if node.module != top or "*" in imported or imported & _PARTIALLY_SHIMMED[top]:
                    needed.add(top)
    return [name for name in SHIM_SOURCES if name in needed]


def build_prelude(code: str) -> str:
    """MicroPython source that installs the shims needed by ``code`` (empty when none are needed)."""
    names = required_shims(code)
    if not names:
        return ""
    parts = ["import sys as _mpyc_sys", BASE_SOURCE]
    parts.extend(SHIM_SOURCES[name] for name in names)
    for name in names:
        parts.append(f"try:\n    _mpyc_install_{name}(_mpyc_sys.modules)\nexcept Exception:\n    pass\n")
    return "\n".join(parts) + "\n"


def load_shims_for_testing(*names: str) -> dict[str, object]:
    """Executes shim sources under the running interpreter and returns ``{module name: shim module}``.

    Used by the test-suite to compare the shims with the real CPython standard library.
    """
    namespace: dict[str, object] = {}
    exec(BASE_SOURCE, namespace)  # noqa: S102 - trusted, in-repo source
    modules: dict[str, object] = {}
    for name in names:
        exec(SHIM_SOURCES[name], namespace)  # noqa: S102
        namespace[f"_mpyc_install_{name}"](modules)  # type: ignore[operator]
    return modules
