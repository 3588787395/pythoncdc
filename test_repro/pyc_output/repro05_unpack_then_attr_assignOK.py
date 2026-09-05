# Source Generated with Decompyle++ (Python version)
# File: repro05_unpack_then_attr_assign.pyc (Python 3.11)

__doc__ = 'Repro 5: yield from with unpack + subsequent attribute assignment'
def f():
    ip, port = yield from get_addr()
    self.host = ip
    self.port = port
code = f.__code__
import dis
dis.dis(code)
