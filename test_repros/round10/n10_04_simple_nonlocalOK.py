# Source Generated with Decompyle++ (Python version)
# File: n10_04_simple_nonlocal.pyc (Python 3.11)

__doc__ = 'n10_04: 负对照 — 最简 nonlocal 闭包（必须 MATCH）'
def simple_nonlocal():
    n = 0
    def inc():
        nonlocal n
        n += 1
        return n
    return inc
