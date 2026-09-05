# Source Generated with Decompyle++ (Python version)
# File: repro08_unpack_then_return.pyc (Python 3.11)

__doc__ = 'Repro 8: yield from with unpack + return'
def f():
    ip, port = yield from get_addr()
    return (ip, port)
code = f.__code__
import dis
dis.dis(code)
