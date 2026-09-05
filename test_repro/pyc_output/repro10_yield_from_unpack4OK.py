# Source Generated with Decompyle++ (Python version)
# File: repro10_yield_from_unpack4.pyc (Python 3.11)

__doc__ = 'Repro 10: yield from with 4-element unpack'
def f():
    a, b, c, d = yield from gen()
code = f.__code__
import dis
dis.dis(code)
