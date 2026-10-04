# Source Generated with Decompyle++ (Python version)
# File: n10_01_simple_import.pyc (Python 3.11)

__doc__ = 'n10_01: 负对照 — 最简 import / dotted import（必须 MATCH）'
import os
import sys as s
def simple_import_use(p):
    if p:
        return os.path.join(p, 'x')
    else:
        return s.version
