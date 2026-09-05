"""Repro 6: multiple yield from with unpack"""
def f():
    a, b = yield from g1()
    c, d = yield from g2()

code = f.__code__
import dis
dis.dis(code)
