"""Repro 9: yield from as expression (no assignment) - existing case"""
def f():
    yield from g()

code = f.__code__
import dis
dis.dis(code)
