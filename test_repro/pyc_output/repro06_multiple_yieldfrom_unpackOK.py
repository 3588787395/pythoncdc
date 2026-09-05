# Source Generated with Decompyle++ (Python version)
# File: repro06_multiple_yieldfrom_unpack.pyc (Python 3.11)

__doc__ = 'Repro 6: multiple yield from with unpack'
def f():
    a, b = yield from g1()
    c, d = yield from g2()
code = f.__code__
import dis
dis.dis(code)
