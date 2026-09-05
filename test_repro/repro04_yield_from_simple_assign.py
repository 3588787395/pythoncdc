"""Repro 4: yield from with simple assignment (existing case, regression test)"""
def f():
    result = yield from g()

code = f.__code__
import dis
dis.dis(code)
