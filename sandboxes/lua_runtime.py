"""Lua Sandbox на базе Lupa (LuaJIT / Lua 5.4).

Создаёт среду выполнения без доступа к вводу-выводу, файловой системе и системным вызовам ОС.
"""

from lupa import LuaRuntime


def create_lua_sandbox() -> LuaRuntime:
    """Создаёт изолированную среду Lua без доступа к ОС и файловой системе."""
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
