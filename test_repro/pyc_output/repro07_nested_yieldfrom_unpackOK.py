# Source Generated with Decompyle++ (Python version)
# File: repro07_nested_yieldfrom_unpack.pyc (Python 3.11)

__doc__ = 'Repro 7: yield from with unpack in nested function'
def outer():
    def inner():
        x, y = yield from gen()
    return inner
code = outer().__code__
import dis
dis.dis(code)
