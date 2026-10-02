"""Lua Sandbox powered by Lupa (LuaJIT / Lua 5.4).

Creates an execution environment without access to I/O, file system, or operating system calls.
"""

from lupa import LuaRuntime


def create_lua_sandbox() -> LuaRuntime:
    """Creates an isolated Lua environment with revoked OS and file system access."""
    runtime = LuaRuntime(unpack_returned_tuples=True, register_builtins=False)
    runtime.execute("""
    os = nil
    io = nil
    package = nil
    debug = nil
    dofile = nil
    loadfile = nil
    """)
    return runtime
