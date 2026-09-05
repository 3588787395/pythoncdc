"""Repro 1: Basic yield from with unpack assignment - the core bug"""
import types

async def _gen():
    pass

def f():
    x = yield _gen()
    a, b = yield from _gen()

code = f.__code__
print("co_flags:", hex(code.co_flags))
print("co_varnames:", code.co_varnames)

import dis
dis.dis(code)
