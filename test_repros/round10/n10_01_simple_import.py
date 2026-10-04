"""n10_01: 负对照 — 最简 import / dotted import（必须 MATCH）"""
import os
import sys as s


def simple_import_use(p):
    if p:
        return os.path.join(p, "x")
    return s.version
