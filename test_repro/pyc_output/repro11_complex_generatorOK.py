# Source Generated with Decompyle++ (Python version)
# File: repro11_complex_generator.pyc (Python 3.11)

__doc__ = 'Repro 11: yield + yield from unpack + more yield (complex generator)'
def f():
    x = yield init()
    yield process(x)
    a, b = yield from compute()
    yield finish(a, b)
code = f.__code__
import dis
dis.dis(code)
