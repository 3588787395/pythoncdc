"""Repro 3: yield then yield-from with unpack (like dockerspawner)"""
def f():
    yield start_server()
    ip, port = yield from get_addr()

code = f.__code__
import dis
dis.dis(code)
