"""Repro 5: yield from with unpack + subsequent attribute assignment"""
def f():
    ip, port = yield from get_addr()
    self.host = ip
    self.port = port

code = f.__code__
import dis
dis.dis(code)
