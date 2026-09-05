"""Repro 10: yield from with 4-element unpack"""
def f():
    a, b, c, d = yield from gen()

code = f.__code__
import dis
dis.dis(code)
