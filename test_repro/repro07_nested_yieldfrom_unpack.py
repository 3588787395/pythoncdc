"""Repro 7: yield from with unpack in nested function"""
def outer():
    def inner():
        x, y = yield from gen()
    return inner

code = outer().__code__
import dis
dis.dis(code)
