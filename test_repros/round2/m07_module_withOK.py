# Source Generated with Decompyle++ (Python version)
# File: m07_module_with.pyc (Python 3.11)

__doc__ = 'm07: module-level with, multi-context and deep nest.'
with _A() as a, _B() as b:
    PAIR = (a, b)
with _A() as c:
    for i in range(2):
        try:
            if i:
                with _B() as d:
                    DEEP = (c, d, i)
        finally:
            FIN = i
