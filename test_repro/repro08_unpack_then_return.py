"""Repro 8: yield from with unpack + return"""
def f():
    ip, port = yield from get_addr()
    return (ip, port)

code = f.__code__
import dis
dis.dis(code)
