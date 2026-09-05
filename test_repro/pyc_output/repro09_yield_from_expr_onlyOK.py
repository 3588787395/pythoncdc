# Source Generated with Decompyle++ (Python version)
# File: repro09_yield_from_expr_only.pyc (Python 3.11)

__doc__ = 'Repro 9: yield from as expression (no assignment) - existing case'
def f():
    yield from g()
code = f.__code__
import dis
dis.dis(code)
