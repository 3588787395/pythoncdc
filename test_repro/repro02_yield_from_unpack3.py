"""Repro 2: yield from with 3-element unpack"""
def f():
    a, b, c = yield from g()

code = f.__code__
import dis
dis.dis(code)
