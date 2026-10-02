"""Lua Sandbox powered by Lupa (LuaJIT / Lua 5.4).

Creates an execution environment without access to I/O, file system, operating system calls,
or Python bridge reflection.
"""

from collections.abc import Callable
from typing import Any

from lupa import LuaRuntime


def _deny_python_attributes(obj: Any, attr_name: str, is_setting: bool) -> str:
    """Blocks Lua code from accessing any attributes or methods of Python objects."""
    raise AttributeError(f"Access to Python attribute '{attr_name}' is forbidden in sandbox")


def create_lua_sandbox(attribute_filter: Callable[[Any, str, bool], str] | None = None) -> LuaRuntime:
    """Creates an isolated Lua environment with revoked OS, file system, and Python bridge access."""
    filter_fn = attribute_filter if attribute_filter is not None else _deny_python_attributes
    runtime = LuaRuntime(
        unpack_returned_tuples=True,
        register_eval=False,
        register_builtins=False,
        attribute_filter=filter_fn,
    )
    runtime.execute("""
    os = nil
    io = nil
    package = nil
    debug = nil
    dofile = nil
    loadfile = nil
    load = nil
    loadstring = nil
    require = nil
    python = nil
    """)
    return runtime
