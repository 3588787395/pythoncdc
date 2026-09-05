# Source Generated with Decompyle++ (Python version)
# File: repro04_yield_from_simple_assign.pyc (Python 3.11)

__doc__ = 'Repro 4: yield from with simple assignment (existing case, regression test)'
def f():
    result = yield from g()
code = f.__code__
import dis
dis.dis(code)
