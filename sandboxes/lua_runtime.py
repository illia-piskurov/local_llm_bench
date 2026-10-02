"""Lua Sandbox powered by Lupa (LuaJIT / Lua 5.4).

Creates an execution environment without access to I/O, file system, operating system calls,
or Python bridge reflection, with instruction-bounded infinite loop protection.
"""

from collections.abc import Callable
from typing import Any

from lupa import LuaRuntime

DEFAULT_LUA_MAX_INSTRUCTIONS = 20_000_000


def _deny_python_attributes(obj: Any, attr_name: str, is_setting: bool) -> str:
    """Blocks Lua code from accessing any attributes or methods of Python objects."""
    raise AttributeError(f"Access to Python attribute '{attr_name}' is forbidden in sandbox")


def create_lua_sandbox(
    attribute_filter: Callable[[Any, str, bool], str] | None = None,
    max_instructions: int = DEFAULT_LUA_MAX_INSTRUCTIONS,
) -> LuaRuntime:
    """Creates an isolated Lua environment with instruction bounds, revoked OS/FS, and Python bridge access."""
    filter_fn = attribute_filter if attribute_filter is not None else _deny_python_attributes
    runtime = LuaRuntime(
        unpack_returned_tuples=True,
        register_eval=False,
        register_builtins=False,
        attribute_filter=filter_fn,
    )
    init_code = f"""
    local instruction_count = 0
    local max_inst = {max_instructions}
    local set_hook = debug.sethook

    local function step_hook()
        instruction_count = instruction_count + 10000
        if instruction_count > max_inst then
            set_hook(function() error("Execution instruction limit exceeded (infinite loop protection)") end, "", 1)
            error("Execution instruction limit exceeded (infinite loop protection)")
        end
    end

    set_hook(step_hook, "", 10000)

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
    """
    runtime.execute(init_code)
    return runtime
