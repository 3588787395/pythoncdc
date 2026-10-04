# Source Generated with Decompyle++ (Python version)
# File: n10_03_simple_global.pyc (Python 3.11)

global TOTAL
__doc__ = 'n10_03: 负对照 — 最简 global 读写（必须 MATCH）'
TOTAL = 0
def simple_global(n):
    global TOTAL
    if n > 0:
        TOTAL += n
    return TOTAL
