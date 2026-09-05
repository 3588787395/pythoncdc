# Source Generated with Decompyle++ (Python version)
# File: repro02_yield_from_unpack3.pyc (Python 3.11)

__doc__ = 'Repro 2: yield from with 3-element unpack'
def f():
    a, b, c = yield from g()
code = f.__code__
import dis
dis.dis(code)
